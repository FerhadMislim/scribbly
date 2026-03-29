# AI Engine

Inference pipeline, model configurations, and LoRA training scripts for Scribbly.

## Getting Started

### Prerequisites

- Python 3.11+
- NVIDIA GPU with 8GB+ VRAM (16GB recommended for SDXL)
- CUDA 12.1+

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download models (see below)
```

## Downloading Models

```bash
# Download base models and ControlNet
bash scripts/download_models.sh
```

This will download:
- Stable Diffusion XL 1.0 (~6.5GB)
- Stable Diffusion 1.5 (~2GB)
- ControlNet Scribble (~500MB)
- ControlNet Canny (~500MB)

## Project Structure

```
ai-engine/
├── pipeline.py           # Core InferencePipeline class
├── preprocess.py         # Image preprocessing (HED, Canny)
├── style_manager.py     # Style configuration loader
├── lora_manager.py      # LoRA loading/unloading
├── animation.py         # AnimateDiff integration
├── config/
│   └── style_config.yaml
├── models/              # Model weights (not in git)
│   ├── sdxl/
│   ├── sd15/
│   ├── controlnet/
│   └── loras/
├── training_configs/    # Kohya_ss configs
├── scripts/
│   ├── download_models.sh
│   └── prepare_dataset.py
└── tests/
```

## Usage

### Basic Inference

```python
from pipeline import InferencePipeline

pipeline = InferencePipeline(
    model_id="stabilityai/stable-diffusion-xl-base-1.0",
    controlnet_id="lllyasviel/control_v11p_sd15_scribble",
    device="cuda"
)

result = pipeline.generate(
    image=input_image,
    prompt="pixar style, cute character",
    style="pixar_3d",
    num_steps=30
)
result.save("output.png")
```

### With LoRA

```python
from lora_manager import LoRAManager

lora_manager = LoRAManager(pipeline)
lora_manager.load("soft_3d_v1", scale=0.8)

result = pipeline.generate(...)
lora_manager.unload()
```

## GPU Requirements

| Model | VRAM | Notes |
|-------|------|-------|
| SDXL | ~10GB | Base model |
| SD1.5 | ~4GB | Fallback for low-VRAM |
| ControlNet | +2GB | Per model |
| LoRA | +100MB | Per LoRA |

## Testing

```bash
# Test inference without GPU
python test_inference.py --cpu

# Test preprocessing
python test_preprocess.py
```
