
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from typing import Optional

# Import ของที่เราทำไว้
from app.core import security
from app.api import deps
from app.schemas.worker import WorkerCreate, WorkerResponse, HandshakeRequest, AuthRequest, WorkerAccessKey
from app.schemas.pagination import PaginatedResponse
from app.services.worker import worker_service


router = APIRouter()

@router.post("/", response_model=WorkerResponse)
def create_worker(worker_in: WorkerCreate):
    fake_user_id = 1

    new_worker = worker_service.create_worker(worker_in, fake_user_id)

    return new_worker

@router.get("/all", response_model=PaginatedResponse[WorkerResponse])
async def get_all_workers(
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
):
    # ในอนาคตต้องดึง user_id จาก Token (Auth) 
    # แต่ตอนนี้ Mock เป็น user_id = 1 ไปก่อน
    fake_current_user_id = 1

    result = worker_service.get_all_workers(
        user_id=fake_current_user_id,
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order
    )

    return result

@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker_by_id(worker_id: int):
    # เรียก Service เพื่อดึงข้อมูลตาม ID
    fake_current_user_id = 1
    worker = worker_service.get_worker_by_id(fake_current_user_id, worker_id)

    if not worker:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Worker not found")
        
    return worker

@router.post("/add-key")
def add_access_key(payload: WorkerAccessKey):

    worker = worker_service.add_access_key(
        worker_id=payload.worker_id,
        access_key_id=payload.access_key_id
    )

    return worker

@router.post("/remove-key/{worker_id}")
def remove_access_key(worker_id: int):

    worker = worker_service.remove_access_key(
        worker_id=worker_id
    )

    return worker

@router.delete("/{worker_id}")
async def delete_worker(worker_id: int):
    fake_current_user_id = 1
    success = worker_service.delete_worker(
        worker_id=worker_id,
        user_id=fake_current_user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"detail": "Worker deleted successfully"}

@router.post("/download/{worker_id}")
def download_worker_zip(
    # ใช้ Deps: ตรวจสอบว่าคนเรียกคือ User เว็บที่ล็อกอินแล้วเท่านั้น
    # current_user: dict = Depends(deps.get_current_web_user)
    worker_id: int,
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

@router.post("/handshake")
def worker_handshake(req: HandshakeRequest):
    result = worker_service.worker_handshake(
        req=req
    )

    return result

@router.post("/auth")
def agent_auth_exchange(req: AuthRequest):
    """
    Agent ใช้ API Key เพื่อขอ Session Token (อายุสั้น) สำหรับทำงาน
    """
    result = worker_service.auth(
        req=req
    )

    return result



@router.post("/submit-task") # dummy
def submit_task(
    data: dict = Body(...),
    # 👇 เอา comment ออก และใช้ deps.get_current_agent ตัวใหม่
    current_worker: dict = Depends(deps.get_current_agent)
):
    worker_id = current_worker["id"]
    print(f"📩 Task Received from Worker {worker_id}: {data}")
    
    # ส่งต่อให้ service บันทึกเวลา
    result = worker_service.process_task(worker_id, data) # (ถ้าคุณเขียน method นี้แล้ว)
    
    return result
