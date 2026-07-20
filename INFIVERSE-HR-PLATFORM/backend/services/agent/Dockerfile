FROM python:3.12.7-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --timeout 300 --retries 3 -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 9000

# Start application on fixed port 9000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000", "--timeout-keep-alive", "30"]
