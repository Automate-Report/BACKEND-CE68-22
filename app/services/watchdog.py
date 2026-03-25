from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import Job, JobStatus
from app.models.workers import Worker, WorkerStatus
from app.models.vulnerabilities import Vulnerability
from app.models.schedules import Schedule, ScheduleAttackType


async def run_watchdog(db: AsyncSession):
    """🛡️ SQL Watchdog: ปรับสถานะงานที่ค้างและคืน Load ให้ Worker อัตโนมัติ"""
    print("🛡️ [Watchdog] SQL checking started...")
    
    # 1. ตั้งค่า Timeout (ใช้ UTC Aware ตามมาตรฐานใหม่)
    now = datetime.now(timezone.utc)

    pending_timeout = now - timedelta(minutes=5)
    running_timeout = now - timedelta(minutes=30)
    worker_offline_timeout = now - timedelta(seconds=600)

    # ---------------------------------------------------------
    # 1. จัดการ WORKER (ใหม่: เช็คความตายของ Worker)
    # ---------------------------------------------------------
    # ปรับ Worker ที่ออนไลน์แต่ Heartbeat ขาดช่วงให้เป็น OFFLINE
    worker_status_query = (
        sa.update(Worker)
        .where(
            Worker.status == WorkerStatus.ONLINE, # เฉพาะตัวที่เคยออนไลน์
            Worker.last_heartbeat < worker_offline_timeout
        )
        .values(
            status=WorkerStatus.OFFLINE,
            current_load=0, # 💡 เมื่อ Offline ควรล้าง Load ทิ้งด้วยเพื่อความปลอดภัย
        )
    )
    worker_update_res = await db.execute(worker_status_query)
    if worker_update_res.rowcount > 0:
        print(f"🛡️ [Watchdog] Marked {worker_update_res.rowcount} workers as OFFLINE due to inactivity.")

    # ---------------------------------------------------------
    # 2. จัดการ STUCK JOBS (เดิม)
    # ---------------------------------------------------------
    stuck_query = sa.select(Job.id, Job.worker_id).where(
        sa.or_(
            sa.and_(Job.status == JobStatus.PENDING, Job.created_at < pending_timeout),
            sa.and_(Job.status == JobStatus.RUNNING, Job.started_at < running_timeout)
        )
    )
    
    result = await db.execute(stuck_query)
    stuck_jobs = result.all()

    if stuck_jobs:
        job_ids_to_fail = [j.id for j in stuck_jobs]
        worker_ids_to_reduce = [j.worker_id for j in stuck_jobs if j.worker_id]

        # BULK UPDATE Jobs to FAILED
        await db.execute(
            sa.update(Job)
            .where(Job.id.in_(job_ids_to_fail))
            .values(status=JobStatus.FAILED)
        )

        # คืน Load ให้ Worker (เฉพาะตัวที่ยังไม่ตาย)
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
    # 3. จัดการ SCHEDULE (เดิม)
    # ---------------------------------------------------------
    schedule_cleanup_query = (
        sa.update(Schedule)
        .where(
            Schedule.is_active == True,
            sa.or_(
                sa.and_(Schedule.end_date != None, Schedule.end_date < now),
                sa.and_(Schedule.cron_expression == "Not Repeat", Schedule.last_run_date != None)
            )
        )
        .values(is_active=False)
    )
    cleanup_result = await db.execute(schedule_cleanup_query)
    if cleanup_result.rowcount > 0:
        print(f"🕵️ [Watchdog] Deactivated {cleanup_result.rowcount} expired schedules.")

    # 4. Final Commit
    await db.commit()