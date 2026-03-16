from pydantic import BaseModel
from datetime import datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str

class UserInfo(BaseModel):
    email: str
    firstname: str
    lastname: str
    role: str
    joinned_at: datetime

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database

class ChangeRole(BaseModel):
    email: str
    role: str