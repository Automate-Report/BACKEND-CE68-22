import json
import os
from datetime import datetime, timedelta, timezone
from typing import List
from app.schemas.schedule import ScheduleCreate
from fastapi import HTTPException
from fastapi.responses import JSONResponse


# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "schedule.json")

class ScheduleService:
    
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

    def get_atk_type(self, schedule_id: int):
        schedules = self._read_json()
        
        for schedule in schedules:
            if schedule["id"] == schedule_id:
                return schedule["attack_type"]
        
        return "Type Not Found"
    
    def update_schedule(self, schedule_input: ScheduleCreate):
        schedules = self._read_json()
        latest_id = max([s["id"] for s in schedules], default=0)
        
        new_schedule = {
            "schedule_id": latest_id + 1,
            "schedule_name": schedule_input.name,
            "project_id": schedule_input.project_id,
            "asset_id": schedule_input.asset,
            "worker_id": schedule_input.worker,
            "cron_expression": schedule_input.cron_expression,
            "attack_type": schedule_input.atk_type,
            "is_active": True,
            "next_run_at": "Temporary Value", # i have to cacl this? is this necessary?
            "start_date": schedule_input.start_date,
            "end_date": schedule_input.end_date,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        
        schedules.append(new_schedule)
        self._save_json(schedules)
        
        # Only return non-sensitive info
        return {
            "shcedule_id": new_schedule["schedule_id"],
            "schedule_name": new_schedule["schedule_name"],
            "schedule_atk_type": new_schedule["attack_type"],
        }

    def edit_schedule(self, schedule_id: int, schedule_input: ScheduleCreate):
        schedules = self._read_json()
        
        for schedule in schedules:
            if schedule["id"] == schedule_id:
                schedule["schedule_name"] = schedule_input.name
                schedule["project_id"] = schedule_input.project_id
                schedule["asset_id"] = schedule_input.asset
                schedule["worker_id"] = schedule_input.worker
                schedule["cron_expression"] = schedule_input.cron_expression
                schedule["attack_type"] = schedule_input.atk_type
                schedule["start_date"] = schedule_input.start_date
                schedule["end_date"] = schedule_input.end_date
                schedule["updated_at"] = datetime.now().isoformat()
                
                self._save_json(schedules)
                
                # Only return non-sensitive info
                return {
                    "shcedule_id": schedule["schedule_id"],
                    "schedule_name": schedule["schedule_name"],
                    "schedule_atk_type": schedule["attack_type"],
                }
        
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    def delete_schedule(self, schedule_id: int) -> bool:
        schedules = self._read_json()
        for i, schedule in enumerate(schedules):
            if schedule["id"] == schedule_id:
                del schedules[i]
                self._save_json(schedules)
                return True
        return False
        
# สร้าง instance ของ Service เพื่อใช้งาน
schedule_service = ScheduleService()