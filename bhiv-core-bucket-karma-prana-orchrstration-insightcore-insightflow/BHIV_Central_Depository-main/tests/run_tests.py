#!/usr/bin/env python3
"""
Comprehensive test runner for AI Integration system
Runs all tests and generates detailed reports
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestRunner:
    """Comprehensive test runner for the AI Integration system"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {},
            "errors": []
        }
    
    def run_pytest_tests(self):
        """Run all pytest tests"""
        logger.info("Running pytest tests...")
        
        test_files = [
            "test_redis_service.py",
            "test_basket_manager.py",
            "test_integration.py"
        ]
        
        for test_file in test_files:
            test_path = self.test_dir / test_file
            if not test_path.exists():
                logger.warning(f"Test file not found: {test_file}")
                continue
            
            logger.info(f"Running {test_file}...")
            start_time = time.time()
            
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    str(test_path), 
                    "-v", 
                    "--tb=short",
                    "--json-report",
                    f"--json-report-file={self.test_dir}/results_{test_file.replace('.py', '.json')}"
                ], 
                capture_output=True, 
                text=True,
                cwd=self.project_root
                )
                
                duration = time.time() - start_time
                
                self.results["tests"][test_file] = {
                    "duration": duration,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "status": "passed" if result.returncode == 0 else "failed"
                }
                
                if result.returncode == 0:
                    logger.info(f"✅ {test_file} passed in {duration:.2f}s")
                else:
                    logger.error(f"❌ {test_file} failed in {duration:.2f}s")
                    logger.error(f"Error output: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error running {test_file}: {e}")
                self.results["errors"].append(f"Error running {test_file}: {e}")
    
    def test_sample_inputs(self):
        """Test that all sample input files are valid JSON"""
        logger.info("Validating sample input files...")
        
        sample_inputs_dir = self.test_dir / "sample_inputs"
        if not sample_inputs_dir.exists():
            logger.warning("Sample inputs directory not found")
            return
        
        input_files = list(sample_inputs_dir.glob("*.json"))
        valid_inputs = 0
        
        for input_file in input_files:
            try:
                with input_file.open() as f:
                    data = json.load(f)
                logger.info(f"✅ Valid JSON: {input_file.name}")
                valid_inputs += 1
                
                # Basic validation
                if not isinstance(data, dict):
                    logger.warning(f"⚠️  {input_file.name}: Root should be an object")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in {input_file.name}: {e}")
                self.results["errors"].append(f"Invalid JSON in {input_file.name}: {e}")
            except Exception as e:
                logger.error(f"❌ Error reading {input_file.name}: {e}")
                self.results["errors"].append(f"Error reading {input_file.name}: {e}")
        
        self.results["sample_inputs"] = {
            "total_files": len(input_files),
            "valid_files": valid_inputs,
            "status": "passed" if valid_inputs == len(input_files) else "failed"
        }
    
    def test_basket_configurations(self):
        """Test that basket configurations are valid"""
        logger.info("Validating basket configurations...")
        
        baskets_dir = self.project_root / "baskets"
        if not baskets_dir.exists():
            logger.warning("Baskets directory not found")
            return
        
        basket_files = list(baskets_dir.glob("*.json"))
        valid_baskets = 0
        
        for basket_file in basket_files:
            try:
                with basket_file.open() as f:
                    basket_config = json.load(f)
                
                # Validate required fields
                required_fields = ["basket_name", "agents", "execution_strategy"]
                missing_fields = [field for field in required_fields if field not in basket_config]
                
                if missing_fields:
                    logger.error(f"❌ {basket_file.name}: Missing fields: {missing_fields}")
                    self.results["errors"].append(f"{basket_file.name}: Missing fields: {missing_fields}")
                else:
                    logger.info(f"✅ Valid basket: {basket_file.name}")
                    valid_baskets += 1
                
                # Validate execution strategy
                valid_strategies = ["sequential", "parallel"]
                if basket_config.get("execution_strategy") not in valid_strategies:
                    logger.warning(f"⚠️  {basket_file.name}: Invalid execution strategy")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in {basket_file.name}: {e}")
                self.results["errors"].append(f"Invalid JSON in {basket_file.name}: {e}")
            except Exception as e:
                logger.error(f"❌ Error reading {basket_file.name}: {e}")
                self.results["errors"].append(f"Error reading {basket_file.name}: {e}")
        
        self.results["basket_configs"] = {
            "total_files": len(basket_files),
            "valid_files": valid_baskets,
            "status": "passed" if valid_baskets == len(basket_files) else "failed"
        }
    
    def test_agent_specifications(self):
        """Test that agent specifications are valid"""
        logger.info("Validating agent specifications...")
        
        agents_dir = self.project_root / "agents"
        if not agents_dir.exists():
            logger.warning("Agents directory not found")
            return
        
        agent_dirs = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('__')]
        valid_agents = 0
        
        for agent_dir in agent_dirs:
            spec_file = agent_dir / "agent_spec.json"
            if not spec_file.exists():
                logger.warning(f"⚠️  No agent_spec.json found in {agent_dir.name}")
                continue
            
            try:
                with spec_file.open() as f:
                    agent_spec = json.load(f)
                
                # Validate required fields
                required_fields = ["name", "domain", "capabilities"]
                missing_fields = [field for field in required_fields if field not in agent_spec]
                
                if missing_fields:
                    logger.error(f"❌ {agent_dir.name}: Missing fields: {missing_fields}")
                    self.results["errors"].append(f"{agent_dir.name}: Missing fields: {missing_fields}")
                else:
                    logger.info(f"✅ Valid agent spec: {agent_dir.name}")
                    valid_agents += 1
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in {agent_dir.name}/agent_spec.json: {e}")
                self.results["errors"].append(f"Invalid JSON in {agent_dir.name}/agent_spec.json: {e}")
            except Exception as e:
                logger.error(f"❌ Error reading {agent_dir.name}/agent_spec.json: {e}")
                self.results["errors"].append(f"Error reading {agent_dir.name}/agent_spec.json: {e}")
        
        self.results["agent_specs"] = {
            "total_agents": len(agent_dirs),
            "valid_specs": valid_agents,
            "status": "passed" if valid_agents > 0 else "failed"
        }
    
    def generate_summary(self):
        """Generate test summary"""
        self.results["end_time"] = datetime.now().isoformat()
        
        # Count passed/failed tests
        total_tests = 0
        passed_tests = 0
        
        for test_name, test_result in self.results["tests"].items():
            total_tests += 1
            if test_result["status"] == "passed":
                passed_tests += 1
        
        # Add validation results
        validation_categories = ["sample_inputs", "basket_configs", "agent_specs"]
        for category in validation_categories:
            if category in self.results:
                total_tests += 1
                if self.results[category]["status"] == "passed":
                    passed_tests += 1
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_errors": len(self.results["errors"])
        }
        
        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        logger.info(f"Total Errors: {len(self.results['errors'])}")
        
        if self.results["errors"]:
            logger.info("\nERRORS:")
            for error in self.results["errors"]:
                logger.error(f"  - {error}")
    
    def save_results(self):
        """Save test results to file"""
        results_file = self.test_dir / "test_results.json"
        with results_file.open("w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Test results saved to: {results_file}")
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        logger.info("Starting comprehensive test suite...")
        logger.info("=" * 60)
        
        # Run all test categories
        self.run_pytest_tests()
        self.test_sample_inputs()
        self.test_basket_configurations()
        self.test_agent_specifications()
        
        # Generate summary and save results
        self.generate_summary()
        self.save_results()
        
        # Return success status
        return self.results["summary"]["failed_tests"] == 0

def main():
    """Main entry point"""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
