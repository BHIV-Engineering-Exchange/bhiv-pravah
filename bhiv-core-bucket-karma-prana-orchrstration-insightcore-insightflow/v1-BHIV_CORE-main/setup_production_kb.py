#!/usr/bin/env python3
"""
Production Knowledge Base Setup Script
Sets up the complete BHIV knowledge base system for production deployment.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

class ProductionKBSetup:
    """Production setup for BHIV Knowledge Base system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.required_services = {
            'qdrant': {'port': 6333, 'url': 'http://localhost:6333'},
            'mongodb': {'port': 27017, 'url': 'mongodb://localhost:27017'},
            'bhiv_api': {'port': 8004, 'url': 'http://localhost:8004'}
        }
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed."""
        logger.info("Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("Python 3.8+ is required")
            return False
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Docker is not installed or not accessible")
                return False
            logger.info(f"Docker found: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.error("Docker is not installed")
            return False
        
        # Check required Python packages
        required_packages = [
            'qdrant-client', 'sentence-transformers', 'fastapi', 
            'uvicorn', 'pymongo', 'pydantic'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Install with: pip install " + " ".join(missing_packages))
            return False
        
        logger.info("✅ All prerequisites satisfied")
        return True
    
    def setup_qdrant(self) -> bool:
        """Setup Qdrant vector database."""
        logger.info("Setting up Qdrant...")
        
        try:
            # Check if Qdrant is already running
            import requests
            response = requests.get(f"{self.required_services['qdrant']['url']}/collections", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Qdrant is already running")
                return True
        except:
            pass
        
        # Start Qdrant with Docker
        try:
            logger.info("Starting Qdrant with Docker...")
            
            # Create data directory
            qdrant_data_dir = self.project_root / "qdrant_data"
            qdrant_data_dir.mkdir(exist_ok=True)
            
            # Run Qdrant container
            cmd = [
                'docker', 'run', '-d',
                '--name', 'qdrant-bhiv',
                '-p', '6333:6333',
                '-v', f"{qdrant_data_dir}:/qdrant/storage",
                'qdrant/qdrant'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Container might already exist
                if "already in use" in result.stderr:
                    logger.info("Qdrant container already exists, starting it...")
                    subprocess.run(['docker', 'start', 'qdrant-bhiv'])
                else:
                    logger.error(f"Failed to start Qdrant: {result.stderr}")
                    return False
            
            # Wait for Qdrant to be ready
            for i in range(30):
                try:
                    response = requests.get(f"{self.required_services['qdrant']['url']}/collections", timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ Qdrant is ready")
                        return True
                except:
                    time.sleep(1)
            
            logger.error("Qdrant failed to start within 30 seconds")
            return False
            
        except Exception as e:
            logger.error(f"Error setting up Qdrant: {str(e)}")
            return False
    
    def setup_mongodb(self) -> bool:
        """Setup MongoDB for logging and analytics."""
        logger.info("Setting up MongoDB...")
        
        try:
            # Check if MongoDB is already running
            import pymongo
            client = pymongo.MongoClient(self.required_services['mongodb']['url'], serverSelectionTimeoutMS=5000)
            client.server_info()
            logger.info("✅ MongoDB is already running")
            return True
        except:
            pass
        
        # Start MongoDB with Docker
        try:
            logger.info("Starting MongoDB with Docker...")
            
            # Create data directory
            mongo_data_dir = self.project_root / "mongo_data"
            mongo_data_dir.mkdir(exist_ok=True)
            
            # Run MongoDB container
            cmd = [
                'docker', 'run', '-d',
                '--name', 'mongodb-bhiv',
                '-p', '27017:27017',
                '-v', f"{mongo_data_dir}:/data/db",
                'mongo:latest'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                if "already in use" in result.stderr:
                    logger.info("MongoDB container already exists, starting it...")
                    subprocess.run(['docker', 'start', 'mongodb-bhiv'])
                else:
                    logger.error(f"Failed to start MongoDB: {result.stderr}")
                    return False
            
            # Wait for MongoDB to be ready
            for i in range(30):
                try:
                    client = pymongo.MongoClient(self.required_services['mongodb']['url'], serverSelectionTimeoutMS=2000)
                    client.server_info()
                    logger.info("✅ MongoDB is ready")
                    return True
                except:
                    time.sleep(1)
            
            logger.error("MongoDB failed to start within 30 seconds")
            return False
            
        except Exception as e:
            logger.error(f"Error setting up MongoDB: {str(e)}")
            return False
    
    def load_knowledge_base(self) -> bool:
        """Load data into the knowledge base."""
        logger.info("Loading knowledge base data...")
        
        try:
            # Run the data loader
            # Avoid Unicode emoji in child stdout on Windows terminals by setting PYTHONIOENCODING
            env = os.environ.copy()
            env.setdefault('PYTHONIOENCODING', 'utf-8')
            result = subprocess.run([
                sys.executable, 'load_data_to_qdrant.py',
                '--init', '--load-pdfs', '--load-texts'
            ], capture_output=True, text=True, cwd=self.project_root, env=env)
            
            if result.returncode == 0:
                logger.info("Knowledge base data loaded successfully")
                return True
            else:
                logger.error(f"Failed to load knowledge base: {result.stderr or result.stdout}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            return False
    
    def test_system(self) -> bool:
        """Test the complete system."""
        logger.info("Testing system integration...")
        
        try:
            # Start the API server in background
            api_process = subprocess.Popen([
                sys.executable, 'simple_api.py', '--port', '8004'
            ], cwd=self.project_root)
            
            # Wait for API to start
            time.sleep(10)
            
            # Test API endpoints
            import requests
            
            # Test health endpoint
            response = requests.get(f"{self.required_services['bhiv_api']['url']}/health", timeout=10)
            if response.status_code != 200:
                logger.error("Health endpoint failed")
                api_process.terminate()
                return False
            
            # Test knowledge base query
            response = requests.post(
                f"{self.required_services['bhiv_api']['url']}/query-kb",
                json={"query": "test query", "user_id": "setup_test"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Knowledge base test successful: {result.get('status', 'unknown')}")
            else:
                logger.error(f"Knowledge base test failed: {response.status_code}")
                api_process.terminate()
                return False
            
            # Terminate test API
            api_process.terminate()
            api_process.wait(timeout=5)
            
            logger.info("✅ System test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"System test failed: {str(e)}")
            return False
    
    def generate_startup_script(self):
        """Generate startup script for production."""
        startup_script = """#!/bin/bash
