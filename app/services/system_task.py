import asyncio
from datetime import datetime
from app.services.schedule import schedule_service
from app.services.job import job_service

async def system_schedule_task():
    """Background Task ที่จะรันตลอดเวลา"""
    print(f"✅ [System Task] Background Scheduler Started at {datetime.now()}")

    last_watchdog_run = 0

    while True:
        try:
            # หา Job ที่ถึงเวลา
            due_schedules = await schedule_service.get_due_schedules()

            for schedule in due_schedules:
                    # สร้าง Job + ส่ง Redis
                await job_service.dispatch_job(schedule)
                    
            current_time = datetime.time()
            if current_time - last_watchdog_run > 300:
                await job_service.run_watchdog()
                last_watchdog_run = current_time
            # หลับ 10 วินาที แล้วตื่นมาเช็คใหม่
            await asyncio.sleep(10)

        except asyncio.CancelledError:
            # จะโดนเรียกเมื่อ Lifespan สั่ง task.cancel()
            print("🧹 [System Task] Cleaning up resources before exit...")
            # เช่น ปิด Redis connection หรือบันทึก log สุดท้าย
        finally:
            print("🏁 [System Task] Task execution finished.")
        
        