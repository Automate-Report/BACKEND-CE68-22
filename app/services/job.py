import json
import os
from datetime import datetime, timedelta
from typing import List

from app.core.redis import QUEUE_KEY, redis_jobs
from app.services.asset import asset_service
from app.services.worker import worker_service
from app.services.project import project_service
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
    
    def create_job(self, schedule_id: int, worker_id: int, attack_type: str, target: str) -> dict:
        """Service: สร้าง Job ใหม่"""
        jobs = self._read_json()
        
        # 1. จำลอง Logic Auto Increment ID
        new_id = 1
        if jobs:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = jobs[-1]["id"] + 1
        
        if attack_type == "sql_intection":
            job_name = f"SQLi - {target}"
        else:
            job_name = f"{attack_type.upper()} - {target}"
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_job= {
            "id": new_id,
            "name": job_name,
            "schedule_id": schedule_id,
            "worker_id": worker_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "finished_at": None
        }
        
        # 3. บันทึก
        jobs.append(new_job)
        self._save_json(jobs)
        
        return new_job
    
    def get_job_by_schedule_id(self, schedule_id: int, user_email: str, 
                            page: int, size: int, sort_by: str = None, order: str = "asc"):
        """Service: ดึง Job ตาม Schedule"""
        jobs = self._read_json()

        result = []
        n = 0
        for job in jobs:
            if job["schedule_id"] == schedule_id:
                n += 1
                worker = worker_service.get_worker_by_id(user_email, job["worker_id"])
                temp = {
                    "id": job["id"],
                    "name": f'Job #{n} {job["name"]}',
                    "status": job["status"],
                    "worker_id": job["worker_id"],
                    "worker_name": worker["name"],
                    "created_at": job["created_at"]
                }
                result.append(temp)

        if sort_by:
            reverse = (order == "desc")
            # Handle กรณี field ไม่มีอยู่จริง หรือต้องการ sort date
            result.sort(key=lambda x: (x.get(sort_by) or ""), reverse=reverse)
        
        # 2. นับจำนวนทั้งหมด (สำหรับ Pagination UI)
        total_count = len(result)
            
        # 3. คำนวณ Pagination Logic
        import math
        total_pages = math.ceil(total_count / size)
        
        offset = (page - 1) * size
        
        # --- จุดที่ต้องแก้: ตัดข้อมูล (Slicing) ---
        # ใช้ Python Slice [start : end]
        paginated_items = result[offset : offset + size]

        return {
            "total": total_count,      # จำนวนทั้งหมด (เช่น 50)
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "items": paginated_items   # ส่งกลับเฉพาะ 10 ตัวของหน้านั้น (ไม่ใช่ทั้งหมด)
        }
    
    def get_number_job_status_by_schedule_id(self, schedule_id: int):
        jobs = self._read_json()

        pending = 0
        running = 0
        completed = 0
        failed = 0

        for job in jobs:
            if job["schedule_id"] == schedule_id:
                if job["status"] == "pending":
                    pending += 1
                elif job["status"] == "running":
                    running += 1
                elif job["status"] == "completed":
                    completed += 1
                elif job["status"] == "failed":
                    failed += 1

        return {
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed
        }
    

    
    def update_job_status(self, job_id: int, status: str):
        jobs = self._read_json()
        print(status)
        for job in jobs:
            if job["id"] == job_id:
                if status == "found" or status == "not found":
                    job["status"] = "completed"
                    job["finished_at"] = datetime.utcnow().isoformat()
                elif status == "running":
                    job["status"] = status
                    job["started_at"] = datetime.utcnow().isoformat()
                elif status == "failed":
                    job["status"] = status
                    job["started_at"] = job["finished_at"] = datetime.utcnow().isoformat()
                self._save_json(jobs)
                return True
        return False

    
    def best_worker(self, user_id: str):
        workers = worker_service.read_all_worker(user_id)
        online_workers = [
            w for w in workers
            if w.get("status") == "online" and w.get("isActive") == True
        ]

        if not online_workers:
            return None
        
        best_worker = min(
            online_workers, 
            key=lambda w: w.get("current_load", 0) / w.get("thread_number", 1)
        )
        
        return best_worker

    async def dispatch_job(self, schedule_data):
        # lock_key = f"lock:schedule:{schedule_data["id"]}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    
        # # ถ้ามี Lock นี้อยู่ใน Redis แล้ว แสดงว่านาทีนี้ส่งงานไปแล้ว



        # if await redis_jobs.exists(lock_key):
        #     return

        

        # asset = asset_service.get_asset_by_id(schedule_data["asset_id"])

        # project = project_service.get_project_by_id(schedule_data["project_id"])

        # user_id = project["email"]

        # best_worker = self.best_worker(user_id)

        # new_job = self.create_job(schedule_data["id"], best_worker["id"], schedule_data["attack_type"], asset["target"])

        # payload = JobWorkerPayload(
        #     job_id=new_job["id"],
        #     target_url=asset["target"],
        #     attack_type=schedule_data["attack_type"],
        # )

        # # ถ้ายังไม่มี ให้สร้าง Lock ไว้ (Expire ใน 60 วินาที)
        # await redis_jobs.setex(lock_key, 60, "locked")
        # queue_name = f"{QUEUE_KEY}:{best_worker["id"]}"
        # await redis_jobs.rpush(queue_name, payload.model_dump_json()) #"system:queue:{worker_id}"
        # print(f"🚀 Job {new_job["id"]} dispatched to Redis!")
        print(f"🚀 Job temp not dispatched to Redis!")

    async def run_watchdog(self):
        # """🛡️ ตรวจสอบงานที่ค้างใน pending นานเกินไป (Watchdog)"""
        # print("🛡️ [Watchdog] Started checking...")
        # timeout_limit = datetime.utcnow() - timedelta(minutes=5)
        # running_timeout_limit = datetime.utcnow() - timedelta(minutes=30)
        # jobs = self._read_json()
        # workers = worker_service._read_json()

        # for job in jobs:
        #     try:
        #         # ใช้คีย์ให้ตรงกับใน JSON ของคุณ (ระวัง created_at vs create_at)
        #         job_created_time = datetime.fromisoformat(job["created_at"])
        #         if job["started_at"]:
        #             job_startup_time = datetime.fromisoformat(job["started_at"])
        #     except (ValueError, KeyError):
        #         continue
            
        #     if (job["status"] == "pending" and job_created_time < timeout_limit) or (job["started_at"] and job["status"] == "running" and job_startup_time < running_timeout_limit):
        #         print(f'🕵️ [Watchdog] Job {job["id"]} is stuck. Marking as failed.')
        #         job["status"] = "failed"
        #         # คืนโหลดให้ Worker ตัวเดิม (ถ้ามี)
        #         for w in workers:
        #             if w["id"] == job["worker_id"]:
        #                 if w and w["current_load"] > 0:
        #                     w["current_load"] -= 1

        
        # self._save_json(jobs)
        # worker_service._save_json(workers)
        pass


# สร้าง Instance ไว้ให้ Router เรียกใช้
job_service = JobService()