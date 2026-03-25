import json
import os

from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tags import Tag #SQL Alchemy Models



class TagService:
    
    async def create_tag(self, tag_name: str, user_id: str, db: AsyncSession) -> dict:
        """Service: สร้าง Tag ใหม่"""
        new_tag_db = Tag(
            user_email = user_id,
            name = tag_name,
            text_color = "#000000",  #MOCK UP===============
            bg_color = "#FFFFFF",  #MOCK UP===============
        )

        try:
            db.add(new_tag_db)
            await db.commit()
            # refresh to get the DB generated content such as created_at
            await db.refresh(new_tag_db)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create tag")
        
        new_tag = {
            "id": new_tag_db.id,
            "name": new_tag_db.name,
        }

        return new_tag
    
    async def get_all_tags_by_user_id(self, user_id: str, db: AsyncSession):
        query = sa.select(Tag).where(Tag.user_email == user_id)
        result = await db.execute(query)
        tags = result.scalars().all()
   
        return tags
    
    async def get_tag_by_id(self, id: int, db:AsyncSession):
        query = sa.select(Tag).where(Tag.id == id)
        result = await db.execute(query)
        tag = result.scalar_one_or_none()

        if tag:
            return tag
            
        return None
    
    async def delete_tag(self, id: int, db: AsyncSession) -> bool:
        """Service: ลบ Tag"""
        query = sa.select(Tag).where(Tag.id == id)
        result = await db.execute(query)
        tag = result.scalar_one_or_none()

        if not tag:
            return False

        db.delete(tag)
        await db.commit()
        return True
        
# สร้าง Instance ไว้ให้ Router เรียกใช้
tag_service = TagService()