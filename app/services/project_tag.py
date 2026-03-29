from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project_tags import ProjectTag #SQL Alchemy Models
from app.models.tags import Tag


class ProjectTagService:
    
    async def create_project_tag(self, tag_id: str, project_id: str, db: AsyncSession) -> dict:
        """Service: สร้างโปรเจกต์ใหม่"""
        new_project_tag_db = ProjectTag(
            project_id = project_id,
            tag_id = tag_id,
        )

        try:
            db.add(new_project_tag_db)
            await db.commit()
            # refresh to get the DB generated content such as created_at
            await db.refresh(new_project_tag_db)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create project tag")
        
        new_project_tag = {
            "project_id": new_project_tag_db.project_id,
            "tag_id": new_project_tag_db.tag_id,
            "created_at": new_project_tag_db.created_at,
        }
        
        return new_project_tag
    
    async def get_all_tag_ids(self, project_id: int, db: AsyncSession):
        query = sa.select(ProjectTag).where(ProjectTag.project_id == project_id)
        result = await db.execute(query)
        project_tags = result.scalars().all()

        tags_id = []
        
        for project_tag in project_tags:
            tags_id.append(project_tag.tag_id)

        return tags_id
    
    async def delete_by_tag_id(self, tag_id: int, db: AsyncSession) -> bool:
        try:
            query = sa.delete(ProjectTag).where(ProjectTag.tag_id == tag_id)
            result = await db.execute(query)
            await db.commit()
            return True
        except:
            await db.rollback()
            return False
    
    async def delete_by_project_id(self, project_id: int, db: AsyncSession) -> bool:
        """Service: ลบโปรเจกต์"""
        try:
            query = sa.delete(ProjectTag).where(ProjectTag.project_id == project_id)
            result = await db.execute(query)
            await db.commit()
            return True
        except:
            await db.rollback()
            return False
    
    async def delete_relation(self, project_id: int, tag_id: int, db: AsyncSession) -> bool:
        query = sa.select(ProjectTag).where(ProjectTag.project_id == project_id and ProjectTag.tag_id == tag_id)
        result = await db.execute(query)
        project_tag = result.scalar_one_or_none()

        if not project_tag:
            return False

        await db.delete(project_tag)
        await db.commit()
        return True
    
    async def get_tags_by_project_id(self, project_id: int, db: AsyncSession):
        """
        ดึงข้อมูล Tags ทั้งหมด (ชื่อ, สี) ที่ผูกกับ Project ID นี้
        """
        # 1. สร้าง Query ที่ Join ระหว่าง ProjectTag (ตารางกลาง) และ Tag (ตารางข้อมูล)
        query = (
            sa.select(
                Tag.name,
                Tag.text_color,
                Tag.bg_color
            )
            .join(ProjectTag, Tag.id == ProjectTag.tag_id)
            .where(ProjectTag.project_id == project_id)
        )

        # 2. Execute Query
        result = await db.execute(query)
        rows = result.all()

        # 3. แปลงผลลัพธ์เป็น List ของ Dictionary เพื่อส่งกลับไปที่ Frontend
        tags = []
        for name, t_color, b_color in rows:
            tags.append({
                "name": name,
                "text_color": t_color,
                "bg_color": b_color
            })

        return tags

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_tag_service = ProjectTagService()
