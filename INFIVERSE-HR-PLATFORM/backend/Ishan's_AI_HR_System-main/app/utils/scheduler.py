import schedule
import time
import threading
from datetime import datetime
from app.utils.database import db_manager
from app.utils.backup_manager import backup_manager
from app.utils.ai_engine import AIEngine
from app.utils.helpers import load_json, save_json
import logging

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Automated task scheduler for system maintenance"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.running = True
            self.setup_jobs()
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Task scheduler stopped")
    
    def setup_jobs(self):
        """Setup scheduled jobs"""
        # Daily backup at 2 AM
        schedule.every().day.at("02:00").do(self.daily_backup)
        
        # Update match scores every 6 hours
        schedule.every(6).hours.do(self.update_match_scores)
        
        # Clean old logs weekly
        schedule.every().sunday.at("03:00").do(self.cleanup_logs)
        
        # System health check every hour
        schedule.every().hour.do(self.health_check)
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def daily_backup(self):
        """Perform daily backup"""
        try:
            backup_manager.create_full_backup()
            logger.info("Daily backup completed")
        except Exception as e:
            logger.error(f"Daily backup failed: {e}")
    
    def update_match_scores(self):
        """Update AI match scores for all candidates"""
        try:
            candidates = load_json("data/candidates.json")
            if isinstance(candidates, list):
                for candidate in candidates:
                    new_score = AIEngine.calculate_match_score(candidate)
                    candidate['match_score'] = new_score
                
                save_json("data/candidates.json", candidates)
                logger.info(f"Updated match scores for {len(candidates)} candidates")
        except Exception as e:
            logger.error(f"Match score update failed: {e}")
    
    def cleanup_logs(self):
        """Clean old logs and data"""
        try:
            db_manager.cleanup_old_logs()
            backup_manager.cleanup_old_backups()
            logger.info("Log cleanup completed")
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")
    
    def health_check(self):
        """Perform system health check"""
        try:
            db_manager.log_system_event("INFO", "scheduled_health_check", "Automated health check")
        except Exception as e:
            logger.error(f"Health check failed: {e}")

# Global scheduler instance
task_scheduler = TaskScheduler()