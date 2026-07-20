"""
Download model pickle files on startup if they don't exist
This runs automatically when the app starts on Render
"""

import os
import requests
import re
import gdown
from pathlib import Path
import sys

def convert_google_drive_url(url: str) -> str:
    """Convert Google Drive share URL to direct download URL"""
    if "drive.google.com" in url:
        # Extract file ID from various Google Drive URL formats
        file_id = None
        
        # Format 1: https://drive.google.com/file/d/FILE_ID/view
        if "/file/d/" in url:
            file_id = url.split("/file/d/")[1].split("/")[0]
        # Format 2: https://drive.google.com/open?id=FILE_ID
        elif "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
        # Format 3: Already direct download format
        elif "uc?export=download" in url:
            return url
        
        if file_id:
            # Convert to direct download URL
            direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            print(f"[Download] Converted Google Drive URL to direct download format")
            return direct_url
    
    return url

def download_file(url: str, filepath: Path, description: str = "file", expected_min_size_mb: float = 1.0):
    """Download a file from URL with validation - uses gdown for Google Drive"""
    try:
        # Check if it's a Google Drive URL
        if "drive.google.com" in url:
            print(f"[Download] Detected Google Drive URL. Using gdown library to handle virus scan warning...")
            
            # Extract file ID from URL
            file_id = None
            if "/file/d/" in url:
                file_id = url.split("/file/d/")[1].split("/")[0]
            elif "id=" in url:
                file_id = url.split("id=")[1].split("&")[0]
            
            if file_id:
                # Use gdown which handles Google Drive's virus scan warning automatically
                gdrive_url = f"https://drive.google.com/uc?id={file_id}"
                print(f"[Download] Downloading {description} from Google Drive (ID: {file_id})...")
                
                try:
                    gdown.download(gdrive_url, str(filepath), quiet=False, fuzzy=True)
                    
                    if not filepath.exists():
                        print(f"[Download] ✗ File was not downloaded")
                        return False
                    
                    file_size_mb = filepath.stat().st_size / (1024 * 1024)
                    
                    # Validate file size
                    if file_size_mb < expected_min_size_mb:
                        print(f"[Download] ✗ ERROR: Downloaded file is too small ({file_size_mb:.2f} MB). Expected at least {expected_min_size_mb:.2f} MB.")
                        print(f"[Download] This usually means the URL is incorrect or the file is corrupted.")
                        filepath.unlink()  # Delete corrupted file
                        return False
                    
                    print(f"[Download] ✓ {description} downloaded successfully! ({file_size_mb:.2f} MB)")
                    return True
                except Exception as e:
                    print(f"[Download] ✗ gdown failed: {str(e)}")
                    print(f"[Download] Falling back to manual download method...")
                    # Fall through to manual method
            else:
                print(f"[Download] ✗ Could not extract file ID from Google Drive URL")
                return False
        
        # Fallback: Manual download for non-Google Drive URLs
        print(f"[Download] Downloading {description} from {url}...")
        response = requests.get(url, stream=True, timeout=300, allow_redirects=True)
        response.raise_for_status()
        
        # Check if we got HTML instead of a file
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' in content_type:
            print(f"[Download] ⚠ WARNING: Received HTML instead of file. URL might be incorrect.")
            return False
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if downloaded % (10 * 1024 * 1024) == 0:  # Print every 10 MB
                            print(f"[Download] {description}: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
        
        file_size_mb = filepath.stat().st_size / (1024 * 1024)
        
        # Validate file size
        if file_size_mb < expected_min_size_mb:
            print(f"[Download] ✗ ERROR: Downloaded file is too small ({file_size_mb:.2f} MB). Expected at least {expected_min_size_mb:.2f} MB.")
            filepath.unlink()  # Delete corrupted file
            return False
        
        print(f"[Download] ✓ {description} downloaded successfully! ({file_size_mb:.2f} MB)")
        return True
    except Exception as e:
        print(f"[Download] ✗ Failed to download {description}: {str(e)}")
        if filepath.exists():
            filepath.unlink()  # Delete partial/corrupted file
        return False

def ensure_models_exist():
    """Ensure model pickle files exist, download if missing"""
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    model_file = models_dir / "led_model_quantized.pkl.gz"
    tokenizer_file = models_dir / "tokenizer.pkl.gz"
    
    # Get download URLs from environment variables
    model_url = os.getenv("MODEL_PICKLE_URL")
    tokenizer_url = os.getenv("TOKENIZER_PICKLE_URL")
    
    # Check if files already exist
    if model_file.exists() and tokenizer_file.exists():
        model_size = model_file.stat().st_size / (1024 * 1024)
        tokenizer_size = tokenizer_file.stat().st_size / (1024 * 1024)
        print(f"[Models] Model files already exist:")
        print(f"  - led_model_quantized.pkl.gz: {model_size:.2f} MB")
        print(f"  - tokenizer.pkl.gz: {tokenizer_size:.2f} MB")
        return True
    
    # If URLs are provided, download files
    if model_url and tokenizer_url:
        print("[Models] Model files not found. Downloading from URLs...")
        success = True
        
        if not model_file.exists():
            success = download_file(model_url, model_file, "model pickle", expected_min_size_mb=100.0) and success
        
        if not tokenizer_file.exists():
            success = download_file(tokenizer_url, tokenizer_file, "tokenizer pickle", expected_min_size_mb=0.3) and success
        
        if success:
            print("[Models] ✓ All model files downloaded successfully!")
            return True
        else:
            print("[Models] ⚠ Some files failed to download. App will use HuggingFace fallback.")
            return False
    else:
        print("[Models] ⚠ Model files not found and download URLs not configured.")
        print("[Models] Set MODEL_PICKLE_URL and TOKENIZER_PICKLE_URL environment variables.")
        print("[Models] App will use HuggingFace fallback (may be slow).")
        return False

if __name__ == "__main__":
    ensure_models_exist()

