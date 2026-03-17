import json
import os
import io
import zipfile

from datetime import datetime
from fastapi import HTTPException

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.access_keys import AccessKey

from app.core import security

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "access_keys.json")

class AccessKeyService:

    async def create_access_key(self, db: AsyncSession):
        """Service: สร้าง API Key"""
        new_access_key_db = AccessKey(
            key = security.generate_access_key(),
        )

        try:
            db.add(new_access_key_db)
            await db.commit()

            await db.refresh(new_access_key_db)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not access key")

        return new_access_key_db
    
    async def get_access_key_by_id(self, id: int, db: AsyncSession):
        query = sa.select(AccessKey).where(AccessKey.id == id)
        result = await db.execute(query)
        access_key = result.scalar_one_or_none()

        if not access_key:
            return None
            
        return access_key
    
    async def delete_access_key_by_id(self, id: int, db: AsyncSession):
        query = sa.select(AccessKey).where(AccessKey.id == id)
        result = await db.execute(query)
        access_key = result.scalar_one_or_none()

        if not access_key:
            return False
        
        db.delete(access_key)
        await db.commit()
        return True
   

access_key_service = AccessKeyService()