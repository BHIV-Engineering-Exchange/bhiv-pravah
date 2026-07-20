# Redis Connection Setup Guide

## Your Redis Cloud Credentials
- **Host**: redis-17252.c265.us-east-1-2.ec2.cloud.redislabs.com
- **Port**: 17252
- **Username**: default
- **Password**: gK22JxYlv9HCpBBuNWpizNT1YjBOOoAD

## Step 1: Test Redis Connection

```bash
cd backend
npm run test:redis
```

Expected output:
```
🔄 Testing Redis connection...
🔗 Redis client connecting...
✅ Redis client ready!

📝 Testing Redis operations:
✅ SET operation successful
✅ GET operation successful: Hello Redis!
✅ JSON operation successful: Artha
✅ Cleanup successful

🎉 Redis connection test completed successfully!
```

## Step 2: Environment Configuration

Your `.env` file should have:
```env
# Redis Configuration
REDIS_HOST=redis-17252.c265.us-east-1-2.ec2.cloud.redislabs.com
REDIS_PORT=17252
REDIS_PASSWORD=gK22JxYlv9HCpBBuNWpizNT1YjBOOoAD
```

## Step 3: How Redis is Used in Artha

### 1. **Caching API Responses**
```javascript
// Automatically caches GET requests
app.use('/api/v1/accounts', cacheMiddleware(3600), accountsRoutes);
```

### 2. **Session Storage**
```javascript
// Stores user sessions and JWT tokens
await cacheSet(`session:${userId}`, sessionData, 86400);
```

### 3. **Performance Optimization**
```javascript
// Caches expensive database queries
const cachedData = await cacheGet('expensive:query:key');
if (!cachedData) {
  const data = await expensiveQuery();
  await cacheSet('expensive:query:key', data, 1800);
}
```

## Step 4: Redis Functions Available

### Basic Operations
```javascript
import { cacheGet, cacheSet, cacheDel } from './config/redis.js';

// Store data
await cacheSet('key', { data: 'value' }, 3600); // 1 hour

// Retrieve data
const data = await cacheGet('key');

// Delete data
await cacheDel('key');
```

### Cache Middleware
```javascript
import { cacheMiddleware } from './middleware/cache.js';

// Cache responses for 1 hour
app.use('/api/v1/reports', cacheMiddleware(3600), reportsRoutes);
```

## Step 5: Start Server with Redis

```bash
cd backend
npm run dev
```

You should see:
```
🚀 Server running on port 5000
✅ Connected to MongoDB Atlas
✅ Redis client ready!
📊 Database seeded successfully
```

## Step 6: Verify Redis is Working

### Test API with caching:
```bash
# First request (cache miss)
curl http://localhost:5000/api/v1/accounts

# Second request (cache hit - faster response)
curl http://localhost:5000/api/v1/accounts
```

### Check server logs for cache activity:
```
Cache miss: /api/v1/accounts
Cache hit: /api/v1/accounts
```

## Troubleshooting

### Issue 1: Connection Timeout
```
Error: connect ETIMEDOUT
```
**Solution**: Check firewall/network settings

### Issue 2: Authentication Failed
```
Error: WRONGPASS invalid username-password pair
```
**Solution**: Verify password is correct

### Issue 3: Host Not Found
```
Error: getaddrinfo ENOTFOUND
```
**Solution**: Check host URL is correct

## Redis Benefits in Artha

1. **⚡ Faster API Responses** - Cached data loads instantly
2. **📊 Reduced Database Load** - Less queries to MongoDB
3. **🔄 Session Management** - Efficient user session storage
4. **📈 Better Performance** - Overall application speed improvement

## Production Configuration

For production, Redis provides:
- **High Availability** - Automatic failover
- **Persistence** - Data survives restarts
- **Clustering** - Horizontal scaling
- **Security** - SSL/TLS encryption

Your Redis Cloud instance is already production-ready! 🚀