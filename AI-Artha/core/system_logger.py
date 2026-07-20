#!/usr/bin/env python3
"""
System Logger - Comprehensive logging to MongoDB
Logs all key system events, user actions, and errors to system_logs collection
"""

import time
import json
import traceback
from typing import Dict, Any
from datetime import datetime
from core.mongodb import get_collection

class SystemLogger:
    """Centralized system logger that saves to MongoDB"""
    
    def __init__(self):
        pass
        
    def log(self, level: str, message: str, module: str = None, user_id: str = None, 
            extra_data: Dict[str, Any] = None, error: Exception = None):
        """
        Log system event to MongoDB
        
        Args:
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            message: Log message
            module: Module/component name
            user_id: User ID if applicable
            extra_data: Additional data to log
            error: Exception object if logging an error
        """
        try:
            # Prepare log entry
            log_entry = {
                'level': level.upper(),
                'message': message,
                'module': module or 'system',
                'timestamp': time.time(),
                'user_id': user_id,
                'extra_data': json.dumps(extra_data) if extra_data else None,
                'error_details': str(error) if error else None,
                'traceback': traceback.format_exc() if error else None
            }
            
            # Save to MongoDB
            collection = get_collection("system_logs")
            if collection is not None:
                collection.insert_one(log_entry)
            
            # Print to console for immediate visibility
            timestamp_str = datetime.fromtimestamp(log_entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            console_msg = f"[{timestamp_str}] {level.upper()}: {message}"
            if module:
                console_msg += f" (module: {module})"
            if user_id:
                console_msg += f" (user: {user_id})"
            print(console_msg)
            
        except Exception as log_error:
            # Fallback logging to prevent infinite loops
            print(f"LOGGING ERROR: Failed to log message '{message}': {log_error}")
    
    # Convenience methods for different log levels
    def info(self, message: str, module: str = None, user_id: str = None, extra_data: Dict[str, Any] = None):
        """Log INFO level message"""
        self.log('INFO', message, module, user_id, extra_data)
    
    def warning(self, message: str, module: str = None, user_id: str = None, extra_data: Dict[str, Any] = None):
        """Log WARNING level message"""
        self.log('WARNING', message, module, user_id, extra_data)
    
    def error(self, message: str, module: str = None, user_id: str = None, 
              extra_data: Dict[str, Any] = None, error: Exception = None):
        """Log ERROR level message"""
        self.log('ERROR', message, module, user_id, extra_data, error)
    
    def debug(self, message: str, module: str = None, user_id: str = None, extra_data: Dict[str, Any] = None):
        """Log DEBUG level message"""
        self.log('DEBUG', message, module, user_id, extra_data)
    
    def user_action(self, action: str, user_id: str, details: Dict[str, Any] = None):
        """Log user action"""
        self.info(f"User action: {action}", module="user_actions", user_id=user_id, extra_data=details)
    
    def system_event(self, event: str, details: Dict[str, Any] = None):
        """Log system event"""
        self.info(f"System event: {event}", module="system_events", extra_data=details)
    
    def database_operation(self, operation: str, table: str, user_id: str = None, details: Dict[str, Any] = None):
        """Log database operation"""
        self.info(f"Database {operation} on {table}", module="database", user_id=user_id, extra_data=details)
    
    def api_request(self, endpoint: str, method: str, user_id: str = None, details: Dict[str, Any] = None):
        """Log API request"""
        self.info(f"{method} {endpoint}", module="api", user_id=user_id, extra_data=details)
    
    def get_recent_logs(self, limit: int = 50, level: str = None) -> list:
        """Get recent logs from MongoDB"""
        try:
            collection = get_collection("system_logs")
            if collection is None:
                return []
            
            query = {"level": level.upper()} if level else {}
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            
            logs = []
            for doc in cursor:
                logs.append({
                    'level': doc.get('level'),
                    'message': doc.get('message'),
                    'module': doc.get('module'),
                    'timestamp': doc.get('timestamp'),
                    'user_id': doc.get('user_id'),
                    'extra_data': json.loads(doc['extra_data']) if doc.get('extra_data') else None,
                    'formatted_time': datetime.fromtimestamp(doc['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return logs
            
        except Exception as e:
            print(f"Failed to retrieve logs: {e}")
            return []
    
    def get_log_stats(self) -> list:
        """Get log statistics grouped by module for ERROR level"""
        try:
            collection = get_collection("system_logs")
            if collection is None:
                return []
            
            pipeline = [
                {"$match": {"level": "ERROR"}},
                {"$group": {"_id": "$module", "count": {"$sum": 1}}}
            ]
            result = collection.aggregate(pipeline)
            return list(result)
            
        except Exception as e:
            print(f"Failed to get log stats: {e}")
            return []

# Global logger instance
system_logger = SystemLogger()

# Convenience functions for easy import
def log_info(message: str, module: str = None, user_id: str = None, extra_data: Dict[str, Any] = None):
    system_logger.info(message, module, user_id, extra_data)

def log_warning(message: str, module: str = None, user_id: str = None, extra_data: Dict[str, Any] = None):
    system_logger.warning(message, module, user_id, extra_data)

def log_error(message: str, module: str = None, user_id: str = None, extra_data: Dict[str, Any] = None, error: Exception = None):
    system_logger.error(message, module, user_id, extra_data, error)

def log_user_action(action: str, user_id: str, details: Dict[str, Any] = None):
    system_logger.user_action(action, user_id, details)

def log_system_event(event: str, details: Dict[str, Any] = None):
    system_logger.system_event(event, details)

def log_database_operation(operation: str, table: str, user_id: str = None, details: Dict[str, Any] = None):
    system_logger.database_operation(operation, table, user_id, details)

def log_api_request(endpoint: str, method: str, user_id: str = None, details: Dict[str, Any] = None):
    system_logger.api_request(endpoint, method, user_id, details)