# ============================================================================
# BASE STAGE - Common dependencies for all stages
# ============================================================================
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for the app
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for temporary files
RUN mkdir -p /tmp/recipe-app

# Expose port
EXPOSE 8000

# ============================================================================
# DEVELOPMENT STAGE - With hot-reload support
# ============================================================================
FROM base as development

# Note: Application code is mounted via volumes in docker-compose.yml
# This allows hot-reload without rebuilding the container

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Development command (will be overridden by docker-compose.yml)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================================
# PRODUCTION STAGE - Optimized for deployment
# ============================================================================
FROM base as production

# Copy application code
COPY . .

# Health check for production
HEALTHCHECK --interval=300s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Production command
CMD ["python", "main.py"]
