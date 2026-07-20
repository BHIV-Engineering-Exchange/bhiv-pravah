# VERCEL DEPLOYMENT GUIDE

## Quick Start (3 Steps)

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Deploy
```bash
# Option A: Use the deployment script (Recommended)
./deploy-vercel.ps1

# Option B: Manual deployment
vercel --prod
```

### Step 3: Set Environment Variables
Go to https://vercel.com/dashboard → Your Project → Settings → Environment Variables

Add these variables:
```
GROQ_API_KEY=your_key_here
MONGODB_CONNECTION_STRING=mongodb+srv://...
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your-bucket
```

---

## What Gets Deployed

Your BHIV services as serverless functions:

```
https://your-project.vercel.app/
  ├── /api/creator-core        (Blueprint generation)
  ├── /api/bhiv-core           (Blueprint execution)
  ├── /api/bucket              (Artifact storage)
  └── /api/prompt-runner       (Prompt conversion)
```

---

## Architecture Changes

### Before (Local):
```
localhost:8000 → Creator Core
localhost:8001 → BHIV Core
localhost:8003 → Prompt Runner
localhost:8005 → Bucket
```

### After (Vercel):
```
https://your-domain.vercel.app/api/creator-core
https://your-domain.vercel.app/api/bhiv-core
https://your-domain.vercel.app/api/prompt-runner
https://your-domain.vercel.app/api/bucket
```

---

## File Structure

```
project/
├── api/                      # Serverless functions
│   ├── creator-core.py      # Blueprint generator
│   ├── bhiv-core.py         # Blueprint executor
│   ├── bucket.py            # Storage service
│   └── prompt-runner.py     # Prompt converter
├── vercel.json              # Vercel configuration
├── requirements-vercel.txt  # Python dependencies
├── .env.vercel              # Environment template
└── deploy-vercel.ps1        # Deployment script
```

---

## External Services (Required)

### Database: MongoDB Atlas
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free cluster
3. Get connection string
4. Add to `MONGODB_CONNECTION_STRING`

### Storage: AWS S3
1. Go to https://aws.amazon.com/
2. Create S3 bucket
3. Get access keys
4. Add to `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

### LLM: Groq API
1. Go to https://console.groq.com
2. Get API key
3. Add to `GROQ_API_KEY`

---

## Testing After Deployment

```bash
# Test health endpoints
curl https://your-project.vercel.app/api/creator-core/health
curl https://your-project.vercel.app/api/bhiv-core/health
curl https://your-project.vercel.app/api/bucket/health
curl https://your-project.vercel.app/api/prompt-runner/health

# Test endpoints
curl -X POST https://your-project.vercel.app/api/creator-core/creator-core/generate-blueprint \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "module": "education"}'
```

---

## Troubleshooting

### Build fails
- Check `requirements-vercel.txt` has all dependencies
- Verify Python version is 3.11+
- Check for import errors in api/*.py

### Functions timeout
- Vercel has 60s limit
- Long operations will fail
- Use job queues for heavy processing

### Environment variables not loading
- Verify variables are set in Vercel dashboard
- Re-deploy after adding variables: `vercel --prod`
- Check `.env.vercel` for required variables

### Database connection fails
- Verify MongoDB connection string
- Check network access in MongoDB Atlas
- Ensure MongoDB_USER and password are URL-encoded

---

## Cost Estimate

- **Vercel**: Free tier (144,000 function invocations/month)
- **MongoDB Atlas**: Free tier (512MB)
- **AWS S3**: Pay-as-you-go (~$0.023 per GB)

---

## Rollback

```bash
# Go back to previous deployment
vercel rollback

# Or redeploy from git
git push origin main
```

---

## Next Steps

1. ✅ Deploy with `./deploy-vercel.ps1`
2. ✅ Add environment variables in Vercel dashboard
3. ✅ Test each API endpoint
4. ✅ Monitor Vercel logs: `vercel logs`
5. ✅ Set up GitHub integration for auto-deploy
