"""
Tests for the StyleManager class.
"""

import sys
from pathlib import Path

import pytest
import yaml

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStyle:
    """Test cases for Style dataclass."""

    def test_get_prompts_default(self):
        """Test get_prompts returns default prompts."""
        from style_manager import Style

        style = Style(
            id="test",
            display_name="Test",
            description="Test style",
            positive_prompt="positive",
            negative_prompt="negative",
            recommended_steps=25,
            guidance_scale=7.5,
            recommended_model="sd15",
            thumbnail_url="",
        )

        positive, negative = style.get_prompts()
        assert positive == "positive"
        assert negative == "negative"

    def test_get_prompts_custom(self):
        """Test get_prompts with custom prompt."""
        from style_manager import Style

        style = Style(
            id="test",
            display_name="Test",
            description="Test style",
            positive_prompt="default positive",
            negative_prompt="negative",
            recommended_steps=25,
            guidance_scale=7.5,
            recommended_model="sd15",
            thumbnail_url="",
        )

        positive, negative = style.get_prompts(custom_prompt="custom prompt")
        assert positive == "custom prompt"
        assert negative == "negative"


class TestStyleManager:
    """Test cases for StyleManager."""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file."""
        config = {
            "styles": [
                {
                    "id": "test_style",
                    "display_name": "Test Style",
                    "description": "A test style",
                    "positive_prompt": "test positive prompt",
                    "negative_prompt": "test negative prompt",
                    "recommended_steps": 20,
                    "guidance_scale": 7.0,
                    "recommended_model": "sd15",
                    "thumbnail_url": "/test.png",
                },
                {
                    "id": "another_style",
                    "display_name": "Another Style",
                    "description": "Another test style",
                    "positive_prompt": "another positive",
                    "negative_prompt": "another negative",
                    "recommended_steps": 30,
                    "guidance_scale": 8.0,
                    "recommended_model": "sdxl",
                    "thumbnail_url": "/another.png",
                },
            ],
            "defaults": {
                "num_images": 1,
                "image_size": 512,
            },
            "safety": {
                "always_include": ["scary", "violent"],
                "child_safe_only": True,
            },
        }

        file_path = tmp_path / "style_config.yaml"
        with open(file_path, "w") as f:
            yaml.dump(config, f)

        return file_path

    def test_load_styles(self, config_file):
        """Test loading styles from config."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)

        assert len(manager.list_styles()) == 2
        assert "test_style" in manager.get_style_ids()

    def test_get_style(self, config_file):
        """Test getting a specific style."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)
        style = manager.get_style("test_style")

        assert style is not None
        assert style.id == "test_style"
        assert style.display_name == "Test Style"
        assert style.positive_prompt == "test positive prompt"

    def test_get_style_not_found(self, config_file):
        """Test getting non-existent style returns None."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)
        style = manager.get_style("nonexistent")

        assert style is None

    def test_get_prompts(self, config_file):
        """Test getting prompts for a style."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)
        positive, negative = manager.get_prompts("test_style", "custom cat")

        assert positive == "custom cat"
        assert negative == "test negative prompt"

    def test_get_prompts_no_custom(self, config_file):
        """Test getting prompts without custom prompt."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)
        positive, negative = manager.get_prompts("test_style")

        assert positive == "test positive prompt"
        assert negative == "test negative prompt"

    def test_get_prompts_invalid_style(self, config_file):
        """Test getting prompts for invalid style raises error."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)

        with pytest.raises(ValueError, match="Unknown style"):
            manager.get_prompts("invalid_style")

    def test_get_default_settings(self, config_file):
        """Test getting default settings for a style."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)
        settings = manager.get_default_settings("test_style")

        assert settings["num_steps"] == 20
        assert settings["guidance_scale"] == 7.0
        assert settings["model"] == "sd15"
        assert settings["num_images"] == 1  # from defaults

    def test_get_safety_terms(self, config_file):
        """Test getting safety terms."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)
        terms = manager.get_safety_terms()

        assert "scary" in terms
        assert "violent" in terms

    def test_is_child_safe(self, config_file):
        """Test child safe check."""
        from style_manager import StyleManager

        manager = StyleManager(config_file)

        assert manager.is_child_safe() is True


class TestStyleManagerIntegration:
    """Integration tests with real config."""

    def test_load_real_config(self):
        """Test loading the actual style_config.yaml."""
        from style_manager import StyleManager

        config_path = Path(__file__).parent.parent / "config" / "style_config.yaml"

        if not config_path.exists():
            pytest.skip("Config file not found")

        manager = StyleManager(config_path)

        # Check all expected styles exist
        expected_styles = [
            "pixar_3d",
            "anime",
            "storybook",
            "soft_illustration",
            "sketch_colored",
            "watercolor",
            "comic",
        ]

        for style_id in expected_styles:
            style = manager.get_style(style_id)
            assert style is not None, f"Missing style: {style_id}"

        # Check safety terms
        safety_terms = manager.get_safety_terms()
        assert "scary" in safety_terms
        assert "violent" in safety_terms
        assert "nsfw" in safety_terms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
