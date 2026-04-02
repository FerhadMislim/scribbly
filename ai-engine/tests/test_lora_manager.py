"""
Tests for LoRAManager
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_loras_dir():
    """Create a temporary directory for LoRA files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_pipeline():
    """Create a mock InferencePipeline."""
    pipe = MagicMock()
    pipe.is_loaded = True
    pipe._pipeline = MagicMock()
    return pipe


@pytest.fixture
def lora_manager(temp_loras_dir, mock_pipeline):
    """Create a LoRAManager with mock pipeline."""
    from lora_manager import LoRAManager

    manager = LoRAManager(pipeline=mock_pipeline, loras_dir=temp_loras_dir)
    return manager


class TestLoRAManagerInit:
    """Tests for LoRAManager initialization."""

    def test_init_creates_loras_dir(self, temp_loras_dir):
        """Test that init creates loras directory if it doesn't exist."""
        from lora_manager import LoRAManager

        new_dir = temp_loras_dir / "new_loras"
        manager = LoRAManager(loras_dir=new_dir)

        assert new_dir.exists()
        assert manager.loras_dir == new_dir

    def test_init_with_existing_dir(self, temp_loras_dir):
        """Test init with existing directory."""
        from lora_manager import LoRAManager

        manager = LoRAManager(loras_dir=temp_loras_dir)

        assert manager.loras_dir == temp_loras_dir


class TestListAvailable:
    """Tests for listing available LoRAs."""

    def test_list_available_empty(self, lora_manager):
        """Test listing when no LoRAs registered."""
        loras = lora_manager.list_available()

        assert loras == []

    def test_list_available_with_metadata(self, lora_manager, temp_loras_dir):
        """Test listing with LoRAs in metadata."""
        metadata = {
            "loras": [
                {
                    "id": "lora_001",
                    "name": "Test LoRA",
                    "style_id": "style_001",
                    "path": "test_lora.safetensors",
                    "trigger_word": "testword",
                    "scale": 0.8,
                }
            ]
        }

        metadata_path = temp_loras_dir / "loras.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        loras = lora_manager.list_available()

        assert len(loras) == 1
        assert loras[0]["id"] == "lora_001"


class TestLoadUnload:
    """Tests for loading and unloading LoRAs."""

    def test_load_requires_pipeline(self, lora_manager, temp_loras_dir):
        """Test that load raises error without pipeline."""
        from lora_manager import LoRAManager

        manager = LoRAManager(loras_dir=temp_loras_dir)

        with pytest.raises(RuntimeError, match="No pipeline attached"):
            manager.load("test.safetensors")

    def test_load_nonexistent_file(self, lora_manager, temp_loras_dir):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            lora_manager.load("nonexistent.safetensors")

    def test_load_calls_pipeline_methods(
        self, lora_manager, mock_pipeline, temp_loras_dir
    ):
        """Test that load calls pipeline methods correctly."""
        lora_path = temp_loras_dir / "test.safetensors"
        lora_path.touch()

        lora_manager.load(lora_path, scale=0.7)

        mock_pipeline._pipeline.load_lora_weights.assert_called_once()
        mock_pipeline._pipeline.fuse_lora.assert_called_once_with(lora_scale=0.7)

    def test_load_registers_lora(self, lora_manager, mock_pipeline, temp_loras_dir):
        """Test that loaded LoRA is tracked."""
        lora_path = temp_loras_dir / "test.safetensors"
        lora_path.touch()

        lora_manager.load(lora_path, scale=0.8)

        assert str(lora_path) in lora_manager.get_loaded_loras()
        assert lora_manager.get_loaded_loras()[str(lora_path)] == 0.8

    def test_unload_all(self, lora_manager, mock_pipeline, temp_loras_dir):
        """Test unloading all LoRAs."""
        lora_path = temp_loras_dir / "test.safetensors"
        lora_path.touch()

        lora_manager.load(lora_path, scale=0.8)
        assert lora_manager.is_loaded

        lora_manager.unload()

        assert not lora_manager.is_loaded
        mock_pipeline._pipeline.unfuse_lora.assert_called()
        mock_pipeline._pipeline.unload_lora_weights.assert_called()

    def test_unload_specific(self, lora_manager, mock_pipeline, temp_loras_dir):
        """Test unloading specific LoRA."""
        lora1 = temp_loras_dir / "lora1.safetensors"
        lora2 = temp_loras_dir / "lora2.safetensors"
        lora1.touch()
        lora2.touch()

        lora_manager.load(lora1, scale=0.8)
        lora_manager.load(lora2, scale=0.6)

        lora_manager.unload(lora1)

        loaded = lora_manager.get_loaded_loras()
        assert str(lora1) not in loaded
        assert str(lora2) in loaded


