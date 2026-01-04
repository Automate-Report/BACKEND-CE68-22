from pydantic import BaseModel

class CredentialCreate(BaseModel):
    asset_id: int
    username: str
    password: str

class CredentialResponse(BaseModel):
    asset_id: int
    username: str
    password: str

    class Config:
        orm_mode = True