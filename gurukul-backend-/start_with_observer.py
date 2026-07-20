#!/usr/bin/env python3
"""
Integrated Gurukul Backend and Pravah Bhiv Observer Launcher
Launches Gurukul Backend API, Vaani Engine along with Pravah Bhiv Control Plane and Observer.
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
        self.root_dir = Path(__file__).resolve().parent
        self.backend_dir = self.root_dir / "backend"
        self.vaani_dir = self.root_dir / "vaani-engine"
        self.pravah_backend_dir = self.root_dir / "pravah-bhiv" / "backend"

    def print_banner(self):
        print("=" * 80)
        print("   INTEGRATED GURUKUL BACKEND SYSTEM WITH PRAVAH BHIV OBSERVER")
        print("=" * 80)
        print(f" Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(" Initializing components...")
        print()

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
        time.sleep(3)
        
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
                "PRAVAH_GURUKUL_API": "http://localhost:3000",
                "PRAVAH_CONTROL_PLANE": "http://localhost:7000"
            }
        )
        time.sleep(2)

        # 3. Vaani Sovereign Voice Engine (port 8008)
        self.start_process(
            "Vaani-Engine",
            [sys.executable, "voice_service_api.py"],
            self.vaani_dir
        )
        time.sleep(2)

        # 4. Gurukul Backend API (port 3000)
        self.start_process(
            "Gurukul-Backend",
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"],
            self.backend_dir,
            {
                "PRAVAH_URL": "http://localhost:7000/api/runtime",
                "TANTRA_API_KEY": "default-secret-key-change-in-prod",
                "SSPL_SECRET_KEY": "default-secret-key-change-in-prod",
                "TANTRA_DEBUG_LOG": "true",
                "PYTHONPATH": "."
            }
        )

        print("\n" + "=" * 80)
        print(" SYSTEM LAUNCHED SUCCESSFULLY")
        print("=" * 80)
        print(" Access Points:")
        print("   • Observer Dashboard: http://localhost:8600")
        print("   • Control Plane API:  http://localhost:7000")
        print("   • Gurukul Backend:    http://localhost:3000")
        print("\nPress Ctrl+C to shut down all processes.")
        print("=" * 80 + "\n")

        # Keep alive and monitor
        try:
            while self.running:
                # Check if any crucial service has died
                for name, process in self.processes:
                    if process.poll() is not None:
                        # Process exited
                        if self.running:
                            print(f"[WARN] Service {name} has exited unexpectedly with code {process.poll()}")
                            # Attempt restart if not shutting down
                            if name in ("Control-Plane", "Observer"):
                                print(f"[RESTART] Restarting {name}...")
                                if name == "Control-Plane":
                                    self.start_process("Control-Plane", [sys.executable, "wsgi.py"], self.pravah_backend_dir, {"CONTROL_PLANE_PORT": "7000", "ENVIRONMENT": "dev"})
                                elif name == "Observer":
                                    self.start_process("Observer", [sys.executable, "observer_server.py"], self.pravah_backend_dir, {"PRAVAH_OBSERVER_PORT": "8600", "PRAVAH_GURUKUL_API": "http://localhost:3000", "PRAVAH_CONTROL_PLANE": "http://localhost:7000"})
                time.sleep(5)
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            print(f"[ERROR] Launcher error: {e}")
            self.shutdown()

if __name__ == "__main__":
    launcher = IntegratedLauncher()
    
    # Register signal handlers for graceful shutdown on Windows/Unix
    def signal_handler(sig, frame):
        launcher.shutdown()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    launcher.run()
