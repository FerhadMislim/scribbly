"""
Device selection helpers for AI inference.
"""

from __future__ import annotations

import logging

import torch

logger = logging.getLogger(__name__)


def resolve_torch_device(preferred_device: str | None = "auto") -> tuple[str, torch.dtype]:
    """
    Resolve the best available torch device for inference.

    Args:
        preferred_device: One of "auto", "cuda", or "cpu". Any falsey value is
            treated as "auto".

    Returns:
        A tuple of resolved device name and recommended dtype.
    """
    normalized = (preferred_device or "auto").lower()

    if normalized not in {"auto", "cuda", "cpu"}:
        raise ValueError(
            f"Unsupported device preference: {preferred_device}. "
            "Use 'auto', 'cuda', or 'cpu'."
        )

    cuda_available = torch.cuda.is_available()

    if normalized == "cpu":
        return "cpu", torch.float32

    if normalized == "cuda":
        if cuda_available:
            return "cuda", torch.float16
        logger.warning("CUDA requested but not available, falling back to CPU")
        return "cpu", torch.float32

    if cuda_available:
        return "cuda", torch.float16

    return "cpu", torch.float32

