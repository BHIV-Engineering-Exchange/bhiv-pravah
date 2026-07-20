#!/usr/bin/env python3
"""
Integrated BHIV System Launcher
Starts BHIV_Integrator_Core with all dashboards and services
"""

import os
import sys
import subprocess
import time
import signal
import threading
from datetime import datetime

class IntegratedBHIVLauncher:
    """Launch and manage the complete BHIV integrated system"""

    def __init__(self):
        self.processes = []
        self.running = True
        self.service_configs = {
            # BHIV Integrator Core (NEW)
            'bhiv_integrator': {
                'script': 'BHIV_Integrator_Core/app.py',
                'port': 8005,
                'name': 'BHIV Integrator Core',
                'type': 'fastapi',
                'description': 'Central integration layer with event broker and compliance'
            },

            # Existing APIs
            'main_api': {
                'script': 'api_app.py',
                'port': 8000,
                'name': 'Main Logistics API',
                'type': 'fastapi',
                'description': 'Core logistics and inventory API'
            },
            'crm_api': {
                'script': 'crm_api.py',
                'port': 8001,
                'name': 'CRM API',
                'type': 'fastapi',
                'description': 'Customer relationship management API'
            },

            # Dashboards
            'crm_dashboard': {
                'script': 'crm_dashboard.py',
                'port': 8501,
                'name': 'CRM Dashboard',
                'type': 'streamlit',
                'description': 'CRM management interface'
            },
            'main_dashboard': {
                'script': 'dashboard_app.py',
                'port': 8502,
                'name': 'Main Logistics Dashboard',
                'type': 'streamlit',
                'description': 'Logistics and inventory dashboard'
            },
            'supplier_dashboard': {
                'script': 'dashboard_with_supplier.py',
                'port': 8503,
                'name': 'Enhanced Supplier Dashboard',
                'type': 'streamlit',
                'description': 'Supplier management system'
            },
            'product_catalog': {
                'script': 'product_catalog_dashboard.py',
                'port': 8504,
                'name': 'Product Catalog Dashboard',
                'type': 'streamlit',
                'description': 'Product management and catalog'
            },
            'supplier_showcase': {
                'script': 'supplier_showcase.py',
                'port': 8505,
                'name': 'Supplier Showcase Portal',
                'type': 'streamlit',
                'description': 'Professional supplier portal'
            }
        }

    def print_banner(self):
        """Print startup banner"""
        print("=" * 100)
        print("INTEGRATED BHIV SYSTEM WITH COMPLIANCE")
        print("=" * 100)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Launching BHIV_Integrator_Core + All Dashboards + Compliance Integration...")
        print()

    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("[CHECK] Checking dependencies...")

        required_packages = [
            'fastapi', 'uvicorn', 'streamlit', 'requests',
            'pydantic', 'sqlalchemy', 'pandas', 'plotly'
        ]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(f"[OK] {package}")
            except ImportError:
                print(f"[ERROR] {package} - MISSING")
                missing_packages.append(package)

        if missing_packages:
            print(f"\n[WARN] Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False

        print("[OK] All dependencies satisfied")
        return True

    def start_fastapi_service(self, service_key):
        """Start a FastAPI service"""
        config = self.service_configs[service_key]
        print(f"\n[API] Starting {config['name']} on port {config['port']}...")

        try:
            if service_key == 'bhiv_integrator':
                # Special handling for BHIV Integrator Core
                process = subprocess.Popen([
                    sys.executable, '-m', 'uvicorn', 'BHIV_Integrator_Core.app:app',
                    '--host', '0.0.0.0', '--port', str(config['port']), '--reload'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
            else:
                # Standard FastAPI start
                process = subprocess.Popen([
                    sys.executable, '-m', 'uvicorn', f'{service_key}:app',
                    '--host', '0.0.0.0', '--port', str(config['port']), '--reload'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.processes.append((config['name'], process, config['port']))

            # Give it time to start
            time.sleep(5)

            if process.poll() is None:
                print(f"[OK] {config['name']} started on http://localhost:{config['port']}")
                print(f"[DOCS] API Documentation: http://localhost:{config['port']}/docs")
                print(f"[DESC] {config['description']}")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"[ERROR] {config['name']} failed to start: {stderr.decode()}")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to start {config['name']}: {e}")
            return False

    def start_streamlit_service(self, service_key):
        """Start a Streamlit dashboard service"""
        config = self.service_configs[service_key]
        print(f"\n[DASH] Starting {config['name']} on port {config['port']}...")

        try:
            process = subprocess.Popen([
                'streamlit', 'run', config['script'],
                f'--server.port={config["port"]}',
                '--server.headless=true'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.processes.append((config['name'], process, config['port']))

            # Give it time to start
            time.sleep(8)

            if process.poll() is None:
                print(f"[OK] {config['name']} started on http://localhost:{config['port']}")
                print(f"[DESC] {config['description']}")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"[ERROR] {config['name']} failed to start: {stderr.decode()}")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to start {config['name']}: {e}")
            return False

    def print_system_status(self):
        """Print comprehensive system status and URLs"""
        print("\n" + "=" * 100)
        print("COMPLETE INTEGRATED BHIV SYSTEM STATUS")
        print("=" * 100)

        print("Core Integration Services:")
        print("   BHIV Integrator Core:     http://localhost:8005")
        print("      -> Central event broker, compliance, unified logging")
        print("      -> API Docs:            http://localhost:8005/docs")
        print("      -> Event Broker:        http://localhost:8005/event")
        print("      -> Health Check:        http://localhost:8005/health")

        print("\n[API] Logistics & CRM APIs:")
        print("   Main Logistics API:       http://localhost:8000")
        print("      -> Orders, inventory, procurement, delivery")
        print("      -> API Docs:            http://localhost:8000/docs")
        print("   CRM API:                  http://localhost:8001")
        print("      -> Accounts, leads, opportunities")
        print("      -> API Docs:            http://localhost:8001/docs")

        print("\n[DASH] All Dashboards:")
        print("   CRM Dashboard:            http://localhost:8501")
        print("      -> Account/lead management, natural language queries")
        print("   Main Logistics:           http://localhost:8502")
        print("      -> Inventory, orders, AI agents")
        print("   Supplier Management:      http://localhost:8503")
        print("      -> Supplier contacts, enhanced management")
        print("   Product Catalog:          http://localhost:8504")
        print("      -> Product management, image upload")
        print("   Supplier Showcase:        http://localhost:8505")
        print("      -> Professional supplier portal")

        print("\nIntegration Endpoints (BHIV Integrator Core):")
        print("   Event Broker:")
        print("      -> Publish:             POST http://localhost:8005/event/publish")
        print("      -> Subscribe:           POST http://localhost:8005/event/subscribe")
        print("      -> Events:              GET http://localhost:8005/event/events")
        print("   Logistics Integration:")
        print("      -> Procurement:         POST http://localhost:8005/logistics/procurement")
        print("      -> Delivery:            POST http://localhost:8005/logistics/delivery")
        print("      -> Inventory:           PUT http://localhost:8005/logistics/inventory/{id}")
        print("   CRM Integration:")
        print("      -> Accounts:            POST http://localhost:8005/crm/accounts")
        print("      -> Leads:               POST http://localhost:8005/crm/leads")
        print("      -> Opportunities:       POST http://localhost:8005/crm/opportunities")
        print("   Task Management:")
        print("      -> Tasks:               POST http://localhost:8005/task/tasks")
        print("      -> Reviews:             POST http://localhost:8005/task/review")
        print("      -> Feedback:            POST http://localhost:8005/task/feedback")

        print("\nBHIV Core Integration:")
        print("   Agent Registration:       POST http://localhost:8005/bhiv/agent/register")
        print("   Decision Engine:          POST http://localhost:8005/bhiv/agent/decide")
        print("   System Status:            GET http://localhost:8005/bhiv/status")

        print("\nCompliance Integration (Sankalp):")
        print("   Consent Management:       Real-time user consent validation")
        print("   Audit Trails:             Immutable event logging")
        print("   Data Privacy:             Automated compliance checks")
        print("   Compliance Reports:       Audit log analysis")

        print("\n" + "=" * 100)

    def print_integration_guide(self):
        """Print integration workflow guide"""
        print("INTEGRATION WORKFLOW:")
        print("=" * 50)
        print("1. Order Creation:")
        print("   -> POST /logistics/procurement -> Triggers CRM lead creation")
        print("   -> BHIV Integrator routes to CRM -> Event broker notifies")
        print()
        print("2. Delivery Processing:")
        print("   -> POST /logistics/delivery -> Updates CRM opportunity")
        print("   -> Compliance checks applied -> Audit trail created")
        print()
        print("3. Task Management:")
        print("   -> POST /task/tasks -> AI agent decision routing")
        print("   -> Event triggers -> Feedback collection")
        print()
        print("4. AI Agent Integration:")
        print("   -> BHIV Core decisions -> Unified logging")
        print("   -> Compliance monitoring -> Real-time dashboards")
        print("=" * 50)

    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            time.sleep(15)

            for name, process, port in self.processes:
                if process.poll() is not None:
                    print(f"[WARN] {name} (port {port}) process has stopped")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n[STOP] Received signal {signum}, shutting down integrated system...")
        self.shutdown()

    def shutdown(self):
        """Shutdown all processes"""
        print("\n[CYCLE] Shutting down integrated BHIV system...")
        self.running = False

        for name, process, port in self.processes:
            if process.poll() is None:
                print(f"[STOP] Stopping {name} (port {port})...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=8)
                    print(f"[OK] {name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"[WARN] Force killing {name}...")
                    process.kill()

        print("[OK] All integrated system processes stopped")
        print("[BYE] Integrated BHIV system shutdown complete")

    def run(self):
        """Run the complete integrated BHIV system"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.print_banner()

        # Check dependencies
        if not self.check_dependencies():
            print("[ERROR] Dependency check failed. Please install missing packages.")
            return False

        # Start all services in order
        services_started = 0
        total_services = len(self.service_configs)

        print("\n[START] Starting Core Integration Services...")

        # Start BHIV Integrator Core first (most critical)
        if self.start_fastapi_service('bhiv_integrator'):
            services_started += 1

        # Start existing APIs
        api_services = ['main_api', 'crm_api']
        for service in api_services:
            if self.start_fastapi_service(service):
                services_started += 1

        # Start Streamlit dashboards
        streamlit_services = ['crm_dashboard', 'main_dashboard', 'supplier_dashboard',
                            'product_catalog', 'supplier_showcase']
        for service in streamlit_services:
            if self.start_streamlit_service(service):
                services_started += 1

        if services_started == 0:
            print("[ERROR] No services started successfully")
            return False

        # Print comprehensive status
        self.print_system_status()
        self.print_integration_guide()

        if services_started < total_services:
            print(f"[WARN] Only {services_started}/{total_services} services started successfully")
        else:
            print("[SUCCESS] ALL INTEGRATED BHIV SERVICES STARTED SUCCESSFULLY!")

        print(f"\n[CYCLE] Integrated system running ({services_started}/{total_services} services active)")
        print("BHIV_Integrator_Core provides unified event-driven integration")
        print("Full compliance monitoring via Sankalp integration")
        print("AI agent routing and decision support")
        print("Press Ctrl+C to stop all services.")

        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.shutdown()
        return True

def main():
    """Main function"""
    launcher = IntegratedBHIVLauncher()

    try:
        success = launcher.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] Integrated system startup failed: {e}")
        launcher.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()