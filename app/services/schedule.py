import json
import os
from datetime import datetime, timedelta, timezone
from typing import List
from app.schemas.schedule import ScheduleCreate
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from croniter import croniter
from app.services.job import job_service
from app.services.asset import asset_service

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "test_schedule.json")
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "schedules.json")

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


    def get_all_schedules(self, project_id: int, page: int, size: int, search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        schedules = self._read_json()
        # 1. กรอง Project
        all_matches = []
        for sch in schedules:
            if filter == "ALL":
                if search:
                    if sch["project_id"] == project_id and search in sch["schedule_name"]:
                        jobstatus = job_service.get_number_job_status_by_schedule_id(sch["schedule_id"])
                        displaytable_sch = {
                            "id": sch["schedule_id"],
                            "project_id": sch["project_id"],
                            "name": sch["schedule_name"],
                            "asset_name": asset_service.get_asset_by_id(sch["asset_id"])["name"],
                            "atk_type": sch["attack_type"],
                            "start_date": sch["start_date"],
                            "end_date": sch["end_date"],
                            "job_status": {
                                "failed": jobstatus["failed"],
                                "finished": jobstatus["completed"],
                                "ongoing": jobstatus["running"],    
                                "scheduled": jobstatus["pending"],
                            }
                        }
                        all_matches.append(displaytable_sch)
                else:
                    if sch["project_id"] == project_id:
                        jobstatus = job_service.get_number_job_status_by_schedule_id(sch["schedule_id"])
                        displaytable_sch = {
                            "id": sch["schedule_id"],
                            "project_id": sch["project_id"],
                            "name": sch["schedule_name"],
                            "asset_name": asset_service.get_asset_by_id(sch["asset_id"])["name"],
                            "atk_type": sch["attack_type"],
                            "start_date": sch["start_date"],
                            "end_date": sch["end_date"],
                            "job_status": {
                                "failed": jobstatus["failed"],
                                "finished": jobstatus["completed"],
                                "ongoing": jobstatus["running"],    
                                "scheduled": jobstatus["pending"],
                            }
                        }
                        all_matches.append(displaytable_sch)
            else:
                # ต้องกลับมาทำส่วนของ filterตอนที่รู้ว่าจะ filter อะไร
                pass
        
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
    
    def get_by_id(self, schedule_id: int):
        schedules = self._read_json()
        
        for schedule in schedules:
            if schedule["schedule_id"] == schedule_id:
                return schedule
        
        return "Schedule Not Found"
    
    
    def create_schedule(self, schedule_input: ScheduleCreate, user_id: str):
        schedules = self._read_json()
        latest_id = max([s["schedule_id"] for s in schedules], default=0)
        
        new_schedule = {
            "schedule_id": latest_id + 1,
            "schedule_name": schedule_input.name,
            "project_id": schedule_input.project_id,
            "asset_id": schedule_input.asset,
            "cron_expression": schedule_input.cron_expression,
            "attack_type": schedule_input.atk_type,
            "is_active": True,
            "start_date": schedule_input.start_date,
            "end_date": schedule_input.end_date,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": user_id,
        }
        
        schedules.append(new_schedule)
        self._save_json(schedules)
        
        # Only return non-sensitive info
        return {
            "schedule_id": new_schedule["schedule_id"],
            "schedule_name": new_schedule["schedule_name"],
            "schedule_atk_type": new_schedule["attack_type"],
        }

    def edit_schedule(self, schedule_id: int, schedule_input: ScheduleCreate):
        schedules = self._read_json()
        
        for schedule in schedules:
            if schedule["schedule_id"] == schedule_id:
                schedule["schedule_name"] = schedule_input.name
                schedule["project_id"] = schedule_input.project_id
                schedule["asset_id"] = schedule_input.asset
                schedule["cron_expression"] = schedule_input.cron_expression
                schedule["attack_type"] = schedule_input.atk_type
                schedule["start_date"] = schedule_input.start_date
                schedule["end_date"] = schedule_input.end_date
                schedule["updated_at"] = datetime.now().isoformat()
                
                self._save_json(schedules)
                
                # Only return non-sensitive info
                return {
                    "schedule_id": schedule["schedule_id"],
                    "schedule_name": schedule["schedule_name"],
                    "schedule_atk_type": schedule["attack_type"],
                }
        
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    def delete_schedule(self, schedule_id: int) -> bool:
        schedules = self._read_json()
        for i, schedule in enumerate(schedules):
            if schedule["schedule_id"] == schedule_id:
                del schedules[i]
                self._save_json(schedules)
                return True
        return False
    
    def get_schedule_ids_by_project_id(self, project_id: int):
        schedules = self._read_json()
        schedule_ids = []
        for schedule in schedules:
            if schedule["project_id"] == project_id:
                schedule_ids.append(schedule["schedule_id"])

        return schedule_ids
    
    async def _is_due_now(self, schedule: dict):
        now = datetime.now(timezone.utc)
        
        # 1. เช็คว่า Active หรือไม่
        if not schedule.get("is_active", False):
            return False
        
        # 2. เช็ค start_date (ห้ามรันก่อนเวลา)
        start_date_str = schedule.get("start_date")
        if start_date_str:
            try:
                # แปลง format "2026-03-07 09:24:00+00:00"
                start_date = datetime.fromisoformat(start_date_str.replace(" ", "T"))
                if now < start_date:
                    return False # ยังไม่ถึงเวลาเริ่ม
            except Exception as e:
                print(f"⚠️ Error parsing start_date: {e}")

        # 3. เช็ค end_date (ถ้ามี)
        end_date_str = schedule.get("end_date")
        cron_string = schedule.get("cron_expression", "") # ดึงค่า cron มาไว้เช็คตรงนี้

        if end_date_str and cron_string != "Not Repeat": # 💡 เพิ่มเงื่อนไข: ถ้าไม่ใช่ Not Repeat ถึงจะเช็ค Expired
            try:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                
                if now > end_date:
                    schedule_id = schedule.get("schedule_id")
                    await self.deactivate_schedule(schedule_id)
                    print(f"🚫 [Schedule] {schedule_id} expired (Passed end_date)")
                    return False
            except Exception as e:
                print(f"⚠️ Error parsing end_date: {e}")

        # 4. จัดการ Not Repeat (จะรันได้ปกติแล้ว)
        if cron_string == "Not Repeat":
            return True

        # 5. จัดการ Cron ปกติ
        expressions = [e.strip() for e in cron_string.split("Z") if e.strip()]
        now_truncated = now.replace(second=0, microsecond=0)

        for expr in expressions:
            try:
                prev_run = croniter(expr, now_truncated + timedelta(seconds=1)).get_prev(datetime)
                if prev_run == now_truncated:
                    return True
            except Exception:
                continue
                
        return False
    
    async def get_due_schedules(self):
        schedules = self._read_json()

        due_schedules = []

        for schedule in schedules:
            if await self._is_due_now(schedule):
                due_schedules.append(schedule)

        return due_schedules
    
    async def deactivate_schedule(self, schedule_id: int):
        schedules = self._read_json() # อ่านไฟล์ทั้งหมดออกมา
        updated = False
        
        for s in schedules:
            if s["schedule_id"] == schedule_id:
                s["is_active"] = False
                s["updated_at"] = datetime.now().isoformat()
                updated = True
                break
                
        if updated:
            self._save_json(schedules) # ฟังก์ชันสำหรับเขียนทับไฟล์ JSON เดิม

        
# สร้าง instance ของ Service เพื่อใช้งาน
schedule_service = ScheduleService()