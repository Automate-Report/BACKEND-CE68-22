
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from typing import Optional
from datetime import datetime

# Import ของที่เราทำไว้
from app.schemas.worker import WorkerCreate, WorkerResponse, VerifyRequest
from app.schemas.pagination import PaginatedResponse
from app.services.worker import worker_service
from app.services.access_key import access_key_service



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

@router.post("/gen-key/{worker_id}")
def gen_access_key(worker_id: int):
    key = access_key_service.get_access_key_by_worker_id(worker_id)

    if not key:
        access_key_service.create_access_key(worker_id)
        return key
    
    raise HTTPException(status_code=404, detail="This worker has already access key.")


@router.post("/remove-key/{worker_id}")
def remove_access_key(worker_id: int):

    key = access_key_service.get_access_key_by_worker_id(worker_id)

    if not key:
        raise HTTPException(status_code=404, detail="This worker has not access key.")

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

@router.put("/{worker_id}", response_model=WorkerResponse)
async def update_worker(worker_id: int, worker_in: WorkerCreate):
    fake_current_user_id = 1
    updated_worker = worker_service.update_worker(
        worker_id=worker_id,
        worker_in=worker_in,
        user_id=fake_current_user_id
    )
    if not updated_worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return updated_worker

@router.get("/download/{worker_id}")
def download_worker_zip(
    # ใช้ Deps: ตรวจสอบว่าคนเรียกคือ User เว็บที่ล็อกอินแล้วเท่านั้น
    # current_user: dict = Depends(deps.get_current_web_user)
    worker_id: int,
):
    result = worker_service.download_worker(worker_id)

    return result

# Verify Access Key for Get Token
@router.post("/verify")
def verify_access_key(req: VerifyRequest):
    result = worker_service.verify_worker(req)

    return result

#HeartBeat
@router.post("/heartbeat")
def heartbeat(worker_id: int = Depends(worker_service.verify_token)): 
    # worker_id นี้ได้มาจากการแกะ Token ที่ถูกต้องแล้ว
    
    result = worker_service.update_heartbeat(worker_id)
    if not result:
        # กรณีนี้ยากที่จะเกิด ถ้า Token ผ่านแล้ว แต่เผื่อไว้
        raise HTTPException(status_code=404, detail="Worker not found")
        
    return {"status": "ok", "timestamp": datetime.utcnow()}
    
#Dummy task
@router.post("/submit-task")
def submit_task(data: dict = Body(...), current_worker_id: int = Depends(worker_service.verify_token)):
    print(f"Logged in worker is: {current_worker_id}")
    return data


