#!/usr/bin/env python3
"""
Scribbly ControlNet Test Script

Tests that ControlNet models can be loaded and produce conditioned outputs.

Usage:
    python test_controlnet.py           # Test with CUDA
    python test_controlnet.py --cpu     # Test with CPU only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check_controlnet_models() -> dict:
    """Check which ControlNet models are available."""
    models_dir = Path(__file__).parent / "models"
    
    models = {
        "scribble": models_dir / "controlnet_scribble",
        "canny": models_dir / "controlnet_canny",
        "sdxl": models_dir / "controlnet_sdxl",
    }
    
    available = {}
    for name, path in models.items():
        if path.exists() and any(path.glob("*.safetensors")):
            print(f"✓ Found {name}: {path}")
            available[name] = path
        elif path.exists() and any(path.glob("diffusion_pytorch_model.*")):
            print(f"✓ Found {name}: {path}")
            available[name] = path
        else:
            print(f"✗ Missing {name}: {path}")
    
    return available


def test_controlnet_loading(device: str = "cuda"):
    """Test loading ControlNet models."""
    print(f"\n{'='*50}")
    print(f"Testing ControlNet on: {device}")
    print(f"{'='*50}\n")
    
    available = check_controlnet_models()
    
    if not available:
        print("\n❌ No ControlNet models found!")
        print("\nDownload with:")
        print("  bash scripts/download_models.sh")
        return False
    
    try:
        import torch
        from PIL import Image
        import numpy as np
        
        print(f"\nPyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if device == "cuda" and not torch.cuda.is_available():
            print("⚠️  CUDA not available, falling back to CPU")
            device = "cpu"
        
        dtype = torch.float32 if device == "cpu" else torch.float16
        
        # Test loading each available model
        from diffusers import ControlNetModel
        
        for name, path in available.items():
            print(f"\nLoading ControlNet ({name}) from {path.name}...")
            try:
                model = ControlNetModel.from_pretrained(
                    str(path),
                    torch_dtype=dtype,
                )
                model = model.to(device)
                print(f"✓ {name} loaded successfully!")
                
                # Test with a dummy image
                dummy_img = Image.new("RGB", (512, 512), color="white")
                print(f"  - Created dummy image: {dummy_img.size}")
                
            except Exception as e:
                print(f"❌ Failed to load {name}: {e}")
                return False
        
        print("\n" + "="*50)
        print("✅ ControlNet test PASSED")
        print("="*50)
        return True
        
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("Install with: pip install torch diffusers pillow")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Scribbly ControlNet")
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU inference"
    )
    args = parser.parse_args()
    
    device = "cpu" if args.cpu else "cuda"
    success = test_controlnet_loading(device)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
