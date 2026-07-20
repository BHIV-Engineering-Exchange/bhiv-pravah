# Deployment Guide for Render (512MB Limit)

## Problem
Render has a 512MB deployment limit, but the LED model is ~1.4GB. Solution: Download, quantize, and pickle the model locally, then upload the smaller pickle files.

## Steps

### 1. Download and Create Pickle Files (Local Machine)

```bash
cd backend
python download_and_pickle_model.py
```

This will:
- Download the model from HuggingFace
- Quantize it (reduces size by ~4x)
- Save as compressed pickle: `models/led_model_quantized.pkl.gz`
- Also save tokenizer: `models/tokenizer.pkl.gz`

**Expected output:**
- `led_model_quantized.pkl.gz`: ~200-400 MB (instead of 1.4GB)
- `tokenizer.pkl.gz`: ~1-2 MB

### 2. Upload Pickle Files to Render

Upload these files to your Render deployment:
- `backend/models/led_model_quantized.pkl.gz`
- `backend/models/tokenizer.pkl.gz` (if saved separately)

**Methods:**
- **Option A**: Add to git (if under 512MB total)
- **Option B**: Use Render's file upload feature
- **Option C**: Download from cloud storage during deployment

### 3. Deploy on Render

The `PDFSummarizer` will automatically detect and load from pickle files if they exist in `backend/models/`.

## File Structure on Render

```
backend/
├── models/
│   ├── led_model_quantized.pkl.gz  (200-400 MB)
│   └── tokenizer.pkl.gz            (1-2 MB)
├── pdf_summarizer.py
├── main.py
└── ...
```

## Size Reduction

- **Original model**: ~1.4 GB
- **Quantized + Compressed pickle**: ~200-400 MB
- **Reduction**: ~70-85% smaller ✅

## Notes

1. **Quantization**: Uses INT8 quantization (4x size reduction)
2. **Compression**: Gzip compression (additional size reduction)
3. **Performance**: Quantized models run slightly slower but use less memory
4. **Compatibility**: Works on both CPU and GPU

## Troubleshooting

### Pickle file not found
- Make sure files are uploaded to `backend/models/`
- Check file names match exactly

### Out of memory on Render
- Quantized model should fit in 512MB limit
- If still too large, consider using API-based models (Groq/Gemini) instead

### Model loading fails
- Check Python version compatibility
- Ensure all dependencies are installed: `torch`, `transformers`

