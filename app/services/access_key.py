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

        
        new_access_key = {
            "id": new_access_key_db.id,
            "key": new_access_key_db.key,
            "created_at": new_access_key_db.created_at

        }

        return new_access_key
    
    def get_access_key_by_id(self, id: int):
        access_keys = self._read_json()
        for key in access_keys:
            if key["id"] == id:
                return key
            
        return None
    
    def get_access_key_by_worker_id(self, worker_id: int):
        access_keys = self._read_json()
        for key in access_keys:
            if key["worker_id"] == worker_id:
                return key
            
        return None
    
    def delete_access_key_by_id(self, id: int):
        access_keys =self._read_json()
        for i, key in enumerate(access_keys):
            if key["id"] == id:
                del access_keys[i]
                self._save_json(access_keys)
                return True
            
        return False
   

access_key_service = AccessKeyService()