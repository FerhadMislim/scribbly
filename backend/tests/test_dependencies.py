"""
Tests for dependencies module.
"""


import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.asyncio


class TestGetCurrentUserId:
    """Tests for get_current_user_id dependency."""

    async def test_returns_user_id_from_header(self):
        """Test that user ID is returned from header."""
        from app.dependencies import get_current_user_id

        result = await get_current_user_id(x_user_id="user-123")

        assert result == "user-123"

    async def test_returns_none_when_no_header(self):
        """Test that None is returned when no header."""
        from app.dependencies import get_current_user_id

        result = await get_current_user_id(x_user_id=None)

        assert result is None


class TestRequireCurrentUserId:
    """Tests for require_current_user_id dependency."""

    async def test_returns_user_id_when_present(self):
        """Test that user ID is returned when present."""
        from app.dependencies import require_current_user_id

        result = await require_current_user_id(current_user_id="user-123")

        assert result == "user-123"

    async def test_raises_401_when_missing(self):
        """Test that 401 is raised when user ID is missing."""
        from app.dependencies import require_current_user_id

        with pytest.raises(HTTPException) as exc_info:
            await require_current_user_id(current_user_id=None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail
