import datetime
import json
import os
from turtle import title
from typing import List, Optional

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "noti.json")

class NotificationService:
    
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

    def get_notification_from_user_email(self, user_email:str, skip:int, limit:int, isUnread:bool):
        allnoti = self._read_json()
        
        # Match noti:user
        filtered = []
        for noti in allnoti:
            if noti["user_email"] == user_email:

                # Unread case
                if isUnread and (noti["status"] == "unread"):
                    filtered.append(noti)
                
                # Allnoti case
                if (not isUnread):
                    filtered.append(noti)
        
        # Sort by timestamp
        filtered.sort(
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        # Paginated
        paginated = filtered[skip: skip + limit]

        # Send back
        return paginated

    def create_notification(self, user_email:str, type:str, message:str, link:str = None):
        allnoti = self._read_json()
        latest_id = max([noti["id"] for noti in allnoti], default=0)

        new_noti = {
            "id": latest_id + 1,
            "user_email": user_email,
            "type": type,
            "message": message,
            "hyperlink": link,
            "created_at": datetime.now().isoformat(),
            "status": "unread"
        }

        allnoti.append(new_noti)
        self._save_json(allnoti)

    def change_status_to_read(self, noti_id:int):
        allnoti = self._read_json()
        for noti in allnoti:
            if noti["id"] == noti_id:
                noti["status"] = "read"
                break
        self._save_json(allnoti)

notification_service = NotificationService()