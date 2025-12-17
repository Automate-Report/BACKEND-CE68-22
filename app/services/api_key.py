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
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "api_keys.json")

class APIKeyService:
    __crptography_key = ""
    
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

    def create_api_key(self):
        """Service: สร้าง API Key"""
        api_keys = self._read_json()

        new_id = 1
        if api_keys:
            new_id = api_keys[-1]["id"] + 1
        
        new_api_key = {
            "id": new_id,
            "key": security.generate_api_key(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        api_keys.append(new_api_key)
        self._save_json(api_keys)

        return new_api_key
    
    def get_api_key_by_id(self, id: int):
        api_keys = self._read_json()
        for key in api_keys:
            if key["id"] == id:
                return key
            
        return None
   

api_key_service = APIKeyService()