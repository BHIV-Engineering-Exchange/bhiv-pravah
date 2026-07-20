# Production Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- MongoDB Atlas account (or local MongoDB replica set)
- Domain name with SSL certificate (for production)
- Minimum 2GB RAM, 2 CPU cores

## Quick Production Deployment

### 1. Environment Setup

```bash
# Generate secure production configuration
cd backend && npm run generate:config

# Or manually copy and edit
cp .env.prod.example .env.production
cp backend/.env.production.example backend/.env.production
```

### 2. Deploy with Script

```bash
# Linux/Mac
chmod +x scripts/deploy.sh
./scripts/deploy.sh --seed

# Windows
scripts\deploy-prod.bat --seed
```

### 3. Verify Deployment

```bash
# Check all services
curl http://localhost:5000/health/detailed

# Check individual components
curl http://localhost:5000/ready    # Backend readiness
curl http://localhost/health        # Frontend health
curl http://localhost:5000/metrics  # Performance metrics
```

## Manual Deployment Steps

### 1. Environment Variables

Required variables in `.env.production`:
```bash
MONGO_ROOT_USER=your_mongo_user
MONGO_ROOT_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
```

Required variables in `backend/.env.production`:
```bash
NODE_ENV=production
PORT=5000
MONGODB_URI=mongodb://username:password@mongo:27017/artha_prod?authSource=admin&replicaSet=rs0
JWT_SECRET=your_jwt_secret_min_32_chars
REDIS_URL=redis://:password@redis:6379
```

### 2. Build and Start Services

```bash
# Build images
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Initialize MongoDB replica set
docker exec artha-mongo-prod mongosh --eval "rs.initiate()"

# Create database indexes
docker exec artha-backend-prod npm run create-indexes

# Seed database (optional)
docker exec artha-backend-prod npm run seed
```

## Production Architecture

### Services

- **MongoDB**: Replica set with authentication
- **Redis**: Caching layer with password protection
- **Backend**: Node.js API with performance monitoring
- **Frontend**: Nginx with compression and security headers
- **Nginx**: Reverse proxy with SSL termination

### Health Monitoring

| Endpoint | Purpose | Access |
|----------|---------|--------|
| `/health` | Basic API health | Public |
| `/health/detailed` | Comprehensive system status | Admin |
| `/ready` | Kubernetes readiness probe | Public |
| `/live` | Kubernetes liveness probe | Public |
| `/metrics` | Performance metrics | Public |
| `/status` | System component status | Admin |

### Performance Features

- **Redis Caching**: Automatic caching for GET requests
- **Database Indexing**: Optimized queries with compound indexes
- **Request Monitoring**: Response time and memory tracking
- **Compression**: Gzip compression for all responses
- **Connection Pooling**: Efficient database connections

## Backup and Restore

### Create Backup

```bash
# Automated backup
./scripts/backup.sh

# Manual backup
docker exec artha-mongo-prod mongodump \
  --authenticationDatabase=admin \
  -u $MONGO_ROOT_USER \
  -p $MONGO_ROOT_PASSWORD \
  --db=artha_prod \
  --gzip \
  --archive=/tmp/backup.gz
```

### Restore Database

```bash
# Restore from backup
./scripts/restore.sh backups/artha_backup_20250125_120000.gz
```

## Monitoring and Maintenance

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker logs artha-backend-prod -f
docker logs artha-frontend-prod -f
docker logs artha-mongo-prod -f
docker logs artha-redis-prod -f
```

### Performance Monitoring

```bash
# System health
curl http://localhost:5000/health/detailed

# Performance metrics
curl http://localhost:5000/metrics

