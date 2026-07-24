#!/usr/bin/env python3
"""
Simple NAS Connection Script for BHIV Knowledge Base
Connect to company NAS server at 192.168.0.94 (Guruukul_DB share)
"""

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_nas():
    """Connect to NAS using credentials from .env file."""
    
    # Get NAS configuration from environment
    nas_ip = os.getenv("NAS_IP", "192.168.0.94")
    nas_share = os.getenv("NAS_SHARE", "Guruukul_DB")
    nas_drive = os.getenv("NAS_DRIVE", "G:")
    nas_username = os.getenv("NAS_USERNAME")
    nas_password = os.getenv("NAS_PASSWORD")
    nas_domain = os.getenv("NAS_DOMAIN", "WORKGROUP")
    
    print("🚀 BHIV Knowledge Base - Simple NAS Connection")
    print("=" * 50)
    
    # Check if using guest access or specific credentials
    use_guest_access = (not nas_username or nas_username == "guest" or not nas_password)

    if use_guest_access:
        print("🔓 Using guest access (no credentials required)")
        nas_username = ""
        nas_password = ""
    else:
        print(f"🔐 Using credentials for user: {nas_username}")

        if nas_username == "your_nas_username_here" or nas_password == "your_nas_password_here":
            print("❌ Please update the NAS credentials in .env file!")
            print("Replace 'your_nas_username_here' and 'your_nas_password_here' with actual values")
            return False
    
    # Test connectivity first
    print(f"🔍 Testing connectivity to {nas_ip}...")
    try:
        result = subprocess.run(
            ["ping", "-n", "3", nas_ip], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode != 0:
            print(f"❌ Cannot reach NAS server {nas_ip}")
            print("Please check your network connection and NAS server status")
            return False
        print(f"✅ NAS server {nas_ip} is reachable")
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False
    
    # Disconnect any existing connection
    print(f"🔄 Disconnecting any existing connection to {nas_drive}...")
    try:
        subprocess.run(["net", "use", nas_drive, "/delete", "/y"], 
                      capture_output=True, text=True)
    except:
        pass  # Ignore errors if no existing connection
    
    # Connect to NAS
    unc_path = f"\\\\{nas_ip}\\{nas_share}"
    print(f"🔗 Connecting to {unc_path} as {nas_drive}...")
    
    try:
        if use_guest_access:
            # Use guest access (no credentials)
            cmd = ["net", "use", nas_drive, unc_path, "/persistent:yes"]
        else:
            # Use specific credentials
            cmd = [
                "net", "use", nas_drive, unc_path,
                f"/user:{nas_domain}\\{nas_username}", nas_password,
                "/persistent:yes"
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully connected to NAS at {nas_drive}")
            
            # Test access
            if test_nas_access(nas_drive):
                print("✅ NAS access verified!")
                
                # Create required folders
                if setup_folders(nas_drive):
                    print("✅ Knowledge base folders created!")
                    print("\n🎉 NAS setup complete!")
                    print("\nNext steps:")
                    print("1. Run: python setup_qdrant.py --start")
                    print("2. Run: python load_data_to_qdrant.py --init")
                    print("3. Test: python cli_runner.py explain 'what is dharma' knowledge_agent")
                    return True
                else:
                    print("⚠️ Warning: Could not create all folders, but connection is working")
                    return True
            else:
                print("❌ Cannot access NAS share")
                return False
        else:
            print(f"❌ Failed to connect: {result.stderr}")
            print("\nPossible issues:")
            print("- Incorrect username/password")
            print("- Wrong domain name")
            print("- Insufficient permissions")
            print("- Network connectivity issues")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_nas_access(drive_letter):
    """Test if we can access the NAS drive."""
    try:
        test_path = Path(drive_letter)
        if test_path.exists():
            # Try to list contents
            list(test_path.iterdir())
            return True
        return False
    except Exception as e:
        print(f"Access test failed: {e}")
        return False

def setup_folders(drive_letter):
    """Create required folders for knowledge base."""
    folders = [
        "qdrant_embeddings",
        "source_documents", 
        "metadata",
        "qdrant_data"
    ]
    
    success = True
    for folder in folders:
        try:
            folder_path = Path(drive_letter) / folder
            folder_path.mkdir(exist_ok=True)
            print(f"📁 Created folder: {folder_path}")
        except Exception as e:
            print(f"❌ Failed to create {folder}: {e}")
            success = False
    
    return success

def check_connection_status():
    """Check current NAS connection status."""
    print("🔍 Checking NAS connection status...")
    
    try:
        result = subprocess.run(["net", "use"], capture_output=True, text=True)
        if "G:" in result.stdout and "192.168.0.94" in result.stdout:
            print("✅ NAS is connected at G: drive")
            
            # Test access
            if test_nas_access("G:"):
                print("✅ NAS access is working")
                return True
            else:
                print("❌ NAS is connected but not accessible")
                return False
        else:
            print("❌ NAS is not connected")
            return False
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        check_connection_status()
    else:
        connect_nas()
