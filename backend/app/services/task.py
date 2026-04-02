"""
Task service for managing async task status.
"""

import logging

import redis

from app.config import settings
from app.schemas.task import TaskStatus

logger = logging.getLogger(__name__)

TASK_KEY_PREFIX = "task:"


class TaskService:
    """Service for managing task status in Redis."""

    def __init__(self) -> None:
        """Initialize Redis client."""
        self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _get_key(self, task_id: str) -> str:
        """Get Redis key for task."""
        return f"{TASK_KEY_PREFIX}{task_id}"

    def create_task(self, task_id: str, status: TaskStatus = TaskStatus.QUEUED) -> None:
        """Create a new task with initial status."""
        self._client.hset(
            self._get_key(task_id),
            mapping={
                "status": status.value,
                "created_at": str(int(self._client.time()[0])),
            },
        )
        logger.info(f"Created task {task_id} with status {status.value}")

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result_url: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update task status."""
        key = self._get_key(task_id)
        updates = {"status": status.value}
        if result_url:
            updates["result_url"] = result_url
        if error:
            updates["error"] = error
        if status in (TaskStatus.COMPLETE, TaskStatus.FAILED):
            updates["completed_at"] = str(int(self._client.time()[0]))

        self._client.hset(key, mapping=updates)
        logger.info(f"Updated task {task_id} to status {status.value}")

    def get_status(self, task_id: str) -> dict[str, str] | None:
        """Get task status."""
        data = self._client.hgetall(self._get_key(task_id))
        if not data:
            return None
        return data

    def delete_task(self, task_id: str) -> None:
        """Delete task."""
        self._client.delete(self._get_key(task_id))


_task_service: TaskService | None = None


def get_task_service() -> TaskService:
    """Get or create task service singleton."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service
