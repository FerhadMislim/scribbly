"""
Tests for the InferencePipeline class.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch
from PIL import Image

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestInferencePipeline:
    """Test cases for InferencePipeline."""

    @pytest.fixture
    def dummy_image(self):
        """Create a dummy test image."""
        return Image.new("RGB", (512, 512), color="white")

    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance without loading models."""
        from pipeline import InferencePipeline
        
        # Use CPU and disable expensive operations for testing
        pipe = InferencePipeline(
            model_id="runwayml/stable-diffusion-v1-5",
            controlnet_id="lllyasviel/control_v11p_sd15_scribble",
            device="cpu",
            dtype=torch.float32,
            enable_xformers=False,
            enable_cpu_offload=False,
        )
        return pipe

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes with correct parameters."""
        assert pipeline.model_id == "runwayml/stable-diffusion-v1-5"
        assert pipeline.controlnet_id == "lllyasviel/control_v11p_sd15_scribble"
        assert pipeline.device == "cpu"
        assert pipeline.dtype == torch.float32
        assert pipeline.is_loaded is False

    def test_pipeline_load_unload(self, pipeline):
        """Test pipeline load and unload methods."""
        # Initially not loaded
        assert pipeline.is_loaded is False
        
        # Can't test actual load without models, but can verify method exists
        assert hasattr(pipeline, 'load')
        assert hasattr(pipeline, 'unload')

    def test_preprocess_returns_image(self, pipeline, dummy_image):
        """Test preprocess returns a PIL Image."""
        result = pipeline.preprocess(dummy_image)
        assert isinstance(result, Image.Image)

    def test_context_manager(self):
        """Test pipeline as context manager."""
        from pipeline import InferencePipeline
        
        # Mock the load and unload
        with patch.object(InferencePipeline, 'load') as mock_load, \
             patch.object(InferencePipeline, 'unload') as mock_unload:
            
            pipe = InferencePipeline(device="cpu", dtype=torch.float32)
            with pipe as p:
                assert p is not None
            
            mock_load.assert_called_once()
            mock_unload.assert_called_once()

    def test_generate_batch_validation(self, pipeline, dummy_image):
        """Test batch generation validates input lengths."""
        images = [dummy_image, dummy_image]
        prompts = ["prompt1"]  # Only one prompt
        
        with pytest.raises(ValueError, match="must match"):
            pipeline.generate_batch(images, prompts)

    def test_create_pipeline_sd15(self):
        """Test factory function for SD1.5."""
        from pipeline import create_pipeline
        
        pipe = create_pipeline(model="sd15", device="cpu")
        
        assert pipe.model_id == "runwayml/stable-diffusion-v1-5"
        assert pipe.controlnet_id == "lllyasviel/control_v11p_sd15_scribble"

    def test_create_pipeline_unknown_model(self):
        """Test factory function raises error for unknown model."""
        from pipeline import create_pipeline
        
        with pytest.raises(ValueError, match="Unknown model"):
            create_pipeline(model="unknown")

    def test_get_local_path(self, pipeline):
        """Test local path resolution."""
        # Test with unknown model ID - should always return None
        path = pipeline._get_local_path("unknown/model")
        assert path is None
        
        # Test with known model ID - only works if local models exist
        path = pipeline._get_local_path("runwayml/stable-diffusion-v1-5")
        if path is not None:
            assert "sd15" in str(path)


class TestPipelineMemory:
    """Test memory management in pipeline."""

    def test_unload_clears_memory(self):
        """Test unload clears GPU memory."""
        import torch
        from pipeline import InferencePipeline
        
        # Create pipeline but don't load
        pipe = InferencePipeline(device="cpu", dtype=torch.float32)
        pipe.unload()  # Should not raise
        
        assert pipe.is_loaded is False

    def test_double_load_is_safe(self):
        """Test loading twice is safe (idempotent)."""
        from pipeline import InferencePipeline
        
        pipe = InferencePipeline(device="cpu", dtype=torch.float32)
        
        # Mock to avoid actual loading
        pipe._is_loaded = True
        pipe._pipeline = MagicMock()
        
        # Should be safe
        pipe.load()
        
        assert pipe.is_loaded is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
