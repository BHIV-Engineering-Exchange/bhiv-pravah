#!/usr/bin/env python3
"""
Test script to access NAS using Windows UNC path
"""

import os
import pathlib
from pathlib import Path

def test_windows_path():
    """Test accessing NAS using Windows UNC path"""
    
    # Windows UNC path to the NAS share
    nas_path = r"\\192.168.0.94\Guruukul_DB"
    
    print(f"Testing access to: {nas_path}")
    
    try:
        # Method 1: Using os.listdir
        print("\n=== Method 1: Using os.listdir ===")
        files = os.listdir(nas_path)
        print("✅ SUCCESS with os.listdir!")
        print("Files and folders:")
        for file in files:
            full_path = os.path.join(nas_path, file)
            is_dir = os.path.isdir(full_path)
            print(f"  - {file} ({'DIR' if is_dir else 'FILE'})")
        
        return True
        
    except Exception as e1:
        print(f"❌ os.listdir failed: {e1}")
        
        try:
            # Method 2: Using pathlib
            print("\n=== Method 2: Using pathlib ===")
            path = Path(nas_path)
            if path.exists():
                print("✅ Path exists!")
                if path.is_dir():
                    print("✅ Path is a directory!")
                    files = list(path.iterdir())
                    print("Files and folders:")
                    for file in files:
                        print(f"  - {file.name} ({'DIR' if file.is_dir() else 'FILE'})")
                    return True
                else:
                    print("❌ Path is not a directory")
            else:
                print("❌ Path does not exist")
                
        except Exception as e2:
            print(f"❌ pathlib failed: {e2}")
            
            try:
                # Method 3: Using os.path.exists
                print("\n=== Method 3: Using os.path.exists ===")
                if os.path.exists(nas_path):
                    print("✅ Path exists with os.path.exists!")
                    return True
                else:
                    print("❌ Path does not exist with os.path.exists")
                    
            except Exception as e3:
                print(f"❌ os.path.exists failed: {e3}")
    
    return False

def test_file_operations():
    """Test basic file operations on the NAS"""
    
    nas_path = r"\\192.168.0.94\Guruukul_DB"
    
    try:
        # Test reading a file if it exists
        test_file = os.path.join(nas_path, "env")
        if os.path.exists(test_file):
            print(f"\n=== Testing file read: {test_file} ===")
            with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(100)  # Read first 100 characters
                print(f"✅ File read successful! First 100 chars: {content[:100]}")
        
        # Test creating a test file
        test_write_file = os.path.join(nas_path, "python_test.txt")
        print(f"\n=== Testing file write: {test_write_file} ===")
        with open(test_write_file, 'w') as f:
            f.write("Test from Python - BHIV Knowledge Base Connection Test")
        print("✅ File write successful!")
        
        # Test reading it back
        with open(test_write_file, 'r') as f:
            content = f.read()
            print(f"✅ File read back successful: {content}")
        
        # Clean up test file
        os.remove(test_write_file)
        print("✅ Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Windows UNC path access to NAS...")
    
    if test_windows_path():
        print("\n" + "="*50)
        print("🎉 SUCCESS! NAS is accessible via Windows path")
        print("="*50)
        
        # Test file operations
        test_file_operations()
        
    else:
        print("\n" + "="*50)
        print("❌ FAILED! Cannot access NAS via Windows path")
        print("="*50)
