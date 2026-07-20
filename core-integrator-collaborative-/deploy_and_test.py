"""
BHIV Microservices Deployment and Testing Script
=================================================
1. Tests each service individually
2. Deploys all services in correct order
3. Provides health monitoring
4. Offers graceful shutdown
"""

import sys
import subprocess
import time
import requests
import os
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Colors for console output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

class MicroserviceTester:
    """Test individual microservices"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        
    def test_port_available(self, port: int) -> bool:
        """Check if port is available"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0
    
    def test_prompt_runner(self) -> Tuple[bool, str]:
        """Test Prompt Runner service"""
        prompt_runner_url = os.getenv("PROMPT_RUNNER_URL", "http://127.0.0.1:8003")
        print_info(f"Testing Prompt Runner at {prompt_runner_url}...")
        
        try:
            response = requests.get(f"{prompt_runner_url}/health", timeout=5)
            if response.status_code == 200:
                return True, "Prompt Runner is healthy"
            return False, f"Health check returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"Prompt Runner not reachable at {prompt_runner_url}"
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
    
    def test_creator_core(self) -> Tuple[bool, str]:
        """Test Creator Core service"""
        print_info("Testing Creator Core (Port 8000)...")
        
        # Check if service is running
        try:
            response = requests.get("http://127.0.0.1:8000/", timeout=5)
            if response.status_code == 200:
                return True, "Creator Core is healthy"
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
        
        if not self.test_port_available(8000):
            return False, "Port 8000 is already in use"
        
        # Check files
        main_path = self.base_path / "creator-core" / "Core-Integrator-Sprint-1.1" / "main.py"
        if not main_path.exists():
            return False, f"Main script not found: {main_path}"
        
        return True, "Creator Core files verified and ready"
    
    def test_bhiv_core(self) -> Tuple[bool, str]:
        """Test BHIV Core service"""
        print_info("Testing BHIV Core (Port 8001)...")
        
        # Check if service is running
        try:
            response = requests.get("http://127.0.0.1:8001/", timeout=5)
            if response.status_code == 200:
                return True, "BHIV Core is healthy"
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
        
        if not self.test_port_available(8001):
            return False, "Port 8001 is already in use"
        
        # Check main file
        main_path = self.base_path / "main.py"
        if not main_path.exists():
            return False, f"Main script not found: {main_path}"
        
        return True, "BHIV Core files verified and ready"
    
    def test_integration_bridge(self) -> Tuple[bool, str]:
        """Test Integration Bridge service"""
        print_info("Testing Integration Bridge (Port 8004)...")
        
        # Check if service is running
        try:
            response = requests.get("http://127.0.0.1:8004/pipeline/health", timeout=5)
            if response.status_code == 200:
                return True, "Integration Bridge is healthy"
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
        
        if not self.test_port_available(8004):
            return False, "Port 8004 is already in use"
        
        # Check file
        bridge_path = self.base_path / "integration_bridge.py"
        if not bridge_path.exists():
            return False, f"Bridge script not found: {bridge_path}"
        
        return True, "Integration Bridge files verified and ready"
    
    def test_bucket(self) -> Tuple[bool, str]:
        """Test BHIV Bucket service"""
        print_info("Testing BHIV Bucket (Port 8005)...")
        
        # Check if service is running
        try:
            response = requests.get("http://127.0.0.1:8005/bucket/stats", timeout=5)
            if response.status_code == 200:
                return True, "BHIV Bucket is healthy"
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
        
        if not self.test_port_available(8005):
            return False, "Port 8005 is already in use"
        
        # Check file
        bucket_path = self.base_path / "bhiv_bucket.py"
        if not bucket_path.exists():
            return False, f"Bucket script not found: {bucket_path}"
        
        return True, "BHIV Bucket files verified and ready"
    
    def test_all_services(self) -> Dict[str, Tuple[bool, str]]:
        """Test all services and return results"""
        results = {
            "Prompt Runner": self.test_prompt_runner(),
            "Creator Core": self.test_creator_core(),
            "BHIV Core": self.test_bhiv_core(),
            "Integration Bridge": self.test_integration_bridge(),
            "BHIV Bucket": self.test_bucket()
        }
        return results


