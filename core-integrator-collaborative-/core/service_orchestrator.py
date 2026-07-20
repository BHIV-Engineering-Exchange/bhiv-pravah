"""
Service Orchestrator for BHIV Core-Integrator
Manages automatic service startup in dependency order with health checks
"""

import subprocess
import time
import logging
import signal
import sys
import os
import socket
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    from config import ConfigManager
    from core import get_service_mesh
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ServiceOrchestrator:
    """
    Orchestrates service startup and lifecycle management
    - Respects service dependencies
    - Waits for health checks
    - Handles graceful shutdown
    """
    
    def __init__(self):
        """Initialize orchestrator"""
        self.config = self._load_config()
        self.services = self.config.get('services', {})
        self.processes: Dict[str, subprocess.Popen] = {}
        self.dependency_graph = self._build_dependency_graph()
        self.service_startup_order = self._calculate_startup_order()
        self.mesh = None
        self.running_services: Set[str] = set()
        
        logger.info("Service Orchestrator initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration"""
        try:
            return ConfigManager.get_config()
        except:
            # Fallback config
            return {
                'services': {
                    'prompt_runner': {'port': 8003, 'depends_on': []},
                    'creator_core': {'port': 8000, 'depends_on': []},
                    'bhiv_core': {'port': 8001, 'depends_on': []},
                    'cet': {'port': 8006, 'depends_on': []},
                    'sarathi': {'port': 8007, 'depends_on': []},
                    'gate': {'port': 8008, 'depends_on': []},
                    'integration_bridge': {'port': 8004, 'depends_on': ['prompt_runner', 'creator_core', 'cet', 'sarathi', 'gate', 'bhiv_core', 'bucket']},
                    'bucket': {'port': 8005, 'depends_on': []},
                },
                'global': {'health_check_timeout': 5}
            }
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build service dependency graph"""
        graph = {}
        for service_name, service_config in self.services.items():
            graph[service_name] = service_config.get('depends_on', [])
        return graph
    
    def _calculate_startup_order(self) -> List[str]:
        """
        Calculate service startup order using topological sort
        Services with no dependencies start first
        """
        order = []
        visited = set()
        visiting = set()
        
        def visit(service: str, path: List[str] = None):
            """Depth-first traversal to detect cycles and order services"""
            if path is None:
                path = []
            
            if service in visited:
                return
            
            if service in visiting:
                cycle = " → ".join(path + [service])
                raise ValueError(f"Circular dependency detected: {cycle}")
            
            visiting.add(service)
            
            # Visit all dependencies first
            for dep in self.dependency_graph.get(service, []):
                visit(dep, path + [service])
            
            visiting.remove(service)
            visited.add(service)
            order.append(service)
        
        # Visit all services
        for service in self.services:
            visit(service)
        
        return order
    
    def get_startup_order(self) -> List[str]:
        """Get services in startup order"""
        return self.service_startup_order
    
    def print_startup_plan(self):
        """Print the planned startup sequence"""
        print("\n" + "="*70)
        print("SERVICE STARTUP PLAN")
        print("="*70)
        
        startup_order = self.get_startup_order()
        
        for i, service_name in enumerate(startup_order, 1):
            deps = self.dependency_graph.get(service_name, [])
            service_config = self.services.get(service_name, {})
            port = service_config.get('port', 'N/A')
            
            deps_str = ", ".join(deps) if deps else "None"
            print(f"\n{i}. {service_name.upper()}")
            print(f"   Port: {port}")
            print(f"   Dependencies: {deps_str}")
            print(f"   Status: Ready to start")
        
        print("\n" + "="*70 + "\n")
    
    def start_services(self, wait_for_health: bool = True, health_check_timeout: int = 30) -> bool:
        """
        Start all services in dependency order
        
        Args:
            wait_for_health: Wait for health checks before proceeding
            health_check_timeout: Max seconds to wait for health checks
            
        Returns:
            True if all services started successfully
        """
        print("\n" + "="*70)
        print("STARTING BHIV SERVICES")
        print("="*70 + "\n")
        
        self.print_startup_plan()
        
        startup_order = self.get_startup_order()
        
        try:
            for service_name in startup_order:
                print(f"-> Starting {service_name}...", end=" ", flush=True)
                if self._is_service_healthy(service_name):
                    print("[OK] Already running (healthy)")
                    continue
                
                if self._start_service(service_name):
                    self.running_services.add(service_name)
                    print(f"[OK] Started (PID: {self.processes[service_name].pid})")
                    
                    # Wait for health check if enabled
                    if wait_for_health:
                        if self._wait_for_health(service_name, health_check_timeout):
                            print(f"   [OK] Health check passed")
                        else:
                            print(f"   [WARN] Health check timeout (continuing)")
                else:
                    print(f"[ERROR] Failed to start")
                    self._shutdown_all()
                    return False
                
                # Small delay between service starts
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\n\n[WARN] Interrupted by user")
            self._shutdown_all()
            return False
        except Exception as e:
            print(f"\n\n[ERROR] Error during startup: {str(e)}")
            logger.error(f"Orchestrator error: {str(e)}", exc_info=True)
            self._shutdown_all()
            return False
        
        print("\n" + "="*70)
        print("[OK] ALL SERVICES STARTED SUCCESSFULLY")
        print("="*70)
        self._print_service_summary()
        
        return True
    
    def _start_service(self, service_name: str) -> bool:
        """
        Start a single service
        
        Returns:
            True if successful
        """
        try:
            # Get service runner script
            runner_script = self._get_service_runner(service_name)
            
            if not runner_script or not Path(runner_script).exists():
                logger.error(f"Runner script not found for {service_name}: {runner_script}")
                return False
            
            # Get service port
            service_config = self.services.get(service_name, {})
            port = service_config.get('port')
            if port and self._is_port_in_use(int(port)):
                logger.error(f"Port {port} already in use for {service_name}.")
                return False
            
            # Set environment variables
            env = os.environ.copy()
            self._apply_default_auth_env(env)
            if port:
                env[f"{service_name.upper()}_PORT"] = str(port)
            
            # Add root and src to PYTHONPATH
            root_dir = str(Path(__file__).parent.parent)
            src_dir = str(Path(root_dir) / "src")
            current_pythonpath = env.get("PYTHONPATH", "")
            new_pythonpath = os.pathsep.join(filter(None, [root_dir, src_dir, current_pythonpath]))
            env["PYTHONPATH"] = new_pythonpath
            # Create logs directory and open service log file
            logs_dir = Path(__file__).parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            log_file = open(logs_dir / f"{service_name}.log", "w", encoding="utf-8")
            
            # Start process
            process = subprocess.Popen(
                [sys.executable, runner_script],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                cwd=str(Path(__file__).parent.parent)
            )
            log_file.close()
            
            self.processes[service_name] = process
            time.sleep(0.5)  # Give process time to start
            
            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"{service_name} crashed immediately:\n{stderr}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to start {service_name}: {str(e)}")
            return False

    def _is_service_healthy(self, service_name: str) -> bool:
        try:
            if self.mesh is None:
                self.mesh = get_service_mesh()
            return self.mesh.health_check(service_name)
        except Exception:
            return False

    def _is_port_in_use(self, port: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            return sock.connect_ex(("127.0.0.1", port)) == 0
        finally:
            sock.close()

    def _apply_default_auth_env(self, env: Dict[str, str]) -> None:
        """
        Ensure all services share consistent auth defaults in local startup.
        This avoids startup crashes when .env is absent.
        """
        env.setdefault("AUTH_ENABLED", "true")
        env.setdefault("AUTH_API_KEY", "prod_shakti_tantra_secret_key_2026")
        env.setdefault("AUTH_SECRET_KEY", "prod_shakti_tantra_secret_key_2026")
        env.setdefault("RATE_LIMIT_IP_PER_MIN", "10000")
        env.setdefault("RATE_LIMIT_USER_PER_MIN", "10000")
    
    def _get_service_runner(self, service_name: str) -> Optional[str]:
        """Get the runner script path for a service"""
        service_config = self.services.get(service_name, {})
        configured_runner = service_config.get("runner_script")
        if configured_runner:
            return configured_runner
        runners = {
            'prompt_runner': 'prompt-runner01/run_server.py',
            'creator_core': 'creator-core/Core-Integrator-Sprint-1.1/main.py',
            'bhiv_core': 'main.py',
            'integration_bridge': 'integration_bridge.py',
            'bucket': 'bhiv_bucket.py',
            'cet': 'cet_service.py',
            'sarathi': 'sarathi_service.py',
            'gate': 'gate_service.py',
            'control_plane': 'control_plane_service.py',
            'telemetry': 'telemetry_service.py',
        }
        return runners.get(service_name)
    
    def _wait_for_health(self, service_name: str, timeout: int = 30) -> bool:
        """
        Wait for service health check to pass
        
        Args:
            service_name: Service to check
            timeout: Max seconds to wait
            
        Returns:
            True if healthy, False if timeout
        """
        try:
            if self.mesh is None:
                self.mesh = get_service_mesh()
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.mesh.health_check(service_name):
                    return True
                time.sleep(1)
            
            return False
        except:
            # Mesh not available, assume healthy
            return True
    
    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all running services"""
        status = {}
        
        for service_name, process in self.processes.items():
            pid = process.pid if process else None
            running = process.poll() is None if process else False
            
            status[service_name] = {
                'running': running,
                'pid': pid,
                'process': process
            }
        
        return status
    
    def _print_service_summary(self):
        """Print summary of all running services"""
        print("\nRunning Services:")
        print("-" * 70)
        
        try:
            config = ConfigManager.get_config()
        except:
            config = self.config
        
        for service_name in self.get_startup_order():
            status = self.get_service_status().get(service_name, {})
            running = status.get('running', False)
            pid = status.get('pid', 'N/A')
            
            if service_name in config['services']:
                service_config = config['services'][service_name]
                port = service_config.get('port', 'N/A')
                url = f"http://127.0.0.1:{port}" if port != 'N/A' else 'N/A'
            else:
                url = 'N/A'
            
            if running:
                icon = "[OK]"
            elif self._is_service_healthy(service_name):
                icon = "[OK]"
            else:
                icon = "[X]"
            print(f"{icon} {service_name:20s} | PID: {str(pid):6s} | Port: {str(port):5s} | URL: {url}")
        
        print("-" * 70)
    
    def monitor_services(self, check_interval: int = 5):
        """
        Monitor running services (blocks until interrupted)
        
        Args:
            check_interval: Seconds between health checks
        """
        print("\n" + "="*70)
        print("MONITORING SERVICES")
        print("="*70)
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check if all processes are still running
                dead_services = []
                for service_name, process in self.processes.items():
                    if process and process.poll() is not None:
                        dead_services.append(service_name)
                
                # Print status
                self._print_service_summary()
                
                if dead_services:
                    print(f"\n[WARN] Dead services detected: {', '.join(dead_services)}")
                
                print(f"\nLast check: {datetime.now().strftime('%H:%M:%S')}")
                print(f"Waiting {check_interval}s for next check...")
                print("-" * 70)
                
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self._shutdown_all()
    
    def _shutdown_all(self):
        """Gracefully shutdown all services"""
        print("\n" + "="*70)
        print("SHUTTING DOWN SERVICES")
        print("="*70 + "\n")
        
        if not self.processes:
            print("No services running")
            return
        
        # Terminate processes in reverse startup order
        shutdown_order = list(reversed(self.get_startup_order()))
        
        for service_name in shutdown_order:
            if service_name not in self.processes:
                continue
            
            process = self.processes[service_name]
            
            if process and process.poll() is None:
                print(f"Stopping {service_name}...", end=" ", flush=True)
                
                try:
                    process.terminate()
                    # Wait up to 3 seconds for graceful shutdown
                    process.wait(timeout=3)
                    print("[OK] Stopped")
                except subprocess.TimeoutExpired:
                    print("(timeout, killing)...", end=" ", flush=True)
                    process.kill()
                    process.wait()
                    print("[OK] Killed")
                except Exception as e:
                    print(f"[ERROR] Error: {str(e)}")
        
        self.processes.clear()
        self.running_services.clear()
        
        print("\n" + "="*70)
        print("[OK] ALL SERVICES STOPPED")
        print("="*70 + "\n")


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nReceived interrupt signal")
    sys.exit(0)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n" + "="*70)
    print("BHIV CORE-INTEGRATOR SERVICE ORCHESTRATOR")
    print("="*70)
    
    orchestrator = ServiceOrchestrator()
    
    # Show startup plan
    orchestrator.print_startup_plan()
    
    # Start services
    if orchestrator.start_services(wait_for_health=True):
        # Monitor services
        orchestrator.monitor_services(check_interval=5)
    else:
        print("\n[ERROR] Failed to start services")
        sys.exit(1)
