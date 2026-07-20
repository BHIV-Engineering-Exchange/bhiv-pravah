#!/usr/bin/env python3
"""
CRM System Startup Script
"""

import os
import sys
import subprocess
import time
import signal
import threading
from datetime import datetime

class CRMSystemLauncher:
    """Launch and manage CRM system components"""
    
    def __init__(self):
        self.processes = []
        self.running = True
        
    def print_banner(self):
        """Print startup banner"""  
        print("=" * 80)
        print("🏢 AI AGENT CRM SYSTEM")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🚀 Initializing CRM components...")
        print()
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'streamlit',
            'sqlalchemy',
            'pandas',
            'plotly'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} - MISSING")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False
        
        print("✅ All dependencies satisfied")
        return True
    
    def initialize_database(self):
        """Initialize the database"""
        print("\n🗄️ Initializing database...")
        
        try:
            from database.models import init_database
            init_database()
            print("✅ Database initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    
    def start_crm_api(self):
        """Start the CRM API server"""
        print("\n🌐 Starting CRM API server...")
        
        try:
            # Start CRM API on port 8001
            process = subprocess.Popen([
                sys.executable, 'crm_api.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(('CRM API', process))
            
            # Give it time to start
            time.sleep(3)
            
            if process.poll() is None:
                print("✅ CRM API server started on http://localhost:8001")
                print("📚 API Documentation: http://localhost:8001/docs")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ CRM API failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start CRM API: {e}")
            return False
    
    def start_main_api(self):
        """Start the main logistics API server"""
        print("\n🚛 Starting main logistics API server...")
        
        try:
            # Start main API on port 8000
            process = subprocess.Popen([
                sys.executable, 'api_app.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(('Main API', process))
            
            # Give it time to start
            time.sleep(3)
            
            if process.poll() is None:
                print("✅ Main API server started on http://localhost:8000")
                print("📚 API Documentation: http://localhost:8000/docs")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Main API failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start main API: {e}")
            return False
    
    def start_crm_dashboard(self):
        """Start the CRM dashboard"""
        print("\n📊 Starting CRM dashboard...")
        
        try:
            # Start Streamlit dashboard
            process = subprocess.Popen([
                'streamlit', 'run', 'crm_dashboard.py', '--server.port=8501'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(('CRM Dashboard', process))
            
            # Give it time to start
            time.sleep(5)
            
            if process.poll() is None:
                print("✅ CRM Dashboard started on http://localhost:8501")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ CRM Dashboard failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start CRM dashboard: {e}")
            return False
    
    def start_main_dashboard(self):
        """Start the main logistics dashboard"""
        print("\n📈 Starting main logistics dashboard...")
        
        try:
            # Start main dashboard on port 8502
            process = subprocess.Popen([
                'streamlit', 'run', 'dashboard_app.py', '--server.port=8502'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(('Main Dashboard', process))
            
            # Give it time to start
            time.sleep(5)
            
            if process.poll() is None:
                print("✅ Main Dashboard started on http://localhost:8502")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Main Dashboard failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start main dashboard: {e}")
            return False
    
    def print_system_status(self):
        """Print system status and URLs"""
        print("\n" + "=" * 80)
        print("🎯 SYSTEM STATUS")
        print("=" * 80)
        
        print("🌐 API Endpoints:")
        print("   • CRM API:           http://localhost:8001")
        print("   • CRM API Docs:      http://localhost:8001/docs")
        print("   • Main API:          http://localhost:8000")
        print("   • Main API Docs:     http://localhost:8000/docs")
        
        print("\n📊 Dashboards:")
        print("   • CRM Dashboard:     http://localhost:8501")
        print("   • Main Dashboard:    http://localhost:8502")
        
        print("\n🔧 Management:")
        print("   • Health Check:      http://localhost:8001/health")
        print("   • CRM Dashboard:     http://localhost:8001/dashboard")
        
        print("\n📝 Sample API Calls:")
        print("   • Get Accounts:      GET http://localhost:8001/accounts")
        print("   • Get Leads:         GET http://localhost:8001/leads")
        print("   • Get Opportunities: GET http://localhost:8001/opportunities")
        print("   • Get Orders:        GET http://localhost:8000/orders")
        
        print("\n🔑 Integration Setup:")
        print("   • Office 365:        Set OFFICE365_* environment variables")
        print("   • Google Maps:       Set GOOGLE_MAPS_API_KEY environment variable")
        print("   • OpenAI:            Set OPENAI_API_KEY environment variable")
        
        print("\n" + "=" * 80)
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            time.sleep(10)
            
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"⚠️ {name} process has stopped")
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Shutdown all processes"""
        print("\n🔄 Shutting down CRM system...")
        self.running = False
        
        for name, process in self.processes:
            if process.poll() is None:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"✅ {name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"⚠️ Force killing {name}...")
                    process.kill()
        
        print("✅ All processes stopped")
        print("👋 CRM system shutdown complete")
    
    def run(self):
        """Run the complete CRM system"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Dependency check failed. Please install missing packages.")
            return False
        
        # Initialize database
        if not self.initialize_database():
            print("❌ Database initialization failed.")
            return False
        
        # Start services
        services_started = 0
        total_services = 4
        
        if self.start_crm_api():
            services_started += 1
        
        if self.start_main_api():
            services_started += 1
        
        if self.start_crm_dashboard():
            services_started += 1
        
        if self.start_main_dashboard():
            services_started += 1
        
        if services_started == 0:
            print("❌ No services started successfully")
            return False
        
        # Print status
        self.print_system_status()
        
        if services_started < total_services:
            print(f"⚠️ Only {services_started}/{total_services} services started successfully")
        else:
            print("🎉 All services started successfully!")
        
        print("\n🔄 System is running. Press Ctrl+C to stop.")
        
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
    launcher = CRMSystemLauncher()
    
    try:
        success = launcher.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ System startup failed: {e}")
        launcher.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()