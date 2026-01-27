
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from typing import Optional

# Import ของที่เราทำไว้
from app.core import security
from app.api import deps
from app.schemas.access_key import AccssKeyResponse
from app.services.access_key import access_key_service


router = APIRouter()

@router.post("/", response_model=AccssKeyResponse)
def create_worker():

    new_access_key = access_key_service.create_access_key()

    return new_access_key

@router.get("/{access_key_id}", response_model=AccssKeyResponse)
async def get_access_key_by_id(access_key_id: int):
    # เรียก Service เพื่อดึงข้อมูลตาม ID
    fake_current_user_id = 1
    worker = access_key_service.get_access_key_by_id(access_key_id)

    if not worker:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
        
    return worker

@router.get("/byWorkerId/{worker_id}", response_model=AccssKeyResponse)
async def get_access_key_by_worker_id(worker_id: int):
    # เรียก Service เพื่อดึงข้อมูลตาม ID
    fake_current_user_id = 1
    worker = access_key_service.get_access_key_by_worker_id(worker_id)

    if not worker:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
        
    return worker

@router.delete("/{access_key_id}")
async def delete_access_key(access_key_id: int):
    success = access_key_service.delete_access_key_by_id(access_key_id)

    if not success:
        raise HTTPException(status_code=404, detail="Access Key not found")
    return {"detail": "Access Key deleted successfully"}

