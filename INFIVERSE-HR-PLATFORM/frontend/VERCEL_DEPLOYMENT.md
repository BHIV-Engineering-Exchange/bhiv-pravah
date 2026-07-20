# Vercel Deployment Guide for Sampada (HR Recruitment System) Frontend

This guide will walk you through deploying the Sampada frontend to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free tier available)
2. **GitHub Account**: Your code should be in a GitHub repository
3. **Backend Services**: Already deployed on Render (as provided)

## Step 1: Prepare Your Repository

### 1.1 Ensure Code is Committed
```bash
cd frontend
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### 1.2 Verify Build Works Locally
```bash
cd frontend
npm install
npm run build
```

If the build succeeds, you're ready to deploy!

## Step 2: Deploy to Vercel

### Option A: Deploy via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit [vercel.com](https://vercel.com)
   - Click "Add New Project"

2. **Import Your Repository**
   - Connect your GitHub account if not already connected
   - Select your repository containing the frontend code
   - Click "Import"

3. **Configure Project Settings**
   - **Framework Preset**: Vite (or select "Other" if Vite not available)
   - **Root Directory**: `frontend` (if your frontend is in a subdirectory)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

4. **Add Environment Variables**
   Click "Environment Variables" and add the following:

   ```
   VITE_API_BASE_URL=https://bhiv-hr-gateway-l0xp.onrender.com
   VITE_AGENT_SERVICE_URL=https://bhiv-hr-agent-cato.onrender.com
   VITE_LANGGRAPH_SERVICE_URL=https://bhiv-hr-langgraph-luy9.onrender.com
   VITE_ENABLE_CONTROL_CENTER=true
   VITE_API_KEY=<YOUR_API_KEY>
   VITE_ENABLE_GOVERNANCE=true
   ```

   **Important**: 
   - Add these for **Production**, **Preview**, and **Development** environments
   - Use the same `API_KEY_SECRET` value configured on the Render gateway (never commit real keys to git)

5. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete (usually 2-3 minutes)

### Option B: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Navigate to Frontend Directory**
   ```bash
   cd frontend
   ```

4. **Deploy**
   ```bash
   vercel
   ```
   
   Follow the prompts:
   - Link to existing project or create new
   - Confirm settings
   - Add environment variables when prompted

5. **Add Environment Variables via CLI**
   ```bash
   vercel env add VITE_API_BASE_URL
   # Enter: https://bhiv-hr-gateway-l0xp.onrender.com
   
   vercel env add VITE_AGENT_SERVICE_URL
   # Enter: https://bhiv-hr-agent-cato.onrender.com
   
   vercel env add VITE_LANGGRAPH_SERVICE_URL
   # Enter: https://bhiv-hr-langgraph-luy9.onrender.com

   vercel env add VITE_ENABLE_CONTROL_CENTER
   # Enter: true
   
   vercel env add VITE_API_KEY
   # Enter: <YOUR_API_KEY> (matches Render API_KEY_SECRET)

   vercel env add VITE_ENABLE_GOVERNANCE
   # Enter: true
   ```

6. **Redeploy with Environment Variables**
   ```bash
   vercel --prod
   ```

## Step 3: Verify Deployment

1. **Check Build Logs**
   - Go to your project in Vercel dashboard
   - Check the "Deployments" tab
   - Verify build completed successfully

2. **Test Your Application**
   - Visit your Vercel deployment URL (e.g., `your-app.vercel.app`)
   - Test key functionalities:
     - Login/Authentication
     - API calls to backend
     - Dashboard loading
     - Form submissions

3. **Check Browser Console**
   - Open browser DevTools (F12)
   - Check for any CORS errors or API connection issues
   - Verify API calls are going to correct endpoints

## Step 4: Configure Custom Domain (Optional)

1. **Add Domain in Vercel**
   - Go to Project Settings → Domains
   - Add your custom domain
   - Follow DNS configuration instructions

2. **Update Environment Variables**
   - If your backend services need to allow your new domain, update CORS settings

## Step 5: Continuous Deployment

Vercel automatically deploys on every push to your main branch:
- **Production**: Deploys from `main` branch
- **Preview**: Deploys from pull requests and other branches

## Troubleshooting

### Build Fails

1. **Check Build Logs**
   - Look for specific error messages
   - Common issues:
     - Missing dependencies
     - TypeScript errors
     - Environment variable issues

2. **Common Fixes**
   ```bash
   # Clear node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   
   # Check for TypeScript errors
   npm run build
   ```

### API Calls Failing

1. **Check Environment Variables**
   - Verify all environment variables are set in Vercel
   - Ensure URLs are correct (no trailing slashes)
   - Check API key is correct

2. **Check CORS Settings**
   - Ensure backend services allow your Vercel domain
   - Check backend CORS configuration

3. **Check Network Tab**
   - Open browser DevTools → Network tab
   - Check if API calls are being made
   - Look for CORS or 404 errors

### Routing Issues (404 on Refresh)

The `vercel.json` file should handle this, but if you see 404 errors:
- Verify `vercel.json` exists in frontend directory
- Check that rewrites are configured correctly

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Main Gateway API URL | `https://bhiv-hr-gateway-l0xp.onrender.com` |
| `VITE_AGENT_SERVICE_URL` | AI Agent Service URL | `https://bhiv-hr-agent-cato.onrender.com` |
| `VITE_LANGGRAPH_SERVICE_URL` | LangGraph Service URL | `https://bhiv-hr-langgraph-luy9.onrender.com` |
| `VITE_ENABLE_CONTROL_CENTER` | Show Command Center nav + `/control` | `true` |
| `VITE_ENABLE_GOVERNANCE` | Show Governance tab in Control Center | `true` |
| `VITE_API_KEY` | Backend API Authentication Key | `<YOUR_API_KEY>` |

## Control Center verification

After deploy, verify control center wiring:

```bash
# From backend/ — loads .env; requires API_KEY_SECRET
python tests/e2e/control_center/run_comprehensive_evaluation.py
```

Manual: log in as client/recruiter/admin → navigate to `/control` → confirm service health cards show Render URLs and KPI data loads.

See `docs/control-center-evaluation-report.md` for the latest evaluation results.

## Support

If you encounter issues:
1. Check Vercel build logs
2. Check browser console for errors
3. Verify backend services are running on Render
4. Test API endpoints directly using Postman/curl

## Next Steps

After successful deployment:
- Set up monitoring and analytics
- Configure custom domain
- Set up staging environment
- Enable preview deployments for pull requests

