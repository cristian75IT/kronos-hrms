"""KRONOS Storage Manager - Minio integration."""
import io
import logging
from typing import Optional
from minio import Minio
from src.core.config import settings

logger = logging.getLogger(__name__)

class StorageManager:
    """Manager for file storage using MinIO."""
    
    def __init__(self) -> None:
        try:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_use_ssl,
            )
            self.bucket = settings.minio_bucket
            
            # Ensure bucket exists
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created storage bucket: {self.bucket}")
                
        except Exception as e:
            logger.error(f"Failed to initialize storage manager: {str(e)}")
            # Fail silently for now, but log the error
            self.client = None

    def upload_file(self, content: bytes, filename: str, content_type: str) -> Optional[str]:
        """Upload a file to storage and return the path/key."""
        if not self.client:
            return None
            
        try:
            data = io.BytesIO(content)
            self.client.put_object(
                self.bucket,
                filename,
                data,
                len(content),
                content_type=content_type,
            )
            return filename
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            return None

    def get_presigned_url(self, filename: str, expires_in: int = 3600) -> Optional[str]:
        """Get a temporary URL for file access."""
        if not self.client or not filename:
            return None
            
        try:
            return self.client.presigned_get_object(self.bucket, filename, expires=expires_in)
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            return None

    def delete_file(self, filename: str) -> bool:
        """Delete a file from storage."""
        if not self.client or not filename:
            return False
            
        try:
            self.client.remove_object(self.bucket, filename)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False

# Global instance
storage_manager = StorageManager()
