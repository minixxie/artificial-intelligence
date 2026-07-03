#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "Installing CUDA 12.4 compatible torch..."
echo "========================================"
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124

echo "==============================="
echo "Installing other dependencies..."
echo "==============================="
pip install --upgrade -r "$BASE_DIR/requirements.txt"

echo "====================="
echo "Checking GPU status..."
echo "====================="
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'  GPU: {torch.cuda.get_device_name(0)}')
    print(f'  Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
else:
    print('  WARNING: GPU not available — running on CPU will be extremely slow!')
"

export CUDA_VISIBLE_DEVICES=0

echo "========================="
echo "Starting QLoRA training..."
echo "========================="
python3 "$BASE_DIR/scripts/train.py" \
  --model_path "$BASE_DIR/glm-4-9b-chat" \
  --data_path "$BASE_DIR/data/train.jsonl" \
  --output_dir "$BASE_DIR/output"

