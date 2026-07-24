#!/usr/bin/env python3
"""
Company NAS Setup Script for BHIV Knowledge Base
Configure your company's NAS server for Vedabase storage
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

class CompanyNASSetup:
    """Setup and configure company NAS for BHIV Knowledge Base."""
    
    def __init__(self):
        self.system = platform.system()
        self.company_nas_configs = {
            # Update these with your actual company NAS details
            "windows": {
                "unc_path": "\\\\your-company-nas\\vedabase",
                "mapped_drive": "Y:",
                "credentials_required": True,
                "mount_command": "net use Y: \\\\your-company-nas\\vedabase"
            },
            "linux": {
                "mount_point": "/mnt/company-nas/vedabase",
                "nas_address": "your-company-nas.local",
                "share_name": "vedabase",
                "credentials_required": True,
                "mount_command": "sudo mount -t cifs //your-company-nas.local/vedabase /mnt/company-nas/vedabase"
            }
        }
    
    def detect_nas_configuration(self):
        """Detect existing NAS configuration."""
        print(f"🔍 [NAS DETECTION] Scanning for company NAS configuration...")
        
        if self.system == "Windows":
            return self._detect_windows_nas()
        elif self.system == "Linux":
            return self._detect_linux_nas()
        else:
            print(f"❌ [UNSUPPORTED] {self.system} not supported")
            return False
    
    def _detect_windows_nas(self):
        """Detect Windows NAS mounts."""
        print(f"🪟 [WINDOWS] Checking for mapped drives and UNC paths...")
        
        # Check for mapped drives
        try:
            result = subprocess.run(['net', 'use'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"📋 [MAPPED DRIVES] Current mappings:")
                print(result.stdout)
                
                # Check if our target drive is already mapped
                if "Y:" in result.stdout:
                    print(f"✅ [FOUND] Y: drive is already mapped")
                    return True
            
            # Check UNC path accessibility
            test_paths = [
                "\\\\your-company-nas\\vedabase",
                "\\\\company-nas\\shared\\vedabase",
                "\\\\nas\\vedabase"
            ]
            
            for path in test_paths:
                if os.path.exists(path):
                    print(f"✅ [ACCESSIBLE] {path}")
                    return True
                else:
                    print(f"❌ [NOT ACCESSIBLE] {path}")
            
            return False
            
        except Exception as e:
            print(f"❌ [ERROR] Failed to detect Windows NAS: {e}")
            return False
    
    def _detect_linux_nas(self):
        """Detect Linux NAS mounts."""
        print(f"🐧 [LINUX] Checking for mounted NAS shares...")
        
        try:
            # Check mounted filesystems
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"📋 [MOUNTS] Current mounts:")
                nas_mounts = [line for line in result.stdout.split('\n') if 'cifs' in line or 'nfs' in line]
                for mount in nas_mounts:
                    print(f"  {mount}")
                
                # Check if our target mount exists
                if any('/mnt/company-nas' in mount for mount in nas_mounts):
                    print(f"✅ [FOUND] Company NAS is mounted")
                    return True
            
            # Check potential mount points
            test_paths = [
                "/mnt/company-nas/vedabase",
                "/mnt/nas/vedabase",
                "/media/nas/vedabase"
            ]
            
            for path in test_paths:
                if os.path.exists(path):
                    print(f"✅ [ACCESSIBLE] {path}")
                    return True
                else:
                    print(f"❌ [NOT ACCESSIBLE] {path}")
            
            return False
            
        except Exception as e:
            print(f"❌ [ERROR] Failed to detect Linux NAS: {e}")
            return False
    
    def setup_nas_access(self, nas_address, share_name, username=None, password=None):
        """Setup NAS access for the company."""
        print(f"🔧 [SETUP] Configuring NAS access...")
        print(f"📡 [NAS] Address: {nas_address}")
        print(f"📁 [SHARE] Name: {share_name}")
        
        if self.system == "Windows":
            return self._setup_windows_nas(nas_address, share_name, username, password)
        elif self.system == "Linux":
            return self._setup_linux_nas(nas_address, share_name, username, password)
        else:
            print(f"❌ [UNSUPPORTED] {self.system} not supported")
            return False
    
    def _setup_windows_nas(self, nas_address, share_name, username, password):
        """Setup Windows NAS mapping."""
        try:
            unc_path = f"\\\\{nas_address}\\{share_name}"
            
            # Build net use command
            cmd = ['net', 'use', 'Y:', unc_path]
            if username and password:
                cmd.extend([f'/user:{username}', password])
            elif username:
                cmd.extend([f'/user:{username}'])
            
            print(f"🔗 [MAPPING] Mapping Y: to {unc_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ [SUCCESS] Y: drive mapped successfully")
                return True
            else:
                print(f"❌ [FAILED] Mapping failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ [ERROR] Windows NAS setup failed: {e}")
            return False
    
    def _setup_linux_nas(self, nas_address, share_name, username, password):
        """Setup Linux NAS mounting."""
        try:
            mount_point = f"/mnt/company-nas/{share_name}"
            nas_path = f"//{nas_address}/{share_name}"
            
            # Create mount point
            os.makedirs(mount_point, exist_ok=True)
            
            # Build mount command
            cmd = ['sudo', 'mount', '-t', 'cifs', nas_path, mount_point]
            if username and password:
                cmd.extend(['-o', f'username={username},password={password}'])
            elif username:
                cmd.extend(['-o', f'username={username}'])
            
            print(f"🔗 [MOUNTING] Mounting {nas_path} to {mount_point}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ [SUCCESS] NAS mounted successfully")
                return True
            else:
                print(f"❌ [FAILED] Mounting failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ [ERROR] Linux NAS setup failed: {e}")
            return False
    
    def test_nas_access(self):
        """Test NAS access and create test files."""
        print(f"🧪 [TESTING] Testing NAS access...")
        
        test_paths = [
            "Y:\\vedabase" if self.system == "Windows" else "/mnt/company-nas/vedabase",
            "\\\\your-company-nas\\vedabase" if self.system == "Windows" else "/mnt/nas/vedabase"
        ]
        
        for path in test_paths:
            try:
                if os.path.exists(path):
                    print(f"✅ [ACCESSIBLE] {path}")
                    
                    # Try to create a test file
                    test_file = os.path.join(path, "bhiv_test.txt")
                    try:
                        with open(test_file, 'w') as f:
                            f.write("BHIV Knowledge Base Test File")
                        print(f"✅ [WRITE TEST] Can write to {path}")
                        
                        # Clean up test file
                        os.remove(test_file)
                        print(f"✅ [CLEANUP] Test file removed")
                        return True
                        
                    except PermissionError:
                        print(f"⚠️  [READ-ONLY] {path} is read-only")
                        return True  # Read-only is acceptable
                    except Exception as e:
                        print(f"❌ [WRITE FAILED] Cannot write to {path}: {e}")
                else:
                    print(f"❌ [NOT ACCESSIBLE] {path}")
            except Exception as e:
                print(f"❌ [ERROR] Testing {path} failed: {e}")
        
        return False
    
    def generate_nas_config(self, nas_address, share_name):
        """Generate configuration file for the detected NAS."""
        config = {
            "company_nas": {
                "address": nas_address,
                "share_name": share_name,
                "system": self.system,
                "paths": {
                    "windows": f"\\\\{nas_address}\\{share_name}",
                    "linux": f"/mnt/company-nas/{share_name}",
                    "mapped_drive": "Y:" if self.system == "Windows" else None
                }
            }
        }
        
        config_file = "config/company_nas.json"
        os.makedirs("config", exist_ok=True)
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ [CONFIG] NAS configuration saved to {config_file}")
        return config_file


def main():
    """Interactive NAS setup."""
    print(f"🏢 [COMPANY NAS SETUP] BHIV Knowledge Base NAS Configuration")
    print(f"=" * 60)
    
    setup = CompanyNASSetup()
    
    # Step 1: Detect existing configuration
    if setup.detect_nas_configuration():
        print(f"✅ [DETECTED] Existing NAS configuration found")
        if setup.test_nas_access():
            print(f"🎉 [SUCCESS] NAS is ready for BHIV Knowledge Base!")
            return
    
    # Step 2: Interactive setup
    print(f"\n🔧 [MANUAL SETUP] Let's configure your company NAS...")
    
    nas_address = input("Enter your company NAS address (e.g., company-nas.local): ").strip()
    share_name = input("Enter the share name for Vedabase (e.g., vedabase): ").strip()
    
    use_credentials = input("Does your NAS require credentials? (y/n): ").strip().lower() == 'y'
    username = None
    password = None
    
    if use_credentials:
        username = input("Username: ").strip()
        password = input("Password: ").strip()
    
    # Step 3: Setup NAS access
    if setup.setup_nas_access(nas_address, share_name, username, password):
        print(f"✅ [SETUP COMPLETE] NAS access configured")
        
        # Step 4: Test access
        if setup.test_nas_access():
            print(f"🎉 [SUCCESS] NAS is ready for BHIV Knowledge Base!")
            
            # Step 5: Generate config
            setup.generate_nas_config(nas_address, share_name)
            
            print(f"\n📋 [NEXT STEPS]:")
            print(f"1. Copy your Vedic PDFs to the NAS share")
            print(f"2. Run: python load_data_to_qdrant.py --init --load-pdfs")
            print(f"3. Test: python cli_runner.py explain 'what is dharma' knowledge_agent")
        else:
            print(f"❌ [FAILED] NAS access test failed")
    else:
        print(f"❌ [FAILED] NAS setup failed")


if __name__ == "__main__":
    main()
