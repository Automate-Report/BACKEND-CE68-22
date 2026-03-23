import math
from datetime import datetime, timedelta, timezone
from typing import List
from app.schemas.schedule import ScheduleCreate
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from croniter import croniter
from app.services.job import job_service
from app.services.asset import asset_service

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schedules import Schedule
from app.models.assets import Asset
from app.models.jobs import Job, JobStatus

class ScheduleService:

    async def get_all_schedules(self, project_id: int, page: int, size: int, db: AsyncSession, search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูลโปรเจกต์ทั้งหมดของ user นั้น"""
        query = (
            sa.select(
                Schedule, 
                Asset.name.label("asset_name"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.FAILED).label("failed"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.COMPLETED).label("completed"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.RUNNING).label("running"),
                sa.sql.func.count(Job.id).filter(Job.status == JobStatus.PENDING).label("pending")
            )
            .join(Asset, Schedule.asset_id == Asset.id)
            .join(Job, Schedule.id == Job.schedule_id, isouter=True)
            .where(Schedule.project_id == project_id)
            .group_by(Schedule.id, Asset.name)
        )

        if search:
            query = query.where(Schedule.name.ilike(f"%{search}%"))

        if filter and filter != "ALL":
            if filter == "not_repeat":
                query = query.where(Schedule.cron_expression == "Not Repeat")
            elif filter == "active":
                query = query.where(Schedule.is_active == True)
            elif filter == "expired":
                query = query.where(Schedule.is_active == False)

        count_query = sa.select(sa.sql.func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # 5. Execute and Format
        result = await db.execute(query)
        rows = result.all()

        paginated_items = []
        
        for row in rows:
            sch = row[0]       # The Schedule object
            asset_name = row[1] # The joined Asset name
            
            paginated_items.append({
                "id": sch.id,
                "project_id": sch.project_id,
                "name": sch.name,
                "asset_name": asset_name,
                "atk_type": sch.attack_type,
                "start_date": sch.start_date,
                "end_date": sch.end_date,
                "job_status": {
                    "failed": row.failed,
                    "finished": row.completed,
                    "ongoing": row.running,
                    "scheduled": row.pending,
                }
            })

        return {
            "total": total_count,
            "page": page,
            "size": size,
            "total_pages": math.ceil(total_count / size) if size > 0 else 0,
            "items": paginated_items
        }
    
    async def get_by_id(self, schedule_id: int, db: AsyncSession):
        query = sa.select(Schedule).where(Schedule.id == schedule_id)
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return None
        
        return {
            "schedule_id": schedule.id,
            "schedule_name": schedule.name,
            "project_id": schedule.project_id,
            "asset_id": schedule.asset_id,
            "cron_expression": schedule.cron_expression,
            "attack_type": schedule.cron_expression.lower(),
            "is_active": schedule.is_active,
            "start_date": schedule.start_date,
            "end_date": schedule.end_date,
            "created_at": schedule.created_at,
            "updated_at": schedule.updated_at
        }
    
    
    async def create_schedule(self, schedule_input: ScheduleCreate, user_id: str, db: AsyncSession):
        is_immediate = schedule_input.cron_expression in ["Not Repeat", "now", ""]
        now = datetime.now(timezone.utc)

        if schedule_input.cron_expression == "Not Repeat":
            end_date = None
        else:
            end_date = schedule_input.end_date
        
        new_schedule_db = Schedule(
            name = schedule_input.name,
            project_id = schedule_input.project_id,
            asset_id = schedule_input.asset,
            cron_expression = schedule_input.cron_expression,
            attack_type = schedule_input.atk_type.upper(),
            is_active = True,
            start_date = schedule_input.start_date or now,
            end_date = end_date,
            created_by = user_id,
            last_run_date = now if is_immediate else None
        )

        try:
            db.add(new_schedule_db)
            await db.commit()
            await db.refresh(new_schedule_db)
            
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create schedule")
        
        new_schedule = {
            "schedule_id": new_schedule_db.id,
            "schedule_name": new_schedule_db.name,
            "project_id": new_schedule_db.project_id,
            "asset_id": new_schedule_db.asset_id,
            "cron_expression": new_schedule_db.cron_expression,
            "attack_type": new_schedule_db.attack_type,
            "is_active": new_schedule_db.is_active,
            "start_date": new_schedule_db.start_date,
            "end_date": new_schedule_db.end_date,
            "created_at": new_schedule_db.created_at,
            "updated_at": new_schedule_db.updated_at,
            "created_by": new_schedule_db.created_by,
        }

        if is_immediate:
            import asyncio
            from app.core.db import async_session
            from app.services.job import job_service
            asyncio.create_task(job_service.dispatch_job(schedule_data=new_schedule_db, session=async_session))

        # Only return non-sensitive info
        return {
            "schedule_id": new_schedule["schedule_id"],
            "schedule_name": new_schedule["schedule_name"],
            "schedule_atk_type": new_schedule["attack_type"],
        }

    async def edit_schedule(self, schedule_id: int, schedule_input: ScheduleCreate, db: AsyncSession):
        query = sa.select(Schedule).where(Schedule.id == schedule_id)
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return None
        

        schedule.name = schedule_input.name
        schedule.project_id = schedule_input.project_id
        schedule.asset_id = schedule_input.asset
        schedule.cron_expression = schedule_input.cron_expression
        schedule.attack_type = schedule_input.atk_type.upper()
        schedule.start_date = schedule_input.start_date
        schedule.end_date = schedule_input.end_date

        try:
            await db.commit()
            await db.refresh(schedule) # This ensures all DB-generated fields are loaded

            return {
                "schedule_id": schedule.id,
                "schedule_name": schedule.name,
                "schedule_atk_type": schedule.attack_type,
            }

        except Exception as e:
            await db.rollback()
            # Log the error so you can see it in the terminal
            print(f"Database Error: {e}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")
                
    async def delete_schedule(self, schedule_id: int, db: AsyncSession) -> bool:
        query = sa.select(Schedule).where(Schedule.id == schedule_id)
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return None
        
        try:
            # 2. Delete using the session
            await db.delete(schedule)
            
            # 3. Commit the transaction
            await db.commit()
            return True
        except Exception as e:
            # 4. Rollback if something goes wrong (e.g., Foreign Key constraint)
            await db.rollback()
            print(f"Delete Error: {e}")
            return False
    
    def get_schedule_ids_by_project_id(self, project_id: int):
        schedules = self._read_json()
        schedule_ids = []
        for schedule in schedules:
            if schedule["project_id"] == project_id:
                schedule_ids.append(schedule["schedule_id"])

        return schedule_ids
     
    async def get_due_schedules(self, db: AsyncSession) -> List[Schedule]:
        now = datetime.now(timezone.utc)
        now_truncated = now.replace(second=0, microsecond=0)

        # 1. ดึงเฉพาะงานที่ "มีโอกาส" จะรันได้ออกมาจาก DB ก่อน (SQL Optimization)
        query = sa.select(Schedule).where(
            Schedule.is_active == True,
            sa.or_(Schedule.start_date == None, Schedule.start_date <= now),
            sa.or_(Schedule.end_date == None, Schedule.end_date >= now)
        )

        result = await db.execute(query)
        schedules = result.scalars().all()

        due_schedules = []
        for sch in schedules:
            # ป้องกันการรันซ้ำในนาทีเดียวกัน (ถ้าเพิ่งรันไปตอนต้นนาที ไม่ต้องรันอีก)
            if sch.last_run_date and sch.last_run_date.replace(second=0, microsecond=0) == now_truncated:
                continue

            # --- กรณีที่ 1: รันครั้งเดียว (Not Repeat) ---
            if sch.cron_expression == "Not Repeat":
                # ถ้านาทีนี้ >= start_date และยังไม่เคยรันเลย ให้รันได้
                if not sch.last_run_date:
                    due_schedules.append(sch)
                continue

            # --- กรณีที่ 2: รันตาม Cron ---
            expressions = [e.strip() for e in sch.cron_expression.split("Z") if e.strip()]
            for expr in expressions:
                try:
                    # เช็กว่ารอบที่ควรจะรันล่าสุด (prev) คือนาทีปัจจุบันหรือไม่
                    it = croniter(expr, now_truncated + timedelta(seconds=1))
                    prev_run = it.get_prev(datetime)
                    
                    if prev_run == now_truncated:
                        due_schedules.append(sch)
                        break 
                except Exception:
                    continue

        return due_schedules
    
    async def deactivate_schedule(self, schedule_id: int, db: AsyncSession):
        schedule = await db.get(Schedule, schedule_id)

        if schedule:
            schedule.is_active = False # 2. เปลี่ยนค่าที่ตัวแปร
            await db.commit()          # 3. บันทึก (SQLAlchemy จะสร้าง UPDATE ให้เอง)
            await db.refresh(schedule) # 4. ดึงค่าล่าสุดจาก DB กลับมา
            return True
        return False


        
# สร้าง instance ของ Service เพื่อใช้งาน
schedule_service = ScheduleService()