# Setup Notes for Sovereign Fusion Layer

## Important: Install Dependencies First

Before running the system, make sure to install all dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### Key Dependencies

The following dependencies are required for the Sovereign Fusion Layer:

- `peft>=0.8.0` - For LoRA adapter loading
- `accelerate>=0.24.0` - For model loading
- `pytest>=7.4.0` - For running tests
- `torch>=2.0.0` - For model inference
- `transformers>=4.30.0` - For model loading

## Verification

After installing dependencies, run the verification script:

```bash
python verify_sovereign.py
```

This will check:
- ✓ All imports work correctly
- ✓ Configuration files exist
- ✓ Basic functionality works
- ✓ Database models are properly defined

## Model Setup

The system expects `checkpoint_info.pkl` in the project root with:
- `checkpoint_path`: Path to your fine-tuned model checkpoint
- `base_model_name`: Base model identifier (e.g., "unsloth/llama-3.2-3b-instruct-bnb-4bit")

## Database Setup

The system will automatically create database tables on startup. Make sure:
- Database is configured (via `DATABASE_URL` environment variable)
- Or SQLite will be used as fallback

## Known Issues

1. **peft not installed**: Run `pip install -r requirements.txt`
2. **Model checkpoint not found**: Ensure `checkpoint_info.pkl` exists in project root
3. **Database connection failed**: Check `DATABASE_URL` or SQLite file permissions

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Verify setup: `python verify_sovereign.py`
3. Start server: `uvicorn app.main:app --reload`
4. Test health: `curl http://localhost:8000/api/v1/sovereign/health`

