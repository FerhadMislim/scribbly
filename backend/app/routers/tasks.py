"""
Tasks router for polling task status.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user_id
from app.schemas.task import TaskStatus, TaskStatusResponse
from app.services.task import TaskService, get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
)
async def get_task_status(
    task_id: str,
    current_user: str | None = Depends(get_current_user_id),
    task_service: TaskService = Depends(get_task_service),
) -> TaskStatusResponse:
    """
    Get task status by ID.

    Returns current status and result URL when complete.
    """
    task_data = task_service.get_status(task_id)

    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    task_status = TaskStatus(task_data["status"])

    return TaskStatusResponse(
        task_id=task_id,
        status=task_status,
        result_url=task_data.get("result_url"),
        error=task_data.get("error"),
        poll_url=f"/api/v1/tasks/{task_id}",
    )
