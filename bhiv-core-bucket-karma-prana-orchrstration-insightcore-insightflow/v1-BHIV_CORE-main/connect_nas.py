#!/usr/bin/env python3
"""
NAS Connection Script for BHIV Knowledge Base
Connect to company NAS server at 192.168.0.94 (Guruukul_DB share)
"""

import os
import sys
import subprocess
import platform
import time
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

class NASConnector:
    """Connect to company NAS server for knowledge base access."""
    
    def __init__(self):
        self.system = platform.system()
        self.nas_ip = "192.168.0.94"
        self.share_name = "Guruukul_DB"
        self.drive_letter = "G:"
        self.unc_path = f"\\\\{self.nas_ip}\\{self.share_name}"
        
    def check_nas_connectivity(self) -> bool:
        """Check if NAS server is reachable."""
        logger.info(f"🔍 Testing connectivity to NAS server {self.nas_ip}...")
        
        try:
            if self.system == "Windows":
                # Use ping to test connectivity
                result = subprocess.run(
                    ["ping", "-n", "3", self.nas_ip], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"✅ NAS server {self.nas_ip} is reachable")
                    return True
                else:
                    logger.error(f"❌ NAS server {self.nas_ip} is not reachable")
                    return False
            else:
                # Linux ping
                result = subprocess.run(
                    ["ping", "-c", "3", self.nas_ip], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                return result.returncode == 0
                
        except Exception as e:
            logger.error(f"❌ Connectivity test failed: {e}")
            return False
    
    def check_existing_connection(self) -> bool:
        """Check if NAS is already connected."""
        try:
            if self.system == "Windows":
                # Check if drive is already mapped
                if os.path.exists(f"{self.drive_letter}\\"):
                    logger.info(f"✅ Drive {self.drive_letter} already mapped")
                    return True
                
                # Check net use output
                result = subprocess.run(
                    ["net", "use"], 
                    capture_output=True, 
                    text=True
                )
                if self.nas_ip in result.stdout:
                    logger.info(f"✅ NAS connection already exists")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to check existing connection: {e}")
            return False
    
    def connect_to_nas(self, username: str, password: str, domain: str = "WORKGROUP") -> bool:
        """Connect to the NAS server."""
        logger.info(f"🔗 Connecting to NAS: {self.unc_path}")
        
        try:
            if self.system == "Windows":
                # Disconnect existing connection first
                self.disconnect_nas()
                
                # Build net use command
                if username and password:
                    cmd = [
                        "net", "use", self.drive_letter, self.unc_path,
                        f"/user:{domain}\\{username}", password, "/persistent:yes"
                    ]
                else:
                    cmd = ["net", "use", self.drive_letter, self.unc_path, "/persistent:yes"]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ Successfully connected to NAS at {self.drive_letter}")
                    return True
                else:
                    logger.error(f"❌ Failed to connect: {result.stderr}")
                    return False
                    
            elif self.system == "Linux":
                # Create mount point
                mount_point = f"/mnt/guruukul_db"
                os.makedirs(mount_point, exist_ok=True)
                
                # Mount command
                if username and password:
                    cmd = [
                        "sudo", "mount", "-t", "cifs",
                        f"//{self.nas_ip}/{self.share_name}",
                        mount_point,
                        "-o", f"username={username},password={password},domain={domain}"
                    ]
                else:
                    cmd = [
                        "sudo", "mount", "-t", "cifs",
                        f"//{self.nas_ip}/{self.share_name}",
                        mount_point,
                        "-o", "guest"
                    ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def disconnect_nas(self) -> bool:
        """Disconnect from NAS."""
        try:
            if self.system == "Windows":
                # Try to disconnect the drive
                result = subprocess.run(
                    ["net", "use", self.drive_letter, "/delete", "/y"],
                    capture_output=True, text=True
                )
                # Don't treat this as an error if it fails (drive might not be connected)
                return True
                
        except Exception as e:
            logger.debug(f"Disconnect attempt: {e}")
            return True
    
    def test_nas_access(self) -> bool:
        """Test if we can access the NAS share."""
        try:
            if self.system == "Windows":
                test_path = f"{self.drive_letter}\\"
            else:
                test_path = "/mnt/guruukul_db"
            
            if os.path.exists(test_path):
                # Try to list contents
                contents = os.listdir(test_path)
                logger.info(f"✅ NAS accessible. Found {len(contents)} items")
                logger.info(f"📁 Contents: {', '.join(contents[:5])}")
                return True
            else:
                logger.error(f"❌ NAS path not accessible: {test_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ NAS access test failed: {e}")
            return False
    
    def setup_knowledge_base_folders(self) -> bool:
        """Create necessary folders for knowledge base on NAS."""
        try:
            if self.system == "Windows":
                base_path = f"{self.drive_letter}\\"
            else:
                base_path = "/mnt/guruukul_db"
            
            folders = [
                "qdrant_embeddings",
                "source_documents", 
                "metadata",
                "qdrant_data"
            ]
            
            for folder in folders:
                folder_path = os.path.join(base_path, folder)
                os.makedirs(folder_path, exist_ok=True)
                logger.info(f"📁 Created/verified folder: {folder_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create folders: {e}")
            return False

def main():
    """Main function to connect to NAS."""
    print("🚀 BHIV Knowledge Base - NAS Connection Setup")
    print("=" * 50)
    
    connector = NASConnector()
    
    # Step 1: Check connectivity
    if not connector.check_nas_connectivity():
        print("❌ Cannot reach NAS server. Please check:")
        print("  - Network connection")
        print("  - NAS server is powered on")
        print("  - IP address is correct (192.168.0.94)")
        return False
    
    # Step 2: Check existing connection
    if connector.check_existing_connection():
        print("✅ NAS already connected!")
        if connector.test_nas_access():
            print("🎉 NAS access verified!")
            return True
    
    # Step 3: Get credentials
    print("\n🔐 NAS Authentication Required")
    username = input("Enter NAS username: ").strip()
    password = input("Enter NAS password: ").strip()
    domain = input("Enter domain (or press Enter for WORKGROUP): ").strip() or "WORKGROUP"
    
    # Step 4: Connect
    if connector.connect_to_nas(username, password, domain):
        print("✅ Successfully connected to NAS!")
        
        # Step 5: Test access
        if connector.test_nas_access():
            print("✅ NAS access verified!")
            
            # Step 6: Setup folders
            if connector.setup_knowledge_base_folders():
                print("✅ Knowledge base folders ready!")
                print("\n🎉 NAS setup complete!")
                print("\nNext steps:")
                print("1. Run: python setup_qdrant.py --start")
                print("2. Run: python load_data_to_qdrant.py --init")
                print("3. Test: python cli_runner.py explain 'what is dharma' knowledge_agent")
                return True
            else:
                print("❌ Failed to setup folders")
                return False
        else:
            print("❌ Cannot access NAS share")
            return False
    else:
        print("❌ Failed to connect to NAS")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
