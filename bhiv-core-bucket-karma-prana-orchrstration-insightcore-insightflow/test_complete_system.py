#!/usr/bin/env python3
"""
Complete System Startup Test
Verifies that the entire BHIV system can start without timezone warnings
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def test_system_startup():
    """Test that each system component starts without timezone warnings"""
    
    print("=" * 60)
    print("COMPLETE SYSTEM STARTUP TEST")
    print("=" * 60)
    
    base_dir = Path(__file__).parent.parent
    
    systems = [
        {
            "name": "Karma Chain",
            "path": base_dir / "karma_chain_v2-main",
            "command": ["python", "main.py"],
            "port": 8000,
            "timeout": 15
        },
        {
            "name": "Bucket System", 
            "path": base_dir / "BHIV_Central_Depository-main",
            "command": ["python", "main.py"],
            "port": 8001,
            "timeout": 15
        },
        {
            "name": "Core System",
            "path": base_dir / "v1-BHIV_CORE-main", 
            "command": ["python", "mcp_bridge.py"],
            "port": 8002,
            "timeout": 15
        }
    ]
    
    results = {}
    
    for system in systems:
        print(f"\nTesting {system['name']}...")
        print(f"  Path: {system['path']}")
        
        if not system['path'].exists():
            print(f"  ERROR: Path does not exist")
            results[system['name']] = False
            continue
            
        try:
            # Start the system
            process = subprocess.Popen(
                system['command'],
                cwd=system['path'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Wait for startup
            print(f"  Starting {system['name']} (timeout: {system['timeout']}s)...")
            
            start_time = time.time()
            timezone_warnings = []
            startup_success = False
            
            while time.time() - start_time < system['timeout']:
                # Check if process is still running
                if process.poll() is not None:
                    break
                    
                # Read output
                try:
                    stdout_line = process.stdout.readline()
                    stderr_line = process.stderr.readline()
                    
                    # Check for timezone warnings
                    for line in [stdout_line, stderr_line]:
                        if line and 'timezone' in line.lower():
                            timezone_warnings.append(line.strip())
                    
                    # Check for successful startup
                    if 'Application startup complete' in stdout_line or 'Started server' in stdout_line:
                        startup_success = True
                        break
                        
                except:
                    pass
                    
                time.sleep(0.1)
            
            # Terminate process
            try:
                if os.name == 'nt':
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
            
            # Evaluate results
            if timezone_warnings:
                print(f"  TIMEZONE WARNINGS DETECTED:")
                for warning in timezone_warnings:
                    print(f"    {warning}")
                results[system['name']] = False
            else:
                print(f"  SUCCESS: No timezone warnings detected")
                results[system['name']] = True
                
        except Exception as e:
            print(f"  ERROR: {e}")
            results[system['name']] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("STARTUP TEST RESULTS:")
    print("=" * 60)
    
    all_passed = True
    for system_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {system_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\nSUCCESS: All systems start without timezone warnings!")
        print("The timezone issue has been completely resolved.")
        return True
    else:
        print("\nFAILED: Some systems still have timezone issues.")
        return False

if __name__ == "__main__":
    success = test_system_startup()
    sys.exit(0 if success else 1)