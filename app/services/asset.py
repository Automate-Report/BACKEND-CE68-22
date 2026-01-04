import json
import os
from datetime import datetime
from typing import List, Optional
from app.schemas.asset import AssetCreate

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "assets.json")

class AssetService:
    
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

    def get_all_assets(self, project_id: int, page: int, size: int, sort_by: str = None, order: str = "asc", search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        assets = self._read_json()
        
        # 1. กรอง User
        all_matches = []
        for asset in assets:
            if filter == "ALL":
                if search:
                    if asset["project_id"] == project_id and search in asset["name"]:
                        all_matches.append(asset)
                else:
                    if asset["project_id"] == project_id:
                        all_matches.append(asset)
            else:
                # ต้องกลับมาทำส่วนของ filterตอนที่รู้ว่าจะ filter อะไร
                pass

        if sort_by:
            reverse = (order == "desc")
            # Handle กรณี field ไม่มีอยู่จริง หรือต้องการ sort date
            all_matches.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        
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
    
    def get_asset_by_id(self, project_id:int, asset_id:int):
        assets = self._read_json()

        for asset in assets:
            if asset["project_id"] == project_id and asset["id"] == asset_id:
                return asset
            
        return None

    def create_asset(self, asset_in: AssetCreate) -> dict:
        """Service: สร้าง Asset ใหม่"""
        assets = self._read_json()
        
        # 1. จำลอง Logic Auto Increment ID
        new_id = 1
        if assets:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = assets[-1]["id"] + 1
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_asset = {
            "id": new_id,
            "name": asset_in.name,
            "project_id": asset_in.project_id,
            "description": asset_in.description,
            "target": asset_in.target,
            "type": asset_in.type,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # 3. บันทึก
        assets.append(new_asset)
        self._save_json(assets)
        
        return new_asset
    
    def update_asset(self, asset_id: int, asset_in: AssetCreate):
        """Service: อัปเดต Asset"""
        assets = self._read_json()
        for asset in assets:
            if asset["id"] == asset_id:
                asset["name"] = asset_in.name
                asset["description"] = asset_in.description
                asset["target"] = asset_in.target
                asset["type"] = asset_in.type
                asset["updated_at"] = datetime.now().isoformat()
                self._save_json(assets)
                return asset
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
asset_service = AssetService()