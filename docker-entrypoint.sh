#!/bin/bash

set -o pipefail

# Default values
model="de_core_news_lg"
use_dependencies="True"
use_germalemma="True"

usage() {
    echo "Usage: $0 [-h] [-m MODEL] [-L] [-d] [-g]"
    echo "  -h            Display this help message"
    echo "  -m MODEL      Specify spaCy model (default: $model)"
    echo "  -L            List available/installed models"
    echo "  -d            Disable dependency parsing (faster processing)"
    echo "  -g            Disable GermaLemma (use spaCy lemmatizer only)"
    exit 1
}

# Parse command line options
while getopts "hm:Ldg" opt; do
    case $opt in
        h)
            usage
            ;;
        m)
            model="$OPTARG"
            ;;
        L)
            echo "=== Installed Models ===" >&2

            # List models installed in venv
            INSTALLED=$(python -c "import spacy; import pkg_resources; print('\n'.join([pkg.key for pkg in pkg_resources.working_set if pkg.key.endswith(('-sm', '-md', '-lg', '-trf')) and not pkg.key.startswith('spacy')]))" 2>/dev/null)

            if [ -n "$INSTALLED" ]; then
                echo "$INSTALLED" | while read model; do
                    # Convert package name to model name (e.g., de-core-news-lg -> de_core_news_lg)
                    model_name=$(echo "$model" | sed 's/-/_/g')
                    echo "  $model_name" >&2
                done
            else
                echo "  No models installed in venv" >&2
            fi

            # Check for models in /local/models
            if [ -d "/local/models" ] && [ "$(ls -A /local/models 2>/dev/null)" ]; then
                echo "" >&2
                echo "Models in /local/models:" >&2
                ls -1 /local/models/ 2>/dev/null | while read dir; do
                    if [ -f "/local/models/$dir/config.cfg" ]; then
                        echo "  $dir" >&2
                    fi
                done
            fi

            echo "" >&2

            # Show available models list
            python /app/list_spacy_models.py
            exit 0
            ;;
        d)
            use_dependencies="False"
            ;;
        g)
            use_germalemma="False"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument" >&2
            usage
            ;;
    esac
done

if [ $OPTIND -le $# ]; then
    usage
fi

MODEL_DIR="/local/models"
MODEL_PATH="$MODEL_DIR/$model"

# Ensure MODEL_DIR exists
mkdir -p "$MODEL_DIR"

# Function to check if model is installed and usable
is_model_installed() {
    local model_name="$1"
    # Check if model is installed in the venv
    python -c "import spacy; spacy.load('$model_name')" 2>/dev/null
    return $?
}

# Function to check if preloaded model exists and is valid
has_preloaded_model() {
    local model_path="$1"
    # Check for config.cfg which indicates a valid spaCy model
    if [ -f "$model_path/config.cfg" ]; then
        return 0
    fi
    return 1
}

# Function to install model
install_model() {
    local model_name="$1"

    # Check if model exists in /local/models - if so, we'll use absolute path
    if has_preloaded_model "$MODEL_PATH"; then
        echo "Found preloaded model in $MODEL_PATH" >&2
        echo "Will use absolute path to avoid download" >&2
        return 0
    fi

    # Check if already installed in venv
    if is_model_installed "$model_name"; then
        echo "Model $model_name already installed in venv" >&2
        return 0
    fi

    # Try to download model to /local/models if writable
    if [ -w "$MODEL_DIR" ]; then
        # Download and install to /local/models with progress
        if python /app/download_with_progress.py "$model_name" 2>&1 | tee /tmp/spacy_download.log >&2; then
            # Extract and flatten the model structure for persistence
            SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
            INSTALLED_MODEL="$SITE_PACKAGES/$model_name"

            if [ -d "$INSTALLED_MODEL" ]; then
                echo "Extracting model to $MODEL_PATH for persistence..." >&2

                # Find the actual model directory (e.g., de_core_news_lg-3.8.0)
                VERSIONED_DIR=$(find "$INSTALLED_MODEL" -maxdepth 1 -type d -name "${model_name}-*" | head -1)

                if [ -n "$VERSIONED_DIR" ] && [ -f "$VERSIONED_DIR/config.cfg" ]; then
                    # Copy the versioned model directory contents to MODEL_PATH
                    mkdir -p "$MODEL_PATH"
                    cp -r "$VERSIONED_DIR"/* "$MODEL_PATH/"
                    # Set permissions so user can modify the model files
                    chmod -R a+rwX "$MODEL_PATH" 2>/dev/null || true
                    echo "Model extracted to $MODEL_PATH" >&2
                else
                    # Fallback: just move the whole package
                    echo "Warning: Could not find versioned model directory, moving package as-is" >&2
                    mv "$INSTALLED_MODEL" "$MODEL_PATH" 2>/dev/null || true
                    chmod -R a+rwX "$MODEL_PATH" 2>/dev/null || true
                fi
            fi
            return 0
        else
            echo "Failed to download model $model_name" >&2
            return 1
        fi
    else
        # MODEL_DIR not writable, install to venv (ephemeral)
        echo "Cannot write to $MODEL_DIR, installing to venv (ephemeral)" >&2
        if python /app/download_with_progress.py "$model_name" 2>&1 | tee /tmp/spacy_download.log >&2; then
            return 0
        else
            echo "Failed to download model $model_name" >&2
            return 1
        fi
    fi
}

# Install or verify model
if ! install_model "$model"; then
    echo "ERROR: Could not install model $model, aborting." >&2
    exit 1
fi

# Determine which model path to use
# If preloaded model exists, use absolute path; otherwise use model name
if has_preloaded_model "$MODEL_PATH"; then
    MODEL_TO_USE="$MODEL_PATH"
    echo "Using preloaded model at: $MODEL_TO_USE" >&2
else
    MODEL_TO_USE="$model"
    echo "Using installed model: $MODEL_TO_USE" >&2
fi

# Set environment variables for the Python script
export SPACY_USE_DEPENDENCIES="$use_dependencies"
export SPACY_USE_GERMALEMMA="$use_germalemma"

# Log configuration
echo "Configuration:" >&2
echo "  Model: $MODEL_TO_USE" >&2
echo "  Use dependencies: $use_dependencies" >&2
echo "  Use GermaLemma: $use_germalemma" >&2

# Run the spaCy tagging pipeline
python /app/systems/parse_spacy_pipe.py \
    --spacy_model "$MODEL_TO_USE" \
    --corpus_name "stdin" \
    --gld_token_type "CoNLLUP_Token" \
    --comment_str "#"
