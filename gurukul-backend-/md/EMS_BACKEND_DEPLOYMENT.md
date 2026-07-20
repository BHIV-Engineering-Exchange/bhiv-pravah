# EMS Backend Deployment Guide

## Quick Deployment Steps

### 1. Render Dashboard Setup
- Go to: https://dashboard.render.com
- Click: **New +** → **Web Service**
- Connect: Your GitHub repository

### 2. Service Configuration

**Name:** `ems-backend`

**Build Command:**
```bash
pip install -r "EMS System/requirements.txt"
```

**Start Command:**
```bash
cd "EMS System" && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Plan:** Free (or Starter)

### 3. Environment Variables

#### Copy-Paste Ready:
```
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ENVIRONMENT=production
PYTHON_VERSION=3.11.0
MAIL_FROM=noreply@schoolmanagement.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
USE_CREDENTIALS=true
PASSWORD_TOKEN_EXPIRE_MINUTES=30
```

#### Set Manually:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Generate secure random string
- `FRONTEND_URL` - Set after deploying EMS frontend
- `MAIL_USERNAME` - Your email (if using email features)
- `MAIL_PASSWORD` - App password (if using email features)

### 4. Test After Deployment

```bash
# Health check
curl https://your-ems-backend.onrender.com/health

# Root endpoint
curl https://your-ems-backend.onrender.com/

# API docs
https://your-ems-backend.onrender.com/docs
```

### 5. Expected Response

**Health Check:**
```json
{"status": "healthy"}
```

**Root Endpoint:**
```json
{
  "message": "School Management System API",
  "version": "1.0.0",
  "status": "running"
}
```

## Troubleshooting

- **Port binding issues:** Ensure `$PORT` is used (not `${PORT:-10000}`)
- **Database connection:** Verify `DATABASE_URL` is correct
- **Import errors:** Check that all dependencies are in `requirements.txt`

