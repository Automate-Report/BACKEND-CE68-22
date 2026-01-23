import json
import os
from datetime import datetime
from typing import List, Optional

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "tags.json")

class TagService:
    
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

    def create_tag(self, tag: str, user_id: str) -> dict:
        """Service: สร้าง Tag ใหม่"""
        tags = self._read_json()

        new_id = 1
        if tags:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = tags[-1]["id"] + 1

        new_tag = {
            "id": new_id,
            "name": tag,
            "email": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        new_id += 1
        
        # 3. บันทึก
        tags.append(new_tag)
        self._save_json(tags)
        return new_tag
    
    def get_all_tags(self, user_id: int):
        tags = self._read_json()

        result = []

        for tag in tags:
            if tag["user_id"] == user_id:
                result.append(tag)
            
        return result
    
    def get_tag_by_id(self, id: int):
        tags = self._read_json()

        for tag in tags:
            if tag["id"] == id:
                return tag
            
        return None
    
    def delete_tag(self, id: int) -> bool:
        """Service: ลบ Tag"""
        tags = self._read_json()
        for i, tag in enumerate(tags):
            if tag["id"] == id:
                del tags[i]
                self._save_json(tags)
                return True
        return False

# สร้าง Instance ไว้ให้ Router เรียกใช้
tag_service = TagService()