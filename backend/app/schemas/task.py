"""
Task status schemas.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    """Task status enum."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskStatusResponse(BaseModel):
    """Response schema for task status."""

    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current status")
    result_url: str | None = Field(default=None, description="Result URL when complete")
    error: str | None = Field(default=None, description="Error message when failed")
    poll_url: str = Field(..., description="URL to poll for status")

    model_config = {"from_attributes": True}


class GenerateImageRequest(BaseModel):
    """Request schema for image generation."""

    upload_id: str = Field(..., description="Upload ID from previous step")
    style_id: str = Field(..., description="Style ID for transformation")
    custom_prompt: str | None = Field(
        default=None, description="Optional custom prompt"
    )


class GenerateImageResponse(BaseModel):
    """Response schema for image generation request."""

    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Initial status")
    poll_url: str = Field(..., description="URL to poll for status")
