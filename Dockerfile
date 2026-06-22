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

# Upgrade pip and install core build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Pre-install numpy and build chumpy (Crucial for HMR)
RUN pip install --no-cache-dir numpy==1.26.3
RUN pip install --no-cache-dir chumpy==0.70 --no-build-isolation

# Copy requirements and install all dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# PHASE 134: COLD START OPTIMIZATION (Purge caches only)
RUN rm -rf /root/.cache/pip

# PHASE 121: BAKE ANSUR MATRICES
RUN mkdir -p /app/data/ansur_processed /app/api/models/imputation

# Copy the rest of the application
COPY . .

# Environment variables for Cloud Run
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Command to run the application
# We use the dynamic PORT variable provided by Cloud Run
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