class ServiceManager:
    """Manage microservice lifecycle"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.processes: Dict[str, subprocess.Popen] = {}
        self.service_order = [
            ("bucket", 8005, "bhiv_bucket.py"),
            ("creator_core", 8000, "creator-core/Core-Integrator-Sprint-1.1/main.py"),
            ("bhiv_core", 8001, "main.py"),
            ("integration_bridge", 8004, "integration_bridge.py")
        ]
        
    def load_env_file(self, env_path: Path):
        """Load environment variables from file"""
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        # Remove BOM if present
                        line = line.lstrip('\ufeff')
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
                        
    def start_service(self, service_name: str, port: int, script_path: str) -> Tuple[bool, str]:
        """Start a single service"""
        print_info(f"Starting {service_name} on port {port}...")
        
        full_path = self.base_path / script_path
        
        if not full_path.exists():
            return False, f"Script not found: {full_path}"
        
        # Load specific env files
        if service_name == "creator_core":
            self.load_env_file(self.base_path / "creator-core" / "Core-Integrator-Sprint-1.1" / ".env.local")
        
        # Set port in environment
        env = os.environ.copy()
        env["PORT"] = str(port)
        
        try:
            # Start process
            process = subprocess.Popen(
                [sys.executable, str(full_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(self.base_path)
            )
            
            self.processes[service_name] = process
            time.sleep(2)  # Give service time to start
            
            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return False, f"Process exited immediately:\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            
            print_success(f"{service_name} started (PID: {process.pid})")
            return True, f"Started on port {port}"
            
        except Exception as e:
            return False, f"Failed to start: {str(e)}"
    
    def check_service_health(self, service_name: str, port: int) -> Tuple[bool, str]:
        """Check if service is responding"""
        endpoints = {
            "bucket": "/bucket/stats",
            "prompt_runner": "/health",
            "creator_core": "/",
            "bhiv_core": "/",
            "integration_bridge": "/pipeline/health"
        }
        
        endpoint = endpoints.get(service_name, "/")
        url = f"http://127.0.0.1:{port}{endpoint}"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True, "Healthy"
            else:
                return False, f"Status code: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except Exception as e:
            return False, str(e)
    
    def start_all_services(self) -> bool:
        """Start all services in order"""
        print_header("STARTING ALL SERVICES")
        
        all_started = True
        
        for service_name, port, script_path in self.service_order:
            success, message = self.start_service(service_name, port, script_path)
            
            if success:
                # Wait and check health
                print_info(f"Waiting for {service_name} to be ready...")
                time.sleep(3)
                
                healthy, health_msg = self.check_service_health(service_name, port)
                if healthy:
                    print_success(f"{service_name} is healthy: {health_msg}")
                else:
                    print_warning(f"{service_name} started but health check failed: {health_msg}")
            else:
                print_error(f"Failed to start {service_name}: {message}")
                all_started = False
        
        return all_started
    
    def monitor_services(self):
        """Monitor all running services"""
        print_header("SERVICE MONITORING")
        print_info("Monitoring services... (Press Ctrl+C to stop)\n")
        
        try:
            while True:
                print(f"\n{Colors.CYAN}[{datetime.now().strftime('%H:%M:%S')}]{Colors.RESET} Service Status:")
                print("-" * 70)
                
                all_healthy = True
                for service_name, port, _ in self.service_order:
                    # Check if process is running
                    process = self.processes.get(service_name)
                    process_alive = process and process.poll() is None
                    
                    # Check health endpoint
                    healthy, health_msg = self.check_service_health(service_name, port)
                    
                    status_icon = Colors.GREEN + "✓" if healthy else Colors.RED + "✗"
                    pid = f"PID: {process.pid}" if process_alive else "STOPPED"
                    
                    print(f"{status_icon} {service_name:20s} | {pid:15s} | Port: {port} | {health_msg}{Colors.RESET}")
                    
                    if not healthy:
                        all_healthy = False
                
                print("-" * 70)
                
                if all_healthy:
                    print_success("All services are healthy")
                else:
                    print_warning("Some services are unhealthy")
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n\nStopping monitoring...")
            self.shutdown_all()
    
    def shutdown_all(self):
        """Gracefully shutdown all services"""
        print_header("SHUTTING DOWN ALL SERVICES")
        
        # Shutdown in reverse order
        for service_name, _, _ in reversed(self.service_order):
            if service_name in self.processes:
                process = self.processes[service_name]
                
                if process and process.poll() is None:
                    print_info(f"Stopping {service_name}...")
                    
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                        print_success(f"{service_name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                        print_warning(f"{service_name} killed (timeout)")
                    except Exception as e:
                        print_error(f"Error stopping {service_name}: {str(e)}")
        
        self.processes.clear()
        print_success("All services stopped")


def main():
    """Main entry point"""
    print_header("BHIV MICROSERVICES DEPLOYMENT AND TESTING")
    
    # Step 1: Test all services individually
    print_header("STEP 1: TESTING SERVICES INDIVIDUALLY")
    
    tester = MicroserviceTester()
    test_results = tester.test_all_services()
    
    all_passed = True
    for service_name, (success, message) in test_results.items():
        if success:
            print_success(f"{service_name}: {message}")
        else:
            print_error(f"{service_name}: {message}")
            all_passed = False
    
    if not all_passed:
        print_warning("\nSome tests failed. Do you want to continue with deployment? (y/n): ", end="")
        response = input().strip().lower()
        if response != 'y':
            print_info("Deployment cancelled")
            return
    
    # Step 2: Deploy all services
    print_header("STEP 2: DEPLOYING ALL SERVICES")
    
    manager = ServiceManager()
    
    # Setup signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print("\n\nInterrupt received...")
        manager.shutdown_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    if manager.start_all_services():
        print_success("\n✅ All services deployed successfully!")
        
        # Step 3: Monitor services
        print_header("STEP 3: MONITORING SERVICES")
        manager.monitor_services()
    else:
        print_error("\n❌ Failed to deploy all services")
        manager.shutdown_all()
        sys.exit(1)


if __name__ == "__main__":
    main()
