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
    role: str = "owner"
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database

class ProjectSummaryResponese(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    role: str = "owner"
    assets_cnt: int
    vuln_cnt: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database
