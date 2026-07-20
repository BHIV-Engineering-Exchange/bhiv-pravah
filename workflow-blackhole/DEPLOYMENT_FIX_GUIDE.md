# Fix ERR_CONNECTION_REFUSED on Deployed App

## Problem
Frontend deployed on Vercel is trying to connect to `http://localhost:5001`, which doesn't exist from the browser.

```
POST http://localhost:5001/api/biometric-attendance/salary-calculation 
net::ERR_CONNECTION_REFUSED
```

## Solution

You need to deploy your backend and update the API URL in the frontend.

### Step 1: Deploy Backend

Choose one of these options:

#### Option A: Render (Recommended - Free tier available)
1. Go to https://render.com
2. Create new Web Service
3. Connect your GitHub repo
4. Environment: Node
5. Build Command: `npm install && npm install --prefix server && node server/index.js`
6. Note the deployed URL (e.g., `https://workflow-api.onrender.com`)

#### Option B: Railway
1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Add MongoDB URI environment variable
4. Deploy server folder
5. Note the deployed URL

#### Option C: Heroku (Legacy - Still works)
```bash
heroku create your-app-name
heroku config:set MONGODB_URI=your_mongodb_uri
git push heroku main
```

### Step 2: Update Frontend Environment Variable

In `client/.env.production`:
```
VITE_API_URL=https://your-backend-url.com
```

Replace `https://your-backend-url.com` with your actual backend URL (without `/api`).

### Step 3: Redeploy Frontend on Vercel

1. Go to Vercel Dashboard
2. Select your project
3. Settings → Environment Variables
4. Add: `VITE_API_URL = https://your-backend-url.com`
5. Trigger redeploy (or push to main)

### Step 4: Verify

After deployment, check:
- Browser console should show: `🔧 Using VITE_API_URL: https://your-backend-url.com`
- API calls should succeed (no ERR_CONNECTION_REFUSED)

## Files Modified

- `client/src/pages/BiometricAttendanceDashboard.jsx` - Now uses `VITE_API_URL` env var
- `client/.env.production` - Set your backend URL here

## Local Testing

If running locally:
1. Start backend: `cd server && node index.js`
2. Start frontend: `cd client && npm run dev`
3. Frontend will auto-detect backend on `http://localhost:5001`

## Backend Requirements

Ensure your deployed backend has:
- `server/index.js` running on port 5001 (or set PORT env var)
- MongoDB connection configured
- CORS enabled for your Vercel domain
- All required routes:
  - `/api/biometric-attendance/*`
  - `/api/hourly-salary/*`
  - `/api/attendance/*`
  - `/api/enhanced-salary/*`

## Environment Variables for Backend

When deploying backend, set these:

```
MONGODB_URI=your_mongodb_connection_string
PORT=5001
JWT_SECRET=your_jwt_secret
NODE_ENV=production
```
