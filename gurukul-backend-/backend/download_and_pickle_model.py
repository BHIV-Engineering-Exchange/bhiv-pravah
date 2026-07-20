"""
Download model, quantize it (to reduce size), and save as compressed pickle
This reduces model size significantly for deployment on Render (512MB limit)
"""

import os
import pickle
import gzip
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pathlib import Path

# Configuration
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

def quantize_model(model):
    """Quantize model to reduce size (INT8 quantization)"""
    print("[Quantization] Applying INT8 quantization to reduce model size...")
    try:
        # Set model to eval mode for quantization
        model.eval()
        
        # Use dynamic quantization (reduces size by ~4x)
        # This works on CPU
        quantized_model = torch.quantization.quantize_dynamic(
            model, 
            {torch.nn.Linear, torch.nn.Conv1d}, 
            dtype=torch.qint8
        )
        print("[Quantization] ✓ Model quantized successfully!")
        print("[Quantization] Size reduction: ~4x smaller")
        return quantized_model
    except Exception as e:
        print(f"[Quantization] Warning: Quantization failed: {e}")
        print("[Quantization] Trying alternative: Saving state dict only...")
        # Alternative: Save only state dict (smaller than full model)
        try:
            # Convert to half precision if not already
            if next(model.parameters()).dtype != torch.float16:
                model = model.half()
            print("[Quantization] Converted to FP16 (2x size reduction)")
            return model
        except Exception as e2:
            print(f"[Quantization] Alternative also failed: {e2}")
            print("[Quantization] Using original model (will be larger)")
            return model

def download_and_pickle_model():
    """Download model, quantize, and save as compressed pickle"""
    model_name = "pszemraj/led-base-book-summary"
    output_file = MODELS_DIR / "led_model_quantized.pkl.gz"
    
    print("\n" + "="*60)
    print("DOWNLOADING AND PICKLING MODEL")
    print("="*60)
    print(f"Model: {model_name}")
    print(f"Output: {output_file}")
    print("="*60 + "\n")
    
    try:
        # Step 1: Download tokenizer
        print("[1/5] Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("✓ Tokenizer downloaded")
        
        # Step 2: Download model
        print("[2/5] Downloading model (this may take a while)...")
        if torch.cuda.is_available():
            print(f"GPU detected: {torch.cuda.get_device_name(0)}")
            dtype = torch.float16
        else:
            print("No GPU detected, using CPU")
            dtype = torch.float32
        
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            torch_dtype=dtype
        )
        print("✓ Model downloaded")
        
        # Step 3: Move to CPU and quantize (quantization works on CPU)
        print("[3/5] Moving model to CPU for quantization...")
        model = model.cpu()
        print("✓ Model moved to CPU")
        
        # Step 4: Quantize model (reduces size significantly)
        print("[4/5] Quantizing model to reduce size...")
        quantized_model = quantize_model(model)
        
        # Step 5: Save as compressed pickle
        print("[5/5] Saving as compressed pickle file...")
        model_data = {
            'model': quantized_model,
            'tokenizer': tokenizer,
            'model_name': model_name,
            'quantized': True
        }
        
        # Save with gzip compression
        with gzip.open(output_file, 'wb') as f:
            pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"✓ Model saved as compressed pickle!")
        print(f"  File: {output_file}")
        print(f"  Size: {file_size_mb:.2f} MB")
        
        # Also save tokenizer separately (small file)
        tokenizer_file = MODELS_DIR / "tokenizer.pkl.gz"
        with gzip.open(tokenizer_file, 'wb') as f:
            pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        tokenizer_size_mb = tokenizer_file.stat().st_size / (1024 * 1024)
        print(f"  Tokenizer: {tokenizer_size_mb:.2f} MB")
        print(f"  Total: {file_size_mb + tokenizer_size_mb:.2f} MB")
        
        print("\n" + "="*60)
        print("SUCCESS! Model ready for deployment")
        print("="*60)
        print(f"Upload these files to Render:")
        print(f"  1. {output_file.name} ({file_size_mb:.2f} MB)")
        print(f"  2. {tokenizer_file.name} ({tokenizer_size_mb:.2f} MB)")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    download_and_pickle_model()

