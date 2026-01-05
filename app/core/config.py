from pydantic_settings import BaseSettings

class AuthenSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"

authen_settings = AuthenSettings()
