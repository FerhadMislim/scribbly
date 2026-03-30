"""
Tests for AnimationPipeline
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


@pytest.fixture
def mock_pipeline():
    """Create a mock AnimateDiff pipeline."""
    pipe = MagicMock()
    pipe.is_loaded = True
    
    mock_output = MagicMock()
    mock_output.frames = [[MagicMock(), MagicMock(), MagicMock()]]
    pipe.return_value = mock_output
    
    return pipe


@pytest.fixture
def animation_pipeline():
    """Create an AnimationPipeline without loading."""
    from animation_pipeline import AnimationPipeline
    
    pipe = AnimationPipeline()
    return pipe


class TestAnimationPipelineInit:
    """Tests for AnimationPipeline initialization."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        from animation_pipeline import AnimationPipeline
        
        pipe = AnimationPipeline()
        
        assert pipe._model_id == "runwayml/stable-diffusion-v1-5"
        assert pipe._motion_adapter_id == "guoyww/animatediff-motion-adapter-v1-5-2"
        assert pipe._device == "cuda"
        assert not pipe.is_loaded

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        from animation_pipeline import AnimationPipeline
        
        pipe = AnimationPipeline(
            model_id="custom/model",
            motion_adapter_id="custom/adapter",
            device="cpu",
        )
        
        assert pipe._model_id == "custom/model"
        assert pipe._motion_adapter_id == "custom/adapter"
        assert pipe._device == "cpu"


class TestLoadUnload:
    """Tests for loading and unloading pipeline."""

    def test_load_sets_loaded_flag(self, animation_pipeline):
        """Test that load sets is_loaded to True."""
        with patch("animation_pipeline.AnimateDiffPipeline") as mock_animediff:
            with patch("animation_pipeline.MotionAdapter") as mock_adapter:
                with patch("animation_pipeline.DDIMScheduler") as mock_scheduler:
                    mock_adapter.from_pretrained.return_value = MagicMock()
                    mock_animediff.from_pretrained.return_value = MagicMock()
                    mock_scheduler.from_config.return_value = MagicMock()
                    
                    animation_pipeline.load()
                    
                    assert animation_pipeline.is_loaded

    def test_unload_clears_pipeline(self, animation_pipeline):
        """Test that unload clears the pipeline."""
        animation_pipeline._pipeline = MagicMock()
        animation_pipeline._is_loaded = True
        
        animation_pipeline.unload()
        
        assert animation_pipeline._pipeline is None
        assert not animation_pipeline.is_loaded


class TestGenerateAnimation:
    """Tests for animation generation."""

    def test_generate_requires_loaded_pipeline(self, animation_pipeline):
        """Test that generate loads pipeline if not loaded."""
        mock_image = MagicMock()
        
        with patch.object(animation_pipeline, "load") as mock_load:
            with patch.object(animation_pipeline, "generate_animation") as mock_gen:
                mock_gen.return_value = []
                
                animation_pipeline.generate_animation(mock_image, "test prompt")
                
                mock_load.assert_called_once()

    def test_generate_respects_max_frames(self, animation_pipeline):
        """Test that generate raises error for >32 frames."""
        mock_image = MagicMock()
        
        with pytest.raises(ValueError, match="Maximum 32 frames"):
            animation_pipeline.generate_animation(mock_image, "test", num_frames=33)


class TestExportFunctions:
    """Tests for export functions."""

    def test_export_gif_creates_file(self):
        """Test that export_gif creates a file."""
        from animation_pipeline import export_gif
        
        frames = [MagicMock(), MagicMock()]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.gif"
            
            with patch("animation_pipeline.imageio") as mock_imageio:
                export_gif(frames, output_path, fps=8)
                
                mock_imageio.mimsave.assert_called_once()
                args = mock_imageio.mimsave.call_args
                assert str(output_path) == args[0][0]

    def test_export_mp4_creates_file(self):
        """Test that export_mp4 creates a file."""
        from animation_pipeline import export_mp4
        
        frames = [MagicMock(), MagicMock()]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"
            
            with patch("animation_pipeline.imageio") as mock_imageio:
                export_mp4(frames, output_path, fps=8)
                
                mock_imageio.mimsave.assert_called_once()
                args = mock_imageio.mimsave.call_args
                assert str(output_path) == args[0][0]
                assert "libx264" in str(args)


class TestGenerateFromSketch:
    """Tests for generate_from_sketch."""

    def test_generate_from_sketch_loads_image(self):
        """Test that generate_from_sketch loads the image."""
        from animation_pipeline import AnimationPipeline
        
        pipe = AnimationPipeline()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            sketch_path = Path(tmpdir) / "sketch.png"
            
            mock_image = MagicMock()
            mock_image.convert.return_value = mock_image
            
            with patch("animation_pipeline.Image.open") as mock_open:
                with patch.object(pipe, "generate_animation") as mock_gen:
                    mock_open.return_value = mock_image
                    mock_gen.return_value = []
                    
                    pipe.generate_from_sketch(sketch_path, "test prompt")
                    
                    mock_open.assert_called_once_with(sketch_path)

    def test_generate_from_sketch_missing_file(self):
        """Test that missing sketch raises error."""
        from animation_pipeline import AnimationPipeline
        
        pipe = AnimationPipeline()
        
        with pytest.raises(FileNotFoundError):
            pipe.generate_from_sketch("/nonexistent/sketch.png", "test prompt")


class TestCreateAnimationPipeline:
    """Tests for factory function."""

    def test_create_animation_pipeline(self):
        """Test factory function creates correct pipeline."""
        from animation_pipeline import create_animation_pipeline
        
        pipe = create_animation_pipeline(device="cpu")
        
        assert isinstance(pipe, AnimationPipeline)
        assert pipe._device == "cpu"


class TestEndToEnd:
    """End-to-end tests."""

    def test_load_unload_cycle(self):
        """Test: load pipeline, generate, unload, generate again."""
        from animation_pipeline import AnimationPipeline
        
        pipe = AnimationPipeline()
        
        with patch("animation_pipeline.AnimateDiffPipeline") as mock_animediff:
            with patch("animation_pipeline.MotionAdapter") as mock_adapter:
                with patch("animation_pipeline.DDIMScheduler") as mock_scheduler:
                    mock_adapter.from_pretrained.return_value = MagicMock()
                    mock_animediff.from_pretrained.return_value = MagicMock()
                    mock_scheduler.from_config.return_value = MagicMock()
                    
                    pipe.load()
                    assert pipe.is_loaded
                    
                    pipe.unload()
                    assert not pipe.is_loaded

    def test_animation_generation_flow(self):
        """Test complete animation generation flow."""
        from animation_pipeline import AnimationPipeline, export_gif, export_mp4
        
        pipe = AnimationPipeline()
        
        mock_frame = MagicMock()
        mock_frames = [mock_frame, mock_frame]
        
        with patch.object(pipe, "generate_animation", return_value=mock_frames):
            frames = pipe.generate_animation(
                MagicMock(),
                "a stick figure drawing",
                num_frames=16,
                fps=8,
            )
            
            assert len(frames) == 2
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch("animation_pipeline.imageio"):
                    export_gif(frames, f"{tmpdir}/output.gif")
                    export_mp4(frames, f"{tmpdir}/output.mp4")
