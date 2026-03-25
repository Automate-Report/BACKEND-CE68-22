from minio import Minio
from minio.error import S3Error
from app.core.config import settings

class MinIOClient:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

    def check_bucket(self, bucket_name: str):
        return self.client.bucket_exists(bucket_name)

    def upload_file(self, bucket_name: str, object_name: str, file_path: str, content_type: str = None):
        """Upload a file to MinIO"""
        try:
            self.client.fput_object(bucket_name, object_name, file_path, content_type=content_type)
            return True
        except S3Error as e:
            raise Exception(f"Failed to upload file: {e}")

    def download_file(self, bucket_name: str, object_name: str, file_path: str):
        """Download a file from MinIO"""
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            return True
        except S3Error as e:
            raise Exception(f"Failed to download file: {e}")

    def delete_file(self, bucket_name: str, object_name: str):
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(bucket_name, object_name)
            return True
        except S3Error as e:
            raise Exception(f"Failed to delete file: {e}")

    def get_presigned_url(self, bucket_name: str, object_name: str, expires: int = 3600):
        """Generate a presigned URL for an object"""
        try:
            url = self.client.presigned_get_object(bucket_name, object_name, expires=expires)
            return url
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

# Global instance
minio_service = MinIOClient()