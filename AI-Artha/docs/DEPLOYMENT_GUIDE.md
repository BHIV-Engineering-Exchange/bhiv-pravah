# Deployment Guide

## Overview

This guide covers deploying ARTHA as a production BHIV ecosystem participant.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- MongoDB 7+ (or Docker)
- Redis 7+ (optional, for caching)
- Node.js 18+ (for local development)

## Production Deployment

### 1. Environment Configuration

Create `.env` file:

```bash
# Required
MONGODB_URI=mongodb://mongodb:27017/artha
JWT_SECRET=<your-jwt-secret>
HMAC_SECRET=<your-hmac-secret>

# Optional
REDIS_URL=redis://redis:6379
NODE_ENV=production
PORT=5000
APP_ID=ARTHA
BHIV_APP_ID=ARTHA

# Frontend
SPA_URL=https://your-frontend-domain.com
API_PUBLIC_URL=https://your-api-domain.com

# CORS
CORS_ORIGIN=https://your-frontend-domain.com
ALLOW_LOCALHOST_CORS=false

# SETU (optional)
SETU_ENABLED=false
SETU_BASE_URL=
SETU_API_KEY=
```

### 2. Docker Compose Production

```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Verify health
curl http://localhost:5000/health

# Check governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer <token>"
```

### 3. Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s-deployment.example.yml

# Verify pods
kubectl get pods -l app=artha

# Check logs
kubectl logs -l app=artha -f
```

## Fresh Installation

### 1. Start MongoDB

```bash
# Using Docker
docker run -d --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7
```

### 2. Initialize Application

```bash
cd backend

# Install dependencies
npm install

# Seed database
node scripts/seed.js
node scripts/seed-tds.js

# Verify integrity
node scripts/verify-integrity.js
```

### 3. Verify Governance

```bash
# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@artha.com","password":"password"}'

# Check governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer <token>"

# Run verification suite
curl http://localhost:5000/api/v1/governance/verification/run \
  -H "Authorization: Bearer <token>"

# Run adversarial suite
curl http://localhost:5000/api/v1/governance/adversarial/run \
  -H "Authorization: Bearer <token>"
```

## Health Verification

### Health Endpoints

```bash
# Basic health
curl http://localhost:5000/health

# Detailed health
curl http://localhost:5000/health/detailed

# Readiness probe
curl http://localhost:5000/ready

# Liveness probe
curl http://localhost:5000/live
```

### Governance Health

```bash
# Governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer <token>"

# Capability verification
curl http://localhost:5000/api/v1/governance/capabilities/verify \
  -H "Authorization: Bearer <token>"

# Circuit breaker status
curl http://localhost:5000/api/v1/governance/circuit-breakers \
  -H "Authorization: Bearer <token>"
```

## Runtime Startup Evidence

When the server starts, it automatically captures:

1. **Deployment Evidence:**
   - Server started
   - Capabilities loaded
   - Routes registered
   - Provenance chain initialized

2. **Provenance Record:**
   - Deployment event recorded
   - Genesis block created

3. **Capability Registry:**
   - All contracts loaded
   - Route mappings validated
   - Contract hashes computed

## Rollback Procedure

### Docker Rollback

```bash
# Stop current version
docker-compose -f docker-compose.prod.yml down

# Start previous version
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl http://localhost:5000/health
```

### Database Rollback

```bash
# Restore from backup
mongorestore --uri="mongodb://localhost:27017/artha" --archive=<backup-file>

# Restart application
docker-compose -f docker-compose.prod.yml restart
```

## Monitoring

### Prometheus Metrics

```bash
# Get Prometheus metrics
curl http://localhost:5000/metrics
```

### Observability Dashboard

```bash
# Get observability data
curl http://localhost:5000/observability
```

### Runtime Status

```bash
# Get full runtime status
curl http://localhost:5000/api/v1/runtime/status \
  -H "Authorization: Bearer <token>"
```

## Incident Recovery

### Circuit Breaker Reset

```bash
# Reset specific circuit breaker
curl -X POST http://localhost:5000/api/v1/governance/circuit-breakers/mongodb/reset \
  -H "Authorization: Bearer <token>"

# Reset all circuit breakers
curl -X POST http://localhost:5000/api/v1/governance/circuit-breakers/reset-all \
  -H "Authorization: Bearer <token>"
```

### Provenance Chain Recovery

If provenance chain is corrupted:

1. Check chain integrity: `GET /api/v1/governance/provenance/verify`
2. If invalid, restart application (chain reinitializes from genesis)
3. Record recovery event in provenance chain

### Contract Recovery

If contracts are tampered:

1. Check contract integrity: `GET /api/v1/governance/capabilities/verify`
2. Restore original contract files
3. Restart application to reload contracts
4. Verify integrity again

## Security Checklist

- [ ] Environment variables secured
- [ ] JWT_SECRET and HMAC_SECRET are strong and unique
- [ ] CORS configured for production domains only
- [ ] Rate limiting enabled
- [ ] Input sanitization enabled
- [ ] Authority enforcement enabled
- [ ] Policy engine enabled
- [ ] Circuit breakers registered
- [ ] Health checks configured
- [ ] Monitoring enabled
- [ ] Backup strategy in place
- [ ] Incident response plan documented
