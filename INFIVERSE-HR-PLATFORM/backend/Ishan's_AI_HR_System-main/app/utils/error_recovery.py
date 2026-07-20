import os
import json
import csv
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorRecovery:
    """Handles system errors and provides recovery mechanisms"""
    
    @staticmethod
    def safe_file_operation(operation_func, file_path: str, fallback_data=None, max_retries: int = 3):
        """Safely perform file operations with retry logic"""
        for attempt in range(max_retries):
            try:
                return operation_func()
            except PermissionError as e:
                logger.warning(f"Permission error on {file_path} (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return ErrorRecovery._handle_permission_error(file_path, fallback_data)
            except FileNotFoundError as e:
                logger.warning(f"File not found {file_path} (attempt {attempt + 1}): {e}")
                return ErrorRecovery._create_missing_file(file_path, fallback_data)
            except Exception as e:
                logger.error(f"Unexpected error with {file_path} (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return fallback_data
        
        return fallback_data
    
    @staticmethod
    def _handle_permission_error(file_path: str, fallback_data):
        """Handle permission errors by using alternative storage"""
        logger.error(f"Cannot write to {file_path} due to permissions")
        
        # Try to write to a backup location
        backup_path = f"{file_path}.backup"
        try:
            if file_path.endswith('.json'):
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(fallback_data or {}, f, indent=2)
            elif file_path.endswith('.csv'):
                with open(backup_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if fallback_data:
                        writer.writerows(fallback_data)
            
            logger.info(f"Data saved to backup location: {backup_path}")
            return fallback_data
        except Exception as e:
            logger.error(f"Failed to create backup file: {e}")
            return fallback_data
    
    @staticmethod
    def _create_missing_file(file_path: str, fallback_data):
        """Create missing file with fallback data"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(fallback_data or [], f, indent=2)
            elif file_path.endswith('.csv'):
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if fallback_data:
                        writer.writerows(fallback_data)
            
            logger.info(f"Created missing file: {file_path}")
            return fallback_data
        except Exception as e:
            logger.error(f"Failed to create missing file {file_path}: {e}")
            return fallback_data
    
    @staticmethod
    def log_error(error: Exception, context: str, additional_info: Optional[Dict[str, Any]] = None):
        """Log errors with context and additional information"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "additional_info": additional_info or {}
        }
        
        # Try to log to system log
        try:
            system_logs = []
            if os.path.exists("feedback/system_log.json"):
                with open("feedback/system_log.json", 'r', encoding='utf-8') as f:
                    system_logs = json.load(f)
            
            system_logs.append({
                "timestamp": error_entry["timestamp"],
                "event": "error_logged",
                "details": error_entry
            })
            
            with open("feedback/system_log.json", 'w', encoding='utf-8') as f:
                json.dump(system_logs, f, indent=2)
        
        except Exception as log_error:
            logger.error(f"Failed to log error to system log: {log_error}")
        
        # Always log to Python logger
        logger.error(f"Error in {context}: {error}")
        if additional_info:
            logger.error(f"Additional info: {additional_info}")
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get system health status with error recovery information"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "issues": [],
            "recovery_actions": []
        }
        
        # Check critical files
        critical_files = [
            "data/candidates.json",
            "feedback/system_log.json",
            "feedback/feedback_log.csv"
        ]
        
        for file_path in critical_files:
            if not os.path.exists(file_path):
                health_status["issues"].append(f"Missing file: {file_path}")
                health_status["recovery_actions"].append(f"Will create {file_path} on next operation")
                health_status["status"] = "degraded"
            else:
                try:
                    # Test file access
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.read(1)
                except Exception as e:
                    health_status["issues"].append(f"Cannot read {file_path}: {e}")
                    health_status["status"] = "degraded"
        
        return health_status