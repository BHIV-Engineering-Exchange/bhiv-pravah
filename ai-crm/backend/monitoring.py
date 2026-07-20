#!/usr/bin/env python3
"""
Comprehensive monitoring and alerting system
Tracks system health, performance, and sends notifications
"""

import os
import time
import json
import smtplib
import psutil
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from database.service import DatabaseService

# AI/ML imports for predictive analytics
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import gym
from gym import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
import requests

class SystemMonitor:
    def __init__(self):
        self.alerts_sent = {}
        self.metrics_history = []
        self.alert_cooldown = 300  # 5 minutes

        # AI/ML components
        self.burnout_model = None
        self.performance_model = None
        self.feedback_rl_agent = None
        self.scaler = StandardScaler()

        # Initialize models
        self._initialize_models()
        
    def collect_system_metrics(self) -> Dict:
        """Collect system performance metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict(),
            "process_count": len(psutil.pids())
        }
    
    def collect_application_metrics(self) -> Dict:
        """Collect application-specific metrics"""
        try:
            with DatabaseService() as db:
                orders = db.get_orders()
                returns = db.get_returns()

                # Calculate business metrics
                total_orders = len(orders)
                pending_orders = len([o for o in orders if o.get('Status') == 'Processing'])
                total_returns = len(returns)

                # Get recent activity (last 24 hours)
                recent_cutoff = datetime.now() - timedelta(hours=24)
                recent_orders = len([o for o in orders if 'OrderDate' in o and
                                    datetime.fromisoformat(o['OrderDate']) > recent_cutoff])

                # Collect employee performance data for AI analysis
                employee_metrics = self._collect_employee_metrics()

                return {
                    "total_orders": total_orders,
                    "pending_orders": pending_orders,
                    "total_returns": total_returns,
                    "recent_orders_24h": recent_orders,
                    "order_processing_rate": recent_orders / 24 if recent_orders > 0 else 0,
                    "employee_metrics": employee_metrics
                }
        except Exception as e:
            return {"error": str(e)}
    
    def check_api_health(self) -> Dict:
        """Check API endpoint health"""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_agent_health(self) -> Dict:
        """Check agent system health"""
        try:
            # Check if agent log file exists and is recent
            log_file = "data/logs.csv"
            if os.path.exists(log_file):
                stat = os.stat(log_file)
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                age_hours = (datetime.now() - last_modified).total_seconds() / 3600
                
                return {
                    "status": "healthy" if age_hours < 1 else "stale",
                    "last_activity": last_modified.isoformat(),
                    "age_hours": age_hours
                }
            else:
                return {"status": "no_activity", "error": "No log file found"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def detect_anomalies(self, metrics: Dict) -> List[Dict]:
        """Detect system anomalies and issues"""
        anomalies = []

        # High resource usage
        if metrics.get("cpu_percent", 0) > 80:
            anomalies.append({
                "type": "high_cpu",
                "severity": "warning",
                "message": f"High CPU usage: {metrics['cpu_percent']:.1f}%"
            })

        if metrics.get("memory_percent", 0) > 85:
            anomalies.append({
                "type": "high_memory",
                "severity": "critical",
                "message": f"High memory usage: {metrics['memory_percent']:.1f}%"
            })

        if metrics.get("disk_percent", 0) > 90:
            anomalies.append({
                "type": "high_disk",
                "severity": "critical",
                "message": f"High disk usage: {metrics['disk_percent']:.1f}%"
            })

        # Application-specific anomalies
        app_metrics = metrics.get("application", {})
        if app_metrics.get("pending_orders", 0) > 100:
            anomalies.append({
                "type": "high_pending_orders",
                "severity": "warning",
                "message": f"High pending orders: {app_metrics['pending_orders']}"
            })

        # API health issues
        api_health = metrics.get("api", {})
        if api_health.get("status") != "healthy":
            anomalies.append({
                "type": "api_unhealthy",
                "severity": "critical",
                "message": f"API unhealthy: {api_health.get('error', 'Unknown error')}"
            })

        # AI-powered employee burnout detection
        employee_anomalies = self._detect_employee_burnout(metrics)
        anomalies.extend(employee_anomalies)

        # AI-powered performance trend analysis
        performance_anomalies = self._detect_performance_trends(metrics)
        anomalies.extend(performance_anomalies)

        return anomalies
    
    def send_email_alert(self, subject: str, body: str) -> bool:
        """Send email alert"""
        try:
            smtp_host = os.getenv("SMTP_HOST")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            alert_recipients = os.getenv("ALERT_RECIPIENTS", "").split(",")
            
            if not all([smtp_host, smtp_user, smtp_password]) or not alert_recipients:
                print("⚠️  Email configuration incomplete, skipping email alert")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = ", ".join(alert_recipients)
            msg['Subject'] = f"[AI Agent Alert] {subject}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"📧 Email alert sent: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    def send_slack_alert(self, message: str) -> bool:
        """Send Slack alert"""
        try:
            webhook_url = os.getenv("SLACK_WEBHOOK_URL")
            if not webhook_url:
                return False
            
            import requests
            payload = {
                "text": f"🚨 AI Agent Alert: {message}",
                "username": "AI Agent Monitor"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"💬 Slack alert sent: {message}")
                return True
            else:
                print(f"❌ Slack alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send Slack alert: {e}")
            return False
    
    def should_send_alert(self, alert_type: str) -> bool:
        """Check if we should send an alert (respects cooldown)"""
        now = time.time()
        last_sent = self.alerts_sent.get(alert_type, 0)
        
        if now - last_sent > self.alert_cooldown:
            self.alerts_sent[alert_type] = now
            return True
        return False
    
    def handle_anomalies(self, anomalies: List[Dict]):
        """Handle detected anomalies"""
        for anomaly in anomalies:
            alert_type = anomaly["type"]
            severity = anomaly["severity"]
            message = anomaly["message"]
            
            if self.should_send_alert(alert_type):
                print(f"🚨 {severity.upper()}: {message}")
                
                # Send alerts based on severity
                if severity == "critical":
                    self.send_email_alert(f"Critical Alert: {alert_type}", message)
                    self.send_slack_alert(message)
                elif severity == "warning":
                    self.send_slack_alert(message)
    
    def generate_health_report(self, metrics: Dict) -> str:
        """Generate comprehensive health report"""
        report = []
        report.append("🏥 AI Agent System Health Report")
        report.append("=" * 40)
        report.append(f"Timestamp: {metrics['timestamp']}")
        report.append("")
        
        # System metrics
        report.append("💻 System Metrics:")
        report.append(f"  CPU Usage: {metrics.get('cpu_percent', 0):.1f}%")
        report.append(f"  Memory Usage: {metrics.get('memory_percent', 0):.1f}%")
        report.append(f"  Disk Usage: {metrics.get('disk_percent', 0):.1f}%")
        report.append("")
        
        # Application metrics
        app_metrics = metrics.get("application", {})
        if app_metrics and "error" not in app_metrics:
            report.append("📊 Application Metrics:")
            report.append(f"  Total Orders: {app_metrics.get('total_orders', 0)}")
            report.append(f"  Pending Orders: {app_metrics.get('pending_orders', 0)}")
            report.append(f"  Total Returns: {app_metrics.get('total_returns', 0)}")
            report.append(f"  Recent Orders (24h): {app_metrics.get('recent_orders_24h', 0)}")
            report.append("")
        
        # API health
        api_health = metrics.get("api", {})
        report.append("🔗 API Health:")
        report.append(f"  Status: {api_health.get('status', 'unknown')}")
        if "response_time" in api_health:
            report.append(f"  Response Time: {api_health['response_time']:.3f}s")
        report.append("")
        
        # Agent health
        agent_health = metrics.get("agent", {})
        report.append("🤖 Agent Health:")
        report.append(f"  Status: {agent_health.get('status', 'unknown')}")
        if "last_activity" in agent_health:
            report.append(f"  Last Activity: {agent_health['last_activity']}")
        
        return "\n".join(report)
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        print("🔍 Running monitoring cycle...")
        
        # Collect all metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            **self.collect_system_metrics(),
            "application": self.collect_application_metrics(),
            "api": self.check_api_health(),
            "agent": self.check_agent_health()
        }
        
        # Store metrics history
        self.metrics_history.append(metrics)
        
        # Keep only last 100 entries
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        # Detect and handle anomalies
        anomalies = self.detect_anomalies(metrics)
        if anomalies:
            self.handle_anomalies(anomalies)
        
        # Save metrics to file
        with open("data/monitoring_metrics.json", "w") as f:
            json.dump(self.metrics_history, f, indent=2)
        
        # Generate and save health report
        report = self.generate_health_report(metrics)
        with open("data/health_report.txt", "w") as f:
            f.write(report)
        
        print(f"✅ Monitoring cycle completed - {len(anomalies)} anomalies detected")

        # Generate personalized feedback using RL
        feedback = self._generate_personalized_feedback(metrics)

        return metrics, anomalies, feedback

    def _initialize_models(self):
        """Initialize AI/ML models"""
        try:
            # Initialize burnout prediction model
            self.burnout_model = RandomForestClassifier(n_estimators=100, random_state=42)

            # Initialize performance forecasting model
            self.performance_model = keras.Sequential([
                layers.Dense(64, activation='relu', input_shape=(10,)),
                layers.Dense(32, activation='relu'),
                layers.Dense(1, activation='linear')
            ])
            self.performance_model.compile(optimizer='adam', loss='mse')

            # Initialize RL environment and agent for feedback
            self.feedback_env = FeedbackEnvironment()
            self.feedback_rl_agent = PPO("MlpPolicy", self.feedback_env, verbose=0)

            print("🤖 AI/ML models initialized successfully")
        except Exception as e:
            print(f"⚠️  Failed to initialize AI/ML models: {e}")

    def _collect_employee_metrics(self) -> Dict:
        """Collect employee performance and wellness metrics"""
        try:
            # Simulate employee data collection (in real implementation, this would come from HR systems)
            # For demo purposes, we'll generate synthetic data
            return {
                "avg_work_hours": np.random.normal(8, 1.5),
                "task_completion_rate": np.random.uniform(0.7, 1.0),
                "error_rate": np.random.uniform(0, 0.1),
                "response_time": np.random.normal(30, 10),
                "break_frequency": np.random.uniform(0.5, 2.0),
                "collaboration_score": np.random.uniform(0.6, 1.0),
                "stress_indicators": np.random.uniform(0, 1.0),
                "engagement_score": np.random.uniform(0.5, 1.0)
            }
        except Exception as e:
            return {"error": str(e)}

    def _detect_employee_burnout(self, metrics: Dict) -> List[Dict]:
        """Predict employee burnout using ML model"""
        anomalies = []
        try:
            if self.burnout_model is None:
                return anomalies

            employee_data = metrics.get("application", {}).get("employee_metrics", {})
            if not employee_data or "error" in employee_data:
                return anomalies

            # Prepare features for burnout prediction
            features = np.array([
                employee_data.get("avg_work_hours", 8),
                employee_data.get("task_completion_rate", 0.8),
                employee_data.get("error_rate", 0.05),
                employee_data.get("response_time", 30),
                employee_data.get("break_frequency", 1.0),
                employee_data.get("collaboration_score", 0.8),
                employee_data.get("stress_indicators", 0.3),
                employee_data.get("engagement_score", 0.7)
            ]).reshape(1, -1)

            # Scale features
            features_scaled = self.scaler.transform(features)

            # Predict burnout probability
            burnout_prob = self.burnout_model.predict_proba(features_scaled)[0][1]

            if burnout_prob > 0.7:
                anomalies.append({
                    "type": "employee_burnout_risk",
                    "severity": "critical",
                    "message": f"High burnout risk detected (probability: {burnout_prob:.2f})",
                    "employee_data": employee_data
                })
            elif burnout_prob > 0.5:
                anomalies.append({
                    "type": "employee_burnout_warning",
                    "severity": "warning",
                    "message": f"Moderate burnout risk detected (probability: {burnout_prob:.2f})",
                    "employee_data": employee_data
                })

        except Exception as e:
            print(f"⚠️  Burnout detection error: {e}")

        return anomalies

    def _detect_performance_trends(self, metrics: Dict) -> List[Dict]:
        """Forecast performance trends using TensorFlow model"""
        anomalies = []
        try:
            if self.performance_model is None or len(self.metrics_history) < 5:
                return anomalies

            # Prepare time series data for forecasting
            recent_metrics = self.metrics_history[-10:]
            features = []

            for m in recent_metrics:
                app_metrics = m.get("application", {})
                emp_metrics = app_metrics.get("employee_metrics", {})

                feature_vector = [
                    app_metrics.get("total_orders", 0),
                    app_metrics.get("pending_orders", 0),
                    app_metrics.get("order_processing_rate", 0),
                    emp_metrics.get("task_completion_rate", 0.8),
                    emp_metrics.get("error_rate", 0.05),
                    emp_metrics.get("engagement_score", 0.7),
                    m.get("cpu_percent", 0),
                    m.get("memory_percent", 0),
                    len(recent_metrics),  # time index
                    1 if m.get("api", {}).get("status") == "healthy" else 0
                ]
                features.append(feature_vector)

            if len(features) >= 5:
                features_array = np.array(features[-5:])
                predictions = self.performance_model.predict(features_array, verbose=0)

                # Check for declining trends
                recent_predictions = predictions[-3:]
                if len(recent_predictions) >= 3:
                    trend = np.polyfit(range(len(recent_predictions)), recent_predictions.flatten(), 1)[0]
                    if trend < -0.1:  # Significant decline
                        anomalies.append({
                            "type": "performance_decline_trend",
                            "severity": "warning",
                            "message": f"Performance decline detected (trend: {trend:.3f})",
                            "trend_data": recent_predictions.tolist()
                        })

        except Exception as e:
            print(f"⚠️  Performance trend detection error: {e}")

        return anomalies

    def _generate_personalized_feedback(self, metrics: Dict) -> Dict:
        """Generate personalized feedback using RL agent"""
        try:
            if self.feedback_rl_agent is None:
                return {"feedback": "RL agent not initialized"}

            # Prepare state for RL agent
            employee_data = metrics.get("application", {}).get("employee_metrics", {})
            app_metrics = metrics.get("application", {})

            state = np.array([
                employee_data.get("task_completion_rate", 0.8),
                employee_data.get("error_rate", 0.05),
                employee_data.get("engagement_score", 0.7),
                employee_data.get("stress_indicators", 0.3),
                app_metrics.get("pending_orders", 0) / 100,  # normalized
                app_metrics.get("order_processing_rate", 0),
                1 if metrics.get("api", {}).get("status") == "healthy" else 0
            ])

            # Get action from RL agent
            action, _ = self.feedback_rl_agent.predict(state, deterministic=True)

            # Map action to feedback type
            feedback_types = [
                "encouragement",
                "break_reminder",
                "training_suggestion",
                "workload_adjustment",
                "positive_reinforcement"
            ]

            feedback_type = feedback_types[action % len(feedback_types)]

            # Generate dynamic reward based on task completion
            task_completion = employee_data.get("task_completion_rate", 0.8)
            reward = task_completion * 10 - employee_data.get("error_rate", 0.05) * 50

            return {
                "feedback_type": feedback_type,
                "reward": reward,
                "personalized_message": self._create_feedback_message(feedback_type, employee_data),
                "action_taken": action
            }

        except Exception as e:
            return {"error": str(e)}

    def _create_feedback_message(self, feedback_type: str, employee_data: Dict) -> str:
        """Create personalized feedback message"""
        messages = {
            "encouragement": "Great job today! Keep up the excellent work on task completion.",
            "break_reminder": "You've been working hard. Consider taking a short break to recharge.",
            "training_suggestion": "Based on your performance, you might benefit from additional training in error reduction.",
            "workload_adjustment": "Your current workload seems optimal. Continue maintaining this balance.",
            "positive_reinforcement": "Outstanding performance! Your engagement and accuracy are exemplary."
        }
        return messages.get(feedback_type, "Keep up the good work!")

    def integrate_hr_systems(self) -> Dict:
        """Integrate with external HR systems (Workday/BambooHR)"""
        results = {}

        try:
            # Workday integration
            workday_url = os.getenv("WORKDAY_API_URL")
            workday_token = os.getenv("WORKDAY_API_TOKEN")

            if workday_url and workday_token:
                headers = {"Authorization": f"Bearer {workday_token}"}
                response = requests.get(f"{workday_url}/employees", headers=headers, timeout=10)

                if response.status_code == 200:
                    results["workday"] = {
                        "status": "success",
                        "employee_count": len(response.json()),
                        "last_sync": datetime.now().isoformat()
                    }
                else:
                    results["workday"] = {"status": "error", "message": f"API error: {response.status_code}"}

            # BambooHR integration
            bamboo_url = os.getenv("BAMBOOHR_API_URL")
            bamboo_key = os.getenv("BAMBOOHR_API_KEY")

            if bamboo_url and bamboo_key:
                headers = {"Authorization": f"Basic {bamboo_key}"}
                response = requests.get(f"{bamboo_url}/employees/directory", headers=headers, timeout=10)

                if response.status_code == 200:
                    results["bamboohr"] = {
                        "status": "success",
                        "data": response.json(),
                        "last_sync": datetime.now().isoformat()
                    }
                else:
                    results["bamboohr"] = {"status": "error", "message": f"API error: {response.status_code}"}

        except Exception as e:
            results["error"] = str(e)

        return results


class FeedbackEnvironment(gym.Env):
    """Custom RL environment for personalized feedback generation"""

    def __init__(self):
        super(FeedbackEnvironment, self).__init__()

        # Action space: different types of feedback
        self.action_space = spaces.Discrete(5)

        # Observation space: employee metrics
        self.observation_space = spaces.Box(low=0, high=1, shape=(7,), dtype=np.float32)

        self.current_state = None
        self.episode_length = 0

    def reset(self):
        """Reset environment"""
        self.current_state = self.observation_space.sample()
        self.episode_length = 0
        return self.current_state

    def step(self, action):
        """Execute action and return reward"""
        self.episode_length += 1

        # Calculate reward based on action appropriateness
        # Higher reward for actions that match employee state
        task_completion = self.current_state[0]
        error_rate = self.current_state[1]
        engagement = self.current_state[2]
        stress = self.current_state[3]

        if action == 0:  # encouragement
            reward = task_completion * 2
        elif action == 1:  # break reminder
            reward = stress * 3 - task_completion
        elif action == 2:  # training suggestion
            reward = error_rate * 4
        elif action == 3:  # workload adjustment
            reward = (1 - engagement) * 2 + stress * 2
        elif action == 4:  # positive reinforcement
            reward = engagement * 3
        else:
            reward = 0

        # Add bonus for task completion linked to logistics deliveries
        logistics_completion_bonus = task_completion * 5

        total_reward = reward + logistics_completion_bonus

        # Episode ends after certain length
        done = self.episode_length >= 10

        # Generate new state (simplified)
        self.current_state = self.observation_space.sample()

        return self.current_state, total_reward, done, {}


def main():
    """Main monitoring loop"""
    monitor = SystemMonitor()

    print("🔍 Starting AI Agent System Monitor with ML/AI capabilities")
    print("Press Ctrl+C to stop")

    try:
        while True:
            metrics, anomalies, feedback = monitor.run_monitoring_cycle()

            # Log AI insights
            if feedback and "error" not in feedback:
                print(f"🤖 AI Feedback: {feedback.get('personalized_message', 'N/A')} (Reward: {feedback.get('reward', 0):.2f})")

            # HR system integration (run less frequently)
            if int(time.time()) % 3600 == 0:  # Every hour
                hr_data = monitor.integrate_hr_systems()
                if hr_data:
                    print(f"🏢 HR Systems sync completed: {len(hr_data)} systems updated")

            # Wait for next cycle
            interval = int(os.getenv("MONITORING_INTERVAL", "60"))  # 1 minute default
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    main()