import json
import os
from datetime import datetime
from typing import List, Optional

from app.schemas.project import ProjectCreate
from app.schemas.userauthen import UserInfo

from app.services.project_member import project_member_service
from app.services.userauthen import userauthen_service

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

    def get_all_projects(self, user_id: str, page: int, size: int, sort_by: str = None, order: str = "asc", search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        projects = self._read_json()

        rel_project_id = project_member_service.get_project_id_by_user_id(user_id) # get project_id from relation project member
        
        # 1. กรอง User
        all_matches = []
        for proj in projects:
            if filter == "ALL":
                if search:
                    if proj["email"] == user_id and search in proj["name"]:
                        all_matches.append(proj)
                else:
                    if proj["email"] == user_id:
                        all_matches.append(proj)
            else:
                # ต้องกลับมาทำส่วนของ filterตอนที่รู้ว่าจะ filter อะไร
                pass

        if rel_project_id is not []:
            for id in rel_project_id:
                all_matches.append(self.get_project_by_id(id))

        if sort_by:
            reverse = (order == "desc")
            # Handle กรณี field ไม่มีอยู่จริง หรือต้องการ sort date
            all_matches.sort(key=lambda x: (x.get(sort_by) or ""), reverse=reverse)
        
        # 2. นับจำนวนทั้งหมด (สำหรับ Pagination UI)
        total_count = len(all_matches)
            
        # 3. คำนวณ Pagination Logic
        import math
        total_pages = math.ceil(total_count / size)
        
        offset = (page - 1) * size
        
        # --- จุดที่ต้องแก้: ตัดข้อมูล (Slicing) ---
        # ใช้ Python Slice [start : end]
        paginated_items = all_matches[offset : offset + size]

        return {
            "total": total_count,      # จำนวนทั้งหมด (เช่น 50)
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "items": paginated_items   # ส่งกลับเฉพาะ 10 ตัวของหน้านั้น (ไม่ใช่ทั้งหมด)
        }
    
    def get_project_by_id(self, project_id:int):
        projects = self._read_json()

        for proj in projects:
            if proj["id"] == project_id:
                return proj

        return None
    
    def get_owner_info_by_project_id(self, project_id: int):
        """Get Owner Info by Project ID"""

        projects = self._read_json()
        for proj in projects:
            if proj["id"] == project_id:
                user = userauthen_service.get_user_by_id(proj["email"])

                user_info = UserInfo(
                    email=user["email"],
                    firstname=user["firstname"],
                    lastname=user["lastname"],
                    role="owner",
                    joinned_at=proj["created_at"]
                )
                return user_info
            
        return None


    def create_project(self, name: str, description: str, user_id: str) -> dict:
        """Service: สร้างโปรเจกต์ใหม่"""
        projects = self._read_json()

        new_id = 1
        if projects:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = projects[-1]["id"] + 1

        new_project = {
            "id": new_id,
            "name": name,
            "description": description,
            "email": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # 3. บันทึก
        projects.append(new_project)
        self._save_json(projects)
        
        return new_project
    
    def update_project(self, project_id: int, project_in: ProjectCreate, user_id: str) -> Optional[dict]:
        """Service: อัปเดตโปรเจกต์"""
        projects = self._read_json()
        for proj in projects:
            if proj["id"] == project_id and proj["email"] == user_id:
                proj["name"] = project_in.name
                proj["description"] = project_in.description
                proj["updated_at"] = datetime.now().isoformat()
                self._save_json(projects)
                return proj
        return None
    
    def delete_project(self, project_id: int) -> bool:
        """Service: ลบโปรเจกต์"""
        projects = self._read_json()
        for i, proj in enumerate(projects):
            if proj["id"] == project_id:
                del projects[i]
                self._save_json(projects)
                return True
        return False

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_service = ProjectService()