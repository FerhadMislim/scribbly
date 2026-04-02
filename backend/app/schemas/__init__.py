"""
Pydantic schemas for request/response validation.

Example schema:
```python
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
```
"""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response schema for successful upload."""

    upload_id: str = Field(..., description="Unique upload identifier")
    preview_url: str = Field(..., description="Presigned URL for preview")
    status: str = Field(default="uploaded", description="Upload status")


class ValidationErrorDetail(BaseModel):
    """Detail for field-level validation errors."""

    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Error message")


class UploadErrorResponse(BaseModel):
    """Response schema for upload validation errors."""

    detail: str | list[ValidationErrorDetail] = Field(
        ..., description="Error detail"
    )
