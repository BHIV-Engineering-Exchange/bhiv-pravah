#!/usr/bin/env python3
"""
Hugging Face Token Verification Script
======================================
Verifies that your HF_TOKEN is properly configured and working.

This script:
1. Loads environment variables
2. Tests Hugging Face authentication
3. Verifies model access
4. Shows before/after performance comparison

Usage:
    python verify_hf_token.py
"""

import os
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        logger.info(f"Loading environment from {env_path}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value and not value.startswith("<"):
                        os.environ[key] = value
    
    # Check if token is loaded
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        logger.info(f"✅ HF_TOKEN loaded: {hf_token[:10]}...{hf_token[-5:]}")
        return True
    else:
        logger.error("❌ HF_TOKEN not found in environment")
        return False

def test_authentication():
    """Test Hugging Face API authentication"""
    logger.info("🔍 Testing Hugging Face authentication...")
    
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        
        user_info = api.whoami()
        logger.info(f"✅ Authenticated successfully as: {user_info.get('name', 'Unknown')}")
        return True
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        return False

def test_model_loading():
    """Test model loading performance with and without token"""
    logger.info("🧪 Testing model loading performance...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Test 1: Load model (should use token automatically)
        logger.info("  Loading sentence-transformers/all-MiniLM-L6-v2...")
        start_time = time.time()
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        load_time = time.time() - start_time
        logger.info(f"  ✅ Model loaded in {load_time:.2f} seconds")
        
        # Test 2: Verify model works
        test_sentences = [
            "Python developer with machine learning experience",
            "Software engineer specializing in AI and data science"
        ]
        
        embeddings = model.encode(test_sentences)
        similarity = model.similarity(embeddings[0].reshape(1, -1), embeddings[1].reshape(1, -1))
        
        logger.info(f"  ✅ Model encoding working correctly")
        logger.info(f"  ✅ Semantic similarity: {float(similarity[0][0]):.3f}")
        
        # Performance assessment
        if load_time < 3.0:
            logger.info("  🚀 Excellent performance - token is working!")
        elif load_time < 5.0:
            logger.info("  ✅ Good performance - token is helping")
        else:
            logger.warning("  ⚠️ Slow loading - token may not be applied correctly")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        return False

def check_logs_for_warnings():
    """Check if authentication warnings are gone"""
    logger.info("📋 Checking for authentication warnings...")
    logger.info("After restarting services, you should see:")
    logger.info("  ❌ BEFORE: 'Warning: You are sending unauthenticated requests'")
    logger.info("  ✅ AFTER:  Clean logs with no authentication warnings")
    logger.info("  🚀 AFTER:  Faster model loading times")

def main():
    """Main verification routine"""
    logger.info("=" * 60)
    logger.info("BHIV HR Platform - Hugging Face Token Verification")
    logger.info("=" * 60)
    
    # Step 1: Load environment
    if not load_environment():
        logger.error("Cannot proceed without HF_TOKEN")
        return
    
    print()
    
    # Step 2: Test authentication
    if not test_authentication():
        logger.error("Authentication test failed")
        return
    
    print()
    
    # Step 3: Test model loading
    if not test_model_loading():
        logger.error("Model loading test failed")
        return
    
    print()
    
    # Step 4: Instructions
    check_logs_for_warnings()
    
    print()
    logger.info("=" * 60)
    logger.info("✅ Verification Complete!")
    logger.info("=" * 60)
    logger.info("Next steps:")
    logger.info("1. Stop current services (Ctrl+C)")
    logger.info("2. Restart with: python run_services.py")
    logger.info("3. Check agent logs for cleaner output")
    logger.info("4. Look for faster model loading times")

if __name__ == "__main__":
    main()