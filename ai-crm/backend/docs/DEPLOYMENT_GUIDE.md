# AI Agent Unified System - Deployment Guide

## Overview
This guide covers deploying the unified AI Agent Logistics + CRM + Infiverse system to various platforms and environments.

## System Architecture

The unified system consists of:
- **Logistics + CRM Backend**: FastAPI (Python) - Main API server with proxied Infiverse endpoints
- **Infiverse Backend**: Express.js (Node.js) - Employee monitoring and workforce management (can run separately or integrated)
- **CRM Dashboard**: Streamlit (Python) - Web interface with Infiverse monitoring views
- **Database**: SQLite/PostgreSQL for main data, MongoDB for Infiverse data
- **Monitoring**: Real-time employee monitoring with AI insights
- **Frontend**: React/Vite app deployed on Vercel (optional)

## Prerequisites
- Python 3.8+
- Node.js 16+
- Git repository
- Environment variables configured
- Database setup completed (SQLite/PostgreSQL + MongoDB)

## Unified System Setup

### 1. Clone Repositories
```bash
# Main unified system (includes Complete-Infiverse)
git clone <main-repo-url>
cd ai-agent_project

<<<<<<< HEAD
# Complete-Infiverse is now included in the main repository
cd Complete-Infiverse/server
npm install
cd ../..
=======
# Optional: Clone Infiverse separately if running independently
git clone https://github.com/sharmavijay45/Complete-Infiverse.git
cd ../Complete-Infiverse
>>>>>>> 9a5d7abfa61aa2769341197651d91d368bfed338
```

### 2. Environment Configuration

#### Main System (.env)
```bash
# Core Settings
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///logistics_agent.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_PORT=8501

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Infiverse Integration
INFIVERSE_BASE_URL=http://localhost:5000  # Complete-Infiverse server URL
INFIVERSE_ENABLED=true
```

#### Infiverse System (.env)
```bash
# Database
MONGODB_URI=mongodb://localhost:27017/infiverse

# AI Services
GEMINI_API_KEY=your-gemini-key
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Monitoring
AUTO_END_DAY_ENABLED=true
MAX_WORKING_HOURS=8
```

### 3. Database Setup

#### SQLite/PostgreSQL (Main System)
```bash
cd ai-agent_project
python migrate_to_database.py
```

#### MongoDB (Infiverse)
```bash
# Install MongoDB
sudo apt install mongodb

# Start MongoDB
sudo systemctl start mongodb

# Or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 4. Running the Unified System

#### Option 1: Run Both Systems Together
```bash
# Terminal 1: Start Complete-Infiverse backend
cd Complete-Infiverse/server
npm install
npm start
# Server runs on http://localhost:5000

# Terminal 2: Start unified AI Agent system
cd ai-agent_project
python api_app.py
# API runs on http://localhost:8000 with proxied Infiverse endpoints

# Terminal 3: Start CRM dashboard
streamlit run crm_dashboard.py --server.port 8501
# Dashboard runs on http://localhost:8501
```

#### Option 2: Run Systems Separately
```bash
# Deploy Complete-Infiverse to Vercel (frontend) and separate server
cd Complete-Infiverse
vercel --prod

# Deploy main system to Railway/Render/Heroku
# Set INFIVERSE_BASE_URL to the deployed Infiverse server URL
```

#### Option 3: Vercel + Vercel (Unified Cloud Deployment)
```bash
# Deploy FastAPI backend to Vercel
cd ai-agent_project
vercel --prod
# Backend URL: https://your-fastapi-app.vercel.app

# Deploy Complete-Infiverse to separate Vercel project
cd Complete-Infiverse
vercel --prod
# Frontend URL: https://your-infiverse-app.vercel.app

# Update FastAPI environment variables
vercel env add INFIVERSE_BASE_URL https://your-infiverse-app.vercel.app

# Redeploy FastAPI with updated INFIVERSE_BASE_URL
vercel --prod
```

#### Option 4: Vercel + Railway (Hybrid Deployment)
```bash
# Deploy FastAPI to Railway (better for long-running tasks)
railway up
# Backend URL: https://your-app.railway.app

# Deploy Complete-Infiverse frontend to Vercel
cd Complete-Infiverse
vercel --prod
# Frontend URL: https://your-infiverse-app.vercel.app

# Update Railway environment
railway variables set INFIVERSE_BASE_URL=https://your-infiverse-app.vercel.app
```

## Local Development

### Setup
```bash
# Clone repository
git clone <repository-url>
cd ai-agent_project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python migrate_to_database.py

