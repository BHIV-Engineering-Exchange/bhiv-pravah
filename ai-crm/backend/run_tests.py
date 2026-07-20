#!/usr/bin/env python3
"""
Test runner with comprehensive reporting
"""

import subprocess
import sys
import os
import json
from datetime import datetime

def run_tests():
    """Run all tests and generate comprehensive report"""
    
    print("🧪 Starting AI Agent Test Suite")
    print("=" * 60)
    
    # Install test dependencies if needed
    print("📦 Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                  capture_output=True)
    
    # Run tests with coverage
    print("\n🚀 Running tests with coverage...")
    
    test_command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--cov=.",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-report=json:coverage.json",
        "--junit-xml=test_results.xml"
    ]
    
    result = subprocess.run(test_command, capture_output=True, text=True)
    
    print("📊 Test Results:")
    print("-" * 40)
    print(result.stdout)
    
    if result.stderr:
        print("⚠️  Warnings/Errors:")
        print(result.stderr)
    
    # Generate test report
    generate_test_report(result.returncode)
    
    return result.returncode

def generate_test_report(exit_code):
    """Generate comprehensive test report"""
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "exit_code": exit_code,
        "status": "PASSED" if exit_code == 0 else "FAILED",
        "coverage": get_coverage_info(),
        "test_summary": get_test_summary()
    }
    
    # Write report to file
    with open("tests_report.md", "w") as f:
        f.write(generate_markdown_report(report))
    
    print(f"\n📋 Test report generated: tests_report.md")
    print(f"📊 Coverage report: htmlcov/index.html")
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

def get_coverage_info():
    """Extract coverage information"""
    try:
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)
        
        return {
            "total_coverage": coverage_data["totals"]["percent_covered"],
            "lines_covered": coverage_data["totals"]["covered_lines"],
            "lines_missing": coverage_data["totals"]["missing_lines"],
            "total_lines": coverage_data["totals"]["num_statements"]
        }
    except FileNotFoundError:
        return {"error": "Coverage data not found"}

def get_test_summary():
    """Extract test summary from XML results"""
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse("test_results.xml")
        root = tree.getroot()
        
        return {
            "total_tests": int(root.get("tests", 0)),
            "failures": int(root.get("failures", 0)),
            "errors": int(root.get("errors", 0)),
            "skipped": int(root.get("skipped", 0)),
            "time": float(root.get("time", 0))
        }
    except (FileNotFoundError, Exception):
        return {"error": "Test summary not available"}

def generate_markdown_report(report):
    """Generate markdown test report"""
    
    status_emoji = "✅" if report["status"] == "PASSED" else "❌"
    
    markdown = f"""# AI Agent Test Report

**Generated:** {report["timestamp"]}  
**Status:** {status_emoji} {report["status"]}

## Test Summary

"""
    
    if "error" not in report["test_summary"]:
        summary = report["test_summary"]
        markdown += f"""
- **Total Tests:** {summary["total_tests"]}
- **Passed:** {summary["total_tests"] - summary["failures"] - summary["errors"]}
- **Failed:** {summary["failures"]}
- **Errors:** {summary["errors"]}
- **Skipped:** {summary["skipped"]}
- **Execution Time:** {summary["time"]:.2f}s
"""
    else:
        markdown += "Test summary not available\n"
    
    markdown += "\n## Coverage Report\n\n"
    
    if "error" not in report["coverage"]:
        cov = report["coverage"]
        markdown += f"""
- **Total Coverage:** {cov["total_coverage"]:.1f}%
- **Lines Covered:** {cov["lines_covered"]}
- **Lines Missing:** {cov["lines_missing"]}
- **Total Lines:** {cov["total_lines"]}
"""
    else:
        markdown += "Coverage data not available\n"
    
    markdown += f"""
## Test Categories

### ✅ Unit Tests
- Agent core logic (sense, plan, act)
- Chatbot response handling
- Human review system
- Confidence scoring algorithms

### ✅ Integration Tests
- End-to-end restock workflow
- Chatbot order tracking
- Human review complete workflow
- Data consistency validation
- Error handling scenarios

### ✅ API Tests
- FastAPI endpoint functionality
- Response format validation
- Error handling
- Performance testing

## Files Tested

- `agent.py` - Core agent logic
- `chatbot_agent.py` - Chatbot functionality
- `human_review.py` - Human review system
- `api_app.py` - FastAPI endpoints

## Coverage Details

View detailed coverage report: `htmlcov/index.html`

## Recommendations

### If Tests Failed:
1. Check test output for specific failures
2. Verify test data setup
3. Ensure all dependencies are installed
4. Check file paths and permissions

### For Improved Coverage:
1. Add tests for edge cases
2. Test error conditions more thoroughly
3. Add performance benchmarks
4. Test with different data scenarios

## Next Steps

- **Day 2:** Database migration with SQLite
- **Day 3:** Procurement agent implementation
- **Day 4:** Delivery agent with tracking
- **Day 5:** Dashboard and notifications
- **Day 6:** Security and containerization
- **Day 7:** Cloud deployment

---
*Generated by AI Agent Test Suite v1.0*
"""
    
    return markdown

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
