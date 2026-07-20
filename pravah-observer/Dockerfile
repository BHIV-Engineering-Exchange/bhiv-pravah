FROM python:3.11-slim
WORKDIR /observer
COPY observer.py .
RUN pip install --no-cache-dir requests
ENV PYTHONUNBUFFERED=1
CMD ["python","observer.py"]