# Start development server
python start_server.py
```

### Development Services
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs

## Production Deployment

### Docker Deployment

#### Single Container
```bash
# Build image
docker build -t ai-agent:latest .

# Run container
docker run -d \
  --name ai-agent \
  -p 8000:8000 \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -e OPENAI_API_KEY=your_key \
  ai-agent:latest
```

#### Docker Compose (Unified System)
```bash
# Start all services (main system + MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# For complete system with Infiverse
docker-compose -f docker-compose.unified.yml up -d
```

### Cloud Platforms

#### Railway.app
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway up

# Set environment variables
railway variables set OPENAI_API_KEY=your_key
```

#### Render.com
1. Connect GitHub repository to Render
2. Create new Web Service
3. Use `render.yaml` configuration
4. Set environment variables in dashboard

#### Heroku
```bash
# Install Heroku CLI
# Create app
heroku create your-app-name

# Set environment variables
heroku config:set OPENAI_API_KEY=your_key

# Deploy
git push heroku main
```

#### Vercel (Infiverse Frontend)
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from Complete-Infiverse directory
cd Complete-Infiverse
vercel

# Set environment variables
vercel env add MONGODB_URI
vercel env add GEMINI_API_KEY
vercel env add CLOUDINARY_CLOUD_NAME
vercel env add CLOUDINARY_API_KEY
vercel env add CLOUDINARY_API_SECRET

# Configure domain (if purchased)
vercel domains add yourdomain.com
```

#### Vercel (FastAPI Backend)
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy FastAPI backend to Vercel
cd ai-agent_project

# Create vercel.json for FastAPI
cat > vercel.json << EOF
{
  "version": 2,
  "builds": [
    {
      "src": "api_app.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api_app.py"
    }
  ],
  "env": {
    "DATABASE_URL": "@database_url",
    "OPENAI_API_KEY": "@openai_api_key",
    "INFIVERSE_BASE_URL": "@infiverse_base_url"
  }
}
EOF

# Create requirements.txt for Vercel
pip freeze > requirements.txt

# Deploy to Vercel
vercel

# Set environment variables in Vercel dashboard or CLI
vercel env add DATABASE_URL
vercel env add OPENAI_API_KEY
vercel env add INFIVERSE_BASE_URL
vercel env add SECRET_KEY
vercel env add JWT_SECRET

# For production deployment
vercel --prod

# Get deployment URL
# Update INFIVERSE_BASE_URL in other deployments to point to Vercel URL
```

#### Vercel + FastAPI Environment Alignment
```bash
# .env for Vercel deployment
DATABASE_URL=postgresql://user:pass@host:5432/db  # Use Vercel Postgres or external DB
OPENAI_API_KEY=sk-...
INFIVERSE_BASE_URL=https://your-infiverse-app.vercel.app
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
API_HOST=0.0.0.0
API_PORT=8000

# Vercel-specific settings
VERCEL_URL=https://your-app.vercel.app
VERCEL_ENV=production
```

#### AWS EC2
```bash
# Launch EC2 instance (Ubuntu 20.04+)
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install dependencies
sudo apt update
sudo apt install python3 python3-pip nginx

# Clone and setup project
git clone <repository-url>
cd ai-agent_project
pip3 install -r requirements.txt

# Configure nginx (see nginx.conf)
sudo cp nginx.conf /etc/nginx/sites-available/ai-agent
sudo ln -s /etc/nginx/sites-available/ai-agent /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Setup systemd service
sudo cp ai-agent.service /etc/systemd/system/
sudo systemctl enable ai-agent
sudo systemctl start ai-agent
```

## Environment Configuration

### Required Variables
```bash
# Core Settings
OPENAI_API_KEY=sk-...                    # OpenAI API key
DATABASE_URL=sqlite:///logistics_agent.db # Database connection

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_PORT=8501

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_RECIPIENTS=admin@company.com

# Feature Flags
ENABLE_SMART_CHATBOT=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_HUMAN_REVIEW=true

# Performance
AGENT_INTERVAL=300                       # 5 minutes
PROCUREMENT_INTERVAL=3600                # 1 hour
DELIVERY_INTERVAL=1800                   # 30 minutes
MONITORING_INTERVAL=60                   # 1 minute

# Infiverse Integration
INFIVERSE_BASE_URL=http://localhost:5000  # Complete-Infiverse server URL (localhost for dev, Vercel URL for prod)
INFIVERSE_ENABLED=true

# Vercel Deployment (when deploying FastAPI to Vercel)
VERCEL_URL=https://your-app.vercel.app  # Auto-set by Vercel
VERCEL_ENV=production  # Auto-set by Vercel
```

