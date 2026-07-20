# FROM python:3.10-slim

# WORKDIR /app

# COPY requirements-minimal.txt .

# RUN pip install -r --no-cache-dir requirements-minimal.txt

# COPY . .

# EXPOSE 5000

# CMD ["uvicorn", "run_hft2:app", "--reload", "--host", "0.0.0.0", "--port", "5000"]

# -------- Stage 1: Builder --------
FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements-minimal.txt .

RUN pip install --no-cache-dir \
    --prefix=/install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements-minimal.txt


FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

# RUN adduser --disabled-password --gecos "" hft2

# RUN mkdir -p /app/data/cache && \
#     chown -R hft2:hft2 /app

# USER hft2

EXPOSE 5000

HEALTHCHECK CMD curl --fail http://localhost:5000/api/health || exit 1

CMD ["python","run_hft2.py"]