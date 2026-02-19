from pydantic import BaseModel
from datetime import datetime

class TagCreate(BaseModel):
    name: str

class TagsResponse(BaseModel):
    id: int
    name: str
    text_color: str
    bg_color: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database
