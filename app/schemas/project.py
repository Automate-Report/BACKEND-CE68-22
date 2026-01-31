from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tag_ids: Optional[List[int]] = []

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attr = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database
