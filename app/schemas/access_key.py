from pydantic import BaseModel
from datetime import datetime

class AccssKeyResponse(BaseModel):
    id: int
    key: str
    created_at: datetime

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database