# Database statistics
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:5000/api/v1/database/stats
```

### Scaling

```bash
# Scale backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Update resource limits in docker-compose.prod.yml
```

## Security Considerations

### Environment Security

- Use strong passwords (minimum 32 characters)
- Enable MongoDB authentication
- Use Redis password protection
- Set secure JWT secrets
- Configure CORS origins properly

### Network Security

- Use SSL/TLS certificates
- Configure firewall rules
- Limit database access to application only
- Use Docker networks for service isolation

### Application Security

- Regular security updates
- Input validation and sanitization
- Rate limiting on API endpoints
- Audit logging for sensitive operations

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   ```bash
   # Check replica set status
   docker exec artha-mongo-prod mongosh --eval "rs.status()"
   
   # Reinitialize if needed
   docker exec artha-mongo-prod mongosh --eval "rs.initiate()"
   ```

2. **Redis Connection Failed**
   ```bash
   # Check Redis status
   docker exec artha-redis-prod redis-cli ping
   
   # Check password authentication
   docker exec artha-redis-prod redis-cli -a $REDIS_PASSWORD ping
   ```

3. **Backend Not Starting**
   ```bash
   # Check environment variables
   docker exec artha-backend-prod env | grep -E "(MONGODB_URI|REDIS_URL)"
   
   # Check application logs
   docker logs artha-backend-prod --tail 100
   ```

4. **Frontend Not Loading**
   ```bash
   # Check Nginx configuration
   docker exec artha-frontend-prod nginx -t
   
   # Check frontend logs
   docker logs artha-frontend-prod --tail 50
   ```

### Performance Issues

1. **Slow Database Queries**
   ```bash
   # Check database indexes
   curl -H "Authorization: Bearer $JWT_TOKEN" \
     http://localhost:5000/api/v1/database/indexes
   
   # Get optimization suggestions
   curl -H "Authorization: Bearer $JWT_TOKEN" \
     http://localhost:5000/api/v1/database/optimize
   ```

2. **High Memory Usage**
   ```bash
   # Check performance metrics
   curl http://localhost:5000/api/v1/performance/metrics
   
   # Reset metrics if needed
   curl -X POST -H "Authorization: Bearer $JWT_TOKEN" \
     http://localhost:5000/api/v1/performance/reset
   ```

## Kubernetes Deployment

### Example Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: artha-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: artha-backend
  template:
    metadata:
      labels:
        app: artha-backend
    spec:
      containers:
      - name: backend
        image: artha-backend:latest
        ports:
        - containerPort: 5000
        env:
        - name: NODE_ENV
          value: "production"
        livenessProbe:
          httpGet:
            path: /live
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
        startupProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 10
          failureThreshold: 30
```

## Maintenance Schedule

### Daily
- Monitor system health endpoints
- Check application logs for errors
- Verify backup completion

### Weekly
- Review performance metrics
- Update security patches
- Clean up old log files

### Monthly
- Database maintenance and optimization
- Security audit and updates
- Capacity planning review

---

## Pravah Deployment (NEW)

For detailed Pravah-specific deployment instructions, see [PRAVAH_DEPLOYMENT.md](./PRAVAH_DEPLOYMENT.md).

### Quick Start

```bash
# Build images
docker build -f backend/Dockerfile.prod -t artha-backend:1.0.0 backend/
docker build -f frontend/Dockerfile.prod -t artha-frontend:1.0.0 frontend/

# Deploy via Pravah
pravah deploy -f pravah-deployment.yaml --secrets-from vault

# Verify
curl https://api.yourdomain.com/health/detailed
```

### Key Features

- **Automated Orchestration**: Pravah manages all container lifecycle
- **Health Monitoring**: Built-in liveness and readiness probes
- **Scaling**: Horizontal scaling with load balancing
- **Secrets Management**: Secure secret injection from vault
- **Backup Automation**: Scheduled backups via CronJobs

### Pravah-Specific Endpoints

All existing health endpoints work seamlessly with Pravah:
- `/health` - Basic health check
- `/health/detailed` - Comprehensive system status
- `/ready` - Readiness probe for traffic routing
- `/live` - Liveness probe for container restart
- `/metrics` - Performance metrics for monitoring

See [PRAVAH_DEPLOYMENT.md](./PRAVAH_DEPLOYMENT.md) for complete guide including:
- Image building and registry management
- Environment configuration
- Deployment pipeline stages
- Scaling and high availability
- Backup and restore procedures
- Troubleshooting guide