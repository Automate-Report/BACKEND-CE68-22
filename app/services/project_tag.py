import json
import os
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project_tags import ProjectTag #SQL Alchemy Models


# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "project_tags.json")

class ProjectTagService:
    
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

        db.delete(project_tag)
        await db.commit()
        return True

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_tag_service = ProjectTagService()
