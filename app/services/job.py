import json
import os
from datetime import datetime
from typing import List

from app.core.redis import QUEUE_KEY, redis_jobs
from app.services.asset import asset_service
from app.schemas.job import JobWorkerPayload

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "jobs.json")

class JobService:
    
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
    
    def create_job(self) -> dict:
        """Service: สร้าง Job ใหม่"""
        jobs = self._read_json()
        
        # 1. จำลอง Logic Auto Increment ID
        new_id = 1
        if jobs:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = jobs[-1]["id"] + 1
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_job= {
            "id": new_id,
            "schedule_id": 1,
            "worker_id": 1,
            "status": "penind",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "finished_at": None
        }
        
        # 3. บันทึก
        jobs.append(new_job)
        self._save_json(jobs)
        
        return new_job

    async def dispatch_job(self, schedule):
        asset = asset_service.get_asset_by_id(schedule.asset_id)

        new_job = self.create_job()

        payload = JobWorkerPayload(
            job_id=new_job["id"],
            target_url=asset["target"],
            attack_type="XSS"
        )

        await redis_jobs.rpush(QUEUE_KEY, payload.model_dump_json())
        print(f"🚀 Job {new_job.id} dispatched to Redis!")

# สร้าง Instance ไว้ให้ Router เรียกใช้
job_service = JobService()