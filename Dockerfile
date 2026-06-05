# AI Body Scan SaaS - Production Dockerfile (Heavy AI Support)
# =========================================================

FROM python:3.11-slim

# Install system dependencies for OpenCV and MediaPipe
# Note: libgl1-mesa-glx is obsolete in newer Debian, using libgl1 instead.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install full ML requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Download crucial ML models during build to bypass Git LFS quota
RUN python scripts/download_models.py

# Environment Defaults
ENV PORT=5001
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 5001

# Entry point
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5001"]
