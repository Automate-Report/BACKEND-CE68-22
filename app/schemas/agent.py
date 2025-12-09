from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class WorkerCreate(BaseModel):
    name: str
    
class WorkerResponse(BaseModel):
    id: int
    name: str
    access_id: int
    job_ids: Optional[List[int]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database