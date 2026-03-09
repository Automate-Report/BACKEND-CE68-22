

import json
import os
import secrets
import string

from datetime import datetime, timedelta
from typing import List

from fastapi import Depends
from app.deps.auth import get_current_user

from app.core.redis import QUEUE_KEY, redis_jobs
from app.services.asset import asset_service
from app.services.worker import worker_service
from app.services.notification import notification_service
from app.services.vulnerability import vuln_service


from app.schemas.job import JobWorkerPayload, SummaryInfoByWorker

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

    def _generate_job_name(self, length=12):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_job(self, schedule_id: int, worker_id: int) -> dict:
        """Service: สร้าง Job ใหม่"""
        jobs = self._read_json()
        
        # 1. จำลอง Logic Auto Increment ID
        new_id = 1
        if jobs:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = jobs[-1]["id"] + 1
        
        job_name = f"job_{self._generate_job_name()}"
            
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
    
    def get_job_by_id(self, job_id: int):
        jobs = self._read_json()

        for job in jobs:
            if job["id"] == job_id:
                return job
            
        return None
    
    def get_job_ids_by_schedule_id(self, schedule_id: int):
        jobs = self._read_json()

        job_ids = []

        for job in jobs:
            if job["schedule_id"] == schedule_id:
                job_ids.append(job["id"])
        return job_ids
    
    def get_job_by_worker_id(self, worker_id: int,
                            page: int, size: int, sort_by: str = None, order: str = "asc"):
        """Service: ดึง Job ตาม Schedule"""
        jobs = self._read_json()

        result = []
        n = 0
        for job in jobs:
            if job["worker_id"] == worker_id:
                n += 1
                temp = {
                    "id": job["id"],
                    "name": job["name"],
                    "schedule_id": job["schedule_id"],
                    "status": job["status"],
                    "started_at": job["started_at"],
                    "finished_at": job["finished_at"]
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

    def get_job_by_schedule_id(self, schedule_id: int, user_email: str, 
                            page: int, size: int, sort_by: str = None, order: str = "asc"):
        """Service: ดึง Job ตาม Schedule"""
        jobs = self._read_json()

        result = []
        n = 0
        for job in jobs:
            if job["schedule_id"] == schedule_id:
                n += 1
                worker = worker_service.get_worker_by_id(job["worker_id"])
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
    
    def get_summary_info_by_worker_id(self, worker_id: int):
        jobs = self._read_json()

        total_findings = 0

        total_jobs = 0
        completed = 0
        failed = 0

        for job in jobs:
            if job["worker_id"] == worker_id:
                total_jobs+=1
                if job["status"] == "completed":
                    completed+=1
                elif job["status"] == "failed":
                    failed+=1

                cnt_findings = vuln_service.cnt_vuln_by_job_id(job["id"]) 
                total_findings+=cnt_findings

        return SummaryInfoByWorker(
            total_jobs=total_jobs,
            total_completed=completed,
            total_failed=failed,
            total_findings=total_findings
        )
    
    def get_total_job_by_worker_id(self, worker_id: int):
        jobs = self._read_json()

        total_jobs = 0

        for job in jobs:
            if job["worker_id"] == worker_id:
                total_jobs+=1

        return total_jobs

    async def get_best_worker(self, project_id: int):
        workers = worker_service.read_all_worker(project_id)

        if not workers:
            return "No Worker", 0
        
        online_workers = [
            w for w in workers
            if w.get("status") == "online" and w.get("isActive") == True
        ]

        if not online_workers:
            return None, 0
        
        worker_scores = []
        for w in online_workers:
            current_load = w.get("current_load", 0)
            worker_id = w.get("id")
            queue_name = f"{QUEUE_KEY}:{worker_id}"
            
            try:
                pending_jobs = await redis_jobs.llen(queue_name)
            except Exception:
                pending_jobs = 0
                
            threads = w.get("thread_number", 1)
            # สูตร: (งานที่ทำอยู่ + งานที่รอคิว) / จำนวน Thread
            # ยิ่งค่าน้อย แปลว่ายิ่งมีโอกาสทำงานเสร็จไวที่สุด
            score = (current_load + pending_jobs) / threads
            worker_scores.append((w, score))

        # เลือก Worker ที่ Score น้อยที่สุด (ว่างสุด หรือคิวสั้นสุดเมื่อเทียบกับกำลังเครื่อง)
        best_w, best_score = min(worker_scores, key=lambda x: x[1])
        print(best_w)
        return best_w, best_score

    async def dispatch_job(self, schedule_data: dict):
        print(f"DEBUG: Starting dispatch for {schedule_data.get('schedule_id')}")
        schedule_id = schedule_data.get("schedule_id")

        # 1. ตรวจสอบ Lock ป้องกันการส่งซ้ำ
        now_str = datetime.utcnow().strftime('%Y%m%d%H%M')
        minute_lock_key = f"lock:schedule:{schedule_data['schedule_id']}:{now_str}"

        is_not_repeat = (schedule_data.get("cron_expression") == "Not Repeat")
        once_lock_key = f"lock:schedule:once:{schedule_id}"

        if is_not_repeat:
            # ถ้าเคยรันไปแล้ว (มี Key ใน Redis) ให้หยุดทันที
            if await redis_jobs.exists(once_lock_key):
                print(f"🚫 [Dispatch] Schedule {schedule_id} (Not Repeat) already dispatched. Skipping.")
                return None
        else:
            # ถ้าเป็นงาน Cron ปกติ เช็ค Lock รายนาที
            if await redis_jobs.exists(minute_lock_key):
                return None

        # 2. ดึงข้อมูล Asset และค้นหา Best Worker
        asset = asset_service.get_asset_by_id(schedule_data["asset_id"])
        best_worker, score = await self.get_best_worker(schedule_data.get("project_id"))
        user_id = schedule_data.get("created_by", "Unknown User")

        # กรณีไม่มี Worker ออนไลน์เลย
        if best_worker in ["No Worker", None]:
            error_msg = f"❌ ไม่สามารถเริ่มงานสแกน {asset['name']} ได้ เนื่องจากไม่มี Worker ออนไลน์ในขณะนี้"
            notification_service.create_notification(user_id, "error", error_msg, f'/projects/{schedule_data.get("project_id")}/workers')
            from app.services.schedule import schedule_service
            await schedule_service.deactivate_schedule(schedule_id)
            print(f"🔒 [Dispatch] No worker online, deactivating schedule: {schedule_id}")
            return None
        
        if is_not_repeat:
            # ล็อกไว้ 24 ชม. หรือจนกว่าจะมีการลบออก เพื่อให้มั่นใจว่ารอบถัดไปจะไม่รันอีก
            await redis_jobs.setex(once_lock_key, 86400, "dispatched")
        else:
            await redis_jobs.setex(minute_lock_key, 60, "locked")

        # 3. สร้างเงื่อนไข Message ตามความยุ่งของ Worker
        if score == 0:
            # กรณี Worker ว่างกริบ ไม่มีงานรัน ไม่มีคิว
            display_message = f"🚀 เริ่มงานสแกนสำหรับ {asset['name']} ทันทีบน Worker {best_worker['name']}"
        else:
            # กรณีต้องไปต่อคิว (หาตัวที่คิวน้อยที่สุดมาให้แล้ว)
            display_message = (
                f"⏳ ขณะนี้ Worker ทุกตัวกำลังติดงานสแกนอื่นอยู่ "
                f"ระบบได้ส่งงานของ {asset['name']} เข้าคิวของ Worker {best_worker.get('name', 'Unknown')} "
                f"ซึ่งคาดว่าจะพร้อมทำงานให้คุณได้เร็วที่สุดครับ"
            )

        # 4. สร้าง Job ในระบบ
        new_job = self.create_job(schedule_data["schedule_id"], best_worker["id"])

        # 5. ส่งงานเข้า Redis Queue เฉพาะตัว
        payload = JobWorkerPayload(
            job_id=new_job["id"],
            target_url=asset["target"],
            attack_type=schedule_data["attack_type"],
            credential=None
        )
        
        queue_name = f"{QUEUE_KEY}:{best_worker['id']}"
        await redis_jobs.rpush(queue_name, payload.model_dump_json())

        # 6. บันทึกการแจ้งเตือน (Notification)
        new_noti = notification_service.create_notification(
            user_email=user_id,
            type="info" if score > 0 else "success",
            message=display_message,
            link=f"/jobs/{new_job['id']}"
        )

        print(f"📢 Notification: {display_message}")
        return new_job

    async def run_watchdog(self):
        """🛡️ ตรวจสอบงานที่ค้างใน pending นานเกินไป (Watchdog)"""
        print("🛡️ [Watchdog] Started checking...")
        timeout_limit = datetime.utcnow() - timedelta(minutes=5)
        running_timeout_limit = datetime.utcnow() - timedelta(minutes=30)
        
        jobs = self._read_json()
        workers = worker_service._read_json()

        updated = False
        for job in jobs:
            # ตรวจสอบว่าเป็น dict และมีคีย์ที่จำเป็น
            if not isinstance(job, dict) or "status" not in job:
                continue

            try:
                job_created_time = datetime.fromisoformat(job.get("created_at", datetime.utcnow().isoformat()))
                job_startup_time = None
                if job.get("started_at"):
                    job_startup_time = datetime.fromisoformat(job["started_at"])
            except (ValueError, TypeError):
                continue
            
            # เช็คเงื่อนไข Stuck
            is_pending_stuck = (job["status"] == "pending" and job_created_time < timeout_limit)
            is_running_stuck = (job["status"] == "running" and job_startup_time and job_startup_time < running_timeout_limit)

            if is_pending_stuck or is_running_stuck:
                print(f'🕵️ [Watchdog] Job {job.get("id")} is stuck. Marking as failed.')
                job["status"] = "failed"
                updated = True
                
                # คืนโหลดให้ Worker (ใช้วิธีที่ปลอดภัยขึ้น)
                target_worker_id = job.get("worker_id")
                if target_worker_id:
                    for w in workers:
                        if isinstance(w, dict) and w.get("id") == target_worker_id:
                            if w.get("current_load", 0) > 0:
                                w["current_load"] -= 1
                            break
        
        if updated:
            self._save_json(jobs)
            worker_service._save_json(workers)


# สร้าง Instance ไว้ให้ Router เรียกใช้
job_service = JobService()