"""
Generate router for image generation endpoints.
"""

import uuid
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.dependencies import get_current_user_id
from app.schemas.task import (
    GenerateImageRequest,
    GenerateImageResponse,
    TaskStatus,
)
from app.services.storage import StorageService, get_storage
from app.services.task import TaskService, get_task_service

router = APIRouter(prefix="/generate", tags=["generate"])

AI_ENGINE_PATH = Path(__file__).resolve().parents[2] / "ai-engine"
if str(AI_ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_PATH))


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

    from style_manager import StyleManager

    style_manager = StyleManager()
    valid_styles = style_manager.get_style_ids()
    if request.style_id not in valid_styles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid style_id: {request.style_id}. Valid: {', '.join(valid_styles)}",
        )

    # Check upload exists - try both .png and .jpeg
    upload_key_png = f"uploads/{current_user}/{request.upload_id}.png"
    upload_key_jpeg = f"uploads/{current_user}/{request.upload_id}.jpeg"

    if not (storage.exists(upload_key_png) or storage.exists(upload_key_jpeg)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Upload not found: {request.upload_id}",
        )

    # Create task
    task_id = str(uuid.uuid4())
    task_service.create_task(task_id, TaskStatus.QUEUED)

    # Queue Celery task (import inside to avoid loading torch in backend)
    from app.tasks.generate import generate_image_task

    generate_image_task.delay(
        task_id=task_id,
        upload_id=request.upload_id,
        style_id=request.style_id,
        custom_prompt=request.custom_prompt,
        user_id=current_user,
        preferred_device="cuda" if settings.GPU_ENABLED else "auto",
    )

    return GenerateImageResponse(
        task_id=task_id,
        status=TaskStatus.QUEUED,
        poll_url=f"/api/v1/tasks/{task_id}",
    )
