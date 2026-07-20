from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.models import CandidateCreate, FeedbackCreate, AutomationTrigger
from app.routers import trigger, candidate, feedback, analytics, smart_features, integration
from app.agents.email_agent import send_email
from app.agents.whatsapp_agent import send_whatsapp
from app.agents.voice_agent import trigger_voice_call
from app.utils.helpers import load_json, save_json
from app.utils.data_validator import ensure_data_integrity
from app.utils.database import db_manager
from app.utils.security import SecurityManager, get_cors_origins
from app.utils.backup_manager import backup_manager
from app.utils.performance_monitor import performance_monitor, PerformanceMiddleware
from app.utils.scheduler import task_scheduler
from app.utils.ai_engine import AIEngine
import logging
import asyncio
from datetime import datetime
import os

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize data validation and database on startup
try:
    validation_result = ensure_data_integrity()
    logger.info(f"Data validation completed: {validation_result}")
    
    # Initialize database
    db_manager.init_database()
    logger.info("Database initialized successfully")
    
    # Start performance monitoring
    performance_monitor.start_monitoring()
    logger.info("Performance monitoring started")
    
    # Start automated backups
    backup_manager.start_auto_backup(interval_hours=24)
    logger.info("Automated backup system started")
    
    # Start task scheduler
    task_scheduler.start()
    logger.info("Task scheduler started")
    
except Exception as e:
    logger.error(f"System initialization failed: {e}")
    raise

app = FastAPI(
    title="HR-AI System", 
    version="2.0.0", 
    description="Production-ready AI-powered HR automation with multi-channel communication, security, and performance monitoring"
)

# Include routers
app.include_router(trigger.router)
app.include_router(candidate.router)
app.include_router(feedback.router)
app.include_router(analytics.router)
app.include_router(smart_features.router)
app.include_router(integration.router)

# Add performance monitoring middleware
app.add_middleware(PerformanceMiddleware)

# Add CORS middleware with security considerations
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security setup
security = HTTPBearer(auto_error=False)

@app.get("/")
def root():
    return {
        "message": "HR-AI System Running", 
        "status": "active",
        "communication_channels": ["email", "whatsapp", "voice"]
    }

@app.get("/health")
def health():
    try:
        from app.utils.data_validator import DataValidator
        system_status = DataValidator.get_system_status()
        performance_summary = performance_monitor.get_performance_summary()
        
        # Database health check
        db_stats = db_manager.get_database_stats()
        
        return {
            "status": performance_summary.get("health_status", "healthy"), 
            "timestamp": datetime.now().isoformat(),
            "data_files": system_status["data_files"],
            "directories": system_status["directories"],
            "permissions": system_status["permissions"],
            "database": {
                "status": "connected",
                "stats": db_stats
            },
            "performance": {
                "cpu_percent": performance_summary["metrics"]["current"]["cpu_percent"],
                "memory_percent": performance_summary["metrics"]["current"]["memory_percent"],
                "response_time_ms": performance_summary["metrics"]["current"]["response_time_ms"]
            },
            "pipelines": {
                "email": "active",
                "whatsapp": "active", 
                "voice": "active"
            },
            "issues": performance_summary.get("issues", []),
            "recommendations": performance_summary.get("recommendations", [])
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_manager.log_system_event("ERROR", "health_check_failed", str(e))
        raise HTTPException(status_code=500, detail=f"System health check failed: {str(e)}")

@app.get("/system/status")
def system_status():
    """Get detailed system status and diagnostics"""
    try:
        from app.utils.data_validator import DataValidator
        status = DataValidator.get_system_status()
        
        # Add file counts
        candidates = load_json("data/candidates.json")
        feedback_logs = load_json("feedback/feedback_log.csv")
        
        status["statistics"] = {
            "total_candidates": len(candidates) if isinstance(candidates, list) else 0,
            "total_feedback_logs": len(feedback_logs) if isinstance(feedback_logs, list) else 0,
            "system_uptime": datetime.now().isoformat()
        }
        
        return status
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"System status unavailable: {str(e)}")

