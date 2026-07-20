# CORS Error Fix - Complete Guide

## Problem Summary
Your frontend (Vercel) cannot communicate with your backend (Render) due to CORS policy blocking the request.

**Error:**
```
Access to XMLHttpRequest at 'https://ai-artha.onrender.com/api/v1/auth/register'
from origin 'https://ai-artha.vercel.app' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present.
Response to preflight request doesn't pass access control check.
Failed to load resource: net::ERR_FAILED
404 error on preflight request.
```

---

## 1. Why This CORS Error is Happening

### Root Causes:
1. **Different Origins**: Frontend (`https://ai-artha.vercel.app`) ≠ Backend (`https://ai-artha.onrender.com`)
2. **Browser Security Policy**: The Same-Origin Policy prevents cross-origin requests by default
3. **Missing CORS Headers**: Backend not responding with `Access-Control-Allow-Origin` header
4. **Preflight Request Failure**: Browser sends OPTIONS request first, but backend returns 404 instead of proper CORS headers

### Why It Matters:
- Prevents malicious scripts from accessing sensitive data on other domains
- Requires explicit server configuration to allow cross-origin requests
- Applies to all modern browsers (not to mobile apps or server-to-server calls)

---

## 2. What a Preflight OPTIONS Request Is

### How It Works:

When your frontend makes a **non-simple request** (POST with JSON, custom headers, etc.), the browser automatically sends a **preflight OPTIONS request** BEFORE the actual request:

```
OPTIONS /api/v1/auth/register HTTP/1.1
Host: ai-artha.onrender.com
Origin: https://ai-artha.vercel.app
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type, authorization
```

### Server Must Respond With:
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://ai-artha.vercel.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Headers: Origin, Content-Type, Authorization
Access-Control-Max-Age: 86400
```

### If Preflight Fails:
- Browser blocks the actual request
- You see "404 error on preflight request" (server doesn't handle OPTIONS)
- You see "No 'Access-Control-Allow-Origin' header" (missing CORS headers)

### Simple Requests (No Preflight):
- GET, HEAD, POST (with specific content types)
- No custom headers
- No Authorization header

---

## 3. Why the Browser Blocks the Request

### Security Reasons:

1. **Prevents CSRF Attacks**: Malicious sites can't make requests to your API on behalf of users
2. **Protects Sensitive Data**: Unauthorized domains can't access your API responses
3. **Enforces Explicit Consent**: Server must explicitly allow each origin
4. **Applies Only to Browsers**: Mobile apps, curl, Postman, server-to-server calls are NOT affected

### Browser Enforcement:
- Browsers implement CORS, not servers
- Curl/Postman won't show CORS errors (they don't enforce it)
- Mobile apps don't enforce CORS
- Server-to-server calls don't enforce CORS

---

## 4. How to Correctly Configure CORS on the Backend

### Key Principles:

1. **CORS middleware MUST be first** (before all routes)
2. **Handle OPTIONS requests** (preflight requests)
3. **Set proper headers** (Allow-Origin, Allow-Methods, Allow-Headers)
4. **Use whitelist** (only allow specific origins in production)
5. **Set credentials** (if using cookies/auth)

### Middleware Order (Critical):
```
1. CORS middleware ← MUST BE FIRST
2. Security middleware (helmet, rate limiting)
3. Body parser
4. Routes
5. Error handler
```

---

## 5. Correct Express CORS Configuration Code

### Updated Configuration (Applied to Your Backend):

```javascript
// --- CORS Configuration (MUST be before all routes) ---
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = [
      'https://ai-artha.vercel.app',      // Production frontend
      'http://localhost:3000',             // Local development
      'http://localhost:5173',             // Vite dev server
      'http://127.0.0.1:3000',
      'http://127.0.0.1:5173',
    ];

    // Allow requests with no origin (mobile apps, curl, etc.)
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,                       // Allow cookies/auth
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'],
  allowedHeaders: [
    'Origin',
    'X-Requested-With',
    'Content-Type',
    'Accept',
    'Authorization',
    'X-CSRF-Token',
    'X-API-Key',
  ],
  exposedHeaders: ['X-Total-Count', 'X-Page-Count'],
  maxAge: 86400,                           // Cache preflight for 24 hours
  preflightContinue: false,                // Don't pass to next handler
};

// Apply CORS middleware (MUST be first)
app.use(cors(corsOptions));

// Handle preflight requests explicitly (safety net)
app.options('*', cors(corsOptions));

