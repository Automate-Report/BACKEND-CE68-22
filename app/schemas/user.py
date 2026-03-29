from pydantic import BaseModel

class PasswordPayload(BaseModel):
    old_password: str
    new_password: str

class InfoPayload(BaseModel):
    firstname: str
    lastname: str
    bio: str