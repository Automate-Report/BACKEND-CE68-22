
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from typing import Optional
from datetime import datetime

# Import ของที่เราทำไว้
from app.schemas.worker import WorkerCreate, WorkerResponse, VerifyRequest, HeartBeatPayload
from app.schemas.pagination import PaginatedResponse
from app.services.worker import worker_service
from app.services.access_key import access_key_service
from app.services.job import job_service
from app.services.userauthen import userauthen_service

from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role


router = APIRouter()

# Verify Access Key for Get Token
@router.post("/verify/")
def verify_access_key(req: VerifyRequest):
    result = worker_service.verify_worker(req)
    return result

#HeartBeat
@router.post("/heartbeat/")
def heartbeat(payload: HeartBeatPayload, worker_id: int = Depends(worker_service.verify_token)): 
    # worker_id นี้ได้มาจากการแกะ Token ที่ถูกต้องแล้ว
    
    result = worker_service.update_heartbeat(worker_id, payload)
    if not result:
        # กรณีนี้ยากที่จะเกิด ถ้า Token ผ่านแล้ว แต่เผื่อไว้
        raise HTTPException(status_code=404, detail="Worker not found")
        
    return {"status": "ok", "timestamp": datetime.utcnow()}

@router.post("/{project_id}")
def create_worker(project_id: int, worker_in: WorkerCreate, user = Depends(get_current_user), role = Depends(get_current_project_role)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")
    
    
    key = access_key_service.create_access_key()
    worker = worker_service.create_worker(
        worker_in=worker_in, 
        project_id=project_id,
        access_key_id=key["id"]
    )

    
    return { 
        "status": "Successfully!",
        "key": key["key"]
    }

@router.get("/{project_id}/all", response_model=PaginatedResponse[WorkerResponse])
async def get_all_workers_by_project_id(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    "),
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if not role:
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")

    result = worker_service.get_all_workers_by_project_id(
        project_id=project_id,
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order,
        search=search,
        filter=filter
    )

    items = result["items"]

    for worker in items:
        worker["owner_name"] = userauthen_service.get_username_by_id(worker["owner"])

    result["items"] = items

    return result

@router.get("/info/{project_id}")
async def get_info_workers_in_project(
    project_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if not role:
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")

    result = worker_service.get_summary_info(project_id=project_id)

    worker_ids = worker_service.get_all_worker_ids_by_project_id(project_id)

    for wid in worker_ids:
        total = job_service.get_total_job_by_worker_id(wid)
        result["total_jobs"]+=total
    return result

@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker_by_id(
    worker_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if not role:
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")
    
    worker = worker_service.get_worker_by_id(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
        
    return worker
 

@router.post("/regen-key/{worker_id}")
def re_access_key(
    worker_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    
    if role == "developer":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")

    worker = worker_service.get_worker_by_id(worker_id)

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found.")
    
    if role == "pentester" and worker.get("owner") != user["sub"]:
        raise HTTPException(status_code=403, detail="Worker does not belong to the user.")
    
    result = access_key_service.delete_access_key_by_id(worker.get("access_key_id"))

    key = access_key_service.create_access_key()
    
    result = worker_service.change_access_key(
        access_key_id=key.get("id"),
        worker_id=worker_id
    )

    return result

@router.delete("/{worker_id}")
async def delete_worker(
    worker_id: int, 
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if role != "owner":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")

    success = worker_service.delete_worker(
        worker_id=worker_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"detail": "Worker deleted successfully"}


@router.put("/{worker_id}", response_model=WorkerResponse)
async def update_worker(
    worker_id: int, 
    worker_in: WorkerCreate, 
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if role == "developer":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")

    updated_worker = worker_service.update_worker(
        worker_id=worker_id,
        worker_in=worker_in,
        user_id=user["sub"],
        role=role
    )
    if not updated_worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return updated_worker

@router.get("/download/{worker_id}")
def download_worker_zip(
    worker_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if role == "developer":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")
    
    result = worker_service.download_worker(worker_id, user["sub"])

    return result


@router.get("/unlink/{worker_id}")
async def disconnect_worker_from_host(
    worker_id: int, 
    role = Depends(get_current_project_role), 
    user = Depends(get_current_user),
):
    if role == "developer":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")
    
    worker_service.disconnect_worker(
        worker_id=worker_id,
        user_id=user["sub"],
        role=role
    )

@router.get("/unlink/all/{project_id}")
async def disconnect_all_worker_from_host_by_project(project_id: int, role = Depends(get_current_project_role), user = Depends(get_current_user)):
    if role != "owner":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")
    
    worker_service.disconnect_workers_in_project(
        project_id=project_id,
        user_id=user["sub"]
    )

@router.post("/{worker_id}/mark-downloaded")
def mark_worker_as_downloaded(worker_id: int, user = Depends(get_current_user)):
    worker_service.download_success(worker_id, user["sub"])
    return {"detail": "Worker marked as downloaded"}
    
#Dummy task
@router.post("/submit-task")
def submit_task(data: dict = Body(...), current_worker_id: int = Depends(worker_service.verify_token)):
    print(f"Logged in worker is: {current_worker_id}")
    return data