class TestStackLorAs:
    """Tests for stacking multiple LoRAs."""

    def test_stack_loras(self, lora_manager, mock_pipeline, temp_loras_dir):
        """Test stacking multiple LoRAs."""
        lora1 = temp_loras_dir / "lora1.safetensors"
        lora2 = temp_loras_dir / "lora2.safetensors"
        lora1.touch()
        lora2.touch()

        lora_manager.stack_loras(
            [
                (lora1, 0.8),
                (lora2, 0.5),
            ]
        )

        loaded = lora_manager.get_loaded_loras()
        assert len(loaded) == 2


class TestTriggerWords:
    """Tests for trigger word handling."""

    def test_get_trigger_words_empty(self, lora_manager):
        """Test getting trigger words for unknown LoRA."""
        assert lora_manager.get_trigger_words("unknown") == ""

    def test_get_trigger_words_from_metadata(self, lora_manager, temp_loras_dir):
        """Test getting trigger words from metadata."""
        metadata = {
            "loras": [
                {
                    "id": "lora_001",
                    "name": "Test",
                    "path": "test.safetensors",
                    "trigger_word": "masterpiece",
                }
            ]
        }

        metadata_path = temp_loras_dir / "loras.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        trigger = lora_manager.get_trigger_words("lora_001")

        assert trigger == "masterpiece"

    def test_inject_trigger_words(self, lora_manager, temp_loras_dir):
        """Test injecting trigger words into prompt."""
        metadata = {
            "loras": [
                {
                    "id": "lora_001",
                    "name": "Test",
                    "path": "test.safetensors",
                    "trigger_word": "masterpiece",
                }
            ]
        }

        metadata_path = temp_loras_dir / "loras.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        result = lora_manager.inject_trigger_words("a cat", "lora_001")

        assert result == "masterpiece, a cat"

    def test_inject_trigger_words_empty(self, lora_manager):
        """Test injecting when no trigger word exists."""
        result = lora_manager.inject_trigger_words("a cat", "unknown")

        assert result == "a cat"


class TestRegisterLora:
    """Tests for registering new LoRAs."""

    def test_register_lora(self, lora_manager, temp_loras_dir):
        """Test registering a new LoRA."""
        lora_id = lora_manager.register_lora(
            name="Test LoRA",
            style_id="style_anime",
            path="anime_style.safetensors",
            trigger_word="anime style",
            scale=0.7,
        )

        assert lora_id == "lora_001"

        metadata = lora_manager._get_metadata()
        assert len(metadata["loras"]) == 1
        assert metadata["loras"][0]["name"] == "Test LoRA"

    def test_register_multiple_loras(self, lora_manager):
        """Test registering multiple LoRAs."""
        lora_manager.register_lora("LoRA 1", "style_1", "lora1.safetensors")
        lora_manager.register_lora("LoRA 2", "style_2", "lora2.safetensors")

        metadata = lora_manager._get_metadata()

        assert len(metadata["loras"]) == 2
        assert metadata["loras"][0]["id"] == "lora_001"
        assert metadata["loras"][1]["id"] == "lora_002"


class TestLoadUnloadCycle:
    """Test load/unload/generate cycle (acceptance criteria)."""

    def test_load_unload_cycle(self, lora_manager, mock_pipeline, temp_loras_dir):
        """Test: load LoRA, generate image, unload LoRA, generate again."""
        lora_path = temp_loras_dir / "test.safetensors"
        lora_path.touch()

        lora_manager.load(lora_path, scale=0.8)
        assert lora_manager.is_loaded

        loaded_after_load = lora_manager.get_loaded_loras()
        assert len(loaded_after_load) == 1

        lora_manager.unload()
        assert not lora_manager.is_loaded

        loaded_after_unload = lora_manager.get_loaded_loras()
        assert len(loaded_after_unload) == 0
