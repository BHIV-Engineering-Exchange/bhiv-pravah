# CORS Configuration - Quick Reference

## What Was Changed

Your `backend/src/server.js` has been updated with the correct CORS configuration.

### Before (Incorrect):
```javascript
const ALLOWED_ORIGIN = 'https://ai-artha.vercel.app';
app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (origin === ALLOWED_ORIGIN) {
    res.header('Access-Control-Allow-Origin', ALLOWED_ORIGIN);
    res.header('Vary', 'Origin');
  }
  res.header('Access-Control-Allow-Credentials', 'true');
  res.header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,PATCH,OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }
  next();
});
```

**Problems:**
- ❌ Doesn't handle development origins
- ❌ Doesn't use the cors package properly
- ❌ Conditional origin check might fail
- ❌ No explicit OPTIONS handler

### After (Correct):
```javascript
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = [
      'https://ai-artha.vercel.app',
      'http://localhost:3000',
      'http://localhost:5173',
      'http://127.0.0.1:3000',
      'http://127.0.0.1:5173',
    ];

    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
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
  maxAge: 86400,
  preflightContinue: false,
};

app.use(cors(corsOptions));
app.options('*', cors(corsOptions));
```

**Benefits:**
- ✅ Uses proper cors package
- ✅ Supports development and production
- ✅ Explicit OPTIONS handler
- ✅ Proper error handling
- ✅ Caches preflight for 24 hours

---

## How to Deploy

### Step 1: Verify Changes Locally
```bash
cd backend
npm install  # Ensure cors package is installed
npm run dev
```

### Step 2: Test Preflight Request
```bash
curl -X OPTIONS http://localhost:5000/api/v1/auth/register \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -v
```

Expected: `HTTP/1.1 200 OK` with CORS headers

### Step 3: Push to GitHub
```bash
git add backend/src/server.js
git commit -m "Fix: Configure CORS properly for production"
git push origin main
```

### Step 4: Render Auto-Deploys
- Render watches your GitHub repo
- Changes deploy automatically
- Check Render dashboard for deployment status

### Step 5: Test from Frontend
```javascript
// In browser console on https://ai-artha.vercel.app
fetch('https://ai-artha.onrender.com/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'test@example.com', password: 'test123' })
})
.then(r => r.json())
.then(data => console.log('Success!', data))
.catch(err => console.error('Error:', err));
```

---

## Key Points to Remember

1. **CORS is browser-enforced**, not server-enforced
   - Curl/Postman won't show CORS errors
   - Mobile apps don't enforce CORS
   - Only browsers enforce it

2. **Preflight OPTIONS request** happens automatically
   - Browser sends it before POST/PUT/DELETE with custom headers
   - Server must respond with 200/204 and CORS headers
   - If preflight fails, actual request is blocked

3. **Whitelist approach** is secure
   - Only allow specific origins
   - Never use wildcard `*` with credentials
   - Add new origins as needed

4. **Middleware order matters**
   - CORS must be first (after dotenv)
   - Before security, rate limiting, routes
   - Before body parser

5. **Credentials require explicit setup**
   - `credentials: true` on server
   - `withCredentials: true` on client (axios)
   - `credentials: 'include'` on client (fetch)

---

## Testing Checklist

- [ ] Preflight OPTIONS request returns 200
- [ ] Response includes `Access-Control-Allow-Origin` header
- [ ] Response includes `Access-Control-Allow-Methods` header
- [ ] Response includes `Access-Control-Allow-Headers` header
- [ ] Actual POST request succeeds
- [ ] Works from browser console
- [ ] Works from frontend app
- [ ] Works in production (Vercel → Render)
- [ ] Works in development (localhost)

---

## If It Still Doesn't Work

1. **Check Render logs**
   ```
   Render Dashboard → Your App → Logs
   ```

2. **Verify backend is running**
   ```bash
   curl https://ai-artha.onrender.com/api/health
   ```

3. **Check frontend origin**
   - Must match exactly: `https://ai-artha.vercel.app`
   - No trailing slash
   - Case-sensitive

4. **Clear browser cache**
   - Ctrl+Shift+Delete (Windows)
   - Cmd+Shift+Delete (Mac)
   - Or use Incognito window

5. **Check browser console**
   - Look for CORS error details
   - Check Network tab for OPTIONS request
   - Verify response headers

---

## Additional Resources

- [MDN CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Express CORS Package](https://github.com/expressjs/cors)
- [CORS Tester Tool](https://www.test-cors.org/)
