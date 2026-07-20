"""
Upload pickle files to 0x0.st with progress indication
"""

import os
import requests
from pathlib import Path
from tqdm import tqdm

def upload_file_with_progress(file_path: str, description: str = "file") -> str:
    """Upload a file to 0x0.st with progress bar"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"✗ File not found: {file_path}")
        return None
    
    file_size = file_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"\n📤 Uploading {description}...")
    print(f"   File: {file_path.name}")
    print(f"   Size: {file_size_mb:.2f} MB")
    print(f"   Destination: https://0x0.st")
    print()
    
    try:
        # Read file in chunks and upload with progress
        url = "https://0x0.st"
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            
            # Use requests with streaming to show progress
            with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc=f"Uploading {file_path.name}") as pbar:
                # Create a custom file-like object that updates progress
                class ProgressFile:
                    def __init__(self, file_obj, progress_bar):
                        self.file_obj = file_obj
                        self.progress_bar = progress_bar
                        
                    def read(self, size=-1):
                        chunk = self.file_obj.read(size)
                        if chunk:
                            self.progress_bar.update(len(chunk))
                        return chunk
                    
                    def __getattr__(self, name):
                        return getattr(self.file_obj, name)
                
                # Reset file pointer
                f.seek(0)
                progress_file = ProgressFile(f, pbar)
                files = {'file': (file_path.name, progress_file, 'application/octet-stream')}
                
                response = requests.post(url, files=files, timeout=600)
                response.raise_for_status()
        
        # Get the URL from response
        file_url = response.text.strip()
        
        print(f"\n✓ {description} uploaded successfully!")
        print(f"   URL: {file_url}")
        
        return file_url
        
    except requests.exceptions.Timeout:
        print(f"\n✗ Upload timed out. File might be too large or connection is slow.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Upload failed: {str(e)}")
        return None
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return None

def main():
    """Main upload function"""
    print("="*60)
    print("0x0.st File Uploader")
    print("="*60)
    
    # File paths
    model_file = Path(__file__).parent / "led_model_quantized.pkl.gz"
    tokenizer_file = Path(__file__).parent / "tokenizer.pkl.gz"
    
    model_url = None
    tokenizer_url = None
    
    # Upload model file
    if model_file.exists():
        model_url = upload_file_with_progress(str(model_file), "Model pickle file")
        if model_url:
            with open("model_url.txt", "w") as f:
                f.write(model_url)
    else:
        print(f"\n✗ Model file not found: {model_file}")
    
    # Upload tokenizer file
    if tokenizer_file.exists():
        tokenizer_url = upload_file_with_progress(str(tokenizer_file), "Tokenizer pickle file")
        if tokenizer_url:
            with open("tokenizer_url.txt", "w") as f:
                f.write(tokenizer_url)
    else:
        print(f"\n✗ Tokenizer file not found: {tokenizer_file}")
    
    # Summary
    print("\n" + "="*60)
    print("Upload Summary")
    print("="*60)
    
    if model_url:
        print(f"✓ Model URL: {model_url}")
    else:
        print("✗ Model upload failed")
    
    if tokenizer_url:
        print(f"✓ Tokenizer URL: {tokenizer_url}")
    else:
        print("✗ Tokenizer upload failed")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Copy the URLs above")
    print("2. Go to Render Dashboard → Your Service → Environment")
    print("3. Update these environment variables:")
    print()
    if model_url:
        print(f"   MODEL_PICKLE_URL={model_url}")
    if tokenizer_url:
        print(f"   TOKENIZER_PICKLE_URL={tokenizer_url}")
    print()
    print("4. Save and Render will automatically redeploy")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Upload canceled by user")
    except Exception as e:
        print(f"\n\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
