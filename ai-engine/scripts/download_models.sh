#!/bin/bash
# ===========================================
# Scribbly AI Model Download Script
# ===========================================
# Usage: bash scripts/download_models.sh
#
# Requirements:
#   - HuggingFace account (for rate limits)
#   - pip install huggingface_hub
#
# For gated models, login with:
#   huggingface-cli login

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_DIR/models"

echo "==========================================="
echo "Scribbly AI Model Downloader"
echo "==========================================="

# Install huggingface_hub if not present
if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface_hub..."
    pip install huggingface_hub
fi

# Create model directories
mkdir -p "$MODELS_DIR/sdxl"
mkdir -p "$MODELS_DIR/sd15"
mkdir -p "$MODELS_DIR/controlnet_scribble"
mkdir -p "$MODELS_DIR/controlnet_canny"
mkdir -p "$MODELS_DIR/controlnet_sdxl"

echo ""
echo "Downloading Stable Diffusion XL 1.0 (~6.5GB)..."
echo "-------------------------------------------"
huggingface-cli download stabilityai/stable-diffusion-xl-base-1.0 \
    --include "*.safetensors" \
    --local-dir "$MODELS_DIR/sdxl"

echo ""
echo "Downloading Stable Diffusion 1.5 (~2GB)..."
echo "-------------------------------------------"
huggingface-cli download runwayml/stable-diffusion-v1-5 \
    --include "*.safetensors" \
    --local-dir "$MODELS_DIR/sd15"

echo ""
echo "Downloading ControlNet Scribble (~500MB)..."
echo "-------------------------------------------"
huggingface-cli download lllyasviel/control_v11p_sd15_scribble \
    --local-dir "$MODELS_DIR/controlnet_scribble"

echo ""
echo "Downloading ControlNet Canny (~500MB)..."
echo "-------------------------------------------"
huggingface-cli download lllyasviel/control_v11p_sd15_canny \
    --local-dir "$MODELS_DIR/controlnet_canny"

echo ""
echo "Downloading ControlNet for SDXL (~1GB)..."
echo "-------------------------------------------"
huggingface-cli download diffusers/controlnet-canny-sdxl-1.0 \
    --local-dir "$MODELS_DIR/controlnet_sdxl"

echo ""
echo "==========================================="
echo "Download complete!"
echo "==========================================="
echo ""
echo "Models stored in: $MODELS_DIR"
echo ""
echo "Verify downloads:"
echo "  ls -la $MODELS_DIR/sdxl/"
echo "  ls -la $MODELS_DIR/sd15/"
echo "  ls -la $MODELS_DIR/controlnet_scribble/"
echo "  ls -la $MODELS_DIR/controlnet_canny/"
echo ""
echo "Next steps:"
echo "  1. Run test inference: python ai-engine/test_inference.py"
echo "  2. Run ControlNet test: python ai-engine/test_controlnet.py"
