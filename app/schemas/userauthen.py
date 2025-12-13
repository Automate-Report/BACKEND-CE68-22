from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str