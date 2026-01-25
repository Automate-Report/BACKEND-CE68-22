import json
import os
from datetime import datetime
from typing import List, Optional


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

    def create_project_tag(self, tag_id: str, project_id: str) -> dict:
        """Service: สร้างโปรเจกต์ใหม่"""
        project_tags = self._read_json()

        new_id = 1
        if project_tags:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = project_tags[-1]["id"] + 1

        new_project_tag = {
            "id": new_id,
            "project_id": project_id,
            "tag_id": tag_id,
            "created_at": datetime.now().isoformat(),
        }
        
        # 3. บันทึก
        project_tags.append(new_project_tag)
        self._save_json(project_tags)
        
        return new_project_tag
    
    def get_all_tag_ids(self, project_id: int):
        project_tags = self._read_json()

        tags = []

        for pt in project_tags:
            if pt["project_id"] == project_id:
                tags.append(pt["tag_id"])

        return tags
    
    def delete_project_tags(self, tag_id: int, project_id: int) -> bool:
        """Service: ลบโปรเจกต์"""
        project_tags = self._read_json()
        for i, proj in enumerate(project_tags):
            if proj["project_id"] == project_id and proj["tag_id"]:
                del project_tags[i]
                self._save_json(project_tags)
                return True
        return False

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_tag_service = ProjectTagService()