import io
import zipfile
import json

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

@router.post("/download/{worker_id}")
def download_worker_zip(
    # ใช้ Deps: ตรวจสอบว่าคนเรียกคือ User เว็บที่ล็อกอินแล้วเท่านั้น
    # current_user: dict = Depends(deps.get_current_web_user)
    worker_id: int,
    currebt_user: dict
):
    """
    API สำหรับ User กดดาวน์โหลด Agent
    ระบบจะสร้างไฟล์ Zip ที่ข้างในมี:
    1. worker_agent.exe (โปรแกรมหลัก)
    2. secret.dat (ไฟล์ความลับที่มี Token เฉพาะตัว ฝังมาให้เลย)
    3. config.dat (ค่าตั้งค่าเริ่มต้น)
    """

    # 1. Mock User ขึ้นมาเอง (หลอกระบบว่าเป็น admin)
    fake_current_user = {"sub": "test_dev_user", "role": "user"}

    result = worker_service.download_worker(
        worker_id=worker_id,
        current_user=fake_current_user
    )

    return result

