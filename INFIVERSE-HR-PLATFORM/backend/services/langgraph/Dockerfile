FROM python:3.12.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 9001

# Health check (will be disabled on Render as it uses dynamic ports)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import httpx; httpx.get('http://localhost:9001/health', timeout=5)" || exit 1

# Port 9001 matches docker-compose.production.yml; override with PORT env if needed
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9001", "--timeout-keep-alive", "30"]