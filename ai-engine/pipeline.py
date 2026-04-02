"""
Scribbly AI Inference Pipeline

Core pipeline for generating styled images from sketches using
Stable Diffusion with ControlNet conditioning.
"""

import logging
import time
from pathlib import Path
from typing import Optional

import torch
from PIL import Image
from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
    DDIMScheduler,
)

logger = logging.getLogger(__name__)


class InferencePipeline:
    """
    Core inference pipeline for generating styled images from sketches.

    Handles:
    - Model loading and caching
    - Image preprocessing
    - ControlNet-conditioned generation
    - Memory management
    - Batch processing
    """

    def __init__(
        self,
        model_id: str = "runwayml/stable-diffusion-v1-5",
        controlnet_id: str = "lllyasviel/control_v11p_sd15_scribble",
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        enable_xformers: bool = True,
        enable_cpu_offload: bool = True,
        models_dir: Optional[Path] = None,
    ):
        """
        Initialize the inference pipeline.

        Args:
            model_id: HuggingFace model ID for base Stable Diffusion model
            controlnet_id: HuggingFace model ID for ControlNet
            device: Device to run inference on ("cuda" or "cpu")
            dtype: Torch dtype for model weights (float16 for GPU, float32 for CPU)
            enable_xformers: Enable xFormers memory efficient attention
            enable_cpu_offload: Enable CPU offload for low VRAM GPUs
            models_dir: Local models directory path
        """
        self.model_id = model_id
        self.controlnet_id = controlnet_id
        self.device = device
        self.dtype = dtype
        self.enable_xformers = enable_xformers
        self.enable_cpu_offload = enable_cpu_offload
        self.models_dir = models_dir or Path(__file__).parent / "models"

        self._pipeline: Optional[StableDiffusionControlNetPipeline] = None
        self._is_loaded = False

        # Performance tracking
        self._last_inference_time: Optional[float] = None

        logger.info(
            f"Initializing InferencePipeline(model={model_id}, "
            f"controlnet={controlnet_id}, device={device})"
        )

    @property
    def is_loaded(self) -> bool:
        """Check if pipeline is loaded."""
        return self._is_loaded

    def load(self) -> None:
        """
        Load the pipeline models into memory.

        This method is called lazily on first generation.
        """
        if self._is_loaded:
            logger.debug("Pipeline already loaded")
            return

        logger.info("Loading ControlNet model...")
        start_time = time.time()

        # Determine local path if available
        controlnet_path = self._get_local_path(self.controlnet_id)
        model_path = self._get_local_path(self.model_id)

        # Load ControlNet
        controlnet = ControlNetModel.from_pretrained(
            str(controlnet_path) if controlnet_path else self.controlnet_id,
            torch_dtype=self.dtype,
        )

        logger.info("Loading Stable Diffusion pipeline...")

        # Load main pipeline with ControlNet
        self._pipeline = StableDiffusionControlNetPipeline.from_pretrained(
            str(model_path) if model_path else self.model_id,
            controlnet=controlnet,
            torch_dtype=self.dtype,
            safety_checker=None,  # Disable for faster inference
        )

        # Move to device
        self._pipeline = self._pipeline.to(self.device)

        # Apply optimizations
        if self.enable_xformers:
            try:
                self._pipeline.enable_xformers_memory_efficient_attention()
                logger.info("Enabled xFormers memory efficient attention")
            except ImportError:
                logger.warning("xFormers not available, skipping")

        if self.enable_cpu_offload and self.device == "cuda":
            self._pipeline.enable_model_cpu_offload()
            logger.info("Enabled CPU offload")

        # Set default scheduler
        self._pipeline.scheduler = DDIMScheduler.from_config(
            self._pipeline.scheduler.config
        )

        load_time = time.time() - start_time
        logger.info(f"Pipeline loaded in {load_time:.2f}s")

        self._is_loaded = True

    def _get_local_path(self, model_id: str) -> Optional[Path]:
        """Get local path for a model if it exists."""
        # Map HuggingFace IDs to local directories
        model_map = {
            "runwayml/stable-diffusion-v1-5": "sd15",
            "stabilityai/stable-diffusion-xl-base-1.0": "sdxl",
            "lllyasviel/control_v11p_sd15_scribble": "controlnet_scribble",
            "lllyasviel/control_v11p_sd15_canny": "controlnet_canny",
        }

        local_dir = model_map.get(model_id)
        if local_dir:
            path = self.models_dir / local_dir
            if path.exists():
                logger.info(f"Using local model: {path}")
                return path

        return None

    def unload(self) -> None:
        """Unload pipeline from memory."""
        if not self._is_loaded:
            return

        logger.info("Unloading pipeline...")
        del self._pipeline
        self._pipeline = None
        self._is_loaded = False

        if self.device == "cuda":
            torch.cuda.empty_cache()

        logger.info("Pipeline unloaded")

    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for ControlNet.

        Applies edge detection to convert sketch to conditioning image.

        Args:
            image: Input PIL Image

        Returns:
            Preprocessed PIL Image (edge map)
        """
        # Import here to avoid heavy imports if not needed
        try:
            from controlnet_aux import HEDdetector

            # Use HED detector for soft edge detection (best for sketches)
            hed = HEDdetector.from_pretrained("lllyasviel/Annotators")
            processed = hed(image)

            logger.debug(f"Preprocessed image: {image.size} -> {processed.size}")
            return processed

        except ImportError:
            logger.warning("controlnet_aux not installed, returning original image")
            return image

    def generate(
        self,
        image: Image.Image,
        prompt: str,
        negative_prompt: str = "",
        num_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        image_size: int = 512,
    ) -> Image.Image:
        """
        Generate a styled image from a sketch.

        Args:
            image: Input sketch as PIL Image
            prompt: Positive prompt for generation
            negative_prompt: Negative prompt to avoid
            num_steps: Number of denoising steps
            guidance_scale: Classifier-free guidance scale
            seed: Random seed for reproducibility
            image_size: Output image size (width and height)

        Returns:
            Generated PIL Image
        """
        # Lazy load
        if not self._is_loaded:
            self.load()

        logger.info(f"Generating image with prompt: '{prompt[:50]}...'")

        # Preprocess the input image
        start_time = time.time()
        condition_image = self.preprocess(image)

        # Resize if needed
        if condition_image.size != (image_size, image_size):
            condition_image = condition_image.resize(
                (image_size, image_size), Image.LANCZOS
            )

        # Set seed for reproducibility
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            generator = None

        # Run inference
        result = self._pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=condition_image,
            num_inference_steps=num_steps,
            guidance_scale=guidance_scale,
            generator=generator,
            height=image_size,
            width=image_size,
        )

        output_image = result.images[0]

        inference_time = time.time() - start_time
        self._last_inference_time = inference_time

        # Log performance
        if inference_time > 30:
            logger.warning(f"Inference took {inference_time:.1f}s (target: <30s)")
        else:
            logger.info(f"Inference completed in {inference_time:.1f}s")

        # Memory cleanup
        if self.device == "cuda":
            torch.cuda.empty_cache()

        return output_image

    def generate_batch(
        self,
        images: list[Image.Image],
        prompts: list[str],
        negative_prompts: Optional[list[str]] = None,
        **kwargs,
    ) -> list[Image.Image]:
        """
        Generate multiple images in batch.

        Args:
            images: List of input sketches
            prompts: List of positive prompts (must match images length)
            negative_prompts: Optional list of negative prompts
            **kwargs: Additional arguments passed to generate()

        Returns:
            List of generated PIL Images
        """
        if len(images) != len(prompts):
            raise ValueError(
                f"Number of images ({len(images)}) must match "
                f"number of prompts ({len(prompts)})"
            )

        if negative_prompts is None:
            negative_prompts = [""] * len(images)

        logger.info(f"Generating batch of {len(images)} images")

        results = []
        for i, (img, prompt, neg_prompt) in enumerate(
            zip(images, prompts, negative_prompts)
        ):
            logger.debug(f"Processing batch item {i + 1}/{len(images)}")
            result = self.generate(img, prompt, neg_prompt, **kwargs)
            results.append(result)

        logger.info(f"Batch generation complete: {len(results)} images")

        return results

    @property
    def last_inference_time(self) -> Optional[float]:
        """Get the last inference time in seconds."""
        return self._last_inference_time

    def __enter__(self):
        """Context manager entry."""
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload()


def create_pipeline(
    model: str = "sd15",
    device: Optional[str] = None,
    models_dir: Optional[Path] = None,
) -> InferencePipeline:
    """
    Factory function to create a pipeline with preset configurations.

    Args:
        model: Model preset ("sd15" or "sdxl")
        device: Device to use (auto-detect if None)
        models_dir: Custom models directory

    Returns:
        Configured InferencePipeline instance
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    configs = {
        "sd15": {
            "model_id": "runwayml/stable-diffusion-v1-5",
            "controlnet_id": "lllyasviel/control_v11p_sd15_scribble",
        },
        "sdxl": {
            "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
            "controlnet_id": "diffusers/controlnet-canny-sdxl-1.0",
        },
    }

    if model not in configs:
        raise ValueError(f"Unknown model: {model}. Use: {list(configs.keys())}")

    config = configs[model]
    dtype = torch.float16 if device == "cuda" else torch.float32

    return InferencePipeline(
        model_id=config["model_id"],
        controlnet_id=config["controlnet_id"],
        device=device,
        dtype=dtype,
        models_dir=models_dir,
    )
