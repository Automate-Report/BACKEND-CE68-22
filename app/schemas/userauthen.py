from pydantic import BaseModel

class UserAuthen(BaseModel):
    email: str
    password: str
