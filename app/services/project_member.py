import json
import os
from datetime import datetime
from typing import List, Optional

from app.schemas.project import ProjectCreate

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "project_members.json")

class ProjectMemberService:
    
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

    def get_project_id_by_user_id(self, user_id: str):
        """Get Project ID from Relation Project and User using User ID"""
        relations = self._read_json()

        all_matches = []
        for rel in relations:
            if rel["email"] == user_id:
                all_matches.append(rel["project_id"])

        return all_matches
    
    def get_user_id_by_project_id(self, project_id: int):
        relations = self._read_json()

        all_matches = []
        for rel in relations:
            if rel["project_id"] == project_id:
                all_matches.append(rel["email"])

        return all_matches

   

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_member_service = ProjectMemberService()