# Multi-stage Docker build for size optimization
FROM python:3.12-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PIP_CACHE_DIR="/tmp/.cache/pip" \
    PYTHONPATH="PYTHONPATH:."
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set the working directory and copy requirements
WORKDIR /app
COPY requirements.txt /app/requirements.txt

# Install Python dependencies in virtual environment
RUN python -m venv venv
RUN venv/bin/pip install --upgrade pip
RUN venv/bin/pip install -r requirements.txt

# Production stage
FROM python:3.12-slim-bookworm AS production

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    wget \
    coreutils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv

# Copy application code
COPY lib /app/lib
COPY systems /app/systems
COPY my_utils /app/my_utils
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY download_with_progress.py /app/download_with_progress.py

# Set environment variables
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH="PYTHONPATH:."

# spaCy processing configuration
ENV SPACY_USE_DEPENDENCIES="True"
ENV SPACY_USE_GERMALEMMA="True"
ENV SPACY_PARSE_TIMEOUT="30"
ENV SPACY_MAX_SENTENCE_LENGTH="500"
ENV SPACY_N_PROCESS="10"
ENV SPACY_BATCH_SIZE="2000"
ENV SPACY_CHUNK_SIZE="20000"

WORKDIR /app
RUN mkdir -p "/app/logs" "/app/tmp" "/local/models"

# Set temp directories to use app directory instead of system /tmp
ENV TMPDIR="/app/tmp"
ENV TEMP="/app/tmp"
ENV TMP="/app/tmp"

# Make entrypoint executable
RUN chmod +x /docker-entrypoint.sh

# Define the entry point
ENTRYPOINT ["/docker-entrypoint.sh"]
