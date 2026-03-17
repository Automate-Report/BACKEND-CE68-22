import math
from typing import Optional
from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.projects import Project #SQL Alchemy Models
from app.schemas.project import ProjectCreate

from app.schemas.project import ProjectCreate
from app.schemas.userauthen import UserInfo

from app.services.project_member import project_member_service
from app.services.project_tag import project_tag_service
from app.services.tag import tag_service
from app.services.userauthen import userauthen_service
from app.services.asset import asset_service
from app.services.vulnerability import vuln_service

class ProjectService:
    async def get_all_projects(self, user_id: str, page: int, size: int, db: AsyncSession, sort_by: str = None, order: str = "asc", search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        query = sa.select(Project).where(Project.user_email == user_id)
        result = await db.execute(query)
        projects = result.scalars().all()

        user_member_roles = project_member_service.get_user_roles_map(user_id)
        
        # 1. กรอง User
        all_matches = []
        for proj in projects:
            user_role = None

            if proj.user_email == user_id:
                user_role = "owner"
            elif proj.user_email in user_member_roles:
                user_role = user_member_roles[proj.user_email]

            if not user_role:
                continue

            asset_cnt = asset_service.cnt_asset_by_project_id(proj.id)
            asset_ids = asset_service.get_asset_ids_by_project_id(proj.id)
            vuln_cnt = vuln_service.cnt_vuln_by_asset_id(asset_ids)

            tag_ids = await project_tag_service.get_all_tag_ids(proj.id, db)

            tag = []

            for id in tag_ids:
                t = tag_service.get_tag_by_id(id)
                tag.append({
                    "name": t["name"],
                    "text_color": t["text_color"],
                    "bg_color": t["bg_color"]
                })
            print(proj)
            proj_with_role = {
                "id": proj.id,
                "name": proj.name,
                "description": proj.description,
                "role": user_role,
                "assets_cnt": asset_cnt,
                "vuln_cnt": vuln_cnt,
                "tags": tag,
                "created_at": proj.created_at,
                "updated_at": proj.updated_at      
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

        print(all_matches)

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

    async def get_project_by_id(self, project_id:int, db: AsyncSession):
        query = sa.select(Project).where(Project.id == project_id)

        result = await db.execute(query)

        project = result.scalar_one_or_none()

        if not project: return None

        return project
    
    async def get_owner_info_by_project_id(self, project_id: int, db: AsyncSession):
        """Get Owner Info by Project ID"""
        query = sa.select(Project).where(
            Project.id == project_id
        )
        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            return None

        user = userauthen_service.get_user_by_id(project.user_email)

        user_info = UserInfo(
            email=user["email"],
            firstname=user["firstname"],
            lastname=user["lastname"],
            role="owner",
            joinned_at=project.created_at
        )
        return user_info

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
        query = sa.select(Project).where(
            Project.id == project_id,
            Project.user_email == user_id
        )
        result = await db.execute(query)
        project_db = result.scalar_one_or_none()

        if not project_db:
            return None
        project_db.name = project_in.name
        project_db.description = project_in.description

        await db.commit()
        await db.refresh(project_db)

        returned_project = {
            "id": project_db.id,
            "name": project_db.name,
            "description": project_db.description,
            "created_at": project_db.created_at,
            "updated_at": project_db.updated_at
        }

        return returned_project
    
    async def delete_project(self, project_id: int, db: AsyncSession) -> bool:
        """Service: ลบโปรเจกต์"""
        query = sa.select(Project).where(Project.id == project_id)
        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            return False
        
        db.delete(project)
        await db.commit()
        return True

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_service = ProjectService()