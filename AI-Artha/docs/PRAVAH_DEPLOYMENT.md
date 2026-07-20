# ARTHA v0.1 Deployment Guide - Pravah Platform

This guide explains how to deploy ARTHA using Pravah in a repeatable, production-ready manner.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Building Images](#building-images)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Pipeline](#deployment-pipeline)
6. [Health Checks & Monitoring](#health-checks--monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Overview

ARTHA is a full-stack accounting system consisting of:
- **Backend**: Node.js/Express API with MongoDB
- **Frontend**: React/Vite SPA
- **Database**: MongoDB with replica set support
- **Cache**: Redis for performance optimization

Pravah orchestrates container deployment across these components.

---

## Prerequisites

### Required
- Pravah CLI/Platform configured
- Docker & Docker Compose (for local testing)
- Git (for source code)
- SSH/Git credentials for repo access

### Secrets Management
Ensure these are stored in Pravah Secrets (not in code):
- `MONGO_ROOT_PASSWORD`
- `MONGO_ROOT_USER`
- `JWT_SECRET` (min 32 chars)
- `JWT_REFRESH_SECRET` (min 32 chars)
- `HMAC_SECRET` (min 32 chars)
- `REDIS_PASSWORD`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

---

## Building Images

### Backend Image

**Dockerfile Location**: `backend/Dockerfile.prod`

Build command:
```bash
docker build -f backend/Dockerfile.prod -t artha-backend:latest backend/
```

Push to registry:
```bash
docker tag artha-backend:latest <registry>/artha-backend:latest
docker push <registry>/artha-backend:latest
```

### Frontend Image

**Dockerfile Location**: `frontend/Dockerfile.prod`

Build command:
```bash
docker build \
  --build-arg VITE_API_URL=https://api.yourdomain.com/api/v1 \
  -f frontend/Dockerfile.prod \
  -t artha-frontend:latest \
  frontend/
```

### Database Image

Use official MongoDB image:
```bash
docker pull mongo:7
docker tag mongo:7 <registry>/mongo:7
docker push <registry>/mongo:7
```

### Redis Image

Use official Redis image:
```bash
docker pull redis:7-alpine
docker tag redis:7-alpine <registry>/redis:7-alpine
docker push <registry>/redis:7-alpine
```

---

## Environment Configuration

### Backend Environment Variables

Create file: `backend/.env.production`

```env
# Server
NODE_ENV=production
PORT=5000
API_VERSION=v1

# Database (use service name from Pravah orchestration)
MONGODB_URI=mongodb://mongo_user:mongo_pass@mongodb-service:27017/artha_prod?authSource=admin

# JWT Secrets (from Pravah Secrets)
JWT_SECRET=${JWT_SECRET}
JWT_EXPIRE=24h
JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET}

# HMAC Secret (from Pravah Secrets)
HMAC_SECRET=${HMAC_SECRET}

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=100

# Redis (use service name)
REDIS_HOST=redis-service
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# Frontend URL
FRONTEND_URL=https://yourdomain.com

# Admin Seed (change after initial setup)
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_PASSWORD=${ADMIN_PASSWORD}

# Logging
LOG_LEVEL=info
```

### Frontend Environment Variables

Create file: `frontend/.env.production`

```env
VITE_API_URL=https://api.yourdomain.com/api/v1
VITE_ENV=production
```

### Storage Configuration

**Local Storage** (default):
```env
STORAGE_TYPE=local
UPLOADS_DIR=/app/uploads
```

**AWS S3** (optional):
```env
STORAGE_TYPE=s3
AWS_BUCKET_NAME=artha-uploads
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
```

---

## Deployment Pipeline

### Stage 1: Build

```bash
# Backend
docker build -f backend/Dockerfile.prod \
  --build-arg NODE_ENV=production \
  -t artha-backend:${VERSION} backend/

# Frontend
docker build -f frontend/Dockerfile.prod \
  --build-arg VITE_API_URL=${API_URL} \
  -t artha-frontend:${VERSION} frontend/

# Push to registry
docker push artha-backend:${VERSION}
docker push artha-frontend:${VERSION}
```

### Stage 2: Test

```bash
# Run test suite in container
docker run --rm \
  -e NODE_ENV=test \
  -e MONGODB_TEST_URI=mongodb://localhost:27017/test \
  artha-backend:${VERSION} \
  npm test

# Lint checks
docker run --rm artha-backend:${VERSION} npm run lint
docker run --rm artha-frontend:${VERSION} npm run lint
```

### Stage 3: Deploy

**Via Pravah YAML**

Create `pravah-deployment.yaml`:

```yaml
apiVersion: artha/v1
kind: Deployment
metadata:
  name: artha-prod
spec:
  replicas: 3
  
  services:
    - name: mongodb
      image: mongo:7
      ports:
        - 27017
      environment:
        MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USER}
        MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
      volumes:
        - /data/db
      healthCheck:
        command: mongosh --eval "db.adminCommand('ping')"
        interval: 30s
        timeout: 10s
    
    - name: redis
      image: redis:7-alpine
      ports:
        - 6379
      command: redis-server --requirepass ${REDIS_PASSWORD}
      volumes:
        - /data
      
    - name: backend
      image: artha-backend:${VERSION}
      replicas: 2
      ports:
        - 5000
      environment:
        NODE_ENV: production
        MONGODB_URI: mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@mongodb:27017/artha_prod?authSource=admin
        JWT_SECRET: ${JWT_SECRET}
        REDIS_HOST: redis
        REDIS_PASSWORD: ${REDIS_PASSWORD}
      healthCheck:
        path: /health
        port: 5000
        interval: 30s
        timeout: 10s
      resources:
        limits:
          cpu: 2
          memory: 2Gi
      
    - name: frontend
      image: artha-frontend:${VERSION}
      replicas: 2
      ports:
        - 80
        - 443
      environment:
        VITE_API_URL: https://api.yourdomain.com/api/v1
      healthCheck:
        path: /health
        port: 80
        interval: 30s
      resources:
        limits:
          cpu: 1
          memory: 512Mi
```

Deploy via Pravah:
```bash
pravah deploy -f pravah-deployment.yaml \
  --set VERSION=1.0.0 \
  --set MONGO_ROOT_PASSWORD=<secret> \
  --secrets-from vault
```

### Stage 4: Verify

```bash
# Check service health
curl https://api.yourdomain.com/health/detailed

# Check replica readiness
curl https://api.yourdomain.com/ready

# Check pod status
pravah status artha-prod

# View logs
pravah logs -f artha-prod/backend
```

---

## Health Checks & Monitoring

### Liveness Probe

**Endpoint**: `GET /live`

Returns 200 if the process is alive.

```yaml
livenessProbe:
  httpGet:
    path: /live
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
```

### Readiness Probe

**Endpoint**: `GET /ready`

Returns 200 if the service is ready to accept traffic.

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 5
```

### Detailed Health

**Endpoint**: `GET /health/detailed`

Returns detailed service status (databases, caches, etc.).

Response Example:
```json
{
  "success": true,
  "timestamp": "2025-02-05T...",
  "services": {
    "mongodb": { "status": "healthy" },
    "redis": { "status": "healthy" }
  },
  "memory": { "heapUsed": "..." }
}
```

### Monitoring Hooks

Point Pravah monitoring to:
- **Metrics**: `GET /health/detailed` (for health)
- **Logs**: `/var/log/artha/app.log`
- **Alerts**: Alert on `GET /health` returning non-200

---

## Migrations & Seed Data

### Running Migrations

```bash
# Create database indexes (run once after first deploy)
docker exec artha-backend npm run create-indexes

# Or via Pravah init script:
pravah exec artha-prod/backend -- npm run create-indexes
```

### Seeding Data

```bash
# Seed initial data
docker exec artha-backend npm run seed

# Or via Pravah:
pravah exec artha-prod/backend -- npm run seed
```

---

## Scaling & High Availability

### Horizontal Scaling

Update replicas in `pravah-deployment.yaml`:

```yaml
services:
  - name: backend
    replicas: 5  # Scale from 2 to 5 instances
```

Apply changes:
```bash
pravah apply -f pravah-deployment.yaml
```

### Load Balancing

Pravah automatically load-balances across replicas using:
- **Algorithm**: Round-robin
- **Session Affinity**: Sticky sessions for frontend connections

### Database Replication

MongoDB replica set is configured via `docker-compose.prod.yml`. Ensure:
- Primary always has 1 copy
- Secondaries for failover
- Arbiter for quorum (optional)

---

## Backup Strategy

### Automated Backups

Schedule via Pravah CronJob:

```yaml
apiVersion: artha/v1
kind: CronJob
metadata:
  name: artha-backup-daily
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  job:
    image: artha-backend:${VERSION}
    command:
      - ./scripts/backup.sh
    volumes:
      - /backups
```

### Manual Backup

```bash
docker exec artha-mongo-prod mongodump \
  --authenticationDatabase admin \
  -u $MONGO_ROOT_USER \
  -p $MONGO_ROOT_PASSWORD \
  --out /backups/dump_$(date +%Y%m%d_%H%M%S)
```

### Restore from Backup

```bash
docker exec artha-mongo-prod mongorestore \
  --authenticationDatabase admin \
  -u $MONGO_ROOT_USER \
  -p $MONGO_ROOT_PASSWORD \
  /backups/dump_YYYYMMDD_HHMMSS
```

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
pravah logs artha-prod/backend

# Common issues:
# - MongoDB not ready: Wait 30s, retry
# - JWT_SECRET not set: Check Pravah Secrets
# - Port 5000 in use: Kill existing process
```

### MongoDB connection failing

```bash
# Check MongoDB status
pravah logs artha-prod/mongodb

# Verify replica set
docker exec artha-mongo-prod mongosh --eval "rs.status()"

# Reinitialize if needed
docker exec artha-mongo-prod mongosh --eval "rs.initiate()"
```

### Frontend not loading

```bash
# Check Nginx logs
pravah logs artha-prod/frontend

# Verify API connectivity
curl -v https://yourdomain.com/api/v1/health

# Check environment variables
pravah describe service artha-prod/frontend
```

### High memory usage

```bash
# Check memory in detail health
curl https://api.yourdomain.com/health/detailed

# Increase limits in Pravah manifest
# Or restart pod to clear memory
pravah restart artha-prod/backend
```

---

## Performance Tuning

### MongoDB Indexing

Ensure all indexes are created:
```bash
docker exec artha-backend npm run create-indexes
```

### Redis Caching

Redis is automatically used for:
- Session storage
- Response caching (TTL: 1 hour)
- Rate limiting

Monitor via:
```bash
redis-cli -p 6379 -a $REDIS_PASSWORD INFO
```

### Node.js Memory

Configure via environment:
```env
NODE_OPTIONS=--max-old-space-size=1024  # 1GB
```

---

## Security Checklist

- [ ] All secrets in Pravah Secrets Manager (not in code)
- [ ] HTTPS enabled on frontend (SSL certificates configured)
- [ ] JWT secrets rotated every 90 days
- [ ] Rate limiting enabled (100 requests / 15 min)
- [ ] CORS configured for frontend domain only
- [ ] Backup encryption enabled
- [ ] Log rotation configured
- [ ] Firewalls restrict port access (only 80/443 public)

---

## Support & Debugging

For issues, collect:
1. **Error logs**: `pravah logs -f artha-prod`
2. **Service status**: `pravah status artha-prod`
3. **Health checks**: `curl https://api.yourdomain.com/health/detailed`
4. **Environment**: `pravah describe deployment artha-prod`

**Contact**: support@artha.bhiv.in
