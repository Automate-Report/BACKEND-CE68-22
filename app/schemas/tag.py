from pydantic import BaseModel

class TagCreate(BaseModel):
    name: str

class TagsResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database
