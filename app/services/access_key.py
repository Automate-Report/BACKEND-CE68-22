import json
import os
import io
import zipfile

from datetime import datetime, timedelta
from typing import List



from app.core import security

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "access_keys.json")

class AccessKeyService:

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

    def create_access_key(self):
        """Service: สร้าง API Key"""
        access_keys = self._read_json()

        new_id = 1
        if access_keys:
            new_id = access_keys[-1]["id"] + 1
        
        new_access_key = {
            "id": new_id,
            "key": security.generate_api_key(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        access_keys.append(new_access_key)
        self._save_json(access_keys)

        return new_access_key
    
    def get_access_key_by_id(self, id: int):
        access_keys = self._read_json()
        for key in access_keys:
            if key["id"] == id:
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