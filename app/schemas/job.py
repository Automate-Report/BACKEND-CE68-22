from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class JobWorkerPayload(BaseModel):
    job_id: int
    target_url: str
    attack_type: str

class JobStatusPayload(BaseModel):
    job_id: int
    status: str

