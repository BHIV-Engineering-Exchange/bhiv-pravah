# Upload Pickle Files to Cloud Storage for Render

Since Render's shell is paid and GitHub has a 100MB limit, we'll upload the pickle files to free cloud storage and download them automatically during deployment.

## Step 1: Upload Files to Cloud Storage

Choose one of these free options:

### Option A: Google Drive (Recommended - Easy)

1. **Upload files to Google Drive:**
   - Go to https://drive.google.com
   - Upload `led_model_quantized.pkl.gz` (202.35 MB)
   - Upload `tokenizer.pkl.gz` (0.53 MB)

2. **Get shareable links:**
   - Right-click each file → "Share" → "Anyone with the link"
   - Copy the link
   - Convert to direct download link:
     - Replace `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`
     - With: `https://drive.google.com/uc?export=download&id=FILE_ID`
     - (Extract FILE_ID from the share link)

3. **Set in Render Environment Variables:**
   ```
   MODEL_PICKLE_URL=https://drive.google.com/uc?export=download&id=YOUR_FILE_ID
   TOKENIZER_PICKLE_URL=https://drive.google.com/uc?export=download&id=YOUR_FILE_ID
   ```

### Option B: Dropbox

1. **Upload to Dropbox**
2. **Get shareable link**
3. **Convert to direct download:**
   - Replace `www.dropbox.com` with `dl.dropboxusercontent.com`
   - Remove `?dl=0` and add `?dl=1`
4. **Set in Render Environment Variables**

### Option C: GitHub Releases (If you have a private repo)

1. Create a new release
2. Upload files as release assets
3. Get direct download URLs
4. Set in Render Environment Variables

### Option D: Free File Hosting Services

- **0x0.st** - https://0x0.st (drag & drop, get direct link)
- **File.io** - https://file.io (temporary, but works)
- **Transfer.sh** - https://transfer.sh (command line)

## Step 2: Set Environment Variables in Render

1. Go to your Render dashboard
2. Select your service
3. Go to "Environment" tab
4. Add these variables:

```
MODEL_PICKLE_URL=https://your-direct-download-url-here
TOKENIZER_PICKLE_URL=https://your-direct-download-url-here
```

## Step 3: Deploy

The app will automatically:
1. Check if pickle files exist
2. Download them from the URLs if missing
3. Use them for summarization

## Verification

After deployment, check the logs. You should see:
```
[Models] Model files not found. Downloading from URLs...
[Download] Downloading model pickle from...
[Download] ✓ model pickle downloaded successfully!
```

## Troubleshooting

### Files not downloading?
- Check URLs are direct download links (not preview pages)
- Verify files are publicly accessible
- Check Render logs for error messages

### Download too slow?
- Use a faster hosting service (S3, etc.)
- Or manually upload via Render's file system (if available)

### Still too large?
- The files are already quantized and compressed
- Consider using API-based models (Groq/Gemini) instead

