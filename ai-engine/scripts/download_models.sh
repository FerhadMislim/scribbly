#!/bin/bash
# ===========================================
# Scribbly AI Model Download Script
# ===========================================
# Usage: bash ai-engine/scripts/download_models.sh
#
# Requirements:
#   - HuggingFace account (for rate limits)
#   - A virtualenv with huggingface_hub, or permission to install it there
#
# For gated models, login with:
#   huggingface-cli login
#   or: python -m huggingface_hub.commands.huggingface_cli login

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_DIR="$(dirname "$PROJECT_DIR")"
MODELS_DIR="$PROJECT_DIR/models"

echo "==========================================="
echo "Scribbly AI Model Downloader"
echo "==========================================="

# Resolve a safe Python environment for huggingface_hub.
PYTHON_BIN=""
if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "${VIRTUAL_ENV}/bin/python" ]; then
    PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
elif [ -x "$REPO_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$REPO_DIR/.venv/bin/python"
elif [ -x "$REPO_DIR/backend/.venv/bin/python" ]; then
    PYTHON_BIN="$REPO_DIR/backend/.venv/bin/python"
fi

HF_CMD=()
if command -v huggingface-cli >/dev/null 2>&1; then
    HF_CMD=("huggingface-cli")
elif command -v hf >/dev/null 2>&1; then
    HF_CMD=("hf")
elif [ -n "$PYTHON_BIN" ]; then
    echo "Installing huggingface_hub into: $PYTHON_BIN"
    "$PYTHON_BIN" -m pip install huggingface_hub
    HF_CMD=("$PYTHON_BIN" "-m" "huggingface_hub.commands.huggingface_cli")
else
    echo "No usable virtualenv found for installing huggingface_hub."
    echo "Activate one first, or create one at .venv or backend/.venv."
    exit 1
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
"${HF_CMD[@]}" download stabilityai/stable-diffusion-xl-base-1.0 \
    --include "*.safetensors" \
    --local-dir "$MODELS_DIR/sdxl"

echo ""
echo "Downloading Stable Diffusion 1.5 (~2GB)..."
echo "-------------------------------------------"
"${HF_CMD[@]}" download runwayml/stable-diffusion-v1-5 \
    --local-dir "$MODELS_DIR/sd15"

echo ""
echo "Downloading ControlNet Scribble (~500MB)..."
echo "-------------------------------------------"
"${HF_CMD[@]}" download lllyasviel/control_v11p_sd15_scribble \
    --local-dir "$MODELS_DIR/controlnet_scribble"

echo ""
echo "Downloading ControlNet Canny (~500MB)..."
echo "-------------------------------------------"
"${HF_CMD[@]}" download lllyasviel/control_v11p_sd15_canny \
    --local-dir "$MODELS_DIR/controlnet_canny"

echo ""
echo "Downloading ControlNet for SDXL (~1GB)..."
echo "-------------------------------------------"
"${HF_CMD[@]}" download diffusers/controlnet-canny-sdxl-1.0 \
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