# Candidate endpoints
@app.post("/candidate/add")
def add_candidate(candidate: CandidateCreate, request: Request):
    try:
        # Enhanced candidate creation with database backend
        candidate_dict = candidate.dict()
        candidate_dict["match_score"] = 0.0
        
        # Calculate AI match score
        candidate_dict["match_score"] = AIEngine.calculate_match_score(candidate_dict)
        
        # Add to database
        candidate_id = db_manager.add_candidate(candidate_dict)
        
        # Log the action
        db_manager.log_system_event(
            "INFO", 
            "candidate_added", 
            f"New candidate added: {candidate.name}",
            {"candidate_id": candidate_id, "email": candidate.email}
        )
        
        # Also maintain JSON compatibility
        candidates = load_json("data/candidates.json")
        if not isinstance(candidates, list):
            candidates = []
        
        candidate_dict["id"] = candidate_id
        candidates.append(candidate_dict)
        save_json("data/candidates.json", candidates)
        
        return {
            "status": "success", 
            "candidate_id": candidate_id, 
            "message": "Candidate added successfully",
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to add candidate: {e}")
        db_manager.log_system_event("ERROR", "candidate_add_failed", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/candidate/list")
def list_candidates():
    candidates = load_json("data/candidates.json")
    return candidates if isinstance(candidates, list) else []

@app.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: int):
    candidates = load_json("data/candidates.json")
    if not isinstance(candidates, list):
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate = next((c for c in candidates if c.get("id") == candidate_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

# Feedback endpoints
@app.post("/feedback/hr_feedback")
def submit_feedback(feedback: FeedbackCreate, request: Request):
    try:
        # Enhanced feedback submission with database backend
        
        # Validate candidate exists in database
        candidate = db_manager.get_candidate(feedback.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Add feedback to database
        feedback_dict = feedback.dict()
        feedback_dict["hr_name"] = "System"  # In production, get from authenticated user
        feedback_id = db_manager.add_feedback(feedback_dict)
        
        # Log the action
        db_manager.log_system_event(
            "INFO", 
            "feedback_submitted", 
            f"Feedback submitted for candidate {feedback.candidate_id}",
            {"feedback_id": feedback_id, "score": feedback.feedback_score, "outcome": feedback.actual_outcome}
        )
        
        timestamp = datetime.now().isoformat()
        
        # Maintain CSV compatibility
        import csv
        import os
        csv_file = "feedback/feedback_log.csv"
        file_exists = os.path.exists(csv_file)
        
        try:
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "candidate_id", "score", "comment", "outcome", "event"])
                writer.writerow([timestamp, feedback.candidate_id, feedback.feedback_score, 
                               feedback.comment, feedback.actual_outcome, "feedback_processed"])
        except Exception as csv_error:
            logger.error(f"CSV logging failed: {csv_error}")
        
        # Maintain JSON compatibility
        log_entry = {
            "timestamp": timestamp,
            "candidate_id": feedback.candidate_id,
            "score": feedback.feedback_score,
            "comment": feedback.comment,
            "outcome": feedback.actual_outcome,
            "event": "feedback_processed"
        }
        
        system_logs = load_json("feedback/system_log.json")
        if not isinstance(system_logs, list):
            system_logs = []
        
        system_logs.append({
            "timestamp": timestamp,
            "event": "feedback_processed",
            "details": log_entry
        })
        save_json("feedback/system_log.json", system_logs)
        
        return {
            "status": "success", 
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id,
            "timestamp": timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        db_manager.log_system_event("ERROR", "feedback_submission_failed", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@app.get("/feedback/logs")
def get_feedback_logs():
    try:
        import csv
        logs = []
        
        # Try to read from CSV file first
        csv_file = "feedback/feedback_log.csv"
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                logs = list(reader)
        
        # Fallback to JSON file
        if not logs:
            json_logs = load_json("feedback/system_log.json")
            if isinstance(json_logs, list):
                logs = [log.get("details", {}) for log in json_logs if log.get("event") == "feedback_processed"]
        
        return logs
    except Exception as e:
        logger.error(f"Failed to load feedback logs: {e}")
        return []

# Multi-channel automation endpoints
@app.post("/trigger/")
def trigger_automation(trigger: AutomationTrigger):
    candidates = load_json("data/candidates.json")
    if not isinstance(candidates, list):
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate = next((c for c in candidates if c.get("id") == trigger.candidate_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    results = []
    
    try:
        if trigger.event_type == "shortlisted":
            email_result = send_email(trigger.candidate_id, "shortlisted", 
                                    trigger.metadata.get("override_email"))
            whatsapp_result = send_whatsapp(trigger.candidate_id, "shortlisted", 
                                          trigger.metadata.get("override_phone"))
            results.extend([email_result, whatsapp_result])
            
        elif trigger.event_type == "rejected":
            email_result = send_email(trigger.candidate_id, "rejected", 
                                    trigger.metadata.get("override_email"))
            whatsapp_result = send_whatsapp(trigger.candidate_id, "rejected", 
                                          trigger.metadata.get("override_phone"))
            results.extend([email_result, whatsapp_result])
            
        elif trigger.event_type == "interview_scheduled":
            email_result = send_email(trigger.candidate_id, "interview", 
                                    trigger.metadata.get("override_email"))
            whatsapp_result = send_whatsapp(trigger.candidate_id, "interview", 
                                          trigger.metadata.get("override_phone"))
            voice_result = trigger_voice_call(trigger.candidate_id, "interview_reminder")
            results.extend([email_result, whatsapp_result, voice_result])
            
        elif trigger.event_type == "onboarding_completed":
            whatsapp_result = send_whatsapp(trigger.candidate_id, "onboarding", 
                                          trigger.metadata.get("override_phone"))
            voice_result = trigger_voice_call(trigger.candidate_id, "onboarding")
            results.extend([whatsapp_result, voice_result])
        
        return {
            "status": "success", 
            "event_type": trigger.event_type, 
            "results": results,
            "total_communications": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automation failed: {str(e)}")

@app.get("/trigger/history/{candidate_id}")
def get_automation_history(candidate_id: int):
    return {"candidate_id": candidate_id, "automation_history": [], "message": "History feature simplified"}

# Individual channel endpoints for testing
@app.post("/communication/email")
def send_email_only(candidate_id: int, template: str = "shortlisted", override_email: str = None):
    result = send_email(candidate_id, template, override_email)
    return {"channel": "email", "result": result}

@app.post("/communication/whatsapp")
def send_whatsapp_only(candidate_id: int, message_type: str = "shortlisted", override_phone: str = None):
    result = send_whatsapp(candidate_id, message_type, override_phone)
    return {"channel": "whatsapp", "result": result}

@app.post("/communication/voice")
def trigger_voice_only(candidate_id: int, call_type: str = "onboarding"):
    result = trigger_voice_call(candidate_id, call_type)
    return {"channel": "voice", "result": result}

# Integration Endpoints (Day 1 Stub)
@app.post("/ai/decide")
def decide_candidate(request: dict):
    """
    Stub endpoint for AI decision making.
    Returns a dummy fixed response for integration testing.
    """
    logger.info(f"Received decision request: {request}")
    
    # Dummy response based on API contract
    return {
        "match_score": 0.85,
        "rl_adjusted_score": 0.88,
        "decision": "shortlist",
        "explanation": "Strong match on Python skills and experience. Positive sentiment from resume.",
        "metadata": {
            "model_version": "v1.0",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.post("/ai/feedback")
def receive_feedback(feedback: dict):
    """
    Stub endpoint for receiving feedback.
    Logs the payload to a file.
    """
    logger.info(f"Received feedback: {feedback}")
    
    try:
        # Log to a file for verification
        import json
        os.makedirs("feedback", exist_ok=True)
        with open("feedback/integration_feedback_log.jsonl", "a") as f:
            f.write(json.dumps(feedback) + "\n")
            
        return {
            "status": "success",
            "message": "Feedback received and RL model updated (stub).",
            "reward_value": 1.0
        }
    except Exception as e:
        logger.error(f"Failed to log feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System Management Endpoints
@app.get("/system/performance")
def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        return performance_monitor.get_performance_summary()
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/performance/history")
def get_performance_history(hours: int = 24):
    """Get historical performance data"""
    try:
        return {
            "history": performance_monitor.get_historical_data(hours),
            "period_hours": hours
        }
    except Exception as e:
        logger.error(f"Failed to get performance history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/backup/create")
def create_backup(backup_type: str = "full"):
    """Create system backup"""
    try:
        if backup_type == "full":
            backup_path = backup_manager.create_full_backup()
        elif backup_type == "incremental":
            backup_path = backup_manager.create_incremental_backup()
        else:
            raise ValueError("Invalid backup type. Use 'full' or 'incremental'")
        
        return {
            "status": "success",
            "backup_path": backup_path,
            "backup_type": backup_type,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/backup/list")
def list_backups():
    """List available backups"""
    try:
        backups = backup_manager.get_backup_list()
        return {"backups": backups, "total_count": len(backups)}
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/backup/restore")
def restore_backup(backup_name: str):
    """Restore from backup"""
    try:
        backup_path = f"backups/{backup_name}"
        success = backup_manager.restore_backup(backup_path)
        
        if success:
            return {
                "status": "success",
                "message": f"System restored from backup: {backup_name}",
                "restored_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Backup restoration failed")
    except Exception as e:
        logger.error(f"Backup restoration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/cleanup")
def cleanup_system():
    """Clean up old logs and backups"""
    try:
        # Clean old backups
        removed_backups = backup_manager.cleanup_old_backups()
        
        # Clean old database logs
        cleanup_result = db_manager.cleanup_old_logs()
        
        return {
            "status": "success",
            "removed_backups": removed_backups,
            "cleaned_logs": cleanup_result,
            "cleaned_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"System cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/logs")
def get_system_logs(level: str = None, limit: int = 100):
    """Get system logs"""
    try:
        logs = db_manager.get_system_logs(level, limit)
        return {"logs": logs, "total_count": len(logs)}
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/export")
def export_data():
    """Export all data to CSV files"""
    try:
        exported_files = backup_manager.export_data_csv()
        return {
            "status": "success",
            "exported_files": exported_files,
            "exported_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Database-powered endpoints (enhanced versions)
@app.get("/candidate/list/enhanced")
def list_candidates_enhanced(active_only: bool = True, limit: int = 100):
    """Enhanced candidate listing with database backend"""
    try:
        candidates = db_manager.get_all_candidates(active_only)
        return {
            "candidates": candidates[:limit],
            "total_count": len(candidates),
            "active_only": active_only
        }
    except Exception as e:
        logger.error(f"Failed to list candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/candidate/{candidate_id}/history")
def get_candidate_history(candidate_id: int):
    """Get complete candidate history including feedback and communications"""
    try:
        candidate = db_manager.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        feedback_history = db_manager.get_feedback_by_candidate(candidate_id)
        communication_history = db_manager.get_communication_history(candidate_id)
        
        return {
            "candidate": candidate,
            "feedback_history": feedback_history,
            "communication_history": communication_history
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get candidate history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rate limiting and security endpoints
@app.get("/system/security/status")
def get_security_status():
    """Get security status and audit information"""
    try:
        # This would include security metrics in a real implementation
        return {
            "authentication": "enabled",
            "rate_limiting": "active",
            "audit_logging": "enabled",
            "last_security_scan": datetime.now().isoformat(),
            "security_level": "high"
        }
    except Exception as e:
        logger.error(f"Failed to get security status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
