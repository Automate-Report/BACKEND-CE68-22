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
        
        new_schedule_db = Schedule(
            name = schedule_input.name,
            project_id = schedule_input.project_id,
            asset_id = schedule_input.asset,
            cron_expression = schedule_input.cron_expression,
            attack_type = schedule_input.atk_type.upper(),
            is_active = True,
            start_date = schedule_input.start_date,
            end_date = schedule_input.end_date,
            created_by = user_id,
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
            from app.services.job import job_service
            asyncio.create_task(job_service.dispatch_job(schedule_data=new_schedule, db=db))

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
    
    async def get_due_schedules(self, db: AsyncSession) -> List[Schedule]:
        now = datetime.now(timezone.utc)
        now_truncated = now.replace(second=0, microsecond=0)

        query = (
            sa.select(Schedule)
            .where(
                Schedule.is_active == True,
                sa.or_(
                    Schedule.start_date == None, 
                    Schedule.start_date <= now
                ),
                sa.or_(
                    Schedule.end_date == None,
                    Schedule.end_date >= now
                )
            )
        )

        result = await db.execute(query)
        schedules = result.scalars().all()

        due_schedules = []
        for sch in schedules:
            if sch.cron_expression == "Not Repeat":
                # For one-time jobs, we usually check if they've been run already
                # or if 'now' is within a small window of their start_date
                due_schedules.append(sch)
                continue

            # 3. Handle Cron Expressions
            # Split by your delimiter (e.g., 'Z') if you store multiple crons
            expressions = [e.strip() for e in sch.cron_expression.split("Z") if e.strip()]
            
            for expr in expressions:
                try:
                    # Use croniter to see if the 'prev' run was exactly 'now'
                    it = croniter(expr, now_truncated + timedelta(seconds=1))
                    prev_run = it.get_prev(datetime)
                    
                    if prev_run == now_truncated:
                        due_schedules.append(sch)
                        break 
                except Exception:
                    continue

        return due_schedules
    
    async def deactivate_schedule(self, schedule_id: int, db: AsyncSession):
        query = (
            sa.update(Schedule)
            .where(Schedule.id == schedule_id)
            .values(is_active=False, updated_at=sa.func.now())
        )
        await db.execute(query)
        await db.commit()

        
# สร้าง instance ของ Service เพื่อใช้งาน
schedule_service = ScheduleService()