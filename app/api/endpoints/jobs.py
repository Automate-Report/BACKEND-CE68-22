from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.schemas.job import JobStatusPayload, JobStatusResponse, CountStatusResponse
from app.schemas.pagination import PaginatedResponse
from app.services.worker import worker_service
from app.services.job import job_service
from app.deps.auth import get_current_user

router = APIRouter()

# update job status
@router.post("/update_status/", status_code=210)
def update_status_job(payload:  JobStatusPayload, current_worker: int = Depends(worker_service.verify_token)):
    success = job_service.update_job_status(payload.job_id, payload.status)
    return success

@router.get("/schedule/{schedule_id}", response_model=PaginatedResponse[JobStatusResponse])
async def get_jobs_by_schedule(
    schedule_id: int,
    user_email: str = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
):
    print("yayay")
    result = job_service.get_job_by_schedule_id(
        schedule_id=schedule_id,
        user_email=user_email,
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order,
    )

    return result

@router.get("/number/{schedule_id}", response_model=CountStatusResponse)
def get_number_job_status_by_schedule_id(schedule_id: int):

    result = job_service.get_number_job_status_by_schedule_id(schedule_id)

    return result

