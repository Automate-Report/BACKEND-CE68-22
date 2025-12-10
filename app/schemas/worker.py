from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WorkerCreate(BaseModel):
    name: str
    access_key_id: str


class WorkerResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database