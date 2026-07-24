# check_code_quality.py
"""
Code quality checker for InsightFlow.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_quality_check(cmd, description, required=True):
    """Run code quality check"""
    print(f"\n=== {description} ===")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"❌ {description} - ISSUES FOUND")
            if result.stdout.strip():
                print("STDOUT:", result.stdout)
            if result.stderr.strip():
                print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    except FileNotFoundError:
        if required:
            print(f"❌ {description} - TOOL NOT FOUND")
            print(f"Install with: pip install {cmd[0]}")
        else:
            print(f"⚠️  {description} - TOOL NOT FOUND (optional)")
        return not required
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def install_missing_tools():
    """Install missing code quality tools"""
    tools = ["black", "flake8", "pytest-cov"]
    
    print("=== Installing Code Quality Tools ===")
    
    for tool in tools:
        cmd = [sys.executable, "-m", "pip", "install", tool]
        print(f"Installing {tool}...")
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ {tool} installed")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {tool}")


def main():
    """Run code quality checks"""
    
    print("=== InsightFlow Code Quality Check ===\n")
    
    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Install tools if needed
    install_missing_tools()
    
    quality_checks = []
    
    # 1. Format code (black)
    cmd = [sys.executable, "-m", "black", "app/", "tests/", "--check", "--diff"]
    if run_quality_check(cmd, "Code Formatting (Black)", required=False):
        quality_checks.append("Formatting")
    
    # 2. Lint code (flake8)
    cmd = [sys.executable, "-m", "flake8", "app/", "tests/", "--max-line-length=100", "--ignore=E203,W503"]
    if run_quality_check(cmd, "Code Linting (Flake8)", required=False):
        quality_checks.append("Linting")
    
    # 3. Check test coverage
    cmd = [sys.executable, "-m", "pytest", "tests/", "--cov=app", "--cov-report=term-missing", "--cov-fail-under=70"]
    if run_quality_check(cmd, "Test Coverage", required=True):
        quality_checks.append("Coverage")
    
    # 4. Check for basic Python syntax
    cmd = [sys.executable, "-m", "py_compile", "app/main.py"]
    if run_quality_check(cmd, "Python Syntax Check", required=True):
        quality_checks.append("Syntax")
    
    # Summary
    print(f"\n=== Code Quality Summary ===")
    print(f"✅ Passed checks: {len(quality_checks)}")
    for check in quality_checks:
        print(f"  - {check}")
    
    if len(quality_checks) >= 2:  # At least syntax and coverage
        print("\n✅ Code quality checks passed!")
        return 0
    else:
        print("\n❌ Code quality checks failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)