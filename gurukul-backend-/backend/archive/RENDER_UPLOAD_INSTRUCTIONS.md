# How to Upload Pickle Files to Render

## Problem
GitHub has a 100MB file size limit, but `led_model_quantized.pkl.gz` is 202.35 MB. So we can't push it via git.

## Solution: Upload Directly to Render

### Option 1: Render Shell/SSH (Recommended)

1. **Get SSH access to your Render service**
   - Go to your Render dashboard
   - Click on your service
   - Find "Shell" or "SSH" option

2. **Create models directory**
   ```bash
   mkdir -p backend/models
   ```

3. **Upload files using SCP or SFTP**
   ```bash
   # From your local machine
   scp backend/models/led_model_quantized.pkl.gz user@your-render-service.onrender.com:/opt/render/project/src/backend/models/
   scp backend/models/tokenizer.pkl.gz user@your-render-service.onrender.com:/opt/render/project/src/backend/models/
   ```

### Option 2: Render File System (If Available)

1. Go to Render dashboard → Your service
2. Look for "File System" or "Upload Files" option
3. Navigate to `backend/models/` directory
4. Upload both `.pkl.gz` files

### Option 3: Build Script Download

Create a build script that downloads from cloud storage:

1. **Upload to cloud storage** (S3, Google Drive, etc.)
2. **Add to Render build command:**
   ```bash
   # In Render build command
   pip install -r requirements.txt && \
   wget https://your-storage-url/led_model_quantized.pkl.gz -O backend/models/led_model_quantized.pkl.gz && \
   wget https://your-storage-url/tokenizer.pkl.gz -O backend/models/tokenizer.pkl.gz
   ```

### Option 4: Render Environment Variables + Download Script

1. Store file URLs in environment variables
2. Create a startup script that downloads files if they don't exist

## Files to Upload

- `backend/models/led_model_quantized.pkl.gz` (202.35 MB)
- `backend/models/tokenizer.pkl.gz` (0.53 MB)

## Verify Upload

After uploading, verify files exist:
```bash
ls -lh backend/models/
```

You should see both `.pkl.gz` files.

## Testing

Once uploaded, the `PDFSummarizer` will automatically detect and use these files. No code changes needed!

