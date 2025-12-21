from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Import Router ที่เราสร้างไว้
from app.api.endpoints import projects, workers, access_keys

app = FastAPI(
    title="CE68-22 Backend API",
    description="API for Project (Master-Agent Architecture)",
    version="1.0.0",
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

# 3. ลงทะเบียน Router (เอา API Projects มาแปะเข้ากับ App หลัก)
# prefix="/projects" แปลว่า URL จะเป็น http://localhost:8000/projects/...
# tags=["Projects"] เอาไว้จัดหมวดหมู่ใน Swagger UI
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(workers.router, prefix="/workers", tags=["Workers"])
app.include_router(access_keys.router, prefix="/access-keys", tags=["Access Keys"])

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