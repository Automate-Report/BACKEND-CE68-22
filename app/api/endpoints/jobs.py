from fastapi import APIRouter, Depends, Body
from typing import List
from app.schemas.job import JobStatusPayload, JobStatusResponse


from app.services.worker import worker_service
from app.services.job import job_service

router = APIRouter()

# update job status
@router.post("/update_status/", status_code=210)
def update_status_job(payload:  JobStatusPayload, current_worker: int = Depends(worker_service.verify_token)):
    success = job_service.update_job_status(payload.job_id, payload.status)
    return success

@router.get("/schedule/{schedule_id}", response_model=List[JobStatusResponse])
def get_jobs_by_schedule(schedule_id: int):
    jobs = job_service.get_job_by_schedule_id(schedule_id, "user@example.com")

    return jobs

