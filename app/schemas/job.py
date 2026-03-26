from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class JobWorkerPayload(BaseModel):
    job_id: int
    target_url: str
    attack_type: str
    credential: Optional[dict] = None
    thread_number: int

class JobStatusPayload(BaseModel):
    job_id: int
    status: str

class JobStatusResponse(BaseModel):
    id: int
    name: str
    worker_id: int
    worker_name: str
    status: str
    created_at: Optional[datetime] = None

class CountStatusResponse(BaseModel):
    pending: int
    running: int
    completed: int
    failed: int

class SummaryInfoByWorker(BaseModel):
    total_jobs: int
    total_completed: int
    total_failed: int
    total_findings: int

class GetJobByWorker(BaseModel):
    id: int
    name: str
    schedule_id: int
    schedule_name: str
    attack_type: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    vuln_count: int