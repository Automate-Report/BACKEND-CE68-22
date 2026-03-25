from app.services.minio import minio_service

# ฟังก์ชันสำหรับ Dependency Injection ใน API Routes
def get_minio():
    return minio_service