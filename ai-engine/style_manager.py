"""
Scribbly Style Manager

Manages art style configurations for AI image generation.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Style:
    """Represents an art style configuration."""

    id: str
    display_name: str
    description: str
    positive_prompt: str
    negative_prompt: str
    recommended_steps: int
    guidance_scale: float
    recommended_model: str
    thumbnail_url: str

    def get_prompts(self, custom_prompt: Optional[str] = None) -> tuple[str, str]:
        """
        Get the positive and negative prompts.

        Args:
            custom_prompt: Optional custom prompt to append/replace

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        positive = custom_prompt if custom_prompt else self.positive_prompt
        negative = self.negative_prompt

        return positive, negative


class StyleManager:
    """
    Manages art style configurations.

    Loads style definitions from YAML config and provides
    easy access to style prompts and settings.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the StyleManager.

        Args:
            config_path: Path to style_config.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "style_config.yaml"

        self.config_path = config_path
        self._styles: dict[str, Style] = {}
        self._defaults: dict = {}
        self._safety: dict = {}

        self.load()

    def load(self) -> None:
        """Load styles from YAML configuration."""
        if not self.config_path.exists():
            logger.warning(f"Style config not found: {self.config_path}")
            return

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        # Load styles
        for style_data in config.get("styles", []):
            style = Style(
                id=style_data["id"],
                display_name=style_data["display_name"],
                description=style_data.get("description", ""),
                positive_prompt=style_data["positive_prompt"],
                negative_prompt=style_data["negative_prompt"],
                recommended_steps=style_data.get("recommended_steps", 25),
                guidance_scale=style_data.get("guidance_scale", 7.5),
                recommended_model=style_data.get("recommended_model", "sd15"),
                thumbnail_url=style_data.get("thumbnail_url", ""),
            )
            self._styles[style.id] = style

        # Load defaults
        self._defaults = config.get("defaults", {})

        # Load safety settings
        self._safety = config.get("safety", {})

        logger.info(f"Loaded {len(self._styles)} styles: {list(self._styles.keys())}")

    def get_style(self, style_id: str) -> Optional[Style]:
        """
        Get a style by ID.

        Args:
            style_id: The style identifier

        Returns:
            Style object or None if not found
        """
        return self._styles.get(style_id)

    def list_styles(self) -> list[Style]:
        """
        Get all available styles.

        Returns:
            List of Style objects
        """
        return list(self._styles.values())

    def get_style_ids(self) -> list[str]:
        """
        Get all style IDs.

        Returns:
            List of style ID strings
        """
        return list(self._styles.keys())

    def get_prompts(
        self,
        style_id: str,
        custom_prompt: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Get prompts for a specific style.

        Args:
            style_id: The style identifier
            custom_prompt: Optional custom prompt to use

        Returns:
            Tuple of (positive_prompt, negative_prompt)

        Raises:
            ValueError: If style_id is not found
        """
        style = self.get_style(style_id)
        if style is None:
            raise ValueError(
                f"Unknown style: {style_id}. Available: {self.get_style_ids()}"
            )

        return style.get_prompts(custom_prompt)

    def get_default_settings(self, style_id: str) -> dict:
        """
        Get default generation settings for a style.

        Args:
            style_id: The style identifier

        Returns:
            Dictionary with generation settings
        """
        style = self.get_style(style_id)
        if style is None:
            raise ValueError(f"Unknown style: {style_id}")

        return {
            "num_steps": style.recommended_steps,
            "guidance_scale": style.guidance_scale,
            "model": style.recommended_model,
            **self._defaults,
        }

    def get_safety_terms(self) -> list[str]:
        """
        Get terms that should always be in negative prompts.

        Returns:
            List of safety terms
        """
        return self._safety.get("always_include", [])

    def is_child_safe(self) -> bool:
        """Check if child-safe mode is enabled."""
        return self._safety.get("child_safe_only", True)


def create_style_manager(config_path: Optional[Path] = None) -> StyleManager:
    """
    Factory function to create a StyleManager.

    Args:
        config_path: Optional custom config path

    Returns:
        Configured StyleManager instance
    """
    return StyleManager(config_path)


# Example usage
if __name__ == "__main__":
    manager = StyleManager()

    print("Available styles:")
    for style in manager.list_styles():
        print(f"  - {style.id}: {style.display_name}")

    print("\nGetting prompts for 'pixar_3d':")
    positive, negative = manager.get_prompts("pixar_3d", "a cute cat")
    print(f"  Positive: {positive[:50]}...")
    print(f"  Negative: {negative}")
