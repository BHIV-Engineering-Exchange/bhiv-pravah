"""
start.py — Orchestrator Redirection Script for Gurukul integration.

Redirects startup calls from Gurukul Orchestrator to the standalone Vaani V1 Sentinel.
"""

import sys
import os
import subprocess

def main():
    python_exe = sys.executable
    standalone_dir = r"c:\Users\soham\OneDrive\Desktop\Vanni"
    sentinel_path = os.path.join(standalone_dir, "sentinel", "main.py")
    
    print("==================================================")
    print("      VAANI V1 ORCHESTRATOR REDIRECT GATEWAY      ")
    print("==================================================")
    print(f"Target Sentinel path: {sentinel_path}")
    print(f"Launching Vaani V1 standalone server...")
    print("==================================================")
    
    try:
        # Start uvicorn server in standalone repository
        # Set CWD to standalone directory so module paths resolve correctly
        sys.exit(subprocess.call([python_exe, sentinel_path], cwd=standalone_dir))
    except Exception as e:
        print(f"Failed to launch standalone sentinel: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
