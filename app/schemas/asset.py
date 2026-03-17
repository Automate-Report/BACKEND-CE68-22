from pydantic import BaseModel, ConfigDict, Field
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

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True # Allows you to create the model using either name
    )

class AssetListForChoose(BaseModel):
    name: str
    id: int
    target: str

    class Config:
        orm_mode = True