# Git Sync Troubleshooting Guide

## Problem Summary

1. **Origin remote not found** - URL has typo (`blackholeinfiverse51` instead of `blackholeinfiverse64`)
2. **Upstream push rejected** - Local branch is behind remote

---

## Quick Fix (Recommended)

Run the automated script:

```powershell
cd C:\Users\A\Desktop\ai-artha\AI-Artha
.\git-fix.bat
```

Choose option **1 (Merge)** when prompted.

---

## Manual Fix (Step-by-Step)

### Step 1: Check Current Remotes

```powershell
git remote -v
```

**Expected output:**
```
origin    https://github.com/blackholeinfiverse51/AI-Artha.git (fetch)
origin    https://github.com/blackholeinfiverse51/AI-Artha.git (push)
upstream  https://github.com/blackholeinfiverse64/AI-Artha.git (fetch)
upstream  https://github.com/blackholeinfiverse64/AI-Artha.git (push)
```

### Step 2: Fix Origin Remote

```powershell
# Remove incorrect origin
git remote remove origin

# Add correct origin
git remote add origin https://github.com/blackholeinfiverse64/AI-Artha.git

# Verify
git remote -v
```

### Step 3: Fetch Latest Changes

```powershell
git fetch upstream
git fetch origin
```

### Step 4: Check Status

```powershell
git status
```

### Step 5: Sync with Upstream

**Option A: Merge (Recommended)**
```powershell
# Merge upstream changes into your local branch
git merge upstream/main

# If no conflicts, push to both remotes
git push origin main
git push upstream main
```

**Option B: Rebase (Clean History)**
```powershell
# Rebase your commits on top of upstream
git rebase upstream/main

# Force push (use with caution)
git push origin main --force-with-lease
git push upstream main --force-with-lease
```

**Option C: Pull and Push**
```powershell
# Pull from upstream (fetch + merge)
git pull upstream main

# Push to both remotes
git push origin main
git push upstream main
```

---

## If You Get Merge Conflicts

### During Merge

```powershell
# Check which files have conflicts
git status

# Open conflicted files and resolve manually
# Look for markers: <<<<<<<, =======, >>>>>>>

# After resolving, stage the files
git add .

# Complete the merge
git commit -m "Merge upstream changes"

# Push to remotes
git push origin main
git push upstream main
```

### During Rebase

```powershell
# Check which files have conflicts
git status

# Resolve conflicts in files

# Stage resolved files
git add .

# Continue rebase
git rebase --continue

# If you want to abort
git rebase --abort

# After successful rebase, force push
git push origin main --force-with-lease
git push upstream main --force-with-lease
```

---

## Understanding Your Setup

### What are Origin and Upstream?

- **origin**: Your fork (blackholeinfiverse64/AI-Artha)
- **upstream**: Original repository (also blackholeinfiverse64/AI-Artha in your case)

Since both point to the same repo, you might only need one remote.

### Simplify to Single Remote

If origin and upstream are the same:

```powershell
# Remove upstream
git remote remove upstream

# Use only origin
git push origin main
```

---

## Common Scenarios

### Scenario 1: You Have Local Commits Not on Remote

```powershell
# Pull remote changes first
git pull origin main --rebase

# Push your commits
git push origin main
```

### Scenario 2: Remote Has Commits You Don't Have

```powershell
# Fetch and merge
git pull origin main

# Or fetch and rebase
git pull origin main --rebase
```

### Scenario 3: Diverged Histories

```powershell
# See the divergence
git log --oneline --graph --all

# Option 1: Merge
git pull origin main

# Option 2: Rebase
git pull origin main --rebase

# Option 3: Force push (DANGEROUS)
git push origin main --force
```

---

## Verification Commands

### Check Remote URLs
```powershell
git remote -v
```

### Check Branch Status
```powershell
git status
git branch -vv
```

### Check Commit History
```powershell
git log --oneline -10
git log --oneline --graph --all -10
```

### Check Differences
```powershell
# Compare local with remote
git diff origin/main

# Compare local with upstream
git diff upstream/main
```

---

## Prevention Tips

### Before Pushing

1. **Always pull first**
   ```powershell
   git pull origin main
   ```

2. **Check status**
   ```powershell
   git status
   ```

3. **Verify remotes**
   ```powershell
   git remote -v
   ```

### Set Up Aliases

Add to `.gitconfig`:

```ini
[alias]
    sync = !git pull origin main && git push origin main
    check = !git remote -v && git status
    graph = log --oneline --graph --all -20
```

Usage:
```powershell
git sync
git check
git graph
```

---

## Emergency Recovery

### If Everything Goes Wrong

```powershell
# Create a backup branch
git branch backup-$(date +%Y%m%d)

# Reset to remote state
git fetch origin
git reset --hard origin/main

# Or reset to upstream
git fetch upstream
git reset --hard upstream/main
```

### Restore from Backup

```powershell
# List backups
git branch | grep backup

# Restore from backup
git checkout backup-20240315
git checkout -b main-restored
```

---

## Current Recommended Action

Based on your error, here's what you should do **RIGHT NOW**:

```powershell
# 1. Fix origin remote
git remote remove origin
git remote add origin https://github.com/blackholeinfiverse64/AI-Artha.git

# 2. Pull latest changes
git pull upstream main

# 3. Push to both remotes
git push origin main
git push upstream main
```

If step 2 shows conflicts, resolve them before step 3.

---

## Need Help?

If you're still stuck:

1. Run this and share output:
   ```powershell
   git remote -v
   git status
   git log --oneline -5
   git log --oneline origin/main -5
   git log --oneline upstream/main -5
   ```

2. Check if you have uncommitted changes:
   ```powershell
   git diff
   git diff --staged
   ```

3. Verify your current branch:
   ```powershell
   git branch
   ```

---

**Last Updated:** 2024-03-15  
**Version:** 1.0.0
