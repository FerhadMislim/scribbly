"""
Tests for database module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


class TestGetDb:
    """Tests for get_db dependency."""

    async def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        from app.database import get_db
        
        mock_session = AsyncMock()
        
        with patch("app.database.async_session_maker") as mock_maker:
            mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            
            gen = get_db()
            session = await gen.__anext__()
            
            assert session == mock_session

    async def test_get_db_closes_on_exception(self):
        """Test that session is closed on exception."""
        from app.database import get_db
        
        mock_session = AsyncMock()
        
        with patch("app.database.async_session_maker") as mock_maker:
            mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            
            gen = get_db()
            session = await gen.__anext__()
            
            try:
                await gen.athrow(ValueError("test"))
            except ValueError:
                pass
            
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestDatabaseConnection:
    """Tests for database connection functions."""

    async def test_init_db_creates_tables(self):
        """Test that init_db creates all tables."""
        with patch("app.database.engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)
            
            from app.database import init_db
            await init_db()
            
            mock_conn.run_sync.assert_called_once()

    async def test_close_db_disposes_engine(self):
        """Test that close_db disposes the engine."""
        mock_engine = AsyncMock()
        
        with patch("app.database.engine", mock_engine):
            from app.database import close_db
            await close_db()
            
            mock_engine.dispose.assert_called_once()
