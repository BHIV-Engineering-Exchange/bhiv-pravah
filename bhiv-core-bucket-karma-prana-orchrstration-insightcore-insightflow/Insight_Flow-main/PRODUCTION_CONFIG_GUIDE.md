# Production Configuration Guide

## Overview
This guide documents which configuration values must be overridden for production deployment of InsightFlow.

## 🚨 Critical Production Overrides

### Database Configuration
```bash
# ❌ Development (localhost)
SOVEREIGN_DB_HOST=localhost
SOVEREIGN_DB_USER=sovereign_user
SOVEREIGN_DB_PASSWORD=sovereign_password

# ✅ Production (must override)
SOVEREIGN_DB_HOST=your-production-db-host.com
SOVEREIGN_DB_USER=your_secure_db_user
SOVEREIGN_DB_PASSWORD=your_secure_db_password
```

### Authentication & Security
```bash
# ❌ Development (placeholder)
JWT_SECRET_KEY=your-super-secret-key-change-in-production
SOVEREIGN_SERVICE_KEY=sovereign-service-key-placeholder
SOVEREIGN_JWT_SECRET=sovereign-jwt-secret-placeholder

# ✅ Production (must override)
JWT_SECRET_KEY=your_actual_production_jwt_secret_256_bits_minimum
SOVEREIGN_SERVICE_KEY=your_actual_sovereign_service_key
SOVEREIGN_JWT_SECRET=your_actual_sovereign_jwt_secret
```

### Service Endpoints
```bash
# ❌ Development (localhost)
SOVEREIGN_AUTH_URL=http://localhost:8003/auth
KARMA_ENDPOINT=http://localhost:8002/api/karma
CORE_FEEDBACK_SERVICE_URL=http://core-feedback:8000/api/scores

# ✅ Production (must override)
SOVEREIGN_AUTH_URL=https://your-auth-service.com/auth
KARMA_ENDPOINT=https://your-karma-service.com/api/karma
CORE_FEEDBACK_SERVICE_URL=https://your-feedback-service.com/api/scores
```

### Environment Settings
```bash
# ❌ Development
ENVIRONMENT=development
DEBUG=true

# ✅ Production (must override)
ENVIRONMENT=production
DEBUG=false
```

### CORS Origins
```bash
# ❌ Development (localhost)
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# ✅ Production (must override)
CORS_ORIGINS=["https://your-frontend-domain.com","https://your-admin-panel.com"]
```

## 📋 Production Environment Template

Create a `.env.production` file with these values:

```bash
# =============================================================================
# PRODUCTION CONFIGURATION - InsightFlow
# =============================================================================

# Environment
ENVIRONMENT=production
DEBUG=false

# Security (REQUIRED - Generate secure values)
JWT_SECRET_KEY=CHANGE_ME_TO_SECURE_256_BIT_KEY
SOVEREIGN_SERVICE_KEY=CHANGE_ME_TO_SECURE_SERVICE_KEY
SOVEREIGN_JWT_SECRET=CHANGE_ME_TO_SECURE_JWT_SECRET

# Database (REQUIRED - Update with production values)
SOVEREIGN_DB_HOST=your-production-db-host
SOVEREIGN_DB_PORT=5432
SOVEREIGN_DB_NAME=insightflow_production
SOVEREIGN_DB_USER=insightflow_prod_user
SOVEREIGN_DB_PASSWORD=CHANGE_ME_TO_SECURE_PASSWORD

# Service Endpoints (REQUIRED - Update with production URLs)
SOVEREIGN_AUTH_URL=https://your-auth-service.com/auth
KARMA_ENDPOINT=https://your-karma-service.com/api/karma
CORE_FEEDBACK_SERVICE_URL=https://your-feedback-service.com/api/scores

# CORS (REQUIRED - Update with production domains)
CORS_ORIGINS=["https://your-frontend.com"]

# Application
APP_NAME=InsightFlow
APP_VERSION=1.0.0

# Features
USE_SOVEREIGN_CORE=true
STP_ENABLED=true
KARMA_ENABLED=true

# Performance Tuning (Optional - defaults are production-ready)
KARMA_CACHE_TTL=300
KARMA_TIMEOUT=10
CORE_FEEDBACK_CACHE_TTL=60
CORE_FEEDBACK_TIMEOUT=10
ROUTING_LOG_RETENTION_DAYS=90

# Q-Learning (Optional - defaults are production-ready)
LEARNING_RATE=0.05
DISCOUNT_FACTOR=0.95
EPSILON=0.05
MIN_EPSILON=0.01
EPSILON_DECAY=0.999
```

## 🔒 Security Checklist

### Before Production Deployment:

- [ ] **JWT_SECRET_KEY**: Generate 256-bit random key
- [ ] **Database Credentials**: Use strong, unique passwords
- [ ] **Service Keys**: Generate secure service authentication keys
- [ ] **HTTPS**: Ensure all service URLs use HTTPS
- [ ] **CORS**: Restrict to production domains only
- [ ] **Debug Mode**: Set DEBUG=false
- [ ] **Environment**: Set ENVIRONMENT=production

### Security Key Generation:
```bash
# Generate secure JWT secret (256-bit)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate service key
python -c "import secrets; print('svc_' + secrets.token_urlsafe(24))"
```

## 🚀 Deployment Commands

### Docker Deployment:
```bash
# Use production environment file
docker-compose --env-file .env.production up -d
```

### Kubernetes Deployment:
```bash
# Create production config map
kubectl create configmap insightflow-prod-config --from-env-file=.env.production

# Apply with production config
kubectl apply -f k8s/production/
```

### Environment Variable Validation:
```bash
# Test configuration before deployment
python -c "from app.core.config import settings; print('✅ Configuration valid')"
```

## ⚠️ Common Production Issues

### Issue 1: Database Connection Fails
**Cause**: Using localhost database host
**Solution**: Update SOVEREIGN_DB_HOST to production database

### Issue 2: CORS Errors
**Cause**: Frontend domain not in CORS_ORIGINS
**Solution**: Add production frontend domain to CORS_ORIGINS

### Issue 3: Service Authentication Fails
**Cause**: Using placeholder service keys
**Solution**: Generate and configure production service keys

### Issue 4: Invalid Environment Variables
**Cause**: Malformed numeric values in environment variables
**Solution**: Configuration now includes safe parsing with fallbacks

## 📊 Configuration Validation

The application now includes automatic validation:

- **Startup Validation**: Invalid configs prevent application start
- **Safe Parsing**: Malformed environment variables use safe defaults
- **Error Logging**: Clear error messages for configuration issues
- **Range Validation**: Numeric values validated for reasonable ranges

## 🔧 Monitoring Production Config

### Health Check Endpoint:
```bash
curl https://your-api.com/health
```

### Configuration Status:
```bash
curl https://your-api.com/api/version
```

### Validate Current Config:
```python
from app.core.config import settings
print(f"Environment: {settings.ENVIRONMENT}")
print(f"Debug Mode: {settings.DEBUG}")
print(f"Database Host: {settings.SOVEREIGN_DB_HOST}")
```

---

**Remember**: Never commit production secrets to version control. Use environment variables or secure secret management systems.