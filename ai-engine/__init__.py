"""
Scribbly AI Engine

Core inference pipeline and utilities for AI-powered image generation.
"""

try:
    from ai_engine.pipeline import InferencePipeline, create_pipeline
except ImportError:
    from pipeline import InferencePipeline, create_pipeline

__all__ = ["InferencePipeline", "create_pipeline"]
__version__ = "1.0.0"
