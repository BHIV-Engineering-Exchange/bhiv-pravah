"""
Database-backed agent integration module
Provides database integration for the main restock agent
"""

import pandas as pd
from datetime import datetime, timedelta
from database.service import DatabaseService
from agent import run_agent as run_restock_agent
import os

def get_agent_status():
    """Get agent status and metrics from database"""
    try:
        with DatabaseService() as db_service:
            # Get recent agent logs
            logs = db_service.get_agent_logs(limit=10)
            
            # Get performance metrics
            performance = db_service.get_performance_metrics(days=7)
            
            # Get current counts
            pending_reviews = db_service.get_pending_reviews()
            restock_requests = db_service.get_restock_requests()
            
            # Calculate last run time
            last_run = None
            if logs:
                last_run = logs[0].get('timestamp')
            
            # Calculate success rate from recent logs
            recent_logs = [log for log in logs if log.get('action') != 'error']
            success_rate = len(recent_logs) / len(logs) * 100 if logs else 100
            
            status = {
                "status": "operational",
                "last_run": last_run,
                "success_rate": round(success_rate, 2),
                "automation_rate": performance.get('automation_rate', 0),
                "pending_reviews": len(pending_reviews),
                "restock_requests_pending": len([r for r in restock_requests if r.get('status') == 'pending']),
                "total_logs": len(logs),
                "uptime": "operational",
                "metrics": {
                    "orders_processed": performance.get('orders_processed', 0),
                    "returns_processed": performance.get('returns_processed', 0),
                    "restocks_created": performance.get('restocks_created', 0),
                    "human_reviews": len(pending_reviews)
                }
            }
            
            return status
            
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "last_run": None,
            "success_rate": 0,
            "automation_rate": 0,
            "pending_reviews": 0,
            "restock_requests_pending": 0,
            "total_logs": 0,
            "uptime": "error",
            "metrics": {}
        }

def run_agent():
    """Run the main restock agent and return success status"""
    try:
        # Run the main agent
        success = run_restock_agent()
        
        # Log the agent run to database if possible
        try:
            with DatabaseService() as db_service:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'agent_run',
                    'status': 'success' if success else 'failed',
                    'details': 'Agent run completed' if success else 'Agent run failed'
                }
                # Note: This assumes there's a method to add logs, 
                # but we'll handle the case where it might not exist
                if hasattr(db_service, 'add_agent_log'):
                    db_service.add_agent_log(log_entry)
        except Exception as db_error:
            print(f"Warning: Could not log to database: {db_error}")
        
        return success
        
    except Exception as e:
        print(f"Agent execution error: {e}")
        
        # Try to log the error to database
        try:
            with DatabaseService() as db_service:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'agent_run',
                    'status': 'error',
                    'details': f'Agent run error: {str(e)}'
                }
                if hasattr(db_service, 'add_agent_log'):
                    db_service.add_agent_log(log_entry)
        except Exception as db_error:
            print(f"Warning: Could not log error to database: {db_error}")
        
        return False

def get_agent_health():
    """Get health check for the agent system"""
    try:
        # Check if key files exist
        data_files = [
            "data/returns.xlsx",
            "data/restock_requests.xlsx", 
            "data/logs.csv"
        ]
        
        file_status = {}
        for file_path in data_files:
            file_status[file_path] = os.path.exists(file_path)
        
        # Check database connectivity
        db_status = False
        try:
            with DatabaseService() as db_service:
                db_service.get_orders(limit=1)
                db_status = True
        except:
            db_status = False
        
        all_healthy = all(file_status.values()) and db_status
        
        return {
            "healthy": all_healthy,
            "files": file_status,
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test the functions
    print("Testing agent_db module...")
    
    print("\n1. Agent Status:")
    status = get_agent_status()
    print(f"Status: {status}")
    
    print("\n2. Agent Health:")
    health = get_agent_health()
    print(f"Health: {health}")
    
    print("\n3. Running Agent:")
    result = run_agent()
    print(f"Agent run result: {result}")