
import json
import os
from turtle import title
from typing import List
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notifications import Notification, NotiStatus, NotiType

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

    async def get_notification_from_user_email(self, db: AsyncSession, user_email:str, skip:int, limit:int, isUnread:bool):
        # 1. สร้าง Base Query
        query = sa.select(Notification).where(Notification.user_email == user_email)

        # 2. Filter: ถ้าต้องการเฉพาะ Unread
        if isUnread:
            # สมมติว่าใน Model คุณเก็บสถานะเป็น Enum หรือ String
            query = query.where(Notification.status == NotiStatus.UNREAD)

        # 3. Sorting: เรียงจากใหม่ไปเก่า (Created At Descending)
        query = query.order_by(Notification.created_at.desc())

        # 4. Pagination: ใช้ Offset (skip) และ Limit
        query = query.offset(skip).limit(limit)

        # 5. Execute Query
        result = await db.execute(query)
        
        # 6. คืนค่าเป็น List ของ Model Objects (หรือจะทำ .dict() ก็ได้)
        notifications = result.scalars().all()
        
        return notifications

    async def create_notification(self, db: AsyncSession, user_email:str, type:NotiType, message:str, link:str = None):
        noti_db = Notification(
            user_email = user_email,
            type = type,
            message = message,
            hyperlink = link,
            status = NotiStatus.UNREAD
        )

        try:
            # 2. เพิ่มลงใน Database
            db.add(noti_db)
            
            # 💡 หมายเหตุ: ปกติเราจะ commit ที่ตัวเรียก (เช่น ใน assign_vulnerability_to_user)
            # แต่ถ้าฟังก์ชันนี้ทำงานแยกเดี่ยวๆ ให้ใส่ flush หรือ commit ตรงนี้ได้ครับ
            await db.flush() 
            
            # 3. คืนค่าเป็น Object ที่มี ID แล้ว
            new_noti = {
                "noti_id": noti_db.id,
                "user_email": noti_db.user_email,
                "type": noti_db.type,
                "message": noti_db.message,
                "hyperlink": noti_db.hyperlink,
                "created_at": noti_db.created_at,
                "status": noti_db.status
            }
            return new_noti
            
        except Exception as e:
            print(f"❌ Error creating notification: {e}")
            # ไม่ต้อง rollback ตรงนี้ถ้าฟังก์ชันนี้ถูกเรียกซ้อนใน transaction อื่น
            raise e

    async def change_status_to_read(self, db: AsyncSession, noti_id:int):
        # 1. ค้นหา Notification ที่ต้องการ
        query = sa.select(Notification).where(Notification.id == noti_id)
        result = await db.execute(query)
        noti = result.scalar_one_or_none()

        # 2. ถ้าไม่พบข้อมูลให้คืนค่า False หรือ Raise Error
        if not noti:
            return False

        # 3. อัปเดตสถานะ (ใช้ Enum หรือ String ตามที่ Model กำหนด)
        noti.status = NotiStatus.READ 

        try:
            # 4. Commit การเปลี่ยนแปลงลง Database
            await db.commit()
            # (Optional) refresh ข้อมูลใน object ถ้าต้องการใช้งานต่อ
            await db.refresh(noti)
            return True
        except Exception as e:
            # หากเกิด Error ให้ Rollback ป้องกันข้อมูลค้าง
            await db.rollback()
            print(f"❌ Error updating notification status: {e}")
            return False

notification_service = NotificationService()