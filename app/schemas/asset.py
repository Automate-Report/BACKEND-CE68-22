from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AssetCreate(BaseModel):
    name: str
    project_id: int
    credential_id: Optional[int] = None
    description: str
    target: str
    type: str

class AssetResponse(BaseModel):
    name: str
    project_id: int
    credential_id: Optional[int] = None
    description: str
    target: str
    type: str
    updated_at: str

    class Config:
        orm_mode = True