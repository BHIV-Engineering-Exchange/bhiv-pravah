# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (Tesseract, Poppler, GCC, curl)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create models directory
RUN mkdir -p models

# Expose the port the app runs on
EXPOSE 3000

# Command to run the application (download models first if URLs provided)
CMD ["sh", "-c", "python download_models_on_startup.py && uvicorn app.main:app --host 0.0.0.0 --port 3000"]
