"""
Generate router for image generation endpoints.
"""

import uuid
from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user_id
from app.schemas.task import (
    GenerateImageRequest,
    GenerateImageResponse,
    TaskStatus,
)
from app.services.storage import StorageService, get_storage
from app.services.task import TaskService, get_task_service

router = APIRouter(prefix="/generate", tags=["generate"])


class StyleId(StrEnum):
    """Valid style IDs."""

    PIXAR_3D = "pixar_3d"
    ANIME = "anime"
    WATERCOLOR = "watercolor"
    SKETCH = "sketch"
    OIL_PAINTING = "oil_painting"
    CARTOON = "cartoon"


@router.post(
    "/image",
    response_model=GenerateImageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_image(
    request: GenerateImageRequest,
    current_user: str | None = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
    storage: StorageService = Depends(get_storage),
) -> GenerateImageResponse:
    """
    Queue image generation task.

    Accepts upload_id, style_id, and optional custom_prompt.
    Returns task_id for polling status.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Validate style
    try:
        StyleId(request.style_id)
    except ValueError:
        valid_styles = [s.value for s in StyleId]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid style_id: {request.style_id}. Valid: {', '.join(valid_styles)}",
        ) from None

    # Check upload exists
    upload_key = f"uploads/{current_user}/{request.upload_id}.png"
    if not await storage.exists(upload_key):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Upload not found: {request.upload_id}",
        )

    # Create task
    task_id = str(uuid.uuid4())
    task_service.create_task(task_id, TaskStatus.QUEUED)

    # Queue Celery task
    from app.tasks.generate import generate_image_task

    generate_image_task.delay(
        task_id=task_id,
        upload_id=request.upload_id,
        style_id=request.style_id,
        custom_prompt=request.custom_prompt,
        user_id=current_user,
    )

    return GenerateImageResponse(
        task_id=task_id,
        status=TaskStatus.QUEUED,
        poll_url=f"/api/v1/tasks/{task_id}",
    )