# BHIV Knowledge Base Production Startup Script

echo "Starting BHIV Knowledge Base System..."

# Start Qdrant
echo "Starting Qdrant..."
docker start qdrant-bhiv || docker run -d --name qdrant-bhiv -p 6333:6333 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant

# Start MongoDB
echo "Starting MongoDB..."
docker start mongodb-bhiv || docker run -d --name mongodb-bhiv -p 27017:27017 -v $(pwd)/mongo_data:/data/db mongo:latest

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Start BHIV API
echo "Starting BHIV API..."
python simple_api.py --port 8004 --host 0.0.0.0

echo "BHIV Knowledge Base System is running!"
echo "API: http://localhost:8004"
echo "Qdrant: http://localhost:6333"
echo "MongoDB: mongodb://localhost:27017"
"""
        
        script_path = self.project_root / "start_production.sh"
        with open(script_path, 'w') as f:
            f.write(startup_script)
        
        # Make executable
        os.chmod(script_path, 0o755)
        logger.info(f"✅ Startup script created: {script_path}")
    
    def run_complete_setup(self) -> bool:
        """Run the complete production setup."""
        logger.info("🚀 Starting BHIV Knowledge Base Production Setup")
        
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Qdrant Setup", self.setup_qdrant),
            ("MongoDB Setup", self.setup_mongodb),
            ("Knowledge Base Loading", self.load_knowledge_base),
            ("System Testing", self.test_system)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*20} {step_name} {'='*20}")
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                return False
            logger.info(f"✅ {step_name} completed")
        
        # Generate startup script
        self.generate_startup_script()
        
        logger.info("\n🎉 BHIV Knowledge Base Production Setup Complete!")
        logger.info("\n📋 Next Steps:")
        logger.info("1. Start the system: ./start_production.sh")
        logger.info("2. Test API: curl http://localhost:8004/health")
        logger.info("3. Query KB: curl -X POST http://localhost:8004/query-kb -H 'Content-Type: application/json' -d '{\"query\":\"test\",\"user_id\":\"test\"}'")
        logger.info("4. View analytics: curl http://localhost:8004/kb-analytics")
        
        return True


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BHIV Knowledge Base Production Setup")
    parser.add_argument("--setup", action="store_true", help="Run complete setup")
    parser.add_argument("--test", action="store_true", help="Test existing setup")
    parser.add_argument("--prereq", action="store_true", help="Check prerequisites only")
    
    args = parser.parse_args()
    
    setup = ProductionKBSetup()
    
    if args.prereq:
        if setup.check_prerequisites():
            print("✅ All prerequisites satisfied")
        else:
            print("❌ Prerequisites not met")
            sys.exit(1)
    elif args.test:
        if setup.test_system():
            print("✅ System test passed")
        else:
            print("❌ System test failed")
            sys.exit(1)
    elif args.setup or not any(vars(args).values()):
        if setup.run_complete_setup():
            print("✅ Production setup completed successfully")
        else:
            print("❌ Production setup failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
