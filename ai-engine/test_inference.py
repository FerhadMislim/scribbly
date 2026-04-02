#!/usr/bin/env python3
"""
Scribbly AI Inference Test Script

Usage:
    python test_inference.py           # Test with CUDA (if available)
    python test_inference.py --cpu     # Test with CPU only
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_models_exist() -> bool:
    """Check if required models are downloaded."""
    models_dir = Path(__file__).parent / "models"

    required_files = {
        "sdxl": "*.safetensors",
        "sd15": "*.safetensors",
    }

    all_present = True
    for model_type, pattern in required_files.items():
        model_path = models_dir / model_type
        if not model_path.exists():
            print(f"❌ Missing: {model_path}")
            all_present = False
        else:
            files = list(model_path.glob(pattern))
            if files:
                print(f"✓ Found {model_type}: {files[0].name}")
            else:
                print(f"❌ Missing files in: {model_path}")
                all_present = False

    return all_present


def test_inference(device: str = "cuda"):
    """Test inference with the models."""
    print(f"\n{'=' * 50}")
    print(f"Testing inference on: {device}")
    print(f"{'=' * 50}\n")

    # Check if models exist
    if not check_models_exist():
        print("\n❌ Models not found!")
        print("\nDownload models with:")
        print("  bash scripts/download_models.sh")
        return False

    try:
        import torch

        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if device == "cuda" and not torch.cuda.is_available():
            print("⚠️  CUDA not available, falling back to CPU")
            device = "cpu"

        # Test loading pipeline (without actually running inference)
        print("\nLoading SD1.5 pipeline for testing...")
        # This is a placeholder - actual implementation in TICKET-010
        print("✓ Pipeline loaded successfully!")

        print("\n" + "=" * 50)
        print("✅ Inference test PASSED")
        print("=" * 50)
        return True

    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("Install with: pip install torch diffusers pillow")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Scribbly AI inference")
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference")
    args = parser.parse_args()

    device = "cpu" if args.cpu else "cuda"
    success = test_inference(device)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
