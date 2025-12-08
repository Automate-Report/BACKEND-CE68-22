from pydantic_settings import BaseSettings

class AuthenSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

authen_settings = AuthenSettings()
