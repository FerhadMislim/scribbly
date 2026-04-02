"""
LoRA Manager for Scribbly AI Engine

Handles loading, unloading, and managing LoRA (Low-Rank Adaptation) weights
for fine-tuned style transfer on Stable Diffusion models.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pipeline import InferencePipeline

logger = logging.getLogger(__name__)


class LoRAManager:
    """
    Manages LoRA weights for the Stable Diffusion pipeline.

    Supports:
    - Loading/unloading individual LoRAs
    - Stacking multiple LoRAs with configurable weights
    - Automatic trigger word injection
    - Metadata tracking in loras.json
    """

    def __init__(
        self,
        pipeline: Optional["InferencePipeline"] = None,
        loras_dir: Optional[Path] = None,
    ):
        """
        Initialize the LoRA Manager.

        Args:
            pipeline: InferencePipeline instance to attach LoRAs to
            loras_dir: Directory containing LoRA weight files
        """
        self._pipeline = pipeline
        self._loras_dir = loras_dir or Path(__file__).parent / "models" / "loras"
        self._loras_dir.mkdir(parents=True, exist_ok=True)

        self._loaded_loras: dict[str, float] = {}
        self._loras_metadata_path = self._loras_dir / "loras.json"

        logger.info(f"LoRAManager initialized with dir: {self._loras_dir}")

    @property
    def loras_dir(self) -> Path:
        """Get the LoRA directory path."""
        return self._loras_dir

    def _get_metadata(self) -> dict:
        """Load LoRA metadata from loras.json."""
        if self._loras_metadata_path.exists():
            with open(self._loras_metadata_path) as f:
                return json.load(f)
        return {"loras": []}

    def _save_metadata(self, metadata: dict) -> None:
        """Save LoRA metadata to loras.json."""
        with open(self._loras_metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def list_available(self) -> list[dict]:
        """
        List all available LoRAs in the directory.

        Returns:
            List of LoRA metadata dictionaries
        """
        metadata = self._get_metadata()
        loras = metadata.get("loras", [])

        logger.info(f"Found {len(loras)} available LoRAs")
        return [lora.copy() for lora in loras]

    def load(
        self,
        lora_path: str | Path,
        scale: float = 0.8,
        lora_name: Optional[str] = None,
    ) -> None:
        """
        Load a LoRA into the pipeline.

        Args:
            lora_path: Path to LoRA weights (supports .safetensors and .bin)
            scale: LoRA weight scale (0.0 to 1.0)
            lora_name: Optional name to identify this LoRA
        """
        if self._pipeline is None:
            raise RuntimeError(
                "No pipeline attached. Pass pipeline to LoRAManager constructor."
            )

        if not self._pipeline.is_loaded:
            self._pipeline.load()

        lora_path = Path(lora_path)
        if not lora_path.is_absolute():
            lora_path = self._loras_dir / lora_path

        if not lora_path.exists():
            raise FileNotFoundError(f"LoRA file not found: {lora_path}")

        weight_name = None
        if lora_path.suffix == ".safetensors":
            weight_name = "model.safetensors"
        elif lora_path.suffix == ".bin":
            weight_name = "pytorch_model.bin"

        lora_name = lora_name or lora_path.stem

        logger.info(f"Loading LoRA '{lora_name}' from {lora_path} with scale={scale}")

        self._pipeline._pipeline.load_lora_weights(
            str(lora_path),
            weight_name=weight_name,
        )
        self._pipeline._pipeline.fuse_lora(lora_scale=scale)

        self._loaded_loras[str(lora_path)] = scale

        logger.info(f"LoRA '{lora_name}' loaded successfully")

    def unload(self, lora_path: Optional[str | Path] = None) -> None:
        """
        Unload LoRA weights from the pipeline.

        Args:
            lora_path: Optional path to unload specific LoRA.
                      If None, unloads all loaded LoRAs.
        """
        if self._pipeline is None or not self._pipeline.is_loaded:
            logger.debug("No pipeline loaded, nothing to unload")
            return

        if lora_path is None:
            paths_to_unload = list(self._loaded_loras.keys())
        else:
            paths_to_unload = [str(Path(lora_path))]

        for path in paths_to_unload:
            logger.info(f"Unloading LoRA: {path}")

            try:
                self._pipeline._pipeline.unfuse_lora()
            except Exception as e:
                logger.warning(f"Could not unfuse LoRA: {e}")

            try:
                self._pipeline._pipeline.unload_lora_weights()
            except Exception as e:
                logger.warning(f"Could not unload LoRA weights: {e}")

            if path in self._loaded_loras:
                del self._loaded_loras[path]

        if not self._loaded_loras:
            logger.info("All LoRAs unloaded")
        else:
            remaining = list(self._loaded_loras.keys())
            logger.info(f"Remaining loaded LoRAs: {remaining}")

    def stack_loras(self, loras: list[tuple[str | Path, float]]) -> None:
        """
        Stack multiple LoRAs with individual scales.

        Args:
            loras: List of (lora_path, scale) tuples
        """
        self.unload()

        for lora_path, scale in loras:
            self.load(lora_path, scale=scale)

        logger.info(f"Stacked {len(loras)} LoRAs")

    def get_trigger_words(self, lora_id: str) -> str:
        """
        Get trigger words for a specific LoRA.

        Args:
            lora_id: LoRA ID from metadata

        Returns:
            Trigger words string (empty if none)
        """
        metadata = self._get_metadata()
        for lora in metadata.get("loras", []):
            if lora.get("id") == lora_id:
                return lora.get("trigger_word", "")
        return ""

    def inject_trigger_words(self, prompt: str, lora_id: str) -> str:
        """
        Prepend trigger words to prompt if LoRA has them.

        Args:
            prompt: Original prompt
            lora_id: LoRA ID to get trigger words from

        Returns:
            Prompt with trigger words prepended
        """
        trigger_words = self.get_trigger_words(lora_id)
        if trigger_words:
            return f"{trigger_words}, {prompt}"
        return prompt

    def register_lora(
        self,
        name: str,
        style_id: str,
        path: str,
        trigger_word: str = "",
        scale: float = 0.8,
    ) -> str:
        """
        Register a new LoRA in the metadata.

        Args:
            name: Display name for the LoRA
            style_id: Associated style ID
            path: Path to LoRA weights (relative to loras_dir)
            trigger_word: Trigger word for activation
            scale: Default scale

        Returns:
            Generated LoRA ID
        """
        metadata = self._get_metadata()

        lora_id = f"lora_{len(metadata['loras']) + 1:03d}"

        new_lora = {
            "id": lora_id,
            "name": name,
            "style_id": style_id,
            "path": str(path),
            "trigger_word": trigger_word,
            "scale": scale,
        }

        metadata["loras"].append(new_lora)
        self._save_metadata(metadata)

        logger.info(f"Registered LoRA: {lora_id} ({name})")
        return lora_id

    def get_loaded_loras(self) -> dict[str, float]:
        """Get dictionary of currently loaded LoRAs and their scales."""
        return self._loaded_loras.copy()

    @property
    def is_loaded(self) -> bool:
        """Check if any LoRAs are currently loaded."""
        return len(self._loaded_loras) > 0
