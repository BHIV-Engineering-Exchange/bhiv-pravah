# Login & Signup Troubleshooting Guide

## Current Status ✅
- **Server**: Running on port 5000 ✅
- **Client**: Running on port 5174 ✅
- **MongoDB**: Connected ✅
- **API URL**: `http://localhost:5000/api` ✅

## Common Login/Signup Errors & Solutions

### 1. "Invalid email or password" Error

**Causes:**
- User doesn't exist in database
- Wrong password
- Email format incorrect
- Network/API connection issue

**Solutions:**

#### a) First Time User - Create Account
1. Go to signup/register page
2. Fill in all required fields:
   - Name
   - Email (valid format)
   - Password (minimum 6 characters)
   - Role (User/Manager/Admin)
   - Department (if User role)
3. Click "Sign Up"
4. Check console for errors (F12)

#### b) Existing User - Check Credentials
1. Verify email is correct
2. Try password reset if needed
3. Check if account exists in database

### 2. "Network Error" or No Response

**Causes:**
- Server not running
- Wrong API URL
- CORS issues
- Firewall blocking

**Solutions:**

#### Check Servers Running:
```powershell
# Check if port 5000 is open (server)
Get-NetTCPConnection -LocalPort 5000

# Check if port 5174 is open (client)
Get-NetTCPConnection -LocalPort 5174
```

#### Start Servers:
```powershell
# Terminal 1: Start Server
cd C:\Users\Microsoft\Desktop\Complete-Infiverse-2\server
node index.js

# Terminal 2: Start Client
cd C:\Users\Microsoft\Desktop\Complete-Infiverse-2\client
npm run dev
```

### 3. CORS Error in Console

**Error Message:**
```
Access to XMLHttpRequest at 'http://localhost:5000/api/auth/login' 
from origin 'http://localhost:5174' has been blocked by CORS policy
```

**Solution:**
This is already configured correctly. If you see this:
1. Restart the server
2. Clear browser cache
3. Check `server/.env` has correct CORS settings

### 4. MongoDB Connection Timeout

**Error Message:**
```
Error: connect ETIMEDOUT
```

**Solution:**
Already fixed! The server is now using the working MongoDB connection.

### 5. "Registration failed" Error

**Common Causes:**
- Email already exists
- Missing required fields
- Invalid email format
- Password too short

**Solutions:**
1. Use a unique email address
2. Fill all required fields
3. Use proper email format: user@domain.com
4. Password must be at least 6 characters
5. Select a valid role
6. If role is "User", select a department

## Testing Login/Signup

### Test User Creation (if no users exist)

Open browser console (F12) and run:
```javascript
// Test API endpoint
fetch('http://localhost:5000/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Test Admin',
    email: '<your_email>',
    password: '<your_password>',
    role: 'Admin'
  })
})
.then(res => res.json())
.then(data => console.log('✅ Registration:', data))
.catch(err => console.error('❌ Error:', err));
```

### Test Login

```javascript
fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: '<your_email>',
    password: '<your_password>'
  })
})
.then(res => res.json())
.then(data => console.log('✅ Login:', data))
.catch(err => console.error('❌ Error:', err));
```

## Step-by-Step: Create Your First Account

### Via Browser UI:

1. **Open the app**: http://localhost:5174

2. **Go to Signup page**: 
   - Look for "Sign Up" or "Register" link
   - Usually at bottom of login page or `/signup` route

3. **Fill the form**:
   ```
   Name: Your Full Name
   Email: youremail@example.com
   Password: <your_password> (min 6 chars)
   Role: Admin (for testing)
   ```

4. **Submit**:
   - Click "Sign Up" or "Register" button
   - Wait for success message
   - Should auto-redirect to dashboard

5. **If successful**:
   - You'll be logged in automatically
   - Token saved in localStorage
   - Redirected to dashboard

### Via PowerShell (Direct API Test):

```powershell
# Test registration
$body = @{
    name = "Test Admin"
    email = "<your_email>"
    password = "<your_password>"
    role = "Admin"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/auth/register" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Test login
$loginBody = @{
    email = "<your_email>"
    password = "<your_password>"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginBody
```

## Checking Browser Console for Errors

1. **Open DevTools**: Press `F12` or `Ctrl+Shift+I`
2. **Go to Console tab**
3. **Look for errors** (red text)
4. **Common error patterns**:
   - `Network Error` → Server not running
   - `404 Not Found` → Wrong API URL
   - `500 Internal Server Error` → Server-side issue
   - `CORS Error` → CORS configuration issue

## Verifying Your Setup

### Check Client .env:
```bash
# File: client/.env
VITE_API_URL=http://localhost:5000/api
VITE_SOCKET_URL=http://localhost:5000
```

### Check Auth Context:
Open browser console and run:
```javascript
localStorage.getItem('WorkflowToken')    // Should show token if logged in
localStorage.getItem('WorkflowUser')     // Should show user JSON if logged in
```

### Clear Stored Data (if stuck):
```javascript
localStorage.clear()  // Clears all stored data
location.reload()     // Reload page
```

## Current Configuration

### API URLs:
- **Production**: https://blackholeworkflow.onrender.com/api
- **Local Development**: http://localhost:5000/api
- **Current Active**: http://localhost:5000/api ✅

### Auth Endpoints:
- **Register**: `POST /api/auth/register`
- **Login**: `POST /api/auth/login`
- **Logout**: Client-side only (clears localStorage)

### Required Fields:

**Registration:**
```json
{
  "name": "string (required)",
  "email": "string (required, valid email)",
  "password": "string (required, min 6 chars)",
  "role": "Admin|Manager|User (required)",
  "department": "string (required if role=User)"
}
```

**Login:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

## Quick Fixes

### Fix 1: Clear Everything and Restart
```powershell
# Kill all node processes
Get-Process node | Stop-Process -Force

# Start fresh
cd C:\Users\Microsoft\Desktop\Complete-Infiverse-2\server
node index.js

# In another terminal
cd C:\Users\Microsoft\Desktop\Complete-Infiverse-2\client
npm run dev
```

### Fix 2: Reset Browser State
1. Open DevTools (F12)
2. Go to Application tab
3. Storage → Local Storage
4. Delete all items
5. Refresh page (F5)

### Fix 3: Check Server Logs
When you try to login/signup, watch the server terminal for:
- Request received
- MongoDB queries
- Error messages
- Response sent

## Contact Support

If issues persist:
1. Take screenshot of browser console error
2. Copy server terminal output
3. Note the exact error message
4. Share the route you're trying to access

---

**Servers Running:**
- Backend: http://localhost:5000 ✅
- Frontend: http://localhost:5174 ✅
- MongoDB: Connected ✅

**Next Steps:**
1. Open http://localhost:5174/login
2. Try logging in or create new account
3. Check browser console (F12) for errors
4. Share error message if issues persist
