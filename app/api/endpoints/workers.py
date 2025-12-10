import io
import zipfile
import json
import os
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from cryptography.fernet import Fernet

# Import ของที่เราทำไว้
from app.core import security
from app.api import deps
from app.schemas.worker import WorkerCreate, WorkerResponse
from app.services.worker import worker_service

# from cryptography.fernet import Fernet
# print(Fernet.generate_key().decode())
# คุณจะได้ String ยาวๆ เช่น "Xj-9...=" ให้ Copy เก็บไว้

ENCRYPTION_KEY = b'gPN8qnR_vSIySogiV5QJBJcsWKoEBYBmebJPdy5rgSs=' 
cipher = Fernet(ENCRYPTION_KEY)

router = APIRouter()

@router.post("/", response_model=WorkerResponse)
def create_worker(worker_in: WorkerCreate):
    fake_user_id = 1

    new_worker = worker_service.create_worker(worker_in, fake_user_id)

    return new_worker

@router.get("/download-worker")
def download_worker_zip(
    # 1. ใช้ Deps: ตรวจสอบว่าคนเรียกคือ User เว็บที่ล็อกอินแล้วเท่านั้น
    # current_user: dict = Depends(deps.get_current_web_user)
):
    """
    API สำหรับ User กดดาวน์โหลด Agent
    ระบบจะสร้างไฟล์ Zip ที่ข้างในมี:
    1. worker_agent.exe (โปรแกรมหลัก)
    2. secret.dat (ไฟล์ความลับที่มี Token เฉพาะตัว ฝังมาให้เลย)
    3. config.dat (ค่าตั้งค่าเริ่มต้น)
    """

    # 1. Mock User ขึ้นมาเอง (หลอกระบบว่าเป็น admin)
    current_user = {"sub": "test_dev_user", "role": "user"}

    # --- A. หาไฟล์ EXE ต้นฉบับ ---
    # (ต้องมั่นใจว่า Build ไฟล์ .exe มาวางไว้ตรงนี้แล้ว)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    EXE_PATH = os.path.join(BASE_DIR, "static", "bin", "worker_agent.exe")
    
    if not os.path.exists(EXE_PATH):
        # ถ้าหาไม่เจอ ให้ return error 500
        return Response(content="Server Error: Worker executable not found.", status_code=500)

    # --- B. สร้าง Identity ใหม่ให้ Agent ---
    new_agent_id = str(uuid.uuid4())
    
    # 2. ใช้ Security: สร้าง Token อายุยาว (10 ปี) โดยระบุ role="agent"
    agent_token = security.create_token(
        data={
            "sub": new_agent_id,        # ID ของ Agent
            "role": "agent",            # สำคัญ! ระบุ Role เพื่อให้ผ่าน deps.get_current_agent
            "owner": current_user["sub"] # ผูกกับ User คนที่กดโหลด
        },
        expires_delta=timedelta(days=1) 
    )

    # --- C. เตรียมเนื้อหาไฟล์ Config ---
    
    # ไฟล์ความลับ (Token)
    secret_data = {
        "agent_id": new_agent_id,
        "access_token": agent_token,
        "owner": current_user["sub"],
        "created_at": str(datetime.now())
    }
    
    # ไฟล์ Config ทั่วไป
    config_data = {
        "api_url": "http://127.0.0.1:8000", # หรือ URL ของ Production
        "task_interval_seconds": 60,
        "log_level": "INFO"
    }

    encrypted_secret = cipher.encrypt(json.dumps(secret_data).encode())
    encrypted_config = cipher.encrypt(json.dumps(config_data).encode())

    # --- D. แพ็คใส่ ZIP (In-Memory) ---
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. ใส่ไฟล์ .exe
        zip_file.write(EXE_PATH, arcname="worker_agent.exe")
        
        # 2. ใส่ไฟล์ .worker_secret (แปลง dict -> json string)
        zip_file.writestr("secret.dat", encrypted_secret)
        
        # 3. ใส่ไฟล์ worker_config.json
        zip_file.writestr("config.dat", encrypted_config)

    # เลื่อน Pointer กลับไปหัวแถว เตรียมส่งออก
    zip_buffer.seek(0)

    # --- E. ส่งกลับให้ Browser ดาวน์โหลด ---
    headers = {
        "Content-Disposition": f'attachment; filename="worker_agent_{new_agent_id[:8]}.zip"'
    }
    
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip", 
        headers=headers
    )

