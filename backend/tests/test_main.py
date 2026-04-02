"""
Tests for main application.
"""

from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio


class TestCreateApp:
    """Tests for create_app function."""

    def test_app_has_correct_title(self):
        """Test that app has correct title from settings."""
        with patch("app.main.setup_logging"):
            with patch("app.database.init_db"):
                with patch("app.database.close_db"):
                    from app.main import create_app

                    app = create_app()

                    assert app.title == "Scribbly"

    def test_app_has_health_endpoint(self):
        """Test that health endpoint exists."""
        with patch("app.main.setup_logging"):
            with patch("app.database.init_db"):
                with patch("app.database.close_db"):
                    from app.main import create_app

                    app = create_app()

                    paths = [route.path for route in app.routes]
                    assert "/health" in paths

    def test_health_returns_correct_status(self):
        """Test that health endpoint returns correct status."""
        from fastapi.testclient import TestClient

        with patch("app.main.setup_logging"):
            with patch("app.database.init_db"):
                with patch("app.database.close_db"):
                    from app.main import create_app

                    app = create_app()

                    client = TestClient(app)
                    response = client.get("/health")

                    assert response.status_code == 200
                    assert response.json() == {"status": "ok", "version": "1.0.0"}

    def test_app_has_cors_middleware(self):
        """Test that CORS middleware is configured."""
        with patch("app.main.setup_logging"):
            with patch("app.database.init_db"):
                with patch("app.database.close_db"):
                    from app.main import create_app

                    app = create_app()

                    cors_middleware = None
                    for middleware in app.user_middleware:
                        if middleware.cls.__name__ == "CORSMiddleware":
                            cors_middleware = middleware
                            break

                    assert cors_middleware is not None


class TestHealthEndpoint:
    """Tests for health endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_health_returns_200(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Test health endpoint returns JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_returns_status_ok(self, client):
        """Test health returns status ok."""
        response = client.get("/health")
        assert response.json()["status"] == "ok"

    def test_health_returns_version(self, client):
        """Test health returns version."""
        response = client.get("/health")
        assert "version" in response.json()


class TestLifespan:
    """Tests for application lifespan."""

    @pytest.mark.asyncio
    async def test_startup_calls_init_db(self):
        """Test that startup calls init_db."""
        with patch("app.main.init_db", new_callable=AsyncMock) as mock_init:
            with patch("app.main.close_db", new_callable=AsyncMock):
                with patch("app.main.setup_logging"):
                    from app.main import create_app

                    app = create_app()

                    async with app.router.lifespan_context(app):
                        mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_calls_close_db(self):
        """Test that shutdown calls close_db."""
        with patch("app.main.init_db", new_callable=AsyncMock):
            with patch("app.main.close_db", new_callable=AsyncMock) as mock_close:
                with patch("app.main.setup_logging"):
                    from app.main import create_app

                    app = create_app()

                    async with app.router.lifespan_context(app):
                        pass

                    mock_close.assert_called_once()
