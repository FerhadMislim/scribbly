"""
Scribbly AI Engine

Core inference pipeline and utilities for AI-powered image generation.
"""

try:
    from ai_engine.pipeline import InferencePipeline, create_pipeline
except ImportError:
    from pipeline import InferencePipeline, create_pipeline

try:
    from ai_engine.device import resolve_torch_device
except ImportError:
    from device import resolve_torch_device

try:
    from ai_engine.style_manager import StyleManager, create_style_manager
except ImportError:
    from style_manager import StyleManager, create_style_manager

__all__ = [
    "InferencePipeline",
    "create_pipeline",
    "resolve_torch_device",
    "StyleManager",
    "create_style_manager",
]
__version__ = "1.0.0"
