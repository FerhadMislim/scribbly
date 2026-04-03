"""
Animation Pipeline for Scribbly AI Engine

Handles animation generation using AnimateDiff motion module.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)

try:
    from ai_engine.device import resolve_torch_device
except ImportError:
    from device import resolve_torch_device


class AnimationPipeline:
    """
    Animation pipeline using AnimateDiff for short animation generation.

    Supports:
    - Generating animations from input images
    - Configurable frame count and FPS
    - Export to GIF and MP4 formats
    """

    def __init__(
        self,
        model_id: str = "runwayml/stable-diffusion-v1-5",
        motion_adapter_id: str = "guoyww/animatediff-motion-adapter-v1-5-2",
        device: str = "cuda",
    ):
        """
        Initialize the Animation Pipeline.

        Args:
            model_id: Base model for diffusion
            motion_adapter_id: AnimateDiff motion adapter model
            device: Device to run on ("cuda" or "cpu")
        """
        resolved_device, _ = resolve_torch_device(device)

        self._model_id = model_id
        self._motion_adapter_id = motion_adapter_id
        self._device = resolved_device

        self._pipeline = None
        self._is_loaded = False

        logger.info(f"AnimationPipeline initialized with model: {model_id}")

    @property
    def is_loaded(self) -> bool:
        """Check if pipeline is loaded."""
        return self._is_loaded

    def load(self) -> None:
        """
        Load the AnimateDiff pipeline.
        """
        from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler
        import torch

        logger.info("Loading AnimateDiff pipeline...")
        start_time = time.time()

        adapter = MotionAdapter.from_pretrained(self._motion_adapter_id)

        self._pipeline = AnimateDiffPipeline.from_pretrained(
            self._model_id,
            motion_adapter=adapter,
            torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
        )

        self._pipeline.scheduler = DDIMScheduler.from_config(
            self._pipeline.scheduler.config
        )

        if self._device == "cuda" and torch.cuda.is_available():
            self._pipeline = self._pipeline.to("cuda")
        else:
            self._pipeline = self._pipeline.to("cpu")

        self._is_loaded = True
        load_time = time.time() - start_time
        logger.info(f"Pipeline loaded in {load_time:.2f}s")

    def unload(self) -> None:
        """Unload the pipeline to free memory."""
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            self._is_loaded = False

            if self._device == "cuda":
                import torch

                torch.cuda.empty_cache()

            logger.info("Pipeline unloaded")

    def generate_animation(
        self,
        image: "Image.Image",
        prompt: str,
        style: str = "animated",
        num_frames: int = 16,
        fps: int = 8,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 25,
    ) -> list["Image.Image"]:
        """
        Generate an animation from an input image.

        Args:
            image: Input PIL Image
            prompt: Text prompt for generation
            style: Style identifier
            num_frames: Number of frames to generate (max 32)
            fps: Frames per second
            guidance_scale: Guidance scale for generation
            num_inference_steps: Number of inference steps

        Returns:
            List of PIL Image frames
        """

        if not self._is_loaded:
            self.load()

        if num_frames > 32:
            raise ValueError("Maximum 32 frames supported")

        logger.info(f"Generating {num_frames} frames...")
        start_time = time.time()

        output = self._pipeline(
            prompt=prompt,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            height=256,
            width=256,
        )

        frames = output.frames[0]

        generation_time = time.time() - start_time
        logger.info(f"Generated {num_frames} frames in {generation_time:.2f}s")

        return frames

    def generate_from_sketch(
        self,
        sketch_path: str | Path,
        prompt: str,
        style: str = "animated",
        num_frames: int = 16,
        fps: int = 8,
    ) -> list["Image.Image"]:
        """
        Generate an animation from a sketch file.

        Args:
            sketch_path: Path to sketch image
            prompt: Text prompt for generation
            style: Style identifier
            num_frames: Number of frames
            fps: Frames per second

        Returns:
            List of PIL Image frames
        """
        from PIL import Image

        sketch_path = Path(sketch_path)
        if not sketch_path.exists():
            raise FileNotFoundError(f"Sketch not found: {sketch_path}")

        image = Image.open(sketch_path).convert("RGB")

        return self.generate_animation(
            image=image,
            prompt=prompt,
            style=style,
            num_frames=num_frames,
            fps=fps,
        )


def export_gif(
    frames: list["Image.Image"],
    path: str | Path,
    fps: int = 8,
) -> None:
    """
    Export frames to GIF.

    Args:
        frames: List of PIL Image frames
        path: Output path
        fps: Frames per second
    """
    import imageio

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    frames_np = [frame.convert("RGBA") for frame in frames]

    imageio.mimsave(str(path), frames_np, fps=fps, loop=0)

    logger.info(f"GIF exported to {path}")


def export_mp4(
    frames: list["Image.Image"],
    path: str | Path,
    fps: int = 8,
    codec: str = "libx264",
) -> None:
    """
    Export frames to MP4.

    Args:
        frames: List of PIL Image frames
        path: Output path
        fps: Frames per second
        codec: Video codec
    """
    import imageio

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    frames_np = [frame.convert("RGBA") for frame in frames]

    imageio.mimsave(str(path), frames_np, fps=fps, codec=codec)

    logger.info(f"MP4 exported to {path}")


def create_animation_pipeline(
    model_id: str = "runwayml/stable-diffusion-v1-5",
    motion_adapter_id: str = "guoyww/animatediff-motion-adapter-v1-5-2",
    device: str = "auto",
) -> AnimationPipeline:
    """
    Factory function to create an AnimationPipeline.

    Args:
        model_id: Base model for diffusion
        motion_adapter_id: AnimateDiff motion adapter model
        device: Device to run on

    Returns:
        Configured AnimationPipeline instance
    """
    return AnimationPipeline(
        model_id=model_id,
        motion_adapter_id=motion_adapter_id,
        device=device,
    )
