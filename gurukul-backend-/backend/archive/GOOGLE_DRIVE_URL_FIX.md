# Fix Google Drive URLs - IMPORTANT!

## Problem
Your current URLs are downloading HTML pages instead of the actual files. The files are only 0.05 MB instead of 202.35 MB!

## Current URLs (WRONG):
```
https://drive.google.com/file/d/1py7o2sbFRF-o6UabvOsfEtZyq0GcaKMR/view?usp=sharing
https://drive.google.com/file/d/1THEp3th1BMfAHQ42JfbfkxolRXBS1NlH/view?usp=sharing
```

## How to Fix

### Step 1: Get the File IDs
From your current URLs, extract the file IDs:
- Model: `1py7o2sbFRF-o6UabvOsfEtZyq0GcaKMR`
- Tokenizer: `1THEp3th1BMfAHQ42JfbfkxolRXBS1NlH`

### Step 2: Convert to Direct Download URLs
Replace in Render Environment Variables:

**MODEL_PICKLE_URL:**
```
https://drive.google.com/uc?export=download&id=1py7o2sbFRF-o6UabvOsfEtZyq0GcaKMR
```

**TOKENIZER_PICKLE_URL:**
```
https://drive.google.com/uc?export=download&id=1THEp3th1BMfAHQ42JfbfkxolRXBS1NlH
```

### Step 3: Update in Render
1. Go to Render Dashboard → Your Service → Environment
2. Update both URLs with the format above
3. Save and redeploy

## Alternative: Use Different Hosting

If Google Drive doesn't work, try:
- **0x0.st** - https://0x0.st (drag & drop, get direct link)
- **Transfer.sh** - https://transfer.sh (command line)
- **GitHub Releases** - If you have a private repo

## Verification

After redeploy, check logs. You should see:
```
[Download] ✓ model pickle downloaded successfully! (202.35 MB)
[Download] ✓ tokenizer pickle downloaded successfully! (0.53 MB)
```

NOT:
```
[Download] ✓ model pickle downloaded successfully! (0.05 MB)  ← WRONG!
```

