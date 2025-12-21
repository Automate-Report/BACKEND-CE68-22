from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class WorkerCreate(BaseModel):
    name: str


class WorkerResponse(BaseModel):
    id: int
    name: str
    status: str
    isActive: bool
    access_key_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database

class HandshakeRequest(BaseModel):
    registration_token: str
    hostname: str

class AuthRequest(BaseModel):
    api_key: str

# Dummy
class TaskSubmitRequest(BaseModel):
    iteration: int
    status: str
    result: Optional[Any] = None #