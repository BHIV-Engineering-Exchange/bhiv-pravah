FROM python:3.10-slim AS builder

WORKDIR /app


COPY requirements-unified.txt .
COPY requirements-optional.txt .
COPY requirements-fyers.txt .

RUN pip install --no-cache-dir \
    --prefix=/install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements-unified.txt \
    -r requirements-optional.txt \
    -r requirements-fyers.txt

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

RUN adduser --disabled-password --gecos "" backend

RUN mkdir -p /app/data/cache && \
    chown -R backend:backend /app

USER backend

EXPOSE 8000

HEALTHCHECK CMD curl --fail http://localhost:8000/tools/health || exit 1

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
