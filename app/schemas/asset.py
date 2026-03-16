from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AssetCreate(BaseModel):
    name: str
    project_id: int
    description: Optional[str] = None
    target: str
    type: str

class AssetResponse(BaseModel):
    id: int
    name: str
    project_id: int
    description: Optional[str] = None
    target: str
    type: str
    updated_at: datetime

class AssetListForChoose(BaseModel):
    name: str
    id: int
    target: str

    class Config:
        orm_mode = True