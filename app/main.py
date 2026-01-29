from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings

from app.services.system_task import system_schedule_task

import asyncio
from contextlib import asynccontextmanager

from app.core.db import engine, Base
from app.models import users, access_keys, asset_credentials, assets, jobs, logs, project_tags, projects, reports, schedules, tags, vulnerabilities, workers

# 1. Import Router ที่เราสร้างไว้
from app.api.endpoints import projects
from app.api.endpoints import auth
from app.api.endpoints import assets
from app.api.endpoints import asset_credentials
from app.api.endpoints import workers
from app.api.endpoints import access_keys
from app.api.endpoints import pentest_log
from app.api.endpoints import tag
from app.api.endpoints import project_tags
from app.api.endpoints import schedule

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # [Startup]: ทำงานตอนเปิด Server
    # async with engine.begin() as conn:
    #     # สร้าง Table ทั้งหมดถ้ายังไม่มี (เหมือน setup_db ของคุณ)
    #     await conn.run_sync(Base.metadata.create_all)
    
    # เริ่มรัน Background Task
    bg_task = asyncio.create_task(system_schedule_task())
    
    yield  # --- ช่วงที่ App รันปกติ ---

    # [Shutdown]: ทำงานตอนปิด Server
    bg_task.cancel() # ปิด Background Task
    try:
        await bg_task # รอให้หยุดรันตามลอจิกใน CancelledError
    except asyncio.CancelledError:
        pass
        
    await engine.dispose()
    print("✅ System Exit.")



app = FastAPI(
    title="CE68-22 Backend API",
    description="API for Project (Master-Agent Architecture)",
    version="1.0.0",
    lifespan=lifespan

)

# 2. ตั้งค่า CORS (สำคัญมาก! เพื่อให้ Next.js คุยกับ FastAPI ได้)
origins = [
    "http://localhost:3000",      # Next.js รันที่ port 3000
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # อนุญาตให้เว็บไหนยิงมาได้บ้าง
    allow_credentials=True,       # อนุญาตให้ส่ง Cookie/Token
    allow_methods=["*"],          # อนุญาตทุกท่า (GET, POST, PUT, DELETE)
    allow_headers=["*"],          # อนุญาตทุก Header
)

# Session (required by Authlib)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
)

# 3. ลงทะเบียน Router (เอา API Projects มาแปะเข้ากับ App หลัก)
# prefix="/projects" แปลว่า URL จะเป็น http://localhost:8000/projects/...
# tags=["Projects"] เอาไว้จัดหมวดหมู่ใน Swagger UI
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(assets.router, prefix="/assets", tags=["Assets"])
app.include_router(asset_credentials.router, prefix="/credentials", tags=["Credentials"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])
app.include_router(workers.router, prefix="/workers", tags=["Workers"])
app.include_router(access_keys.router, prefix="/access-keys", tags=["Access Keys"])
app.include_router(pentest_log.router, prefix="/pentest-logs", tags=["Pentest Logs"])

app.include_router(tag.router, prefix="/tags", tags=["Tags"])
app.include_router(project_tags.router, prefix="/project-tags", tags=["Project Tags"])

# 4. Health Check Endpoint (เอาไว้ยิงเช็คว่า Server ตายหรือยัง)

@app.get("/")
def read_root():
    return {
        "message": "CE68-22 Backend API",
        "status": "running",
        "docs_url": "/docs"       # บอกว่าคู่มือ API อยู่ที่ไหน
    }

# (Optional) สำหรับรันไฟล์นี้ตรงๆ ด้วยคำสั่ง python app/main.py
if __name__ == "__main__":
    import uvicorn
    # reload=True ช่วยให้แก้โค้ดแล้ว Server รีสตาร์ทเอง (เหมาะตอน Dev)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)