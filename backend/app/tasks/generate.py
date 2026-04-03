"""
Image generation Celery task.
"""

import logging
from io import BytesIO

from PIL import Image

from app.celery_app import celery_app
from app.schemas.task import TaskStatus

logger = logging.getLogger(__name__)

DEFAULT_PROMPTS = {
    "pixar_3d": "3D animated character, pixar style, detailed, high quality",
    "anime": "anime style illustration, manga, vibrant colors",
    "watercolor": "watercolor painting, soft colors, artistic",
    "sketch": "pencil sketch, black and white, detailed linework",
    "oil_painting": "oil painting, classic art style, brushstrokes visible",
    "cartoon": "cartoon style, fun, colorful, animated",
}


@celery_app.task(bind=True, max_retries=2)
def generate_image_task(
    self,
    task_id: str,
    upload_id: str,
    style_id: str,
    custom_prompt: str | None,
    user_id: str,
    preferred_device: str = "auto",
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
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ai-engine"))

    from device import resolve_torch_device
    from pipeline import InferencePipeline
    from style_manager import StyleManager

    from app.config import settings
    from app.services.storage import StorageService
    from app.services.task import TaskService

    task_service = TaskService()
    storage = StorageService()

    try:
        task_service.update_status(task_id, TaskStatus.PROCESSING)

        upload_key_png = f"uploads/{user_id}/{upload_id}.png"
        upload_key_jpeg = f"uploads/{user_id}/{upload_id}.jpeg"

        try:
            response = storage._client.get_object(
                Bucket=storage._bucket,
                Key=upload_key_png,
            )
            image_data = response["Body"].read()
            logger.info(f"Found file: {upload_key_png}")
        except Exception:
            response = storage._client.get_object(
                Bucket=storage._bucket,
                Key=upload_key_jpeg,
            )
            image_data = response["Body"].read()
            logger.info(f"Found file: {upload_key_jpeg}")

        input_image = Image.open(BytesIO(image_data))

        style_manager = StyleManager()
        prompt, negative_prompt = style_manager.get_prompts(style_id, custom_prompt)
        generation_settings = style_manager.get_default_settings(style_id)

        device_preference = "cuda" if settings.GPU_ENABLED else preferred_device
        device, dtype = resolve_torch_device(device_preference)

        logger.info(f"Running inference for task {task_id} with style {style_id}")
        logger.info(f"Prompt: {prompt}")
        logger.info(f"Resolved inference device: {device}")

        pipeline = InferencePipeline(
            controlnet_id="lllyasviel/control_v11p_sd15_scribble",
            device=device,
            dtype=dtype,
            enable_xformers=device == "cuda",
            enable_cpu_offload=device == "cuda",
        )

        result = pipeline.generate(
            image=input_image,
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_steps=generation_settings.get("num_steps", 20),
            guidance_scale=generation_settings.get("guidance_scale", 7.5),
            image_size=512,
        )

        result_key = f"results/{user_id}/{task_id}.png"
        buffer = BytesIO()
        result.save(buffer, format="PNG")
        buffer.seek(0)
        storage.upload(result_key, buffer.getvalue(), "image/png")

        result_url = storage.get_presigned_url(result_key)

        task_service.update_status(task_id, TaskStatus.COMPLETE, result_url=result_url)
        logger.info(f"Task {task_id} completed successfully")

    except Exception as exc:
        logger.error(f"Task {task_id} failed: {exc}")
        task_service.update_status(task_id, TaskStatus.FAILED, error=str(exc))
        raise self.retry(exc=exc, countdown=5) from exc
    return None
