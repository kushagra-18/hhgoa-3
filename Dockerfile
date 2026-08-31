# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies for OpenCV, ONNX Runtime, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source code and contracts
COPY contracts/ ./contracts/
COPY src/ ./src/
COPY tests/ ./tests/
COPY README.md .
COPY .env.example .env

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/crops /app/data/cache /app/data/samples /root/.insightface/models

# Generate sample assets
RUN python -m src.generate_samples || true

# Expose FastAPI web port
EXPOSE 8000

# Default command starts FastAPI dashboard
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
