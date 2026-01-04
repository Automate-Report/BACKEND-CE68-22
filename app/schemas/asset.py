from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AssetCreate(BaseModel):
    name: str
    project_id: int
    credential_id: int
    description: Optional[str] = None
    target: str
    type: str

class AssetResponse(BaseModel):
    id: int
    name: str
    project_id: int
    credential_id: int
    description: Optional[str] = None
    target: str
    type: str
    updated_at: datetime

    class Config:
        orm_mode = True