// Then add other middleware...
app.use(helmetConfig);
app.use(limiter);
// ... rest of middleware
```

### What Each Option Does:

| Option | Purpose |
|--------|---------|
| `origin` | Function to validate allowed origins |
| `credentials` | Allow cookies and Authorization headers |
| `methods` | HTTP methods allowed |
| `allowedHeaders` | Headers the client can send |
| `exposedHeaders` | Headers the client can read from response |
| `maxAge` | Cache preflight response (seconds) |
| `preflightContinue` | Pass preflight to next handler (usually false) |

---

## 6. Common Mistakes That Cause This Issue in Production

### ❌ Mistake 1: CORS Middleware Not First
```javascript
// WRONG - CORS after other middleware
app.use(express.json());
app.use(cors(corsOptions));  // Too late!
app.use(routes);
```

**Fix**: Place CORS before everything except dotenv.config()

---

### ❌ Mistake 2: Hardcoded Single Origin
```javascript
// WRONG - Only works for one origin
app.use(cors({ origin: 'https://ai-artha.vercel.app' }));
```

**Problem**: Breaks in development, breaks if you add another frontend

**Fix**: Use origin function with whitelist

---

### ❌ Mistake 3: Wildcard Origin with Credentials
```javascript
// WRONG - Security vulnerability
app.use(cors({ 
  origin: '*',
  credentials: true  // Incompatible!
}));
```

**Problem**: Browsers reject this combination (security risk)

**Fix**: Use specific origins or remove credentials

---

### ❌ Mistake 4: Not Handling OPTIONS Requests
```javascript
// WRONG - No OPTIONS handler
app.post('/api/v1/auth/register', (req, res) => {
  // ...
});
```

**Problem**: Preflight OPTIONS request returns 404

**Fix**: Add `app.options('*', cors(corsOptions))`

---

### ❌ Mistake 5: Wrong Content-Type Header
```javascript
// WRONG - Frontend sends JSON but server expects form-data
fetch('https://api.example.com/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },  // Custom header!
  body: JSON.stringify(data)
});
```

**Problem**: Triggers preflight, but server doesn't allow Content-Type header

**Fix**: Include 'Content-Type' in allowedHeaders

---

### ❌ Mistake 6: Environment-Specific Origins Not Configured
```javascript
// WRONG - Only production origin
const corsOptions = {
  origin: 'https://ai-artha.vercel.app'
};
```

**Problem**: Breaks local development

**Fix**: Include localhost origins for development

---

### ❌ Mistake 7: Helmet Blocking CORS Headers
```javascript
// WRONG - Helmet might block headers
app.use(helmet());
app.use(cors(corsOptions));  // After helmet
```

**Problem**: Helmet's CSP might interfere

**Fix**: Configure helmet to allow CORS, place CORS first

---

### ❌ Mistake 8: Rate Limiting Blocking Preflight
```javascript
// WRONG - Rate limiter before CORS
app.use(limiter);
app.use(cors(corsOptions));
```

**Problem**: Preflight OPTIONS requests get rate limited

**Fix**: Place CORS before rate limiter, or exclude OPTIONS from limiter

---

## Testing Your CORS Configuration

### Test 1: Check Preflight Response
```bash
curl -X OPTIONS https://ai-artha.onrender.com/api/v1/auth/register \
  -H "Origin: https://ai-artha.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -v
```

**Expected Response Headers:**
```
Access-Control-Allow-Origin: https://ai-artha.vercel.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Headers: Origin, X-Requested-With, Content-Type, Accept, Authorization
```

### Test 2: Check Actual Request
```bash
curl -X POST https://ai-artha.onrender.com/api/v1/auth/register \
  -H "Origin: https://ai-artha.vercel.app" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -v
```

**Expected Response Headers:**
```
Access-Control-Allow-Origin: https://ai-artha.vercel.app
Access-Control-Allow-Credentials: true
```

### Test 3: Browser Console Test
```javascript
// In browser console on https://ai-artha.vercel.app
fetch('https://ai-artha.onrender.com/api/v1/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer token'
  },
  credentials: 'include',
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'test123'
  })
})
.then(r => r.json())
.then(data => console.log('Success:', data))
.catch(err => console.error('Error:', err));
```

---

## Deployment Checklist

### Before Deploying to Render:

- [ ] CORS middleware is first in server.js
- [ ] `app.options('*', cors(corsOptions))` is present
- [ ] Production origin (`https://ai-artha.vercel.app`) is in allowedOrigins
- [ ] `credentials: true` is set
- [ ] All required headers are in allowedHeaders
- [ ] `preflightContinue: false` is set
- [ ] No wildcard origin with credentials
- [ ] Rate limiter doesn't block OPTIONS requests
- [ ] Helmet doesn't interfere with CORS headers

### Environment Variables:

Add to `.env.production`:
```
FRONTEND_URL=https://ai-artha.vercel.app
BACKEND_URL=https://ai-artha.onrender.com
NODE_ENV=production
```

### Render Deployment:

1. Push changes to GitHub
2. Render auto-deploys from main branch
3. Check Render logs for CORS configuration
4. Test from browser console

---

## Frontend Configuration (Axios/Fetch)

### Axios Configuration:
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://ai-artha.onrender.com/api/v1',
  withCredentials: true,  // Important for cookies/auth
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add auth token to requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Fetch Configuration:
```javascript
const response = await fetch('https://ai-artha.onrender.com/api/v1/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  credentials: 'include',  // Important for cookies
  body: JSON.stringify(data)
});
```

---

## Troubleshooting

### Issue: Still Getting CORS Error After Fix

1. **Clear browser cache** (Ctrl+Shift+Delete)
2. **Check backend logs** for CORS configuration
3. **Verify origin** matches exactly (case-sensitive, no trailing slash)
4. **Check for typos** in allowedOrigins array
5. **Restart backend** after code changes
6. **Check Render logs** for deployment errors

### Issue: Preflight Returns 404

- CORS middleware not first
- `app.options('*', cors(corsOptions))` missing
- Route handler doesn't exist for OPTIONS

### Issue: Preflight Returns 200 but Still Blocked

- Missing `Access-Control-Allow-Origin` header
- Missing `Access-Control-Allow-Methods` header
- Missing `Access-Control-Allow-Headers` header
- Origin doesn't match exactly

### Issue: Works in Development, Fails in Production

- Production origin not in allowedOrigins
- Environment variables not set correctly
- Render deployment didn't pick up changes
- Different backend URL in production

---

## Summary

Your backend is now configured with:
✅ Proper CORS middleware (first in chain)
✅ Whitelist of allowed origins
✅ Support for credentials (cookies/auth)
✅ Explicit OPTIONS handler
✅ All necessary headers configured
✅ 24-hour preflight cache

The fix has been applied to `backend/src/server.js`. Deploy to Render and test from your Vercel frontend.