### Optional Variables
```bash
# Monitoring
SENTRY_DSN=https://...                   # Error tracking
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Database (for PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=logistics
DB_USER=postgres
DB_PASSWORD=password

# Redis (for caching)
REDIS_URL=redis://localhost:6379

# Load Balancing
WORKERS=4                                # Number of worker processes
```

## Database Setup

### SQLite (Default)
```bash
# Initialize database
python migrate_to_database.py

# Backup database
cp logistics_agent.db logistics_agent.db.backup
```

### PostgreSQL (Production)
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE logistics;
CREATE USER logistics_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE logistics TO logistics_user;

# Update environment
DATABASE_URL=postgresql://logistics_user:secure_password@localhost/logistics

# Run migrations
python migrate_to_database.py
```

## Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificate (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Update nginx configuration for HTTPS
# Restart nginx
sudo systemctl restart nginx
```

### API Security
```python
# Enable authentication in api_app.py
from auth_system import require_auth

@app.get("/protected-endpoint")
@require_auth
def protected_endpoint():
    return {"message": "Authenticated access"}
```

### Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000  # API port
sudo ufw allow 8501  # Dashboard port
```

## Monitoring and Logging

### System Monitoring
```bash
# Start monitoring service
python monitoring.py &

# View system metrics
tail -f data/monitoring_metrics.json

# Check health
python deploy.py health-check
```

### Log Management
```bash
# Rotate logs
sudo apt install logrotate

# Configure log rotation
sudo nano /etc/logrotate.d/ai-agent
```

### Performance Monitoring
- Use tools like htop, iotop for system monitoring
- Monitor API response times
- Track database query performance
- Set up alerts for resource usage

## Backup and Recovery

### Database Backup
```bash
# SQLite backup
cp logistics_agent.db backups/logistics_$(date +%Y%m%d).db

# PostgreSQL backup
pg_dump logistics > backups/logistics_$(date +%Y%m%d).sql
```

### Data Backup
```bash
# Backup data directory
tar -czf backups/data_$(date +%Y%m%d).tar.gz data/

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf /backups/ai-agent_$DATE.tar.gz \
  logistics_agent.db \
  data/ \
  .env.production
```

### Recovery Procedures
```bash
# Restore database
cp backups/logistics_20250101.db logistics_agent.db

# Restore data
tar -xzf backups/data_20250101.tar.gz

# Restart services
sudo systemctl restart ai-agent
```

## Scaling and Load Balancing

### Horizontal Scaling
```bash
# Run multiple API instances
uvicorn api_app:app --host 0.0.0.0 --port 8000 --workers 4

# Use nginx for load balancing
upstream ai_agent {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

### Database Scaling
- Use read replicas for read-heavy workloads
- Implement connection pooling
- Consider database sharding for very large datasets

### Caching
```python
# Redis caching
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Cache API responses
@app.get("/cached-endpoint")
def cached_endpoint():
    cached = r.get("endpoint_data")
    if cached:
        return json.loads(cached)
    
    data = expensive_operation()
    r.setex("endpoint_data", 300, json.dumps(data))  # 5 min cache
    return data
```

## Troubleshooting Deployment

### Common Issues

#### Port Conflicts
```bash
# Check port usage
sudo netstat -tlnp | grep :8000

# Kill process using port
sudo kill -9 <PID>
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x start_server.py
chown -R www-data:www-data /path/to/project
```

#### Memory Issues
```bash
# Check memory usage
free -h

# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Database Connection Issues
```bash
# Test database connection
python -c "from database.service import DatabaseService; print('DB OK')"

# Check database logs
tail -f /var/log/postgresql/postgresql-*.log
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database health
python -c "from database.service import DatabaseService; DatabaseService().get_orders()"

# System health
python deploy.py health-check
```

## Maintenance

### Regular Tasks
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Backup database and data files
- Monitor log files for errors
- Check system resource usage
- Update SSL certificates

### Updates and Patches
```bash
# Pull latest code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run database migrations
python migrate_to_database.py

# Restart services
sudo systemctl restart ai-agent
```

### Performance Tuning
- Optimize database queries
- Adjust worker processes based on CPU cores
- Tune cache settings
- Monitor and adjust resource limits
