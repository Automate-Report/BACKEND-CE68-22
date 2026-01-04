from pydantic import BaseModel
from datetime import datetime

class AssetCreate(BaseModel):
    name: str
    project_id: int
    description: str
    target: str
    type: str

class AssetResponse(BaseModel):
    name: str
    project_id: int
    description: str
    target: str
    type: str
    updated_at: datetime

    class Config:
        orm_mode = True