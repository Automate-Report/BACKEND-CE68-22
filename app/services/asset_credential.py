import json
import os
from datetime import datetime
from typing import List
from app.schemas.asset_credential import AssetCredentialCreate

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "credentials.json")

class AssetCredentialService:
    
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
    
    def get_credential_by_id(self, credential_id:int):
        credentials = self._read_json()

        for cred in credentials:
            if cred["id"] == credential_id:
                return cred
            
        return None
    
    def get_credential_by_asset_id(self, asset_id: int):
        credentials = self._read_json()

        for cred in credentials:
            if cred["asset_id"] == asset_id:
                return cred
        
        return None

    def create_credential(self, credential_in: AssetCredentialCreate) -> dict:
        """Service: สร้าง Credential ใหม่"""
        credentials = self._read_json()
        
        # 1. จำลอง Logic Auto Increment ID
        new_id = 1
        if credentials:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = credentials[-1]["id"] + 1
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_credential = {
            "id": new_id,
            "asset_id": credential_in.asset_id,
            "username": credential_in.username,
            "password": credential_in.password,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # 3. บันทึก
        credentials.append(new_credential)
        self._save_json(credentials)
        
        return new_credential
    
    def update_credential(self, credential_id: int, credential_in: AssetCredentialCreate):
        """Service: อัปเดต Credential"""
        credentials = self._read_json()
        for cred in credentials:
            if cred["id"] == credential_id:
                cred["username"] = credential_in.username
                cred["password"] = credential_in.password
                cred["updated_at"] = datetime.now().isoformat()
                self._save_json(credentials)
                return cred
        return None
    
    def delete_credential(self, credential_id: int) -> bool:
        """Service: ลบ Credential"""
        credentials = self._read_json()
        for i, cred in enumerate(credentials):
            if cred["id"] == credential_id:
                del credentials[i]
                self._save_json(credentials)
                return True
        return False


# สร้าง Instance ไว้ให้ Router เรียกใช้
asset_credential_service = AssetCredentialService()