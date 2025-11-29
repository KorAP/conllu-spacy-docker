#!/bin/bash
# Script to preload spaCy models to a local directory
# Usage: ./preload-models.sh [MODEL_NAME] [TARGET_DIR]

set -e

MODEL_NAME="${1:-de_core_news_lg}"
TARGET_DIR="${2:-./models}"

echo "Preloading spaCy model: $MODEL_NAME"
echo "Target directory: $TARGET_DIR"

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Check if model already exists
if [ -d "$TARGET_DIR/$MODEL_NAME" ]; then
    echo "Model $MODEL_NAME already exists in $TARGET_DIR"
    echo "Remove it first if you want to re-download: rm -rf $TARGET_DIR/$MODEL_NAME"
    exit 0
fi

echo "Downloading model using temporary Docker container..."

# Use a temporary container to download the model
docker run --rm -v "$(realpath $TARGET_DIR)":/models python:3.12-slim-bookworm bash -c "
    set -e
    echo 'Installing spaCy...'
    pip install -q spacy

    echo 'Downloading model $MODEL_NAME...'
    echo 'This may take several minutes depending on your connection speed.'
    python -m spacy download $MODEL_NAME --no-cache-dir 2>&1 | while IFS= read -r line; do
        echo \"\$line\"
        # Show progress dots for download
        if [[ \"\$line\" == *\"Downloading\"* ]]; then
            echo -n \"Progress: \"
        fi
    done

    echo 'Moving model to /models...'
    python -c \"
import spacy
import shutil
import site
import os

# Get the installed model path
site_packages = site.getsitepackages()[0]
model_path = site_packages + '/$MODEL_NAME'

# spaCy packages contain a subdirectory with the versioned model
# Find the actual model directory (e.g., de_core_news_lg-3.8.0)
items = os.listdir(model_path)
model_subdir = None
for item in items:
    item_path = os.path.join(model_path, item)
    if os.path.isdir(item_path) and '$MODEL_NAME' in item:
        model_subdir = item_path
        break

if model_subdir:
    # Copy the actual model directory
    shutil.copytree(model_subdir, '/models/$MODEL_NAME')
    print(f'Model copied successfully from {model_subdir}!')
else:
    # Fallback: copy the whole package
    shutil.copytree(model_path, '/models/$MODEL_NAME')
    print('Model copied successfully!')
\"
"

if [ -d "$TARGET_DIR/$MODEL_NAME" ]; then
    # Set permissions so all users can read/write/execute
    echo "Setting permissions..."
    chmod -R a+rwX "$TARGET_DIR/$MODEL_NAME"

    echo ""
    echo "✓ Model $MODEL_NAME successfully preloaded to $TARGET_DIR/$MODEL_NAME"
    echo ""
    echo "You can now run the container with:"
    echo "  docker run --rm -i -v $(realpath $TARGET_DIR):/local/models korap/conllu-spacy"
else
    echo "✗ Error: Model download failed"
    exit 1
fi
