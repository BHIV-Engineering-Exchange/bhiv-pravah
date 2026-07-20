#!/usr/bin/env python3
"""
Real-time Notification Service
Sends email and console alerts for critical system events
"""

import os
import smtplib
import json
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from enum import Enum

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"

class NotificationService:
    def __init__(self):
        self.email_enabled = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "false").lower() == "true"
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.alert_recipients = os.getenv("ALERT_RECIPIENTS", "").split(",")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        
        # Alert history to prevent spam
        self.alert_history = []
        self.max_history = 100
    
    def send_console_alert(self, level: AlertLevel, title: str, message: str, details: Dict = None):
        """Send console alert with formatting"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Color coding for different alert levels
        colors = {
            AlertLevel.INFO: "\033[94m",      # Blue
            AlertLevel.SUCCESS: "\033[92m",   # Green
            AlertLevel.WARNING: "\033[93m",   # Yellow
            AlertLevel.CRITICAL: "\033[91m"   # Red
        }
        reset_color = "\033[0m"
        
        # Icons for different alert levels
        icons = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.SUCCESS: "✅",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨"
        }
        
        color = colors.get(level, "")
        icon = icons.get(level, "📢")
        
        print(f"\n{color}{'='*60}{reset_color}")
        print(f"{color}{icon} {level.value.upper()} ALERT: {title}{reset_color}")
        print(f"{color}Time: {timestamp}{reset_color}")
        print(f"{color}Message: {message}{reset_color}")
        
        if details:
            print(f"{color}Details:{reset_color}")
            for key, value in details.items():
                print(f"{color}  - {key}: {value}{reset_color}")
        
        print(f"{color}{'='*60}{reset_color}\n")
        
        # Log to file
        self._log_alert(level, title, message, details)
    
    def send_email_alert(self, level: AlertLevel, title: str, message: str, details: Dict = None) -> bool:
        """Send email alert"""
        if not self.email_enabled or not self._email_configured():
            self.send_console_alert(AlertLevel.WARNING, "Email Not Configured", 
                                  "Email notifications are disabled or not configured properly")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ", ".join([r.strip() for r in self.alert_recipients if r.strip()])
            msg['Subject'] = f"[AI Agent {level.value.upper()}] {title}"
            
            # Create email body
            body = self._create_email_body(level, title, message, details)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            self.send_console_alert(AlertLevel.SUCCESS, "Email Sent", 
                                  f"Alert email sent to {len(self.alert_recipients)} recipients")
            return True
            
        except Exception as e:
            self.send_console_alert(AlertLevel.CRITICAL, "Email Failed", 
                                  f"Failed to send email alert: {str(e)}")
            return False
    
    def send_slack_alert(self, level: AlertLevel, title: str, message: str, details: Dict = None) -> bool:
        """Send Slack alert"""
        if not self.slack_webhook:
            return False
        
        try:
            # Color coding for Slack
            colors = {
                AlertLevel.INFO: "#36a64f",      # Green
                AlertLevel.SUCCESS: "#36a64f",   # Green
                AlertLevel.WARNING: "#ff9500",   # Orange
                AlertLevel.CRITICAL: "#ff0000"   # Red
            }
            
            # Create Slack payload
            payload = {
                "username": "AI Agent Monitor",
                "icon_emoji": ":robot_face:",
                "attachments": [{
                    "color": colors.get(level, "#36a64f"),
                    "title": f"{level.value.upper()}: {title}",
                    "text": message,
                    "fields": [
                        {
                            "title": "Timestamp",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True
                        }
                    ],
                    "footer": "AI Agent Logistics System",
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            # Add details as fields
            if details:
                for key, value in details.items():
                    payload["attachments"][0]["fields"].append({
                        "title": key,
                        "value": str(value),
                        "short": True
                    })
            
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.send_console_alert(AlertLevel.SUCCESS, "Slack Alert Sent", 
                                      f"Alert sent to Slack channel")
                return True
            else:
                self.send_console_alert(AlertLevel.WARNING, "Slack Alert Failed", 
                                      f"Slack webhook returned {response.status_code}")
                return False
                
        except Exception as e:
            self.send_console_alert(AlertLevel.WARNING, "Slack Alert Error", 
                                  f"Failed to send Slack alert: {str(e)}")
            return False
    
    def send_alert(self, level: AlertLevel, title: str, message: str, details: Dict = None, 
                   channels: List[str] = None):
        """Send alert to multiple channels"""
        if channels is None:
            channels = ["console"]
            if level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
                channels.extend(["email", "slack"])
        
        # Always send console alert
        self.send_console_alert(level, title, message, details)
        
        # Send to other channels based on configuration
        if "email" in channels and level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
            self.send_email_alert(level, title, message, details)
        
        if "slack" in channels:
            self.send_slack_alert(level, title, message, details)
    
    def _email_configured(self) -> bool:
        """Check if email is properly configured"""
        return all([
            self.smtp_user,
            self.smtp_password,
            self.alert_recipients,
            any(r.strip() for r in self.alert_recipients)
        ])
    
    def _create_email_body(self, level: AlertLevel, title: str, message: str, details: Dict = None) -> str:
        """Create HTML email body"""
        colors = {
            AlertLevel.INFO: "#17a2b8",
            AlertLevel.SUCCESS: "#28a745",
            AlertLevel.WARNING: "#ffc107",
            AlertLevel.CRITICAL: "#dc3545"
        }
        
        color = colors.get(level, "#17a2b8")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">{level.value.upper()} ALERT</h1>
                    <h2 style="margin: 10px 0 0 0; font-size: 20px; font-weight: normal;">{title}</h2>
                </div>
                
                <div style="padding: 30px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">Message:</h3>
                        <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #555;">{message}</p>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <p style="margin: 0; color: #666;"><strong>Timestamp:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        <p style="margin: 5px 0 0 0; color: #666;"><strong>System:</strong> AI Agent Logistics System</p>
                    </div>
        """
        
        if details:
            html += """
                    <div style="background-color: #e9ecef; padding: 20px; border-radius: 5px;">
                        <h3 style="margin: 0 0 15px 0; color: #333;">Details:</h3>
                        <table style="width: 100%; border-collapse: collapse;">
            """
            
            for key, value in details.items():
                html += f"""
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; font-weight: bold; color: #495057; width: 30%;">{key}:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; color: #6c757d;">{value}</td>
                            </tr>
                """
            
            html += """
                        </table>
                    </div>
            """
        
        html += """
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #dee2e6;">
                    <p style="margin: 0; color: #6c757d; font-size: 14px;">
                        This is an automated alert from the AI Agent Logistics System.<br>
                        Dashboard: <a href="http://localhost:8501" style="color: #007bff;">http://localhost:8501</a> | 
                        API: <a href="http://localhost:8000" style="color: #007bff;">http://localhost:8000</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _log_alert(self, level: AlertLevel, title: str, message: str, details: Dict = None):
        """Log alert to file"""
        alert_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "title": title,
            "message": message,
            "details": details or {}
        }
        
        self.alert_history.append(alert_entry)
        
        # Keep only recent alerts
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        # Save to file
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/alert_log.json", "w") as f:
                json.dump(self.alert_history, f, indent=2)
        except Exception as e:
            print(f"Failed to log alert: {e}")

# Global notification service instance
notification_service = NotificationService()

# Convenience functions for easy use
def send_info_alert(title: str, message: str, details: Dict = None):
    """Send info alert"""
    notification_service.send_alert(AlertLevel.INFO, title, message, details)

def send_success_alert(title: str, message: str, details: Dict = None):
    """Send success alert"""
    notification_service.send_alert(AlertLevel.SUCCESS, title, message, details)

def send_warning_alert(title: str, message: str, details: Dict = None):
    """Send warning alert"""
    notification_service.send_alert(AlertLevel.WARNING, title, message, details)

def send_critical_alert(title: str, message: str, details: Dict = None):
    """Send critical alert"""
    notification_service.send_alert(AlertLevel.CRITICAL, title, message, details)

# Test function
def test_notifications():
    """Test all notification channels"""
    print("🧪 Testing Notification System...")
    
    # Test console alerts
    send_info_alert("System Test", "Testing info alert", {"test_id": "001", "status": "running"})
    send_success_alert("Operation Complete", "Test operation completed successfully")
    send_warning_alert("Resource Usage", "High memory usage detected", {"memory_usage": "85%", "threshold": "80%"})
    send_critical_alert("System Error", "Critical system error detected", {"error_code": "500", "component": "database"})
    
    print("✅ Notification system test completed")

if __name__ == "__main__":
    test_notifications()