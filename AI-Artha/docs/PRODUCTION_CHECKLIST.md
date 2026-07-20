# Production Deployment Checklist

## Pre-Deployment

### Security
- [ ] Generate strong JWT secrets (minimum 256 bits)
- [ ] Set secure MongoDB root credentials
- [ ] Configure Redis password
- [ ] Set HMAC secret for ledger integrity
- [ ] Review and configure CORS origins
- [ ] Set up SSL certificates (if using HTTPS)
- [ ] Configure firewall rules
- [ ] Review security headers in nginx.conf

### Environment Configuration
- [ ] Copy `.env.prod.example` to `.env`
- [ ] Configure all required environment variables
- [ ] Set appropriate log levels
- [ ] Configure backup settings (S3 bucket, retention)
- [ ] Set monitoring endpoints (Sentry, etc.)

### Infrastructure
- [ ] Ensure Docker and Docker Compose are installed
- [ ] Verify sufficient disk space (minimum 10GB)
- [ ] Ensure adequate RAM (minimum 4GB)
- [ ] Configure backup storage location
- [ ] Set up monitoring tools

## Deployment

### Initial Setup
- [ ] Run deployment script: `./scripts/deploy-prod.sh`
- [ ] Verify all containers are healthy
- [ ] Initialize MongoDB replica set
- [ ] Test Redis connectivity
- [ ] Seed database (if needed): `--seed` flag

### Verification
- [ ] Check health endpoints:
  - [ ] Backend: `http://localhost:5000/health`
  - [ ] Frontend: `http://localhost/health`
- [ ] Verify API endpoints are accessible
- [ ] Test user authentication
- [ ] Verify file uploads work
- [ ] Check ledger integrity
- [ ] Test backup script

## Post-Deployment

### Monitoring Setup
- [ ] Configure log rotation
- [ ] Set up backup cron job
- [ ] Monitor resource usage
- [ ] Set up alerting for critical errors
- [ ] Configure uptime monitoring

### Security Hardening
- [ ] Change default passwords
- [ ] Disable unnecessary services
- [ ] Configure fail2ban (if applicable)
- [ ] Set up regular security updates
- [ ] Review access logs

### Performance Optimization
- [ ] Monitor response times
- [ ] Check Redis cache hit rates
- [ ] Optimize database queries if needed
- [ ] Configure CDN (if applicable)
- [ ] Set up load balancing (if needed)

## Maintenance

### Regular Tasks
- [ ] Monitor disk space usage
- [ ] Review application logs
- [ ] Check backup integrity
- [ ] Update dependencies
- [ ] Monitor security advisories

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Check error rates
- [ ] Verify backup restoration
- [ ] Update SSL certificates (if needed)

### Monthly Tasks
- [ ] Security audit
- [ ] Performance review
- [ ] Capacity planning
- [ ] Disaster recovery testing

## Troubleshooting

### Common Issues
1. **Container won't start**
   - Check logs: `docker-compose -f docker-compose.prod.yml logs [service]`
   - Verify environment variables
   - Check disk space

2. **Database connection issues**
   - Verify MongoDB container is healthy
   - Check replica set status
   - Review connection string

3. **Redis connection issues**
   - Check Redis container status
   - Verify password configuration
   - Review Redis logs

4. **Performance issues**
   - Monitor resource usage
   - Check cache hit rates
   - Review slow query logs

### Emergency Procedures
1. **Service outage**
   - Check container status
   - Review recent logs
   - Restart affected services
   - Escalate if needed

2. **Data corruption**
   - Stop write operations
   - Restore from backup
   - Verify data integrity
   - Resume operations

3. **Security incident**
   - Isolate affected systems
   - Review access logs
   - Change credentials
   - Apply security patches

## Rollback Plan

### Quick Rollback
```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Restore from backup
./scripts/restore-backup.sh [backup_date]

# Start previous version
docker-compose -f docker-compose.prod.yml up -d
```

### Data Recovery
```bash
# Restore MongoDB
docker exec artha-mongo-prod mongorestore /backup/path

# Restore uploaded files
tar -xzf uploads_backup_[date].tar.gz -C /app/
```

## Support Contacts

- **System Administrator**: [contact info]
- **Database Administrator**: [contact info]
- **Security Team**: [contact info]
- **Development Team**: [contact info]

## Documentation Links

- [API Documentation](./API.md)
- [Database Schema](./DATABASE.md)
- [Security Guidelines](./SECURITY.md)
- [Monitoring Guide](./MONITORING.md)