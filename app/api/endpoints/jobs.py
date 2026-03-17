from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.schemas.job import JobStatusPayload, JobStatusResponse, CountStatusResponse, SummaryInfoByWorker, GetJobByWorker
from app.schemas.pagination import PaginatedResponse
from app.services.worker import worker_service
from app.services.job import job_service
from app.services.schedule import schedule_service
from app.services.vulnerability import vuln_service

from app.deps.auth import get_current_user
from app.deps.worker import get_current_worker
from app.deps.role import get_current_project_role
from app.core.db import get_db

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()

# update job status
@router.post("/update_status/", status_code=210)
async def update_status_job(
    payload:  JobStatusPayload, 
    current_worker: int = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    success = await job_service.update_job_status(
        job_id=payload.job_id, 
        status=payload.status, 
        db=db
    )

    return success

@router.get("/schedule/{schedule_id}", response_model=PaginatedResponse[JobStatusResponse])
async def get_jobs_by_schedule(
    schedule_id: int,
    user_email: str = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):

    result = await job_service.get_job_by_schedule_id(
        schedule_id=schedule_id,
        user_email=user_email,
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order,
        db=db
    )

    return result

@router.get("/number/{schedule_id}", response_model=CountStatusResponse)
async def get_number_job_status_by_schedule_id(
    schedule_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):

    result = await job_service.get_number_job_status_by_schedule_id(
        schedule_id=schedule_id,
        db=db
    )

    return result

@router.get("/summary/{worker_id}", response_model=SummaryInfoByWorker)
async def get_summary_info_job_by_worker_id(
    worker_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    job_info = await job_service.get_summary_info_by_worker_id(worker_id, db)
    return job_info

@router.get("/worker/{worker_id}", response_model=PaginatedResponse[GetJobByWorker])
async def get_jobs_by_worker(
    worker_id: int,
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    "),
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    result = await job_service.get_job_by_worker_id(
        worker_id=worker_id,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order,
        db=db
    )

    items = result.get("items")

    for job in items:
        schedule = schedule_service.get_by_id(job.get("schedule_id"))
        vuln_cnt = vuln_service.cnt_vuln_by_job_id(job.get("id"))
        job["schedule_name"] = schedule["schedule_name"] if schedule else "Unknown"
        job["attack_type"] = schedule["attack_type"] if schedule else "Unknown"
        job["vuln_count"] = vuln_cnt

    result["items"] = items
    return result

