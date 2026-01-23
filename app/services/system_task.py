# import asyncio
# from core.database import AsyncSessionLocal
# from service.schedule_service import ScheduleService
# from service.job_service import JobService

# async def run_scheduler_loop():
#     """Background Task ที่จะรันตลอดเวลา"""
#     print("⏳ System Scheduler Started...")
#     while True:
#         async with AsyncSessionLocal() as db:
#             try:
#                 schedule_service = ScheduleService(db)
#                 job_service = JobService(db)

#                 # 1. หา Job ที่ถึงเวลา
#                 due_schedules = await schedule_service.get_due_schedules()

#                 for schedule in due_schedules:
#                     # 2. สร้าง Job + ส่ง Redis
#                     await job_service.dispatch_job(schedule)
                    
#                     # 3. อัปเดตเวลาครั้งถัดไป
#                     await schedule_service.update_next_run(schedule)

#             except Exception as e:
#                 print(f"❌ Scheduler Error: {e}")
        
#         # หลับ 10 วินาที แล้วตื่นมาเช็คใหม่
#         await asyncio.sleep(10)