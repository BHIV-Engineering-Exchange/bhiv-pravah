# HR-AI System - Production Deployment Guide

## 🚀 Overview

This guide covers deploying the HR-AI System in a production environment with all security, performance, and reliability features enabled.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended), Windows Server 2019+, or macOS
- **Python**: 3.8 or higher
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 10GB free space
- **Network**: Stable internet connection for external integrations

### Required Services
- **Web Server**: Nginx or Apache (for reverse proxy)
- **Process Manager**: PM2, Supervisor, or systemd
- **SSL Certificate**: Let's Encrypt or commercial certificate
- **Monitoring**: Optional but recommended (Prometheus, Grafana)

## 🔧 Installation Steps

### 1. System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and required system packages
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Create application user
sudo useradd -m -s /bin/bash hrai
sudo usermod -aG sudo hrai
```

### 2. Application Setup

```bash
# Switch to application user
sudo su - hrai

# Clone the repository
git clone https://github.com/ISHANSHIRODE01/Ishan_HR_AI_System.git
cd Ishan_HR_AI_System

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn psutil schedule PyJWT cryptography
```

### 3. Configuration

```bash
# Copy production configuration
cp .env.production .env

# Edit configuration file
nano .env
```

**Important Configuration Items:**
- Set a strong `SECRET_KEY`
- Configure `ALLOWED_ORIGINS` for your domain
- Set up email SMTP settings
- Configure WhatsApp and Voice API credentials
- Set appropriate file paths and permissions

### 4. Database Setup

```bash
# Initialize the database
python start_enhanced_system.py --init-only

# Create admin user (if not created automatically)
python -c "
from app.utils.database import db_manager
from app.utils.security import SecurityManager
db_manager.create_user({
    'username': 'admin',
    'password_hash': SecurityManager.hash_password('your-secure-password'),
    'role': 'admin',
    'permissions': ['read', 'write', 'admin']
})
"
```

### 5. SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

### 6. Nginx Configuration

Create `/etc/nginx/sites-available/hrai`:

```nginx
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Dashboard (Streamlit)
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # API (FastAPI)
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    }
    
    # Rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/hrai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Process Management with Supervisor

Create `/etc/supervisor/conf.d/hrai.conf`:

```ini
[program:hrai-api]
command=/home/hrai/Ishan_HR_AI_System/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:5000
directory=/home/hrai/Ishan_HR_AI_System
user=hrai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hrai/api.log
environment=PATH="/home/hrai/Ishan_HR_AI_System/venv/bin"

[program:hrai-dashboard]
command=/home/hrai/Ishan_HR_AI_System/venv/bin/streamlit run dashboard/app.py --server.port=8501 --server.address=127.0.0.1
directory=/home/hrai/Ishan_HR_AI_System
user=hrai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hrai/dashboard.log
environment=PATH="/home/hrai/Ishan_HR_AI_System/venv/bin"

[program:hrai-monitor]
command=/home/hrai/Ishan_HR_AI_System/venv/bin/python start_enhanced_system.py --monitor-only
directory=/home/hrai/Ishan_HR_AI_System
user=hrai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hrai/monitor.log
environment=PATH="/home/hrai/Ishan_HR_AI_System/venv/bin"
```

Start services:
```bash
sudo mkdir -p /var/log/hrai
sudo chown hrai:hrai /var/log/hrai
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

## 🔒 Security Hardening

### 1. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. File Permissions

```bash
# Set proper file permissions
chmod 600 .env
chmod -R 755 app/
chmod -R 700 data/
chmod -R 700 logs/
chmod -R 700 backups/
```

### 3. Database Security

```bash
# Secure database file
chmod 600 data/hr_system.db
chown hrai:hrai data/hr_system.db
```

### 4. Regular Security Updates

```bash
# Create update script
cat > /home/hrai/update_system.sh << 'EOF'
#!/bin/bash
sudo apt update && sudo apt upgrade -y
sudo supervisorctl restart all
sudo systemctl reload nginx
EOF

chmod +x /home/hrai/update_system.sh

# Add to crontab for weekly updates
echo "0 2 * * 0 /home/hrai/update_system.sh" | crontab -
```

## 📊 Monitoring Setup

### 1. System Monitoring

The application includes built-in performance monitoring. Access metrics at:
- `https://api.yourdomain.com/system/performance`
- `https://api.yourdomain.com/system/logs`

