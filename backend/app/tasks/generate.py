"""
Image generation Celery task.
"""

import logging
from io import BytesIO

from PIL import Image

from app.celery_app import celery_app
from app.schemas.task import TaskStatus

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def generate_image_task(
    self,
    task_id: str,
    upload_id: str,
    style_id: str,
    custom_prompt: str | None,
    user_id: str,
) -> None:
    """
    Generate styled image from uploaded artwork.

    Args:
        task_id: Task identifier
        upload_id: Upload ID from artwork upload
        style_id: Style to apply
        custom_prompt: Optional custom prompt
        user_id: User ID
    """
    from app.services.storage import StorageService
    from app.services.task import TaskService

    task_service = TaskService()
    storage = StorageService()

    try:
        task_service.update_status(task_id, TaskStatus.PROCESSING)

        # Download upload - try both .png and .jpeg
        upload_key_png = f"uploads/{user_id}/{upload_id}.png"
        upload_key_jpeg = f"uploads/{user_id}/{upload_id}.jpeg"

        try:
            image_data = storage._client.get_object(
                Bucket=storage._bucket,
                Key=upload_key_png,
            )["Body"].read()
        except Exception:
            image_data = storage._client.get_object(
                Bucket=storage._bucket,
                Key=upload_key_jpeg,
            )["Body"].read()

        image = Image.open(BytesIO(image_data))

        # Run inference (placeholder - actual AI pipeline in TICKET-010)
        logger.info(f"Running inference for task {task_id} with style {style_id}")
        result = image  # Placeholder - replace with actual pipeline

        # Upload result
        result_key = f"results/{user_id}/{task_id}.png"
        buffer = BytesIO()
        result.save(buffer, format="PNG")
        buffer.seek(0)
        storage.upload(result_key, buffer.getvalue(), "image/png")

        # Get presigned URL
        result_url = storage.get_presigned_url(result_key)

        task_service.update_status(task_id, TaskStatus.COMPLETE, result_url=result_url)
        logger.info(f"Task {task_id} completed successfully")

    except Exception as exc:
        logger.error(f"Task {task_id} failed: {exc}")
        task_service.update_status(task_id, TaskStatus.FAILED, error=str(exc))
        raise self.retry(exc=exc, countdown=5) from exc
