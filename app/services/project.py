import math
from typing import Optional
from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.projects import Project #SQL Alchemy Models
from app.models.project_members import ProjectMember, InviteStatus, ProjectRole
from app.schemas.project import ProjectCreate

from app.schemas.project import ProjectCreate
from app.schemas.userauthen import UserInfo

from app.services.project_tag import project_tag_service
from app.services.tag import tag_service
from app.services.userauthen import userauthen_service
from app.services.asset import asset_service
from app.services.vulnerability import vuln_service

class ProjectService:
    async def get_all_projects(self, user_id: str, page: int, size: int, db: AsyncSession, sort_by: str = None, order: str = "asc", search: str = None, filter: str = "ALL"):
        """Service: ดึงโปรเจกต์ที่ User เป็นเจ้าของ 'หรือ' เป็นสมาชิกที่ Join แล้ว"""
    
        # 1. สร้าง Base Query เพื่อหาโปรเจกต์ที่เกี่ยวข้อง
        # ใช้ Left Join กับ ProjectMember เพื่อดูว่า User คนนี้มี Role อะไรในโปรเจกต์นั้น
        query = (
            sa.select(
                Project,
                sa.case(
                    (Project.user_email == user_id, "owner"),
                    else_=ProjectMember.role.cast(sa.String)
                ).label("user_role")
            )
            .join(
                ProjectMember, 
                sa.and_(
                    ProjectMember.project_id == Project.id,
                    ProjectMember.user_email == user_id,
                    ProjectMember.status == InviteStatus.JOINED
                ),
                isouter=True # Left Join เพื่อให้โปรเจกต์ที่เราเป็น Owner ยังอยู่แม้ไม่มีใน ProjectMember
            )
            .where(
                sa.or_(
                    Project.user_email == user_id, # เคสเราเป็นเจ้าของ
                    ProjectMember.user_email == user_id # เคสเราเป็นสมาชิกที่ Join แล้ว
                )
            )
        )

        # 2. การกรอง (Search & Filter) ในระดับ SQL
        if search:
            query = query.where(Project.name.ilike(f"%{search}%"))
        
        if filter != "ALL":
            if filter == "owner":
                query = query.where(Project.user_email == user_id)
            elif filter == "pentester":
                query = query.where(ProjectMember.role == ProjectRole.PENTESTER)
            elif filter == "developer":
                query = query.where(ProjectMember.role == ProjectRole.DEVELOPER)

        # 3. จัดการเรื่อง Sorting
        column_to_sort = getattr(Project, sort_by if sort_by else "created_at", Project.created_at)
        query = query.order_by(column_to_sort.desc() if order == "desc" else column_to_sort.asc())

        # 4. ดึงข้อมูลทั้งหมดมาจัดการต่อ (สำหรับนับ Count และนับ Asset/Vuln)
        result = await db.execute(query)
        rows = result.all() # [(Project, "owner"), (Project, "pentester"), ...]

        all_matches = []
        for proj, role_val in rows:
            # ดึงค่า String จาก Enum ถ้าจำเป็น
            user_role = role_val.value.lower() if hasattr(role_val, "value") else role_val.lower()

            # ✅ ดึง Count ต่างๆ (แนะนำให้ทำ Subquery ในอนาคตเพื่อความเร็ว)
            asset_cnt = await asset_service.cnt_asset_by_project_id(proj.id, db)
            vuln_cnt = await vuln_service.get_cnt_vulns_in_project_id(proj.id, db)
            tags = await project_tag_service.get_tags_by_project_id(proj.id, db) # ปรับให้ดึงข้อมูล tag มาเลย

            all_matches.append({
                "id": proj.id,
                "name": proj.name,
                "description": proj.description,
                "role": user_role,
                "assets_cnt": asset_cnt,
                "vuln_cnt": vuln_cnt,
                "tags": tags,
                "created_at": proj.created_at,
                "updated_at": proj.updated_at      
            })

        # 5. Pagination Logic (เหมือนเดิม)
        total_count = len(all_matches)
        total_pages = math.ceil(total_count / size)
        offset = (page - 1) * size
        paginated_items = all_matches[offset : offset + size]

        return {
            "total": total_count,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "items": paginated_items
        }
    
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

        user = await userauthen_service.get_user_by_id(
            user_id=project.user_email,
            db=db
        )

        user_info = UserInfo(
            email=user.email,
            firstname=user.first_name,
            lastname=user.last_name,
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
        
        await db.delete(project)
        await db.commit()
        return True

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_service = ProjectService()