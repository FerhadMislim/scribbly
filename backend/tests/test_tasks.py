"""
Tests for task service.
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image


class TestTaskService:
    """Tests for TaskService."""

    def test_create_task(self):
        """Test task creation."""
        mock_client = MagicMock()
        mock_client.time.return_value = (1234567890,)

        with patch("app.services.task.redis.from_url") as mock_redis:
            mock_redis.return_value = mock_client

            from app.services.task import TaskService, TaskStatus

            service = TaskService()
            service.create_task("task-123", TaskStatus.QUEUED)

            mock_client.hset.assert_called_once()

    def test_update_status(self):
        """Test status update."""
        mock_client = MagicMock()
        mock_client.time.return_value = (1234567890,)

        with patch("app.services.task.redis.from_url") as mock_redis:
            mock_redis.return_value = mock_client

            from app.services.task import TaskService, TaskStatus

            service = TaskService()
            service.update_status("task-123", TaskStatus.PROCESSING)

            mock_client.hset.assert_called()

    def test_get_status(self):
        """Test getting task status."""
        mock_client = MagicMock()
        mock_client.hgetall.return_value = {
            "status": "queued",
            "created_at": "1234567890",
        }

        with patch("app.services.task.redis.from_url") as mock_redis:
            mock_redis.return_value = mock_client

            from app.services.task import TaskService

            service = TaskService()
            result = service.get_status("task-123")

            assert result["status"] == "queued"

    def test_get_status_not_found(self):
        """Test getting non-existent task."""
        mock_client = MagicMock()
        mock_client.hgetall.return_value = {}

        with patch("app.services.task.redis.from_url") as mock_redis:
            mock_redis.return_value = mock_client

            from app.services.task import TaskService

            service = TaskService()
            result = service.get_status("task-nonexistent")

            assert result is None


class TestTaskSchemas:
    """Tests for task schemas."""

    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        from app.schemas.task import TaskStatus

        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETE.value == "complete"
        assert TaskStatus.FAILED.value == "failed"

    def test_generate_image_request(self):
        """Test GenerateImageRequest schema."""
        from app.schemas.task import GenerateImageRequest

        req = GenerateImageRequest(
            upload_id="upload-123",
            style_id="anime",
            custom_prompt="a cute cat",
        )

        assert req.upload_id == "upload-123"
        assert req.style_id == "anime"
        assert req.custom_prompt == "a cute cat"

    def test_generate_image_response(self):
        """Test GenerateImageResponse schema."""
        from app.schemas.task import GenerateImageResponse, TaskStatus

        resp = GenerateImageResponse(
            task_id="task-123",
            status=TaskStatus.QUEUED,
            poll_url="/api/v1/tasks/task-123",
        )

        assert resp.task_id == "task-123"
        assert resp.status == TaskStatus.QUEUED

    def test_task_status_response(self):
        """Test TaskStatusResponse schema."""
        from app.schemas.task import TaskStatus, TaskStatusResponse

        resp = TaskStatusResponse(
            task_id="task-123",
            status=TaskStatus.COMPLETE,
            result_url="https://s3.example.com/result.png",
            poll_url="/api/v1/tasks/task-123",
        )

        assert resp.task_id == "task-123"
        assert resp.status == TaskStatus.COMPLETE
        assert resp.result_url == "https://s3.example.com/result.png"


class TestStyleValidation:
    """Tests for config-driven style validation."""

    def test_style_manager_contains_hand_drawn_pencil(self):
        """The new pencil style should be available to the API layer."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ai-engine"))

        from style_manager import StyleManager

        manager = StyleManager()

        assert "hand_drawn_pencil" in manager.get_style_ids()


class TestGenerateImageTask:
    """Tests for the Celery image generation task."""

    def test_generate_image_task_uses_style_manager_prompts(self):
        """Task should use StyleManager's current prompt API."""
        image = Image.new("RGB", (64, 64), color="white")
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()

        mock_storage = MagicMock()
        mock_storage._bucket = "scribbly-dev"
        mock_storage._client.get_object.return_value = {
            "Body": BytesIO(image_bytes),
        }
        mock_storage.get_presigned_url.return_value = "https://example.com/result.png"

        mock_task_service = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.generate.return_value = image
        mock_style_manager = MagicMock()
        mock_style_manager.get_prompts.return_value = ("pixar flowers", "blurry")
        mock_style_manager.get_default_settings.return_value = {
            "num_steps": 30,
            "guidance_scale": 8.5,
        }

        with patch("app.tasks.generate.StorageService", return_value=mock_storage), patch(
            "app.tasks.generate.TaskService", return_value=mock_task_service
        ), patch("app.tasks.generate.StyleManager", return_value=mock_style_manager), patch(
            "app.tasks.generate.InferencePipeline", return_value=mock_pipeline
        ), patch(
            "app.tasks.generate.resolve_torch_device",
            return_value=("cuda", "float16"),
        ), patch(
            "app.tasks.generate.settings"
        ) as mock_settings:
            mock_settings.GPU_ENABLED = True

            from app.tasks.generate import generate_image_task

            generate_image_task.run(
                task_id="task-123",
                upload_id="upload-123",
                style_id="pixar_3d",
                custom_prompt="flowers",
                user_id="test-user-123",
            )

        mock_style_manager.get_prompts.assert_called_once_with("pixar_3d", "flowers")
        mock_style_manager.get_default_settings.assert_called_once_with("pixar_3d")
        mock_pipeline.generate.assert_called_once_with(
            image=image,
            prompt="pixar flowers",
            negative_prompt="blurry",
            num_steps=30,
            guidance_scale=8.5,
            image_size=512,
        )
