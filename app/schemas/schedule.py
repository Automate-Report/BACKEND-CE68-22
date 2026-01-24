from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScheduleCreate(BaseModel):
    project_id: int
    name: str
    atk_type: str
    asset: int #จะให้ Front ส่งเป็น ID มาเลย
    worker: int #จะให้ Front ส่งเป็น ID มาเลย
    cron_expression: str #เช่น "0 0 * * *" (ทำที่ Front)
    start_date: datetime
    end_date: Optional[datetime] = None #ถ้าไม่ตั้ง Repeat จะไม่มีค่า end_date

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database