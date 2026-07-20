from datetime import datetime, timedelta
from app.utils.database import db_manager
from app.utils.ai_engine import SmartNotifications
from app.utils.helpers import load_json
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    """Smart notification management system"""
    
    @staticmethod
    def schedule_follow_up(candidate_id: int, days: int = 3):
        """Schedule intelligent follow-up notifications"""
        try:
            follow_up_date = datetime.now() + timedelta(days=days)
            
            notification = {
                "candidate_id": candidate_id,
                "type": "follow_up",
                "scheduled_time": follow_up_date.isoformat(),
                "status": "pending",
                "optimal_time": SmartNotifications.get_optimal_send_time()
            }
            
            # Store notification
            notifications = load_json("feedback/notifications.json")
            if not isinstance(notifications, list):
                notifications = []
            
            notifications.append(notification)
            from app.utils.helpers import save_json
            save_json("feedback/notifications.json", notifications)
            
            logger.info(f"Follow-up scheduled for candidate {candidate_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule follow-up: {e}")
            return False
    
    @staticmethod
    def get_pending_notifications():
        """Get pending notifications"""
        try:
            notifications = load_json("feedback/notifications.json")
            if not isinstance(notifications, list):
                return []
            
            now = datetime.now()
            pending = []
            
            for notif in notifications:
                if notif.get("status") == "pending":
                    scheduled_time = datetime.fromisoformat(notif["scheduled_time"])
                    if scheduled_time <= now:
                        pending.append(notif)
            
            return pending
        except Exception as e:
            logger.error(f"Failed to get pending notifications: {e}")
            return []
    
    @staticmethod
    def send_smart_reminder(candidate_id: int, message_type: str = "interview_reminder"):
        """Send AI-optimized reminder"""
        try:
            candidates = load_json("data/candidates.json")
            candidate = next((c for c in candidates if c.get("id") == candidate_id), None)
            
            if not candidate:
                return {"status": "error", "message": "Candidate not found"}
            
            # Personalize message
            template = "Hi {name}, this is a reminder about your upcoming interview. Your skills in {skills} make you a great fit!"
            personalized_msg = SmartNotifications.personalize_message(template, candidate)
            
            # Log the reminder
            db_manager.log_system_event(
                "INFO",
                "smart_reminder_sent",
                f"Smart reminder sent to candidate {candidate_id}",
                {"message": personalized_msg, "type": message_type}
            )
            
            return {
                "status": "success",
                "message": "Smart reminder sent",
                "personalized_content": personalized_msg
            }
        except Exception as e:
            logger.error(f"Smart reminder failed: {e}")
            return {"status": "error", "message": str(e)}