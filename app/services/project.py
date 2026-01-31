import json
import os
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.projects import Project #SQL Alchemy Models
from app.schemas.project import ProjectCreate, ProjectResponse

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

        all_matches = [
            {
                "id": proj.id,
                "name": proj.name,
                "description": proj.description,
                "created_at": proj.created_at,
                "updated_at": proj.updated_at,
            } for proj in projects]
        
        if sort_by:
            reverse = (order == "desc")
            # Handle กรณี field ไม่มีอยู่จริง หรือต้องการ sort date
            all_matches.sort(key=lambda x: (x.get(sort_by) or ""), reverse=reverse)
        
        # 2. นับจำนวนทั้งหมด (สำหรับ Pagination UI)
        total_count = len(all_matches)
            
        # 3. คำนวณ Pagination Logic
        import math
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
            "email": new_project_db.user_email,
            "created_at": new_project_db.created_at,
            "updated_at": new_project_db.updated_at
        }
        
        return new_project
    
    def update_project(self, project_id: int, project_in: ProjectCreate, user_id: str) -> Optional[dict]:
        """Service: อัปเดตโปรเจกต์"""
        projects = self._read_json()
        for proj in projects:
            if proj["id"] == project_id and proj["email"] == user_id:
                proj["name"] = project_in.name
                proj["description"] = project_in.description
                proj["updated_at"] = datetime.now().isoformat()
                self._save_json(projects)
                return proj
        return None
    
    def delete_project(self, project_id: int) -> bool:
        """Service: ลบโปรเจกต์"""
        projects = self._read_json()
        for i, proj in enumerate(projects):
            if proj["id"] == project_id:
                del projects[i]
                self._save_json(projects)
                return True
        return False

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_service = ProjectService()