# Cloud Deployment Checklist

## Pre-Deployment

### Environment Configuration
- [ ] Copy `.env.production` to deployment server
- [ ] Generate strong JWT_SECRET (min 32 characters)
- [ ] Generate strong ENGINE_SECRET_KEY (min 32 characters)
- [ ] Update ALLOWED_ORIGINS with production domains
- [ ] Configure MONGODB_URI for production database
- [ ] Set NODE_ENV=production

### Security
- [ ] Rotate all default secrets and keys
- [ ] Enable HTTPS/TLS certificates
- [ ] Configure firewall rules (allow 3000, 5173)
- [ ] Set up rate limiting
- [ ] Enable CORS with specific origins only
- [ ] Disable dev-bypass authentication
- [ ] Review and remove debug logs

### Database
- [ ] MongoDB instance running and accessible
- [ ] Database user with proper permissions created
- [ ] Connection pooling configured
- [ ] Indexes created for telemetry collections
- [ ] Backup strategy in place

### Dependencies
- [ ] Run `npm ci` (not `npm install`) for reproducible builds
- [ ] Verify all dependencies are production-ready
- [ ] Remove devDependencies from production build
- [ ] Check for security vulnerabilities: `npm audit`

---

## Deployment Steps

### Backend Deployment

1. **Install Dependencies**
   ```bash
   cd backend
   npm ci --production
   ```

2. **Environment Setup**
   ```bash
   cp .env.production .env
   # Edit .env with production values
   ```

3. **Start Backend**
   ```bash
   # Using PM2 (recommended)
   pm2 start index.js --name sovereign-backend --env production
   
   # Or using systemd
   sudo systemctl start sovereign-backend
   ```

4. **Verify Backend**
   ```bash
   curl http://localhost:3000/health
   ```

### Frontend Deployment

1. **Build Production Bundle**
   ```bash
   cd frontend
   npm ci
   npm run build
   ```

2. **Configure Environment**
   ```bash
   # Create .env.production
   VITE_BACKEND_URL=https://api.yourdomain.com
   ```

3. **Deploy Static Files**
   ```bash
   # Copy dist/ to web server
   cp -r dist/* /var/www/html/
   
   # Or use nginx/apache to serve
   ```

4. **Verify Frontend**
   - Open https://yourdomain.com
   - Check browser console for errors
   - Verify Socket.IO connection

---

## Post-Deployment

### Health Checks
- [ ] Backend responds to health endpoint
- [ ] Frontend loads without errors
- [ ] Socket.IO connection established
- [ ] JWT authentication working
- [ ] Engine can connect to /engine namespace
- [ ] Jobs can be dispatched and processed
- [ ] Telemetry data flowing correctly

### Monitoring Setup
- [ ] Configure logging (Winston/Bunyan)
- [ ] Set up error tracking (Sentry/Rollbar)
- [ ] Enable performance monitoring
- [ ] Configure alerts for:
  - Server downtime
  - High error rates
  - Memory/CPU usage
  - Database connection failures
  - Socket.IO disconnections

### Load Testing
- [ ] Test with 10 concurrent users
- [ ] Test with 100 concurrent jobs
- [ ] Verify reconnection logic under load
- [ ] Check memory leaks (run for 24h)
- [ ] Test JWT rotation during active sessions

---

## JWT Rotation Safety

### Initial Setup
```javascript
// backend/index.js
const { jwtRotation } = require('./auth/jwt_rotation');

// Rotate secret every 30 days
setInterval(() => {
  const newSecret = generateSecureSecret();
  jwtRotation.rotateSecret(newSecret);
}, 30 * 24 * 60 * 60 * 1000);
```

### Rotation Checklist
- [ ] JWT rotation manager initialized
- [ ] Grace period set to 24 hours
- [ ] Rotation logs enabled
- [ ] Token refresh endpoint working
- [ ] Frontend handles token refresh
- [ ] Old tokens work during grace period

### Testing JWT Rotation
```bash
# Test token verification with old secret
node test_jwt_rotation.js

# Verify grace period works
# Verify new tokens use new secret
```

---

## Socket Reconnection Logic

### Frontend Configuration
- [ ] Socket manager initialized
- [ ] Exponential backoff configured
- [ ] Max reconnection attempts: 10
- [ ] Max delay: 30 seconds
- [ ] Connection state listeners added

### Backend Configuration
- [ ] Socket.IO ping timeout: 60s
- [ ] Socket.IO ping interval: 25s
- [ ] Disconnect handlers implemented
- [ ] Job queue persists during disconnect
- [ ] Engine status broadcasts on disconnect

### Testing Reconnection
- [ ] Kill backend - verify frontend reconnects
- [ ] Network disconnect - verify recovery
- [ ] Engine crash - verify job queue safe
- [ ] Multiple rapid disconnects handled
- [ ] Connection state UI updates correctly

---

## Environment Separation

### Development
- File: `.env` or `.env.development`
- JWT expiry: 24h
- Logging: debug
- CORS: localhost
- Auth: dev-bypass enabled

### Staging
- File: `.env.staging`
- JWT expiry: 2h
- Logging: debug
- CORS: staging domain
- Auth: full JWT validation

