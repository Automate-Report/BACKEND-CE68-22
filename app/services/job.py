import math
import secrets
import string

from datetime import datetime
from fastapi import HTTPException

from app.core.redis import QUEUE_KEY, redis_jobs
from app.services.asset import asset_service
from app.services.notification import notification_service

from app.schemas.job import JobWorkerPayload, SummaryInfoByWorker

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Job, JobStatus
from app.models.workers import Worker, WorkerStatus
from app.models.vulnerabilities import Vulnerability
from app.models.schedules import Schedule, ScheduleAttackType
from app.models.notifications import NotiType


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
            job.status = JobStatus.RUNNING
        elif status == "failed":
            job.status = JobStatus.FAILED

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

    async def get_best_worker(self, db: AsyncSession, project_id: int, user_id: str):
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

        if best_score >= 0.7:
            await notification_service.create_notification(
                db=db,
                user_email=user_id,
                type=NotiType.WARNING,
                message=f"Worker {best_w.name} is running at {best_score*100}% capacity. System might be slow.",
                link=f'/projects/{project_id}/workers/{best_w.id}'
            )
            print(f"⚠️ Warning: Best worker {best_w.name} has high load ({best_score}%)")

        return best_w, best_score

    async def dispatch_job(self, db: AsyncSession, schedule_data: Schedule):

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
                user_id = schedule_data.created_by
                asset = await asset_service.get_asset_by_id(schedule_data.asset_id, db)
                best_worker, score = await self.get_best_worker(
                    db=db,
                    project_id=schedule_data.project_id,
                    user_id=user_id
                )

                

                # กรณีไม่มี Worker ออนไลน์เลย
                if best_worker in ["No Worker", None]:
                    error_msg = f"❌ ไม่สามารถเริ่มงานสแกน {asset.name} ได้ เนื่องจากไม่มี Worker ออนไลน์ในขณะนี้"
                    await notification_service.create_notification(
                        db=db,
                        user_email=user_id, 
                        type=NotiType.ERROR, 
                        message=error_msg, 
                        link=f'/projects/{schedule_data.project_id}/workers'
                    )
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
                        f"ระบบได้ส่งงานของ {asset.name} เข้าคิวของ Worker {best_worker.name} "
                        f"ซึ่งคาดว่าจะพร้อมทำงานให้คุณได้เร็วที่สุดครับ"
                    )

                # 4. สร้าง Job ในระบบ
                new_job = await self.create_job(
                    schedule_id=schedule_data.id, 
                    worker_id=best_worker.id,
                    db=db
                )

                print(new_job)

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
                    job_id=new_job["id"],
                    name=new_job["name"],
                    target_url=asset.target,
                    attack_type=attack_type,
                    credential={
                        "username": credential.username if credential else None,
                        "password": credential.password if credential else None
                    },
                    thread_number=best_worker.thread_number
                )

                
                queue_name = f"{QUEUE_KEY}:{best_worker.id}"
                await redis_jobs.rpush(queue_name, payload.model_dump_json())

                # 6. บันทึกการแจ้งเตือน (Notification)
                new_noti = await notification_service.create_notification(
                    db=db,
                    user_email=user_id,
                    type=NotiType.WARNING if score > 0 else NotiType.SUCCESS,
                    message=display_message,
                    link=f"/projects/{schedule_data.project_id}/workers/{best_worker.id}"
                )

                print(f"📢 Notification: {display_message}")
                await db.commit()

                return new_job
            except Exception as e:
                await db.rollback()
                print(f"Background Job Error: {e}")

# สร้าง Instance ไว้ให้ Router เรียกใช้
job_service = JobService()