#!/usr/bin/env python3
"""
Setup script for BHIV HR Platform Advanced Tools
Installs dependencies and downloads required models
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"{description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_advanced_tools():
    """Setup advanced resume extraction tools"""
    
    print("BHIV HR Platform - Advanced Tools Setup")
    print("=" * 50)
    
    # Create necessary directories (logs and data only - assets/resumes already exists)
    directories = [
        "logs",
        "data"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Verify assets/resumes exists
    if os.path.exists("assets/resumes"):
        print("Found existing assets/resumes directory")
    else:
        print("Warning: assets/resumes directory not found")
    
    # Install Python dependencies
    print("\nInstalling Python dependencies...")
    
    # Core requirements
    core_packages = [
        "pandas>=2.0.0",
        "numpy>=1.24.0", 
        "PyPDF2>=3.0.0",
        "python-docx>=0.8.11",
        "psycopg2-binary>=2.9.0",
        "sqlalchemy>=2.0.0"
    ]
    
    for package in core_packages:
        if not run_command(f"pip install {package}", f"Installing {package.split('>=')[0]}"):
            print(f"⚠️ Failed to install {package}")
    
    # NLP packages
    print("\nInstalling NLP packages...")
    nlp_packages = [
        "spacy>=3.7.0",
        "nltk>=3.8.0"
    ]
    
    for package in nlp_packages:
        if not run_command(f"pip install {package}", f"Installing {package.split('>=')[0]}"):
            print(f"⚠️ Failed to install {package}")
    
    # Download spaCy model with verification
    print("\nDownloading spaCy English model...")
    if run_command("python -m spacy download en_core_web_sm", "Downloading spaCy model"):
        # Verify spaCy model installation
        verify_script = '''
import spacy
try:
    nlp = spacy.load("en_core_web_sm")
    print("spaCy model verified successfully")
except OSError:
    print("spaCy model verification failed")
    exit(1)
'''
        with open("temp_spacy_verify.py", "w") as f:
            f.write(verify_script)
        run_command("python temp_spacy_verify.py", "Verifying spaCy model")
        if os.path.exists("temp_spacy_verify.py"):
            os.remove("temp_spacy_verify.py")
    
    # Download NLTK data
    print("\nDownloading NLTK data...")
    nltk_script = '''
import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True) 
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    print("NLTK data downloaded successfully")
except Exception as e:
    print(f"NLTK download error: {e}")
'''
    
    with open("temp_nltk_setup.py", "w") as f:
        f.write(nltk_script)
    
    run_command("python temp_nltk_setup.py", "Downloading NLTK data")
    
    # Cleanup
    if os.path.exists("temp_nltk_setup.py"):
        os.remove("temp_nltk_setup.py")
    
    # Optional advanced packages
    print("\nInstalling optional advanced packages...")
    optional_packages = [
        "scikit-learn>=1.3.0",
        "sentence-transformers>=2.2.0",
        "email-validator>=2.1.0",
        "phonenumbers>=8.13.0"
    ]
    
    for package in optional_packages:
        run_command(f"pip install {package}", f"Installing {package.split('>=')[0]} (optional)")
    
    # Verify installation
    print("\nVerifying installation...")
    
    verification_script = '''
import sys
packages_to_check = [
    "pandas", "numpy", "PyPDF2", "docx", "spacy", "nltk", 
    "psycopg2", "sqlalchemy", "sklearn"
]

missing_packages = []
for package in packages_to_check:
    try:
        __import__(package)
        print(f"OK {package}")
    except ImportError:
        print(f"MISSING {package}")
        missing_packages.append(package)

if missing_packages:
    print(f"\\nMissing packages: {', '.join(missing_packages)}")
    sys.exit(1)
else:
    print("\\nAll core packages installed successfully!")
'''
    
    with open("temp_verify.py", "w") as f:
        f.write(verification_script)
    
    run_command("python temp_verify.py", "Verifying installation")
    
    # Cleanup
    if os.path.exists("temp_verify.py"):
        os.remove("temp_verify.py")
    
    print("\n" + "=" * 50)
    print("Advanced Tools Setup Complete!")
    print("\nNext Steps:")
    print("1. Resume files are already in assets/resumes/ directory")
    print("2. Run: python tools/data/advanced_resume_extractor.py")
    print("3. Check data/candidates.csv for extracted data")
    print("4. Use tools/database/load_candidates.py to sync to database")
    
    print("\nAvailable Tools:")
    print("- Advanced Resume Extractor: tools/data/advanced_resume_extractor.py")
    print("- Database Loader: tools/database/load_candidates.py")
    print("- Original Extractor: tools/data/comprehensive_resume_extractor.py")

if __name__ == "__main__":
    setup_advanced_tools()