# Core Integrator Dockerfile for Production Deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports for all microservices in the Shakti/Tantra suite
# 8000: Creator Core, 8001: BHIV Core, 8003: Prompt Runner, 8004: Integration Bridge,
# 8005: Bucket, 8006: CET, 8007: Sarathi, 8008: Gate, 8009: Control Plane, 8010: Telemetry
EXPOSE 8000 8001 8003 8004 8005 8006 8007 8008 8009 8010

# Health check verifies aggregate system status on the control plane
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8009/system/status || exit 1

# Start all microservices in dependency order using the service orchestrator
CMD ["python", "start_all.py"]