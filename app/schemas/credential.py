from pydantic import BaseModel

class CredentialCreate(BaseModel):
    username: str
    password: str

class CredentialResponse(BaseModel):
    id: int
    username: str
    password: str

    class Config:
        orm_mode = True