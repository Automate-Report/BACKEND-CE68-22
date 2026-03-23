import math
import secrets
import string

from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import HTTPException

from app.core.redis import QUEUE_KEY, redis_jobs
from app.services.asset import asset_service
from app.services.worker import worker_service
from app.services.notification import notification_service
from app.services.vulnerability import vuln_service

from app.schemas.job import JobWorkerPayload, SummaryInfoByWorker

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Job, JobStatus
from app.models.workers import Worker, WorkerStatus
from app.models.vulnerabilities import Vulnerability
from app.models.schedules import Schedule, ScheduleAttackType


class JobService:

    def _generate_job_name(self, length=12):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def create_job(self, schedule_id: int, worker_id: int, db: AsyncSession) -> dict:
        """Service: สร้าง Job ใหม่"""
        job_name = f"job_{self._generate_job_name()}"
        
        new_job_db = Job(
            name = job_name,
            schedule_id = schedule_id,
            worker_id = worker_id,
            status = JobStatus.PENDING,
            started_at = None,
            finished_at = None
        )
        
        try:
            db.add(new_job_db)
            await db.commit()

            await db.refresh(new_job_db)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create job")
        
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_job= {
            "id": new_job_db.id,
            "name": new_job_db.name,
            "schedule_id": new_job_db.schedule_id,
            "worker_id": new_job_db.worker_id,
            "status": new_job_db.status,
            "created_at": new_job_db.created_at,
            "started_at": new_job_db.started_at,
            "finished_at": new_job_db.finished_at
        }
        
        return new_job
    
    async def get_job_by_id(self, job_id: int, db: AsyncSession):
        query = sa.select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job: return None
            
        return job
    
    # def get_job_ids_by_schedule_id(self, schedule_id: int):
    #     jobs = self._read_json()

    #     job_ids = []

    #     for job in jobs:
    #         if job["schedule_id"] == schedule_id:
    #             job_ids.append(job["id"])

    #     return job_ids
    
    async def get_job_by_worker_id(self, worker_id: int,
                            page: int, size: int, db: AsyncSession, sort_by: str = None, order: str = "asc"):
        """Service: ดึง Job ตาม Schedule"""
        query = (
            sa.select(Job)
            .where(Job.worker_id == worker_id)
        )

        # Sorting
        column = getattr(Job, sort_by if sort_by else "created_at", Job.created_at)
        query = query.order_by(column.desc() if order == "desc" else column.asc())
        
        count_query = sa.select(sa.sql.func.count()).select_from(query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar() or 0

        #  Pagination (LIMIT & OFFSET)
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # Execute Final Query
        result = await db.execute(query)
        rows = result.all() # Returns list of tuples: (Worker, first_name, last_name)

        # Format the output
        paginated_items = []
        # Using offset + index to keep the "Job #X" numbering correct across pages

        for i, row in enumerate(rows):
            job = row[0]          # The Job object
            paginated_items.append({
                "id": job.id,
                "name": job.name,
                "schedule_id": job.schedule_id,
                "status": job.status,
                "started_at": job.started_at,
                "finished_at": job.finished_at
            })

        return {
            "total": total_count,      # จำนวนทั้งหมด (เช่น 50)
            "page": page,
            "size": size,
            "total_pages": math.ceil(total_count / size) if size > 0 else 0,
            "items": paginated_items   # ส่งกลับเฉพาะ 10 ตัวของหน้านั้น (ไม่ใช่ทั้งหมด)
        }


    async def get_job_by_schedule_id(self, schedule_id: int, user_email: str, 
                            page: int, size: int, db: AsyncSession, sort_by: str = None, order: str = "asc"):
        """Service: ดึง Job ตาม Schedule"""
        query = (
            sa.select(Job, Worker.name.label("worker_name"))
            .join(Worker, Job.worker_id == Worker.id, isouter=True)
            .where(Job.schedule_id == schedule_id)
        )

        # Sorting
        column = getattr(Job, sort_by if sort_by else "created_at", Job.created_at)
        query = query.order_by(column.desc() if order == "desc" else column.asc())
        
        count_query = sa.select(sa.sql.func.count()).select_from(query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar() or 0

        #  Pagination (LIMIT & OFFSET)
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # Execute Final Query
        result = await db.execute(query)
        rows = result.all() # Returns list of tuples: (Worker, first_name, last_name)

        # Format the output
        paginated_items = []
        # Using offset + index to keep the "Job #X" numbering correct across pages
        start_index = offset + 1
        for i, row in enumerate(rows):
            job = row[0]          # The Job object
            worker_name = row[1]  # The joined name from Worker table
            
            paginated_items.append({
                "id": job.id,
                "name": f"Job #{start_index + i} {job.name}",
                "status": job.status,
                "worker_id": job.worker_id,
                "worker_name": worker_name or "Unknown",
                "created_at": job.created_at
            })

        return {
            "total": total_count,      # จำนวนทั้งหมด (เช่น 50)
            "page": page,
            "size": size,
            "total_pages": math.ceil(total_count / size) if size > 0 else 0,
            "items": paginated_items   # ส่งกลับเฉพาะ 10 ตัวของหน้านั้น (ไม่ใช่ทั้งหมด)
        }
    
    async def get_number_job_status_by_schedule_id(self, schedule_id: int, db: AsyncSession):
        query = (
            sa.select(
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.PENDING).label("pending"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.RUNNING).label("running"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.COMPLETED).label("completed"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.FAILED).label("failed")
            )
            .where(Job.schedule_id == schedule_id)
        )
        result = await db.execute(query)
        stat = result.first()

        if not stat:
            return {"pending": 0, "running": 0, "completed": 0, "failed": 0}


        return {
            "pending": stat.pending,
            "running": stat.running,
            "completed": stat.completed,
            "failed": stat.failed
        }
    
    async def update_job_status(self, job_id: int, status: str, db: AsyncSession):
        query = sa.select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            return None
        
        if status == "found" or status == "not found":
            job.status = JobStatus.COMPLETED
        elif status == "running":
            job["status"] = JobStatus.RUNNING
        elif status == "failed":
            job["status"] = JobStatus.FAILED

        try:
            await db.commit()
            await db.refresh(job) # This ensures all DB-generated fields are loaded

            return True
        except Exception as e:
            await db.rollback()
            # Log the error so you can see it in the terminal
            print(f"Database Error: {e}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_summary_info_by_worker_id(self, worker_id: int, db: AsyncSession):
        query = (
            sa.select(
                sa.func.count(Job.id).label("total"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.COMPLETED).label("completed"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.FAILED).label("failed"),
                sa.sql.func.count(Vulnerability.id).label("total_findings")
            )
            .select_from(Job)
            .join(Vulnerability, Job.id == Vulnerability.job_id, isouter=True)
            .where(Job.worker_id == worker_id)
        )

        result = await db.execute(query)
        stat = result.first()

        if not stat or stat.total == 0:
            return SummaryInfoByWorker(
            total_jobs=0,
            total_completed=0,
            total_failed=0,
            total_findings=0
        )

        return SummaryInfoByWorker(
            total_jobs=stat.total,
            total_completed=stat.completed,
            total_failed=stat.failed,
            total_findings=stat.total_findings
        )
    
    # def get_total_job_by_worker_id(self, worker_id: int):
    #     jobs = self._read_json()

    #     total_jobs = 0

    #     for job in jobs:
    #         if job["worker_id"] == worker_id:
    #             total_jobs+=1

    #     return total_jobs

    async def get_best_worker(self, db: AsyncSession, project_id: int):
        query = (
            sa.select(Worker)
            .where(
                Worker.project_id == project_id,
                Worker.status == WorkerStatus.ONLINE, # Or use your WorkerStatus.ONLINE enum
                Worker.is_active == True
            )
        )

        result = await db.execute(query)
        online_workers = result.scalars().all()

        if not online_workers:
            return None, 0
        
        worker_scores = []
        for w in online_workers:
            current_load = w.current_load
            worker_id = w.id
            queue_name = f"{QUEUE_KEY}:{worker_id}"
            
            try:
                pending_jobs = await redis_jobs.llen(queue_name)
            except Exception:
                pending_jobs = 0
                
            threads = w.thread_number
            # สูตร: (งานที่ทำอยู่ + งานที่รอคิว) / จำนวน Thread
            # ยิ่งค่าน้อย แปลว่ายิ่งมีโอกาสทำงานเสร็จไวที่สุด
            score = (current_load + pending_jobs) / threads
            worker_scores.append((w, score))

        # เลือก Worker ที่ Score น้อยที่สุด (ว่างสุด หรือคิวสั้นสุดเมื่อเทียบกับกำลังเครื่อง)
        best_w, best_score = min(worker_scores, key=lambda x: x[1])

        return best_w, best_score

    async def dispatch_job(self, session, schedule_data: Schedule):
        print(schedule_data)
        async with session() as db:
            try:
                print(f"DEBUG: Starting dispatch for {schedule_data.id}")
                schedule_id = schedule_data.id

                # 1. ตรวจสอบ Lock ป้องกันการส่งซ้ำ
                now_str = datetime.utcnow().strftime('%Y%m%d%H%M')
                minute_lock_key = f"lock:schedule:{schedule_data.id}:{now_str}"

                is_not_repeat = (schedule_data.cron_expression == "Not Repeat")
                once_lock_key = f"lock:schedule:once:{schedule_id}:{schedule_data.created_at}"

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
                asset = await asset_service.get_asset_by_id(schedule_data.asset_id, db)
                best_worker, score = await self.get_best_worker(
                    db=db,
                    project_id=schedule_data.project_id
                )
                user_id = schedule_data.created_by

                # กรณีไม่มี Worker ออนไลน์เลย
                if best_worker in ["No Worker", None]:
                    error_msg = f"❌ ไม่สามารถเริ่มงานสแกน {asset.name} ได้ เนื่องจากไม่มี Worker ออนไลน์ในขณะนี้"
                    notification_service.create_notification(user_id, "error", error_msg, f'/projects/{schedule_data.project_id}/workers')
                    from app.services.schedule import schedule_service
                    await schedule_service.deactivate_schedule(schedule_id, db)
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
                    display_message = f"🚀 เริ่มงานสแกนสำหรับ {asset.name} ทันทีบน Worker {best_worker.name}"
                else:
                    # กรณีต้องไปต่อคิว (หาตัวที่คิวน้อยที่สุดมาให้แล้ว)
                    display_message = (
                        f"⏳ ขณะนี้ Worker ทุกตัวกำลังติดงานสแกนอื่นอยู่ "
                        f"ระบบได้ส่งงานของ {asset['name']} เข้าคิวของ Worker {best_worker.name} "
                        f"ซึ่งคาดว่าจะพร้อมทำงานให้คุณได้เร็วที่สุดครับ"
                    )

                # 4. สร้าง Job ในระบบ
                new_job = await self.create_job(
                    schedule_id=schedule_data.id, 
                    worker_id=best_worker.id,
                    db=db
                )

                if schedule_data.attack_type == ScheduleAttackType.SQLI:
                    attack_type = "sql_injection"
                elif schedule_data.attack_type == ScheduleAttackType.XSS:
                    attack_type = "xss"
                else:
                    attack_type = "all"

                from app.services.asset_credential import asset_credential_service
                credential = await asset_credential_service.get_credential_by_asset_id(asset.id, db)
            

                # 5. ส่งงานเข้า Redis Queue เฉพาะตัว
                payload = JobWorkerPayload(
                    job_id=new_job.id,
                    target_url=asset.target,
                    attack_type=attack_type,
                    credential={
                        "username": credential.username if credential else None,
                        "password": credential.password if credential else None
                    }
                )
                
                queue_name = f"{QUEUE_KEY}:{best_worker.id}"
                await redis_jobs.rpush(queue_name, payload.model_dump_json())

                # 6. บันทึกการแจ้งเตือน (Notification)
                new_noti = notification_service.create_notification(
                    user_email=user_id,
                    type="info" if score > 0 else "success",
                    message=display_message,
                    link=f"/jobs/{new_job.id}"
                )

                print(f"📢 Notification: {display_message}")
                await db.commit()

                return new_job
            except Exception as e:
                await db.rollback()
                print(f"Background Job Error: {e}")
        

    async def run_watchdog(self, db: AsyncSession):
        """🛡️ SQL Watchdog: ปรับสถานะงานที่ค้างและคืน Load ให้ Worker อัตโนมัติ"""
        print("🛡️ [Watchdog] SQL checking started...")
        
        # 1. ตั้งค่า Timeout (ใช้ UTC Aware ตามมาตรฐานใหม่)
        now = datetime.now(timezone.utc)
        pending_timeout = now - timedelta(minutes=5)
        running_timeout = now - timedelta(minutes=30)

        # 2. ค้นหา Job ที่ "ติดค้าง" (Stuck) 
        # เราจะดึงเฉพาะ IDs ของ Job และ Worker มาเพื่อไปลด Load ต่อ
        stuck_query = sa.select(Job.id, Job.worker_id).where(
            sa.or_(
                sa.and_(Job.status == JobStatus.PENDING, Job.created_at < pending_timeout),
                sa.and_(Job.status == JobStatus.RUNNING, Job.started_at < running_timeout)
            )
        )
        
        result = await db.execute(stuck_query)
        stuck_jobs = result.all()

        if stuck_jobs:
            worker_ids_to_reduce = [j.worker_id for j in stuck_jobs if j.worker_id]
            job_ids_to_fail = [j.id for j in stuck_jobs]

            # BULK UPDATE Jobs
            await db.execute(
                sa.update(Job)
                .where(Job.id.in_(job_ids_to_fail))
                .values(
                    status="failed", 
                    error_message="Watchdog: Job timeout (Stuck in pending/running)",
                    updated_at=sa.func.now()
                )
            )

            # Update Workers Load
            if worker_ids_to_reduce:
                for w_id in set(worker_ids_to_reduce):
                    count = worker_ids_to_reduce.count(w_id)
                    await db.execute(
                        sa.update(Worker)
                        .where(Worker.id == w_id)
                        .values(current_load=sa.func.greatest(0, Worker.current_load - count))
                    )
            print(f"🕵️ [Watchdog] Fixed {len(job_ids_to_fail)} stuck jobs.")
        # ---------------------------------------------------------
        # 2. จัดการ SCHEDULE (ใหม่: ปิดพวกที่ค้างหรือหมดอายุ)
        # ---------------------------------------------------------
        # เงื่อนไข: 
        #   - งานที่เลย end_date ไปแล้ว
        #   - หรือ งาน Not Repeat ที่มี last_run_date แล้วแต่ is_active ยังเป็น true (ตกค้างจาก error)
        # schedule_cleanup_query = (
        #     sa.update(Schedule)
        #     .where(
        #         Schedule.is_active == True,
        #         sa.or_(
        #             # กรณี A: เลยเวลา end_date (ถ้ามี)
        #             sa.and_(Schedule.end_date != None, Schedule.end_date < now),
        #             # กรณี B: เป็น Not Repeat ที่รันไปแล้วแต่สถานะไม่ยอมปิด (เกิด Error ระหว่าง Dispatch)
        #             sa.and_(
        #                 Schedule.cron_expression == "Not Repeat",
        #                 Schedule.last_run_date != None
        #             )
        #         )
        #     )
        #     .values(is_active=False, updated_at=sa.func.now())
        # )

        # cleanup_result = await db.execute(schedule_cleanup_query)
        
        # 3. Commit ทั้งหมด
        await db.commit()
        
        # if cleanup_result.rowcount > 0:
        #     print(f"🕵️ [Watchdog] Deactivated {cleanup_result.rowcount} expired/stuck schedules.")


# สร้าง Instance ไว้ให้ Router เรียกใช้
job_service = JobService()