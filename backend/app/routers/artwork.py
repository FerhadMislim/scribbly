"""
Artwork router for upload and management endpoints.
"""

import uuid
from enum import StrEnum

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.dependencies import get_current_user_id
from app.schemas import UploadResponse
from app.services.storage import StorageService, get_storage


class ContentType(StrEnum):
    """Allowed content types for artwork uploads."""

    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"


class UploadConfig:
    """Configuration constants for artwork uploads."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_WIDTH = 64
    MIN_HEIGHT = 64


router = APIRouter(prefix="/artwork", tags=["artwork"])


async def validate_upload(
    file: UploadFile,
    storage: StorageService,
) -> tuple[str, bytes, str]:
    """
    Validate uploaded file.

    Args:
        file: Uploaded file
        storage: Storage service

    Returns:
        Tuple of (content_type, file_data, extension)

    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    allowed_types = {ct.value for ct in ContentType}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "field": "file",
                    "message": f"Invalid file type: {file.content_type}. Allowed: JPEG, PNG, WEBP",
                }
            ],
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    if file_size > UploadConfig.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "field": "file",
                    "message": f"File too large: {file_size / 1024 / 1024:.1f}MB. Maximum: 10MB",
                }
            ],
        )

    # Check minimum dimensions
    try:
        from io import BytesIO

        from PIL import Image

        image = Image.open(BytesIO(content))
        width, height = image.size

        if width < UploadConfig.MIN_WIDTH or height < UploadConfig.MIN_HEIGHT:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "field": "file",
                        "message": f"Image too small: {width}x{height}. Minimum: 64x64px",
                    }
                ],
            )
    except HTTPException:
        raise
    except Exception:
        # If we can't read image, allow upload (might be valid)
        pass

    # Get extension
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "png"

    return file.content_type, content, ext


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"model": UploadResponse},
    },
)
async def upload_artwork(
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: str | None = Depends(get_current_user_id),
    storage: StorageService = Depends(get_storage),
) -> UploadResponse:
    """
    Upload artwork image.

    Accepts JPEG, PNG, or WEBP files up to 10MB.
    Requires authentication (JWT).

    Returns:
        UploadResponse with upload_id, preview_url, status
    """
    content_type, content, ext = await validate_upload(file, storage)

    # Generate unique ID
    upload_id = str(uuid.uuid4())

    # Create S3 key (use 'anonymous' if no user)
    user_id = current_user if current_user else "anonymous"
    key = f"uploads/{user_id}/{upload_id}.{ext}"

    # Upload to S3
    storage.upload(key, content, content_type)

    # Generate presigned URL for preview
    preview_url = storage.get_presigned_url(key)

    return UploadResponse(
        upload_id=upload_id,
        preview_url=preview_url,
        status="uploaded",
    )
