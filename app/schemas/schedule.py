from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScheduleItem(BaseModel):
    schedule_id: int
    schedule_name: str
    project_id: int
    asset_id: int
    cron_expression: str
    attack_type: str
    is_active: bool
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime

class JobStatus(BaseModel):
    failed: int
    finished: int
    ongoing: int
    scheduled: int

class ScheduleResponse(BaseModel):
    id: int
    project_id: int
    name: str
    asset_name: str
    atk_type: str
    start_date: Optional[datetime] = None 
    end_date: Optional[datetime] = None
    job_status: JobStatus
    
class ScheduleCreate(BaseModel):
    project_id: int
    name: str
    atk_type: str
    asset: int #จะให้ Front ส่งเป็น ID มาเลย
    cron_expression: str #เช่น "0 0 * * *" (ทำที่ Front)
    start_date: datetime
    end_date: datetime #ถ้าไม่ตั้ง Repeat end_date = start_date

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database