from pydantic import BaseModel
from datetime import datetime

class AssetCredentialCreate(BaseModel):
    asset_id: int
    username: str
    password: str

class AssetCredentialResponse(BaseModel):
    id: int
    asset_id: int
    username: str
    password: str
    updated_at: datetime

    class Config:
        orm_mode = True