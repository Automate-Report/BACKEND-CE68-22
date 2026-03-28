import asyncio
import time

from datetime import datetime, timezone

from app.services.schedule import schedule_service
from app.services.job import job_service

from app.core.db import async_session

from app.services.watchdog import run_watchdog

async def system_schedule_task():
    print(f"✅ [System Task] Background Scheduler Started at {datetime.now()}")
    last_watchdog_run = 0

    while True:
        async with async_session() as db:
            try:
                due_schedules = await schedule_service.get_due_schedules(db)

                # --- เพิ่มส่วน Debug ตรงนี้ ---
                print(f"DEBUG: due_schedules  {due_schedules}")
                if due_schedules:
                    print(f"DEBUG: first item type: {type(due_schedules[0])}")
                # --------------------------

                for schedule in due_schedules:
                    # สร้าง Job + ส่ง Redis
                    success = await job_service.dispatch_job(
                        db=db,
                        schedule_data=schedule
                    )
                    if not success:
                        continue
                    
                    # ตรวจสอบเงื่อนไข Deactivate
                    cron_exp = schedule.cron_expression
                    is_not_repeat = (cron_exp == "Not Repeat")
                    end_date_str = schedule.end_date
                    
                    is_expired = False
                    if end_date_str:
                        try:
                            if isinstance(end_date_str, datetime):
                                end_date = end_date_str
                            else:
                                # 2. ถ้าเป็น String ให้จัดการตามมาตรฐาน ISO
                                # .replace("Z", "+00:00") จะพังถ้า end_date_str ไม่ใช่ String
                                end_date = datetime.fromisoformat(str(end_date_str).replace("Z", "+00:00"))

                            # 3. ทำให้เป็น Aware Datetime (UTC) เสมอ เพื่อการเปรียบเทียบที่แม่นยำ
                            if end_date.tzinfo is None:
                                end_date = end_date.replace(tzinfo=timezone.utc)

                            # 4. เปรียบเทียบกับเวลาปัจจุบัน
                            if datetime.now(timezone.utc) > end_date:
                                is_expired = True
                                
                        except Exception as e:
                            print(f"⚠️ Date parsing error: {e}")

                    if is_not_repeat or is_expired:
                        schedule_id = schedule.id
                        await schedule_service.deactivate_schedule(
                            schedule_id=schedule_id,
                            db=db
                        )
                        await db.commit()
                        print(f"🔒 [System Task] Deactivated: {schedule_id}")

                # Watchdog...
                current_time = time.time()
                if current_time - last_watchdog_run > 30:
                    await run_watchdog(db)
                    last_watchdog_run = current_time

            except asyncio.CancelledError:
                break
            except Exception as e:
                # error 'str' object has no attribute 'get' จะถูกจับได้ที่นี่
                print(f"❌ [System Task] Unexpected Error: {e}")

            await asyncio.sleep(10)