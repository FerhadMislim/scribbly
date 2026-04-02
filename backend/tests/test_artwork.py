"""
Tests for artwork upload endpoint.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestStorageService:
    """Tests for StorageService."""

    @pytest.mark.asyncio
    async def test_upload_success(self):
        """Test successful file upload."""
        with patch("app.services.storage.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.put_object = MagicMock()
            mock_client.head_bucket = MagicMock()
            mock_boto.return_value = mock_client

            from app.services.storage import StorageService

            service = StorageService()
            url = await service.upload("test/key.png", b"test data", "image/png")

            mock_client.put_object.assert_called_once()
            assert "test/key.png" in url

    @pytest.mark.asyncio
    async def test_get_presigned_url(self):
        """Test presigned URL generation."""
        with patch("app.services.storage.boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.generate_presigned_url = MagicMock(return_value="https://presigned.url")
            mock_client.head_bucket = MagicMock()
            mock_boto.return_value = mock_client

            from app.services.storage import StorageService

            service = StorageService()
            url = await service.get_presigned_url("test/key.png")

            assert url == "https://presigned.url"


class TestSchemas:
    """Tests for upload schemas."""

    def test_upload_response_schema(self):
        """Test UploadResponse schema."""
        from app.schemas import UploadResponse

        response = UploadResponse(
            upload_id="test-123",
            preview_url="https://example.com/preview",
            status="uploaded",
        )

        assert response.upload_id == "test-123"
        assert response.preview_url == "https://example.com/preview"
        assert response.status == "uploaded"

    def test_validation_error_detail_schema(self):
        """Test ValidationErrorDetail schema."""
        from app.schemas import ValidationErrorDetail

        error = ValidationErrorDetail(
            field="file",
            message="File too large",
        )

        assert error.field == "file"
        assert error.message == "File too large"
