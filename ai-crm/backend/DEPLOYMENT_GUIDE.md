# AI Agent Logistics - Deployment Guide

## Quick Start with Docker

### 1. Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 80, 443, 8000, 8501 available

### 2. Environment Setup
```bash
# Copy environment file
cp .env.production .env

# Edit configuration
nano .env
```

### 3. Deploy with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Access Applications
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- Monitoring: http://localhost:3000 (Grafana)
- Metrics: http://localhost:9090 (Prometheus)

## Production Deployment

### 1. SSL/TLS Setup
```bash
# Generate SSL certificates (Let's Encrypt)
certbot certonly --standalone -d yourdomain.com

# Update nginx.conf with SSL configuration
```

### 2. Database Setup
```bash
# PostgreSQL (recommended for production)
docker run -d \
  --name logistics-db \
  -e POSTGRES_DB=logistics \
  -e POSTGRES_USER=logistics_user \
  -e POSTGRES_PASSWORD=secure_password \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15
```

### 3. Monitoring Setup
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d
```

### 4. Backup Strategy
```bash
# Database backup
docker exec logistics-db pg_dump -U logistics_user logistics > backup.sql

# Application data backup
docker run --rm -v logistics_data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz /data
```

## Security Checklist
- [ ] Change default passwords
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Set up monitoring alerts
- [ ] Regular security updates

## Troubleshooting
Common issues and solutions:

### Container won't start
```bash
# Check logs
docker-compose logs service-name

# Check resource usage
docker stats
```

### Database connection issues
```bash
# Test database connection
docker exec -it logistics-api python -c "from database.service import DatabaseService; print('DB OK')"
```

### Performance issues
```bash
# Monitor resource usage
docker exec -it logistics-api python performance_monitor.py
```