### Production
- File: `.env.production`
- JWT expiry: 1h
- Logging: info/error only
- CORS: production domains only
- Auth: full JWT + rate limiting

---

## Cloud Provider Specific

### AWS
- [ ] EC2 instance configured (t3.medium minimum)
- [ ] Security groups allow ports 3000, 5173
- [ ] Elastic IP assigned
- [ ] Route53 DNS configured
- [ ] CloudWatch logs enabled
- [ ] Auto-scaling group (optional)
- [ ] Load balancer (if multi-instance)

### Google Cloud
- [ ] Compute Engine VM created
- [ ] Firewall rules configured
- [ ] Cloud DNS configured
- [ ] Cloud Logging enabled
- [ ] Load balancer configured

### Azure
- [ ] Virtual Machine created
- [ ] Network Security Group configured
- [ ] Azure DNS configured
- [ ] Application Insights enabled
- [ ] Load balancer configured

### DigitalOcean
- [ ] Droplet created (2GB RAM minimum)
- [ ] Firewall configured
- [ ] Domain configured
- [ ] Monitoring enabled

---

## SSL/TLS Configuration

### Using Let's Encrypt
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Configure nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
}
```

### Checklist
- [ ] SSL certificate installed
- [ ] HTTPS redirect configured
- [ ] Certificate auto-renewal enabled
- [ ] Socket.IO works over WSS
- [ ] Mixed content warnings resolved

---

## Process Management

### Using PM2
```bash
# Install PM2
npm install -g pm2

# Start backend
pm2 start backend/index.js --name sovereign-backend

# Start on boot
pm2 startup
pm2 save

# Monitor
pm2 monit

# Logs
pm2 logs sovereign-backend
```

### Checklist
- [ ] PM2 installed and configured
- [ ] Auto-restart on crash enabled
- [ ] Log rotation configured
- [ ] Startup script created
- [ ] Memory limits set

---

## Backup & Recovery

### Database Backups
```bash
# MongoDB backup
mongodump --uri="mongodb://localhost:27017/sovereign-prod" --out=/backups/

# Automated daily backups
0 2 * * * /usr/bin/mongodump --uri="..." --out=/backups/$(date +\%Y\%m\%d)
```

### Checklist
- [ ] Daily database backups scheduled
- [ ] Backup retention policy (30 days)
- [ ] Backup restoration tested
- [ ] Configuration files backed up
- [ ] Recovery procedure documented

---

## Performance Optimization

### Backend
- [ ] Enable gzip compression
- [ ] Configure connection pooling
- [ ] Enable caching (Redis optional)
- [ ] Optimize database queries
- [ ] Remove unnecessary middleware

### Frontend
- [ ] Minify and bundle assets
- [ ] Enable CDN for static files
- [ ] Lazy load components
- [ ] Optimize images
- [ ] Enable service worker (PWA)

---

## Security Hardening

### Server
- [ ] Disable root SSH login
- [ ] Configure fail2ban
- [ ] Enable automatic security updates
- [ ] Install and configure firewall (ufw/iptables)
- [ ] Remove unnecessary services

### Application
- [ ] Helmet.js configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection enabled
- [ ] CSRF tokens implemented

---

## Rollback Plan

### If Deployment Fails
1. Stop new services
   ```bash
   pm2 stop sovereign-backend
   ```

2. Restore previous version
   ```bash
   git checkout <previous-tag>
   npm ci
   pm2 restart sovereign-backend
   ```

3. Restore database if needed
   ```bash
   mongorestore --uri="..." /backups/latest/
   ```

4. Verify rollback successful
   - Check health endpoint
   - Test critical features
   - Monitor error logs

---

## Final Verification

### Smoke Tests
- [ ] User can login
- [ ] Dashboard loads correctly
- [ ] Jobs can be created
- [ ] Engine can connect
- [ ] Telemetry data displays
- [ ] Real-time updates work
- [ ] Error handling works

### Load Tests
- [ ] 100 concurrent users
- [ ] 1000 jobs in queue
- [ ] 24-hour stability test
- [ ] Memory usage stable
- [ ] No connection leaks

### Security Tests
- [ ] JWT validation working
- [ ] HMAC signatures verified
- [ ] Nonce replay prevention
- [ ] Rate limiting active
- [ ] CORS properly configured

---

## Documentation

- [ ] API documentation updated
- [ ] Deployment guide written
- [ ] Troubleshooting guide created
- [ ] Architecture diagrams updated
- [ ] Runbook for on-call team

---

## Sign-Off

- [ ] Development team approval
- [ ] QA team approval
- [ ] Security team approval
- [ ] Operations team notified
- [ ] Stakeholders informed

---

## Post-Launch Monitoring (First 24h)

- [ ] Monitor error rates every hour
- [ ] Check server resources (CPU, RAM, disk)
- [ ] Verify backup jobs running
- [ ] Review security logs
- [ ] Check user feedback
- [ ] Monitor Socket.IO connection stability

---

## Emergency Contacts

- DevOps Lead: [contact]
- Backend Lead: [contact]
- Frontend Lead: [contact]
- Database Admin: [contact]
- Security Team: [contact]

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Version**: _______________
**Status**: ⬜ Success ⬜ Partial ⬜ Rollback
