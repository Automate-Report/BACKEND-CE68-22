from pydantic_settings import BaseSettings
    
class Settings(BaseSettings):
    PROJECT_NAME: str = "Corporate Agent"
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    DATABASE_URL: str
    BACKLIST_REDIS_URL: str
    JOBS_REDIS_URL: str

    # Authentication Settings
    SECRET_KEY: str 
    ALGORITHM: str 

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    FRONTEND_URL: str

    # Session Secret Key
    SESSION_SECRET_KEY: str

    EMBEDED_KEY: str

    # MinIO Settings
    # MINIO_ENDPOINT: str
    # MINIO_ACCESS_KEY: str
    # MINIO_SECRET_KEY: str
    # MINIO_SECURE: bool = False

    class Config:
        env_file = ".env"



settings = Settings()
