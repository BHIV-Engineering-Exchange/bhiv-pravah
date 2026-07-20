#!/usr/bin/env python3
"""
Start monitoring service with real-time notifications
"""

import os
import time
import threading
import subprocess
from datetime import datetime
from notification_service import send_info_alert, send_success_alert, send_warning_alert, send_critical_alert

def monitor_system():
    """Monitor system health and send alerts"""
    print("🔍 Starting system monitoring with real-time alerts...")
    
    send_info_alert("Monitoring Started", "System monitoring service has been activated")
    
    try:
        while True:
            # Import monitoring here to avoid circular imports
            from monitoring import SystemMonitor
            
            monitor = SystemMonitor()
            metrics, anomalies = monitor.run_monitoring_cycle()
            
            # Send alerts for any anomalies detected
            for anomaly in anomalies:
                if anomaly["severity"] == "critical":
                    send_critical_alert(f"Critical: {anomaly['type']}", anomaly["message"])
                elif anomaly["severity"] == "warning":
                    send_warning_alert(f"Warning: {anomaly['type']}", anomaly["message"])
            
            # Wait for next monitoring cycle
            interval = int(os.getenv("MONITORING_INTERVAL", "60"))
            time.sleep(interval)
            
    except KeyboardInterrupt:
        send_info_alert("Monitoring Stopped", "System monitoring service has been stopped")
        print("\n🛑 Monitoring stopped")
    except Exception as e:
        send_critical_alert("Monitoring Error", f"System monitoring encountered an error: {str(e)}")
        print(f"❌ Monitoring error: {e}")

def run_agent_with_notifications():
    """Run agent cycles with notifications"""
    print("🤖 Starting agent monitoring...")
    
    try:
        while True:
            from agent import run_agent
            
            # Run agent cycle
            success = run_agent()
            
            if not success:
                send_critical_alert("Agent Failure", "Agent cycle failed - check logs for details")
            
            # Wait for next agent cycle
            interval = int(os.getenv("AGENT_INTERVAL", "300"))  # 5 minutes
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Agent monitoring stopped")
    except Exception as e:
        send_critical_alert("Agent Monitor Error", f"Agent monitoring encountered an error: {str(e)}")
        print(f"❌ Agent monitor error: {e}")

def main():
    """Main function to start all monitoring services"""
    print("🚀 Starting AI Agent Monitoring with Real-time Notifications")
    print("=" * 60)
    
    # Start system monitoring in background thread
    system_monitor_thread = threading.Thread(target=monitor_system, daemon=True)
    system_monitor_thread.start()
    
    # Start agent monitoring in background thread
    agent_monitor_thread = threading.Thread(target=run_agent_with_notifications, daemon=True)
    agent_monitor_thread.start()
    
    print("✅ All monitoring services started")
    print("📧 Email notifications:", "ENABLED" if os.getenv("ENABLE_EMAIL_NOTIFICATIONS") == "true" else "DISABLED")
    print("💬 Slack notifications:", "ENABLED" if os.getenv("SLACK_WEBHOOK_URL") else "DISABLED")
    print("📊 Console notifications: ENABLED")
    print("\nPress Ctrl+C to stop monitoring")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down monitoring services...")
        send_info_alert("System Shutdown", "AI Agent monitoring services are shutting down")

if __name__ == "__main__":
    main()