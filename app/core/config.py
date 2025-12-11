from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Corporate Agent"
    
    # ✅ ต้องกำหนดเป็นค่าคงที่ (ห้ามเปลี่ยน)
    SECRET_KEY: str = "super-secret-key-fixed-value-1234567890" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()