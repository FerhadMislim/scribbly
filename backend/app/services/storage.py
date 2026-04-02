"""
Storage service for S3/MinIO operations.
"""

import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    S3/MinIO storage service for file operations.

    Supports:
    - Upload files to S3/MinIO
    - Generate presigned URLs for downloads
    - Delete files
    """

    def __init__(self) -> None:
        """Initialize S3 client with MinIO configuration."""
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_KEY,
            aws_secret_access_key=settings.S3_SECRET,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )
        self._bucket = settings.S3_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            try:
                self._client.create_bucket(Bucket=self._bucket)
                logger.info(f"Created bucket: {self._bucket}")
            except ClientError as e:
                logger.warning(f"Could not create bucket: {e}")

    def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload file to S3/MinIO.

        Args:
            key: S3 key (path in bucket)
            data: File data as bytes
            content_type: MIME type

        Returns:
            S3 URL of uploaded file
        """
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            url = f"{settings.S3_ENDPOINT}/{self._bucket}/{key}"
            logger.info(f"Uploaded file: {key}")
            return url
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            raise RuntimeError(f"Failed to upload file: {e}") from e

    def get_presigned_url(
        self,
        key: str,
        expires_seconds: int = 3600,
    ) -> str:
        """
        Generate presigned URL for downloading a file.

        Args:
            key: S3 key
            expires_seconds: URL expiration time

        Returns:
            Presigned URL
        """
        try:
            url = self._client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": key,
                },
                ExpiresIn=expires_seconds,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise RuntimeError(f"Failed to generate presigned URL: {e}") from e

    def delete(self, key: str) -> None:
        """
        Delete file from S3/MinIO.

        Args:
            key: S3 key to delete
        """
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
            logger.info(f"Deleted file: {key}")
        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            raise RuntimeError(f"Failed to delete file: {e}") from e

    def exists(self, key: str) -> bool:
        """
        Check if file exists in S3/MinIO.

        Args:
            key: S3 key

        Returns:
            True if file exists
        """
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False


_storage_service: StorageService | None = None


def get_storage() -> StorageService:
    """Get or create storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
