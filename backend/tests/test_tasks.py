"""
Tests for task service.
"""

from unittest.mock import MagicMock, patch


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


class TestStyleId:
    """Tests for StyleId enum."""

    def test_style_id_values(self):
        """Test StyleId enum values."""
        from app.routers.generate import StyleId

        assert StyleId.PIXAR_3D.value == "pixar_3d"
        assert StyleId.ANIME.value == "anime"
        assert StyleId.WATERCOLOR.value == "watercolor"
        assert StyleId.SKETCH.value == "sketch"
        assert StyleId.OIL_PAINTING.value == "oil_painting"
        assert StyleId.CARTOON.value == "cartoon"
