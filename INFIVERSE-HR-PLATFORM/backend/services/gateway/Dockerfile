FROM python:3.12.7-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 3 -r requirements.txt

# Copy application code and dependencies
COPY app/ ./app/
COPY langgraph_integration.py ./
COPY monitoring.py ./
COPY config.py ./
COPY dependencies.py ./
COPY jwt_auth.py ./
COPY workflow_proxy.py ./
COPY routes/ ./routes/

# Expose port
EXPOSE 8000

# Start application on fixed port 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "30"]
