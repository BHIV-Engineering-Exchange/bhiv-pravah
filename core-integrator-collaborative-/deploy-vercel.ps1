#!/usr/bin/env pwsh
<#
Vercel Deployment Script
Deploy BHIV Core Integrator to Vercel in 1 command
#>

param(
    [string]$ProjectName = "bhiv-core-integrator",
    [string]$Team = ""
)

Write-Host "`n" -ForegroundColor Green
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   BHIV Core Integrator - Vercel Deployment        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`n"

# Step 1: Check prerequisites
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

$required = @("git", "vercel")
foreach ($cmd in $required) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "❌ $cmd is not installed or not in PATH" -ForegroundColor Red
        if ($cmd -eq "vercel") {
            Write-Host "   Install: npm install -g vercel" -ForegroundColor Yellow
        }
        exit 1
    }
    Write-Host "   ✅ $cmd found" -ForegroundColor Green
}

# Step 2: Verify Vercel config
Write-Host "`n[2/5] Verifying Vercel configuration..." -ForegroundColor Yellow
if (!(Test-Path "vercel.json")) {
    Write-Host "❌ vercel.json not found" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ vercel.json found" -ForegroundColor Green

# Step 3: Stage and commit
Write-Host "`n[3/5] Staging changes for git..." -ForegroundColor Yellow
git add vercel.json api/ requirements-vercel.txt .env.vercel
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git add failed" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Changes staged" -ForegroundColor Green

# Step 4: Deploy to Vercel
Write-Host "`n[4/5] Deploying to Vercel..." -ForegroundColor Yellow
if ($Team) {
    vercel --scope=$Team --prod --name=$ProjectName
} else {
    vercel --prod --name=$ProjectName
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Vercel deployment failed" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Deployed to Vercel" -ForegroundColor Green

# Step 5: Configure environment variables
Write-Host "`n[5/5] Setting environment variables..." -ForegroundColor Yellow
Write-Host "   📋 You must manually set these in Vercel Dashboard:" -ForegroundColor Cyan
Write-Host "      Settings → Environment Variables" -ForegroundColor Cyan
Write-Host "`n   Required variables:" -ForegroundColor Yellow
Write-Host "   • GROQ_API_KEY" -ForegroundColor Gray
Write-Host "   • MONGODB_CONNECTION_STRING" -ForegroundColor Gray
Write-Host "   • AWS_ACCESS_KEY_ID" -ForegroundColor Gray
Write-Host "   • AWS_SECRET_ACCESS_KEY" -ForegroundColor Gray
Write-Host "   • AWS_S3_BUCKET" -ForegroundColor Gray
Write-Host "`n   See .env.vercel for all variables" -ForegroundColor Gray

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "`n🔗 Your Vercel URL will be displayed above" -ForegroundColor Cyan
Write-Host "   API endpoints:" -ForegroundColor Cyan
Write-Host "   • https://your-domain.vercel.app/api/creator-core" -ForegroundColor Gray
Write-Host "   • https://your-domain.vercel.app/api/bhiv-core" -ForegroundColor Gray
Write-Host "   • https://your-domain.vercel.app/api/bucket" -ForegroundColor Gray
Write-Host "   • https://your-domain.vercel.app/api/prompt-runner" -ForegroundColor Gray
Write-Host "`n"
