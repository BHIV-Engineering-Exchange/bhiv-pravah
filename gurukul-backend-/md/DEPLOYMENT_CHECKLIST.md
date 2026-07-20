# Render Deployment Checklist

## Pre-Deployment

- [ ] All code pushed to GitHub
- [ ] Database credentials ready (PostgreSQL, MongoDB, Redis)
- [ ] Email SMTP credentials ready (Gmail App Password or other)
- [ ] Environment variables documented

## Service Setup Order

### 1. Databases First
- [ ] Create PostgreSQL database for Gurukul Backend
- [ ] Create PostgreSQL database for EMS Backend
- [ ] Create MongoDB Atlas cluster for Karma Tracker
- [ ] (Optional) Create Redis instance

### 2. Backend Services
- [ ] Deploy Gurukul Backend
- [ ] Deploy EMS Backend
- [ ] Verify both backends are running
- [ ] Test API endpoints

### 3. Frontend Services
- [ ] Deploy Gurukul Frontend
- [ ] Deploy EMS Frontend
- [ ] Update CORS in backends with frontend URLs
- [ ] Test frontend-backend connections

### 4. Background Workers
- [ ] Deploy Bucket Consumer
- [ ] Verify it's connecting to Gurukul Backend
- [ ] Test PRANA packet processing

## Environment Variables Checklist

### Gurukul Backend
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `SECRET_KEY` - JWT secret (auto-generated or custom)
- [ ] `MONGODB_URI` - MongoDB connection string
- [ ] `REDIS_URL` - Redis connection string (optional)
- [ ] `FRONTEND_URL` - Gurukul frontend URL
- [ ] `EMS_FRONTEND_URL` - EMS frontend URL

### EMS Backend
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `SECRET_KEY` - JWT secret (auto-generated or custom)
- [ ] `FRONTEND_URL` - EMS frontend URL
- [ ] `MAIL_USERNAME` - SMTP username
- [ ] `MAIL_PASSWORD` - SMTP password/app password
- [ ] `MAIL_SERVER` - SMTP server (e.g., smtp.gmail.com)
- [ ] `MAIL_PORT` - SMTP port (usually 587)

### Bucket Consumer
- [ ] `GURUKUL_BACKEND_URL` - Gurukul backend service URL
- [ ] `POLL_INTERVAL_SECONDS` - Polling interval (default: 5)
- [ ] `BATCH_SIZE` - Batch size (default: 10)

### Gurukul Frontend
- [ ] `VITE_API_URL` - Gurukul backend URL
- [ ] `VITE_EMS_API_URL` - EMS backend URL

### EMS Frontend
- [ ] `VITE_API_URL` - EMS backend URL

## Post-Deployment Testing

### Backend Health Checks
- [ ] Gurukul Backend: `https://gurukul-backend.onrender.com/docs`
- [ ] EMS Backend: `https://ems-backend.onrender.com/docs`
- [ ] Both APIs return 200 OK

### Frontend Access
- [ ] Gurukul Frontend loads correctly
- [ ] EMS Frontend loads correctly
- [ ] No console errors

### Authentication
- [ ] Can register new users
- [ ] Can login with credentials
- [ ] JWT tokens work correctly
- [ ] Password reset emails sent

### Database Connections
- [ ] Gurukul Backend connects to PostgreSQL
- [ ] EMS Backend connects to PostgreSQL
- [ ] Karma Tracker connects to MongoDB
- [ ] Can create/read data

### Email Service
- [ ] Password reset emails sent
- [ ] School admin credentials emails sent
- [ ] Teacher/Student/Parent credentials emails sent

### PRANA & Karma Integration
- [ ] PRANA packets ingested
- [ ] Bucket Consumer processes packets
- [ ] Karma updates correctly
- [ ] Karma API endpoints work

## CORS Configuration

Update these files after deployment:

### backend/app/main.py
```python
allow_origins=[
    "https://gurukul-frontend.onrender.com",
    "https://ems-frontend.onrender.com",
    # Remove "*" in production
]
```

### EMS System/app/main.py
```python
allow_origins=[
    "https://ems-frontend.onrender.com",
    "https://gurukul-frontend.onrender.com",
    # Remove localhost origins in production
]
```

## Common Issues & Solutions

### Issue: Build fails
- **Solution:** Check build logs, verify all dependencies in requirements.txt

### Issue: Database connection fails
- **Solution:** Verify DATABASE_URL, check if database is paused (free tier)

### Issue: CORS errors
- **Solution:** Update CORS origins in backend to include frontend URLs

### Issue: Email not sending
- **Solution:** Verify SMTP credentials, check email service logs

### Issue: Frontend can't connect to backend
- **Solution:** Verify VITE_API_URL environment variable, check CORS settings

### Issue: Bucket Consumer not working
- **Solution:** Verify GURUKUL_BACKEND_URL, check worker logs

## Monitoring

- [ ] Set up uptime monitoring
- [ ] Configure error alerts
- [ ] Monitor database usage
- [ ] Track API response times

## Security Checklist

- [ ] All secrets in environment variables (not in code)
- [ ] CORS properly configured (no wildcards in production)
- [ ] Database credentials secure
- [ ] JWT secrets are strong
- [ ] HTTPS enabled (automatic on Render)

## Performance Optimization

- [ ] Enable database connection pooling
- [ ] Configure Redis caching (if using)
- [ ] Optimize frontend bundle size
- [ ] Enable CDN for static assets (Render handles this)

## Documentation

- [ ] Update API documentation with production URLs
- [ ] Document all environment variables
- [ ] Create runbook for common operations
- [ ] Document backup procedures

