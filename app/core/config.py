from pydantic_settings import BaseSettings

class AuthenSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    DATABASE_URL: str
    
class Settings(BaseSettings):
    PROJECT_NAME: str = "Corporate Agent"
    SECRET_KEY: str = "super-secret-key-fixed-value-1234567890" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
 
    class Config:
        env_file = ".env"

authen_settings = AuthenSettings()

settings = Settings()
