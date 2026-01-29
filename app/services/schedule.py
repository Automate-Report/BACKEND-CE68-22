import json
import os
from datetime import datetime, timedelta, timezone
from typing import List
from app.schemas.schedule import ScheduleCreate
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from croniter import croniter


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


    def get_all_schedules(self, project_id: int, page: int, size: int, sort_by: str = None, 
                          order: str = "asc", search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        schedules = self._read_json()
        print(123456)
        # 1. กรอง Project
        all_matches = []
        for sch in schedules:
            if filter == "ALL":
                if search:
                    if sch["project_id"] == project_id and search in sch["name"]:
                        displaytable_sch = {
                            "id": sch["schedule_id"],
                            "project_id": sch["project_id"],
                            "name": sch["schedule_name"],
                            "atk_type": sch["attack_type"],
                            "start_date": sch["start_date"],
                            "end_date": sch["end_date"],
                            "job_status": {# ตัวอย่างข้อมูล 
                                "failed": 2,
                                "finished": 42,
                                "ongoing": 1,    
                                "scheduled": 3,
                            }
                        }
                        all_matches.append(displaytable_sch)
                else:
                    if sch["project_id"] == project_id:
                        displaytable_sch = {
                            "id": sch["schedule_id"],
                            "project_id": sch["project_id"],
                            "name": sch["schedule_name"],
                            "atk_type": sch["attack_type"],
                            "start_date": sch["start_date"],
                            "end_date": sch["end_date"],
                            "job_status": {# ตัวอย่างข้อมูล 
                                "failed": 2,
                                "finished": 42,
                                "ongoing": 1,    
                                "scheduled": 3,
                            }
                        }
                        all_matches.append(displaytable_sch)
            else:
                # ต้องกลับมาทำส่วนของ filterตอนที่รู้ว่าจะ filter อะไร
                pass

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
    
    def get_by_id(self, schedule_id: int):
        schedules = self._read_json()
        
        for schedule in schedules:
            if schedule["schedule_id"] == schedule_id:
                return schedule
        
        return "Schedule Not Found"
    
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
    
    async def _is_due_now(self, cron_string: str):
        now = datetime.utcnow().replace(second=0, microsecond=0)

        expressions = [e.strip() for e in cron_string.split("Z")]

        for expr in expressions:
            try:
                # คำนวณจุดรันล่าสุดของ Cron ตัวนั้นๆ
                prev_run = croniter(expr, now + timedelta(seconds=1)).get_prev(datetime)
                if prev_run == now:
                    return True
            except Exception as e:
                print(f"❌ Invalid Cron: {expr} - {e}")
                
        return False
    
    async def get_due_schedules(self):
        
        schedules = self._read_json()

        due_schedules = []

        for schedule in schedules:
            if await self._is_due_now(schedule["cron_expression"]):
                due_schedules.append(schedule)
        return due_schedules

        
# สร้าง instance ของ Service เพื่อใช้งาน
schedule_service = ScheduleService()