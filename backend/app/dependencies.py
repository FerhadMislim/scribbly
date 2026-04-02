"""
Shared dependencies for dependency injection.
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


async def get_current_user_id(
    x_user_id: Annotated[str | None, Header()] = None
) -> str | None:
    """
    Get current user ID from header.

    In production, this would validate JWT token.
    For development, uses X-User-Id header.

    Args:
        x_user_id: User ID from X-User-Id header

    Returns:
        User ID if present
    """
    return x_user_id


async def require_current_user_id(
    current_user_id: Annotated[str | None, Depends(get_current_user_id)]
) -> str:
    """
    Require current user ID - raises 401 if not present.

    Args:
        current_user_id: Current user ID from dependency

    Returns:
        User ID

    Raises:
        HTTPException: If user not authenticated
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return current_user_id


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUserId = Annotated[str, Depends(require_current_user_id)]
OptionalUserId = Annotated[str | None, Depends(get_current_user_id)]
