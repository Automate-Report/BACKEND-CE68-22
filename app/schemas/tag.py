from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TagCreate(BaseModel):
    user_id: str
    name: str

class TagsResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database
