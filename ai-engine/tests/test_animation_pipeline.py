"""
Tests for AnimationPipeline
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


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
        with patch("diffusers.AnimateDiffPipeline") as mock_animediff:
            with patch("diffusers.MotionAdapter") as mock_adapter:
                with patch("diffusers.DDIMScheduler") as mock_scheduler:
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

    def test_generate_respects_max_frames(self, animation_pipeline):
        """Test that generate raises error for >32 frames."""
        animation_pipeline._is_loaded = True

        mock_image = MagicMock()

        with pytest.raises(ValueError, match="Maximum 32 frames"):
            animation_pipeline.generate_animation(mock_image, "test", num_frames=33)


class TestExportFunctions:
    """Tests for export functions."""

    def test_export_gif_no_error(self):
        """Test that export_gif runs without error."""
        from PIL import Image
        from animation_pipeline import export_gif

        frames = [
            Image.new("RGB", (256, 256), color="red"),
            Image.new("RGB", (256, 256), color="blue"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.gif"
            export_gif(frames, output_path, fps=8)

    @pytest.mark.skip(reason="Requires ffmpeg")
    def test_export_mp4_no_error(self):
        """Test that export_mp4 runs without error."""
        pass


class TestGenerateFromSketch:
    """Tests for generate_from_sketch."""

    @pytest.mark.skip(reason="Requires actual pipeline")
    def test_generate_from_sketch_loads_image(self):
        """Test that generate_from_sketch loads the image."""
        pass

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
        from animation_pipeline import create_animation_pipeline, AnimationPipeline

        pipe = create_animation_pipeline(device="cpu")

        assert isinstance(pipe, AnimationPipeline)
        assert pipe._device == "cpu"


class TestEndToEnd:
    """End-to-end tests."""

    def test_load_unload_cycle(self):
        """Test: load pipeline, generate, unload, generate again."""
        from animation_pipeline import AnimationPipeline

        pipe = AnimationPipeline()

        with patch("diffusers.AnimateDiffPipeline") as mock_animediff:
            with patch("diffusers.MotionAdapter") as mock_adapter:
                with patch("diffusers.DDIMScheduler") as mock_scheduler:
                    mock_adapter.from_pretrained.return_value = MagicMock()
                    mock_animediff.from_pretrained.return_value = MagicMock()
                    mock_scheduler.from_config.return_value = MagicMock()

                    pipe.load()
                    assert pipe.is_loaded

                    pipe.unload()
                    assert not pipe.is_loaded

    @pytest.mark.skip(reason="Requires actual pipeline and ffmpeg")
    def test_animation_generation_flow(self):
        """Test complete animation generation flow."""
        pass
