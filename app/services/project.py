import json
import os
import math
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.projects import Project #SQL Alchemy Models
from app.schemas.project import ProjectCreate, ProjectResponse

from app.schemas.project import ProjectCreate
from app.schemas.userauthen import UserInfo

from app.services.project_member import project_member_service
from app.services.project_tag import project_tag_service
from app.services.tag import tag_service
from app.services.userauthen import userauthen_service
from app.services.asset import asset_service
from app.services.vulnerability import vuln_service

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "projects.json")

class ProjectService:
    
    def _ensure_dummy_folder_exists(self):
        """ตรวจสอบว่ามี folder dummy_data หรือยัง ถ้าไม่มีให้สร้าง"""
        folder = os.path.dirname(JSON_FILE_PATH)
        if not os.path.exists(folder):
            os.makedirs(folder)

    def _read_json(self) -> List[dict]:
        """อ่านข้อมูลจากไฟล์ JSON"""
        if not os.path.exists(JSON_FILE_PATH):
            return []
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] # ถ้าไฟล์เสียหรือว่างเปล่า ให้คืนค่า list ว่าง

    def _save_json(self, data: List[dict]):
        """บันทึกข้อมูลลงไฟล์ JSON"""
        self._ensure_dummy_folder_exists()
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
            # default=str ช่วยแปลง datetime เป็น string อัตโนมัติ
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    async def get_all_projects(self, user_id: str, page: int, size: int, db: AsyncSession, sort_by: str = None, order: str = "asc", search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        query = sa.select(Project).where(Project.user_email == user_id)
        result = await db.execute(query)
        projects = result.scalars().all()
        projects = self._read_json()

        user_member_roles = project_member_service.get_user_roles_map(user_id)
        
        # 1. กรอง User
        all_matches = []
        for proj in projects:
            user_role = None

            if proj["email"] == user_id:
                user_role = "owner"
            elif proj["id"] in user_member_roles:
                user_role = user_member_roles[proj["id"]]

            if not user_role:
                continue

            asset_cnt = asset_service.cnt_asset_by_project_id(proj["id"])
            asset_ids = asset_service.get_asset_ids_by_project_id(proj["id"])
            vuln_cnt = vuln_service.cnt_vuln_by_asset_id(asset_ids)

            tag_ids = project_tag_service.get_all_tag_ids(proj["id"])

            tag = []

            for id in tag_ids:
                t = tag_service.get_tag_by_id(id)
                tag.append({
                    "name": t["name"],
                    "text_color": t["text_color"],
                    "bg_color": t["bg_color"]
                })
            
            proj_with_role = {
                **proj, 
                "role": user_role,
                "assets_cnt": asset_cnt,
                "vuln_cnt": vuln_cnt,
                "tags": tag             
            }

            if search and search.lower() not in proj["name"].lower():
                continue
            if filter == "owner" and user_role != "owner":
                continue
            if filter == "pentester" and user_role != "pentester":
                continue
            if filter == "developer" and user_role != "developer":
                continue

            all_matches.append(proj_with_role)

        all_matches = [
            {
                "id": proj.id,
                "name": proj.name,
                "description": proj.description,
                "created_at": proj.created_at,
                "updated_at": proj.updated_at,
            } for proj in projects
        ]
        
        if sort_by:
            reverse = (order == "desc")
            # Handle กรณี field ไม่มีอยู่จริง หรือต้องการ sort date
            all_matches.sort(key=lambda x: (x.get(sort_by) or ""), reverse=reverse)
        
        # 2. นับจำนวนทั้งหมด (สำหรับ Pagination UI)
        total_count = len(all_matches)
            
        # 3. คำนวณ Pagination Logic
        total_pages = math.ceil(total_count / size)
        
        offset = (page - 1) * size
        
        # --- จุดที่ต้องแก้: ตัดข้อมูล (Slicing) ---
        # ใช้ Python Slice [start : end]
        paginated_items = all_matches[offset : offset + size]

        return {
            "total": total_count,      # จำนวนทั้งหมด (เช่น 50)
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "items": paginated_items   # ส่งกลับเฉพาะ 10 ตัวของหน้านั้น (ไม่ใช่ทั้งหมด)
        }
    
    async def get_project_by_id(self, project_id:int, user_id: str, db: AsyncSession):
        query = sa.select(Project).where(Project.id == project_id and Project.user_email == user_id)
        result = await db.execute(query)
        project = result.scalar_one_or_none()
        
        if project:
            return {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            }
            
        return None

    def get_project_by_id(self, project_id:int):
        projects = self._read_json()

        for proj in projects:
            if proj["id"] == project_id:
                return proj

        return None
    
    def get_owner_info_by_project_id(self, project_id: int):
        """Get Owner Info by Project ID"""

        projects = self._read_json()
        for proj in projects:
            if proj["id"] == project_id:
                user = userauthen_service.get_user_by_id(proj["email"])

                user_info = UserInfo(
                    email=user["email"],
                    firstname=user["firstname"],
                    lastname=user["lastname"],
                    role="owner",
                    joinned_at=proj["created_at"]
                )
                return user_info
            
        return None

    async def create_project(self, name: str, description: str, user_id: str, db: AsyncSession) -> dict:
        """Service: สร้างโปรเจกต์ใหม่"""
        new_project_db = Project(
            name = name,
            user_email = user_id,
            description = description
        )

        try:
            db.add(new_project_db)
            await db.commit()
            # refresh to get the DB generated content such as created_at
            await db.refresh(new_project_db)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create project")
        
        new_project = {
            "id": new_project_db.id,
            "name": new_project_db.name,
            "description": new_project_db.description,
            "created_at": new_project_db.created_at,
            "updated_at": new_project_db.updated_at
        }
        
        return new_project
    
    async def update_project(self, project_id: int, project_in: ProjectCreate, user_id: str, db: AsyncSession) -> Optional[dict]:
        """Service: อัปเดตโปรเจกต์"""
        query = sa.select(Project).where(Project.id == project_id and Project.user_email == user_id)
        result = await db.execute(query)
        project_db = result.scalar_one_or_none

        if not project_db:
            return None
        project_db.name = project_in.name
        project_db.description = project_in.description

        await db.commit()
        await db.refresh(project_db)

        returned_project = {
            "id": returned_project.id,
            "name": returned_project.name,
            "description": returned_project.description,
            "created_at": returned_project.created_at,
            "updated_at": returned_project.updated_at
        }

        return returned_project
    
    async def delete_project(self, project_id: int, db: AsyncSession) -> bool:
        """Service: ลบโปรเจกต์"""
        query = sa.select(Project).where(Project.id == project_id)
        result = await db.execute(query)
        project = result.scalar_one_or_none

        if not project:
            return False
        
        db.delete(project)
        await db.commit()
        return True

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_service = ProjectService()