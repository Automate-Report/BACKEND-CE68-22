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
        
    def download_file_as_bytes(self, bucket_name: str, object_name: str) -> bytes:
        """Download a file from MinIO and return its content as bytes"""
        try:
            return self.client.get_object(bucket_name, object_name)
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
        
    def list_objects(self, bucket_name: str, prefix: str = None, recursive: bool = False):
        """List objects in a bucket (wrapper for minio client)"""
        try:
            # เรียกใช้ list_objects จากตัวแปร self.client (SDK ของ Minio)
            return self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive)
        except S3Error as e:
            raise Exception(f"Failed to list objects: {e}")

    def get_object(self, bucket_name: str, object_name: str):
        """Get an object (stream) from MinIO"""
        try:
            # คืนค่าเป็น response object เพื่อให้เอาไป .read() ต่อได้
            return self.client.get_object(bucket_name, object_name)
        except S3Error as e:
            raise Exception(f"Failed to get object: {e}")

# Global instance
minio_service = MinIOClient()