### 2. Log Monitoring

```bash
# Set up log rotation
sudo cat > /etc/logrotate.d/hrai << 'EOF'
/var/log/hrai/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 hrai hrai
    postrotate
        supervisorctl restart all
    endscript
}
EOF
```

### 3. Health Checks

Create a health check script:

```bash
cat > /home/hrai/health_check.sh << 'EOF'
#!/bin/bash
API_URL="https://api.yourdomain.com/health"
DASHBOARD_URL="https://yourdomain.com"

# Check API health
if curl -f -s $API_URL > /dev/null; then
    echo "API: OK"
else
    echo "API: FAILED"
    supervisorctl restart hrai-api
fi

# Check dashboard
if curl -f -s $DASHBOARD_URL > /dev/null; then
    echo "Dashboard: OK"
else
    echo "Dashboard: FAILED"
    supervisorctl restart hrai-dashboard
fi
EOF

chmod +x /home/hrai/health_check.sh

# Run every 5 minutes
echo "*/5 * * * * /home/hrai/health_check.sh" | crontab -
```

## 🔄 Backup Strategy

### 1. Automated Backups

The system includes automated backup functionality. Configure in `.env`:

```env
AUTO_BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=30
```

### 2. Manual Backup

```bash
# Create manual backup
curl -X POST https://api.yourdomain.com/system/backup/create

# Export data to CSV
curl -X POST https://api.yourdomain.com/system/export
```

### 3. Offsite Backup

```bash
# Create offsite backup script
cat > /home/hrai/offsite_backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/hrai/Ishan_HR_AI_System/backups"
REMOTE_SERVER="backup@backup-server.com"
REMOTE_PATH="/backups/hrai/"

# Sync backups to remote server
rsync -avz --delete $BACKUP_DIR/ $REMOTE_SERVER:$REMOTE_PATH

# Clean up old local backups (keep last 7 days)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x /home/hrai/offsite_backup.sh

# Run daily at 3 AM
echo "0 3 * * * /home/hrai/offsite_backup.sh" | crontab -
```

## 🚀 Performance Optimization

### 1. Database Optimization

```bash
# Optimize SQLite database
python -c "
from app.utils.database import db_manager
conn = db_manager.connection
conn.execute('VACUUM')
conn.execute('ANALYZE')
conn.commit()
"
```

### 2. Nginx Optimization

Add to nginx configuration:

```nginx
# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# Enable caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Application Optimization

```bash
# Use production WSGI server with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:5000 --worker-connections 1000
```

## 🔧 Troubleshooting

### Common Issues

1. **Database Lock Errors**
   ```bash
   # Check for long-running processes
   ps aux | grep python
   # Restart services if needed
   sudo supervisorctl restart all
   ```

2. **High Memory Usage**
   ```bash
   # Check memory usage
   free -h
   # Monitor application memory
   curl https://api.yourdomain.com/system/performance
   ```

3. **SSL Certificate Issues**
   ```bash
   # Renew certificate
   sudo certbot renew
   sudo systemctl reload nginx
   ```

### Log Locations

- Application logs: `/var/log/hrai/`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`
- Application database logs: `logs/system.log`

### Emergency Recovery

```bash
# Stop all services
sudo supervisorctl stop all

# Restore from backup
curl -X POST https://api.yourdomain.com/system/backup/restore -d '{"backup_name": "latest_backup"}'

# Start services
sudo supervisorctl start all
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Review system logs and performance metrics
2. **Monthly**: Update system packages and dependencies
3. **Quarterly**: Review and rotate API keys and passwords
4. **Annually**: Security audit and penetration testing

### Monitoring Checklist

- [ ] API response times < 200ms
- [ ] Memory usage < 80%
- [ ] CPU usage < 70%
- [ ] Disk usage < 85%
- [ ] Error rate < 1%
- [ ] Backup success rate 100%

### Contact Information

For technical support:
- **Developer**: Ishan Shirode (ishanshirode01@gmail.com)
- **GitHub**: https://github.com/ISHANSHIRODE01/Ishan_HR_AI_System
- **Documentation**: See README.md for detailed feature documentation

---

**🎉 Congratulations! Your HR-AI System is now production-ready with enterprise-grade security, performance monitoring, and reliability features.**