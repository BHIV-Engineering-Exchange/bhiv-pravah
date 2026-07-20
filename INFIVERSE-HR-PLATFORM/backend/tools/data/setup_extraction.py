#!/usr/bin/env python3
"""
Setup script for resume extraction tools
"""
import subprocess
import sys

def install_dependencies():
    """Install required packages"""
    packages = [
        'pandas', 'PyPDF2', 'python-docx', 'spacy', 'nltk'
    ]
    
    for package in packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    # Download spaCy model
    subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'])

if __name__ == "__main__":
    install_dependencies()
    print("✅ Setup complete!")