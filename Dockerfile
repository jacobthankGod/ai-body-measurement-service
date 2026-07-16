# Use Python 3.11-slim to match pyproject.toml requirements
FROM python:3.11-slim

# Install system dependencies for OpenCV, MediaPipe, and TensorFlow
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libgl1 \
    libglib2.0-0t64 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create a temporary directory for pip to avoid tmpfs exhaustion (455M limit)
# This directory is on the persistent disk.
RUN mkdir -p /app/tmp
ENV TMPDIR=/app/tmp

# Upgrade pip and install core build tools
# We combine these to minimize layers and reclaim space immediately
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir numpy==1.26.3 && \
    pip install --no-cache-dir chumpy==0.70 --no-build-isolation

# Copy requirements and install all dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip /app/tmp/*

# Re-create essential directories
RUN mkdir -p /app/data/ansur_processed /app/api/models/imputation

# Cleanup apt to reclaim space
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application
# .dockerignore now properly excludes large data/ and model/ files
COPY . .

# Final cleanup of build-time temp dir
RUN rm -rf /app/tmp

# Environment variables for AWS EC2 / Docker
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Command to run the application
# Uses PORT env var (set by Docker or EC2 systemd service)
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --h11-max-incoming-body-size 52428800"]
