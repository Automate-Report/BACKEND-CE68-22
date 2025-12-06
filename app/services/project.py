import json
import os
from datetime import datetime
from typing import List, Optional
from app.schemas.project import ProjectCreate

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "projects.json")

class ProjectService:
    
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

    def get_all_projects(self, user_id: int, page:int, size:int):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        projects = self._read_json()
        total_count = 0
        result = []
        for proj in projects:
            if proj["user_id"] == user_id:
                total_count += 1
                result.append(proj)
            
        offset = (page - 1) * size
        import math
        total_pages = math.ceil(total_count / size)

        return {
            "total": total_count,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "items": result
        }

    def create_project(self, project_in: ProjectCreate, user_id: int) -> dict:
        """Service: สร้างโปรเจกต์ใหม่"""
        projects = self._read_json()
        
        # 1. จำลอง Logic Auto Increment ID
        new_id = 1
        if projects:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = projects[-1]["id"] + 1
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_project = {
            "id": new_id,
            "name": project_in.name,
            "description": project_in.description,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # 3. บันทึก
        projects.append(new_project)
        self._save_json(projects)
        
        return new_project
    
    def update_project(self, project_id: int, project_in: ProjectCreate, user_id: int) -> Optional[dict]:
        """Service: อัปเดตโปรเจกต์"""
        projects = self._read_json()
        for proj in projects:
            if proj["id"] == project_id and proj["user_id"] == user_id:
                proj["name"] = project_in.name
                proj["description"] = project_in.description
                proj["updated_at"] = datetime.now().isoformat()
                self._save_json(projects)
                return proj
        return None
    
    def delete_project(self, project_id: int, user_id: int) -> bool:
        """Service: ลบโปรเจกต์"""
        projects = self._read_json()
        for i, proj in enumerate(projects):
            if proj["id"] == project_id and proj["user_id"] == user_id:
                del projects[i]
                self._save_json(projects)
                return True
        return False

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_service = ProjectService()