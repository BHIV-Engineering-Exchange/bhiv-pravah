#!/usr/bin/env python3
"""
Integrated CRM and Pravah Bhiv Observer Launcher
Launches independent CRM runtimes along with Pravah Bhiv Control Plane and Observer.
Pravah Bhiv observes - but does not own - the execution of these systems.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from datetime import datetime
from pathlib import Path

class IntegratedLauncher:
    def __init__(self):
        self.processes = []
        self.running = True
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.crm_backend_dir = self.root_dir / "ai-crm" / "backend"
        self.pravah_backend_dir = self.root_dir / "pravah-bhiv" / "backend"

    def print_banner(self):
        print("=" * 80)
        print("   INTEGRATED CRM SYSTEM WITH PRAVAH BHIV OBSERVER")
        print("=" * 80)
        print(f" Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(" Initializing components...")
        print()

    def check_and_init(self):
        # Database initialization for CRM
        print("[DB] Initializing database...")
        sys.path.append(str(self.crm_backend_dir))
        try:
            # We change CWD temporarily to initialize DB correctly
            old_cwd = os.getcwd()
            os.chdir(str(self.crm_backend_dir))
            from database.models import init_database
            init_database()
            os.chdir(old_cwd)
            print("[DB] Database initialized successfully")
        except Exception as e:
            print(f"[DB] Database initialization notice (SQLite may already exist): {e}")

    def stream_output(self, name, process):
        """Read stdout and stderr streams and prefix them in the terminal."""
        def reader(pipe, prefix):
            try:
                for line in iter(pipe.readline, b''):
                    if not self.running:
                        break
                    print(f"[{prefix}] {line.decode(errors='ignore').rstrip()}")
            except Exception:
                pass
            finally:
                try:
                    pipe.close()
                except Exception:
                    pass

        t1 = threading.Thread(target=reader, args=(process.stdout, name), daemon=True)
        t2 = threading.Thread(target=reader, args=(process.stderr, name), daemon=True)
        t1.start()
        t2.start()

    def start_process(self, name, cmd, cwd, env=None):
        print(f"[START] Starting {name}...")
        try:
            resolved_env = os.environ.copy()
            if env:
                resolved_env.update(env)
            
            # Run the subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(cwd),
                env=resolved_env
            )
            self.processes.append((name, process))
            self.stream_output(name, process)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start {name}: {e}")
            return False

    def shutdown(self):
        """Terminate all child processes gracefully, then kill if needed."""
        print("\n[STOP] Received shutdown signal, stopping all processes...")
        self.running = False
        
        # Terminate processes
        for name, process in self.processes:
            if process.poll() is None:
                print(f"[STOP] Stopping {name} (PID: {process.pid})...")
                try:
                    process.terminate()
                except Exception:
                    pass
                
        # Wait for graceful stop
        time.sleep(2)
        
        # Force kill if still running
        for name, process in self.processes:
            if process.poll() is None:
                print(f"[WARN] Force killing {name} (PID: {process.pid})...")
                try:
                    process.kill()
                except Exception:
                    pass
        print("[SUCCESS] All processes stopped. Shutdown complete.")

    def run(self):
        self.print_banner()
        self.check_and_init()

        # Define services to launch
        # 1. Pravah Bhiv Flask Control Plane (port 7000)
        self.start_process(
            "Control-Plane",
            [sys.executable, "wsgi.py"],
            self.pravah_backend_dir,
            {"CONTROL_PLANE_PORT": "7000", "ENVIRONMENT": "dev"}
        )
        time.sleep(2)

        # 2. Pravah Bhiv Observer Server (port 8600)
        self.start_process(
            "Observer",
            [sys.executable, "observer_server.py"],
            self.pravah_backend_dir,
            {
                "PRAVAH_OBSERVER_PORT": "8600",
                "PRAVAH_CRM_API": "http://localhost:8001",
                "PRAVAH_MAIN_API": "http://localhost:8000",
                "PRAVAH_CRM_DASHBOARD": "http://localhost:8501",
                "PRAVAH_MAIN_DASHBOARD": "http://localhost:8502",
                "PRAVAH_CONTROL_PLANE": "http://localhost:7000"
            }
        )
        time.sleep(2)

        # 3. CRM API (port 8001)
        self.start_process(
            "CRM-API",
            [sys.executable, "crm_api.py"],
            self.crm_backend_dir
        )
        time.sleep(2)

        # 4. Main Logistics API (port 8000)
        self.start_process(
            "Main-API",
            [sys.executable, "api_app.py"],
            self.crm_backend_dir
        )
        time.sleep(2)

        # 5. CRM Dashboard (port 8501)
        self.start_process(
            "CRM-Dashboard",
            ["streamlit", "run", "crm_dashboard.py", "--server.port=8501", "--server.headless=true"],
            self.crm_backend_dir
        )

        # 6. Main Dashboard (port 8502)
        self.start_process(
            "Main-Dashboard",
            ["streamlit", "run", "dashboard_app.py", "--server.port=8502", "--server.headless=true"],
            self.crm_backend_dir
        )

        print("\n" + "=" * 80)
        print(" SYSTEM LAUNCHED SUCCESSFULLY")
        print("=" * 80)
        print(" Access Points:")
        print("   • Observer Dashboard: http://localhost:8600")
        print("   • Control Plane API:  http://localhost:7000")
        print("   • CRM Dashboard:      http://localhost:8501")
        print("   • Logistics Dashboard:http://localhost:8502")
        print("   • CRM API:            http://localhost:8001")
        print("   • Main Logistics API: http://localhost:8000")
        print("\nPress Ctrl+C to shut down all processes.")
        print("=" * 80 + "\n")

        # Keep alive and monitor
        try:
            while self.running:
                # Check if crucial processes crashed
                for name, process in self.processes:
                    exit_code = process.poll()
                    if exit_code is not None:
                        print(f"[WARN] Service {name} has exited unexpectedly with code {exit_code}")
                time.sleep(5)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

if __name__ == "__main__":
    launcher = IntegratedLauncher()
    
    def sig_handler(signum, frame):
        launcher.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    
    launcher.run()
