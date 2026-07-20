# ARTHA Quick Start Guide

## Your Configured Credentials

✅ **Email**: pandeyashmit299@gmail.com  
✅ **MongoDB**: Atlas cluster connected  
✅ **Redis**: Redis Cloud connected  
✅ **JWT**: Secure secrets configured  

## Step-by-Step Setup

### 1. Test All Connections
```bash
# Run the setup script
node setup-and-test.js

# Or manually test connections
cd backend
npm install
npm run test:connections
```

### 2. Start Backend Server
```bash
cd backend
npm run dev
```

Expected output:
```
🚀 Server running on port 5000
✅ Connected to MongoDB Atlas
✅ Redis client connected successfully
📊 Database seeded successfully
```

### 3. Start Frontend (New Terminal)
```bash
cd frontend
npm install
npm run dev
```

### 4. Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/health/detailed

## Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@artha.local | Admin@123456 |
| Accountant | accountant@artha.local | Accountant@123 |
| User | user@example.com | testuser123 |

## Your Environment Configuration

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://blackholeinfiverse54_db_user:Gjpl998Z6hsQLjJF@artha.rzneis7.mongodb.net/artha_dev

# Redis Cloud  
REDIS_URL=redis://default:Gjpl998Z6hsQLjJF@redis-17252.c265.us-east-1-2.ec2.cloud.redislabs.com:17252

# JWT Security
JWT_SECRET=9fee28a266c3481788487fbb19544ad6
```

## Test API Endpoints

### Health Check
```bash
curl http://localhost:5000/health/detailed
```

### Register New User
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "pandeyashmit299@gmail.com",
    "password": "SecurePass123!",
    "name": "Ashmit Pandey",
    "role": "admin"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@artha.local",
    "password": "Admin@123456"
  }'
```

### Get Accounts
```bash
curl http://localhost:5000/api/v1/accounts
```

## Troubleshooting

### MongoDB Connection Issues
- Check if your IP is whitelisted in MongoDB Atlas
- Verify the connection string is correct
- Ensure network access allows connections

### Redis Connection Issues
- Verify Redis Cloud endpoint is accessible
- Check if password is correct
- Test with: `redis-cli -h redis-17252.c265.us-east-1-2.ec2.cloud.redislabs.com -p 17252 -a Gjpl998Z6hsQLjJF ping`

### Port Already in Use
```bash
# Kill process on port 5000
netstat -ano | findstr :5000
# Then kill the PID shown
```

## Features Available

✅ **Authentication** - JWT-based with refresh tokens  
✅ **Ledger System** - Double-entry accounting with HMAC chain  
✅ **Invoicing** - Create, send, track payments  
✅ **Expenses** - Upload receipts, approval workflow  
✅ **GST Compliance** - GSTR1, GSTR3B generation  
✅ **TDS Management** - Calculate, track, file returns  
✅ **Financial Reports** - P&L, Balance Sheet, Cash Flow  
✅ **Dashboard** - Real-time KPIs and analytics  
✅ **Performance Monitoring** - Redis caching, metrics  
✅ **Health Checks** - Multiple monitoring endpoints  

## Production Deployment

When ready for production:
```bash
# Generate secure production config
cd backend && npm run generate:config

# Deploy with Docker
./scripts/deploy.sh --seed
```

Your system is now fully configured and ready to use! 🚀