#!/usr/bin/env python3
"""
Complete Dashboard Launcher
Starts all CRM, Product Image, and Supplier Management dashboards in one command
"""

import os
import sys
import subprocess
import time
import signal
import threading
from datetime import datetime

class CompleteDashboardLauncher:
    """Launch and manage all dashboard components"""
    
    def __init__(self):
        self.processes = []
        self.running = True
        self.dashboard_configs = {
            'crm_api': {'script': 'crm_api.py', 'port': 8001, 'name': 'CRM API', 'type': 'api'},
            'main_api': {'script': 'api_app.py', 'port': 8000, 'name': 'Main API', 'type': 'api'},
            'crm_dashboard': {'script': 'crm_dashboard.py', 'port': 8501, 'name': 'CRM Dashboard', 'type': 'streamlit'},
            'main_dashboard': {'script': 'dashboard_app.py', 'port': 8502, 'name': 'Main Dashboard', 'type': 'streamlit'},
            'supplier_dashboard': {'script': 'dashboard_with_supplier.py', 'port': 8503, 'name': 'Enhanced Supplier Dashboard', 'type': 'streamlit'},
            'product_catalog': {'script': 'product_catalog_dashboard.py', 'port': 8504, 'name': 'Product Catalog Management', 'type': 'streamlit'},
            'supplier_showcase': {'script': 'supplier_showcase.py', 'port': 8505, 'name': 'Supplier Showcase Portal', 'type': 'streamlit'}
        }
        
    def print_banner(self):
        """Print startup banner"""
        print("=" * 80)
        print("COMPLETE AI AGENT DASHBOARD SYSTEM")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Launching all CRM, Product Image & Supplier Management dashboards...")
        print()
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("[CHECK] Checking dependencies...")
        
        required_packages = [
            'fastapi',
            'uvicorn', 
            'streamlit',
            'sqlalchemy',
            'pandas',
            'plotly',
            'pillow'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                if package.lower() == 'pillow':
                    __import__('PIL')
                else:
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
    
    def setup_directories(self):
        """Create necessary directories for image management"""
        print("\n[DIR] Setting up directories...")
        
        directories = [
            'static/images/products',
            'static/images/thumbnails', 
            'static/images/gallery',
            'static/images/temp'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"[OK] {directory}")
    
    def initialize_database(self):
        """Initialize the database"""
        print("\n[DB] Initializing database...")
        
        try:
            from database.models import init_database
            init_database()
            print("[OK] Database initialized successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Database initialization failed: {e}")
            return False
    
    def start_api_service(self, service_key):
        """Start an API service"""
        config = self.dashboard_configs[service_key]
        print(f"\n[API] Starting {config['name']} on port {config['port']}...")
        
        try:
            if service_key == 'main_api':
                # Start with image support
                process = subprocess.Popen([
                    sys.executable, '-m', 'uvicorn', 'api_app:app',
                    '--host', '0.0.0.0', '--port', str(config['port']), '--reload'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                # Standard API start
                process = subprocess.Popen([
                    sys.executable, config['script']
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append((config['name'], process, config['port']))
            
            # Give it time to start
            time.sleep(3)
            
            if process.poll() is None:
                print(f"[OK] {config['name']} started on http://localhost:{config['port']}")
                if config['port'] in [8000, 8001]:
                    print(f"[DOCS] API Documentation: http://localhost:{config['port']}/docs")
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
        config = self.dashboard_configs[service_key]
        print(f"\n[DASH] Starting {config['name']} on port {config['port']}...")
        
        try:
            process = subprocess.Popen([
                'streamlit', 'run', config['script'], 
                f'--server.port={config["port"]}',
                '--server.headless=true'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append((config['name'], process, config['port']))
            
            # Give it time to start
            time.sleep(5)
            
            if process.poll() is None:
                print(f"[OK] {config['name']} started on http://localhost:{config['port']}")
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
        print("\n" + "=" * 80)
        print("[TARGET] COMPLETE SYSTEM STATUS")
        print("=" * 80)
        
        print("[API] API Endpoints:")
        print("   - CRM API:                http://localhost:8001")
        print("   - CRM API Docs:           http://localhost:8001/docs")
        print("   - Main API (with Images): http://localhost:8000")
        print("   - Main API Docs:          http://localhost:8000/docs")

        print("\n[DASH] All Dashboards:")
        print("   - CRM Dashboard:          http://localhost:8501")
        print("     --> Account Management, Leads, Opportunities, Natural Language Queries")
        print("   - Main Dashboard:         http://localhost:8502")
        print("     --> Logistics, Inventory, AI Agents")
        print("   - Enhanced Supplier:      http://localhost:8503")
        print("     --> Supplier Management, Contact System")
        print("   - Product Catalog:        http://localhost:8504")
        print("     --> Product Management, Image Upload, Catalog")
        print("   - Supplier Showcase:      http://localhost:8505")
        print("     --> Professional Supplier Portal, Marketing")

        print("\n[TOOLS] Management & Utilities:")
        print("   - Health Check:           http://localhost:8001/health")
        print("   - Image Storage:          http://localhost:8000/static/images/")
        print("   - CRM Management:         http://localhost:8001/dashboard")

        print("\n[NOTE] Sample API Calls:")
        print("   - Get CRM Accounts:       GET http://localhost:8001/accounts")
        print("   - Get Leads:              GET http://localhost:8001/leads")
        print("   - Get Opportunities:      GET http://localhost:8001/opportunities")
        print("   - Get Orders:             GET http://localhost:8000/orders")
        print("   - Get Inventory:          GET http://localhost:8000/inventory")

        print("\n[KEY] Integration Configuration:")
        print("   - Office 365:             Set OFFICE365_* environment variables")
        print("   - Google Maps:            Set GOOGLE_MAPS_API_KEY environment variable")
        print("   - OpenAI (NLP Queries):   Set OPENAI_API_KEY environment variable")
        
        print("\n[FEATURE] Features Available:")
        print("   [OK] Complete CRM System (Accounts, Contacts, Leads, Opportunities)")
        print("   [OK] Product Image Management & Upload")
        print("   [OK] Professional Supplier Showcase")
        print("   [OK] AI-Powered Natural Language Queries")
        print("   [OK] Autonomous Logistics Agents")
        print("   [OK] Inventory & Order Management")
        print("   [OK] Email Notifications & Alerts")
        print("   [OK] Performance Analytics & Reports")
        
        print("\n" + "=" * 80)
    
    def print_quick_access_guide(self):
        """Print quick access guide"""
        print("[TARGET] QUICK ACCESS GUIDE:")
        print("=" * 50)
        print("[USER] For CRM & Customer Management:")
        print("   -> http://localhost:8501 (CRM Dashboard)")
        print()
        print("[BOX] For Product & Inventory Management:")
        print("   -> http://localhost:8504 (Product Catalog)")
        print("   -> http://localhost:8502 (Main Dashboard)")
        print()
        print("[STORE] For Supplier Management:")
        print("   -> http://localhost:8503 (Enhanced Supplier)")
        print("   -> http://localhost:8505 (Supplier Showcase)")
        print()
        print("[AI] For AI & Natural Language:")
        print("   -> http://localhost:8501 -> Natural Language Query")
        print("=" * 50)
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            time.sleep(10)
            
            for name, process, port in self.processes:
                if process.poll() is not None:
                    print(f"[WARN] {name} (port {port}) process has stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n[STOP] Received signal {signum}, shutting down all dashboards...")
        self.shutdown()
    
    def shutdown(self):
        """Shutdown all processes"""
        print("\n[CYCLE] Shutting down complete dashboard system...")
        self.running = False
        
        for name, process, port in self.processes:
            if process.poll() is None:
                print(f"[STOP] Stopping {name} (port {port})...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"[OK] {name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"[WARN] Force killing {name}...")
                    process.kill()
        
        print("[OK] All dashboard processes stopped")
        print("[BYE] Complete dashboard system shutdown complete")
    
    def run(self):
        """Run the complete dashboard system"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            print("[ERROR] Dependency check failed. Please install missing packages.")
            return False
        
        # Setup directories
        self.setup_directories()
        
        # Initialize database
        if not self.initialize_database():
            print("[ERROR] Database initialization failed.")
            return False
        
        # Start all services
        services_started = 0
        total_services = len(self.dashboard_configs)
        
        # Start APIs first
        api_services = ['crm_api', 'main_api']
        for service in api_services:
            if self.start_api_service(service):
                services_started += 1
        
        # Start Streamlit dashboards
        streamlit_services = ['crm_dashboard', 'main_dashboard', 'supplier_dashboard', 'product_catalog', 'supplier_showcase']
        for service in streamlit_services:
            if self.start_streamlit_service(service):
                services_started += 1
        
        if services_started == 0:
            print("[ERROR] No services started successfully")
            return False
        
        # Print status
        self.print_system_status()
        self.print_quick_access_guide()
        
        if services_started < total_services:
            print(f"[WARN] Only {services_started}/{total_services} services started successfully")
        else:
            print("[SUCCESS] ALL DASHBOARD SERVICES STARTED SUCCESSFULLY!")
        
        print(f"\n[CYCLE] Complete system running ({services_started}/{total_services} services active)")
        print("Press Ctrl+C to stop all dashboards.")
        
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
    launcher = CompleteDashboardLauncher()
    
    try:
        success = launcher.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] Dashboard system startup failed: {e}")
        launcher.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()