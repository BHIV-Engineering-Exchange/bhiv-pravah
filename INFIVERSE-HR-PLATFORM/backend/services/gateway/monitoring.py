# Advanced Monitoring System for BHIV HR Platform

import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional
import json
import asyncio
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from dataclasses import dataclass
import psutil
import requests

# Configure structured logging
import os
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bhiv_hr_platform.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Prometheus Metrics
resume_processed_total = Counter('resumes_processed_total', 'Total resumes processed', ['status'])
api_response_time = Histogram('api_response_seconds', 'API response time', ['endpoint', 'method'])
active_users = Gauge('active_users_current', 'Current active users')
database_connections = Gauge('database_connections_active', 'Active database connections')
match_success_rate = Gauge('match_success_rate', 'AI matching success rate')
error_rate = Counter('errors_total', 'Total errors', ['error_type', 'service'])

# Business Metrics
job_postings_created = Counter('job_postings_created_total', 'Total job postings created')
candidate_matches_generated = Counter('candidate_matches_total', 'Total candidate matches generated')
portal_page_views = Counter('portal_page_views_total', 'Portal page views', ['portal_type', 'page'])
user_sessions = Counter('user_sessions_total', 'User sessions', ['session_type'])

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    metric_name: str
    value: float
    metadata: Dict

class AdvancedMonitor:
    """Advanced monitoring and metrics collection system"""
    
    def __init__(self):
        self.metrics_buffer = deque(maxlen=10000)
        self.error_buffer = deque(maxlen=1000)
        self.performance_history = defaultdict(list)
        self.alert_thresholds = {
            'api_response_time': 2.0,  # seconds
            'error_rate': 0.05,        # 5%
            'database_connections': 50,
            'memory_usage': 0.85       # 85%
        }
        self.start_time = datetime.now()
        
    def log_resume_processing(self, status: str, processing_time: float, file_size: int):
        """Log resume processing metrics"""
        resume_processed_total.labels(status=status).inc()
        
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name='resume_processing',
            value=processing_time,
            metadata={
                'status': status,
                'file_size': file_size,
                'processing_rate': file_size / processing_time if processing_time > 0 else 0
            }
        )
        self.metrics_buffer.append(metric)
        
        logger.info(f"Resume processed: status={status}, time={processing_time:.2f}s, size={file_size}b")
    
    def log_api_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Log API request metrics"""
        api_response_time.labels(endpoint=endpoint, method=method).observe(response_time)
        
        if status_code >= 400:
            error_rate.labels(error_type=f"http_{status_code}", service="gateway").inc()
            
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name='api_request',
            value=response_time,
            metadata={
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code
            }
        )
        self.metrics_buffer.append(metric)
    
    def log_matching_performance(self, job_id: int, candidates_processed: int, 
                               matches_found: int, processing_time: float):
        """Log AI matching performance"""
        success_rate = matches_found / candidates_processed if candidates_processed > 0 else 0
        match_success_rate.set(success_rate)
        candidate_matches_generated.inc(matches_found)
        
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name='ai_matching',
            value=processing_time,
            metadata={
                'job_id': job_id,
                'candidates_processed': candidates_processed,
                'matches_found': matches_found,
                'success_rate': success_rate
            }
        )
        self.metrics_buffer.append(metric)
        
        logger.info(f"AI matching completed: job_id={job_id}, "
                   f"processed={candidates_processed}, matches={matches_found}, "
                   f"time={processing_time:.2f}s, success_rate={success_rate:.2%}")
    
    def log_user_activity(self, user_id: str, action: str, portal_type: str, page: str = None):
        """Log user activity and engagement"""
        user_sessions.labels(session_type=portal_type).inc()
        
        if page:
            portal_page_views.labels(portal_type=portal_type, page=page).inc()
        
        logger.info(f"User activity: user_id={user_id}, action={action}, "
                   f"portal={portal_type}, page={page}")
    
    def log_error(self, error_type: str, service: str, error_message: str, 
                  stack_trace: str = None, metadata: Dict = None):
        """Log errors with structured information"""
        error_rate.labels(error_type=error_type, service=service).inc()
        
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'service': service,
            'message': error_message,
            'stack_trace': stack_trace,
            'metadata': metadata or {}
        }
        
        self.error_buffer.append(error_data)
        
        logger.error(f"Error logged: {error_type} in {service} - {error_message}")
    
    def collect_system_metrics(self):
        """Collect system-level performance metrics"""
        # CPU and Memory
        # Non-blocking sample (interval=1 added ~1s latency to every /metrics/dashboard call)
        cpu_percent = psutil.cpu_percent(interval=0)
        memory = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage('/')
        except:
            # Windows fallback
            disk = psutil.disk_usage('C:\\')
        
        # Database connections (mock - replace with actual DB monitoring)
        db_connections = self._get_database_connections()
        database_connections.set(db_connections)
        
        # Active users (mock - replace with actual session tracking)
        active_user_count = self._get_active_users()
        active_users.set(active_user_count)
        
        system_metrics = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available': memory.available,
            'disk_percent': disk.percent,
            'database_connections': db_connections,
            'active_users': active_user_count
        }
        
        # Check for alerts
        self._check_system_alerts(system_metrics)
        
        return system_metrics
    
    def _get_database_connections(self) -> int:
        """Get current database connection count"""
        # Mock implementation - replace with actual database monitoring
        return len(self.metrics_buffer) % 20 + 5
    
    def _get_active_users(self) -> int:
        """Get current active user count"""
        # Mock implementation - replace with actual session tracking
        recent_activity = [m for m in self.metrics_buffer 
                          if m.timestamp > datetime.now() - timedelta(minutes=15)]
        return len(set(m.metadata.get('user_id') for m in recent_activity 
                      if m.metadata.get('user_id')))
    
    def _check_system_alerts(self, metrics: Dict):
        """Check system metrics against alert thresholds"""
        alerts = []
        
        if metrics['memory_percent'] > self.alert_thresholds['memory_usage'] * 100:
            alerts.append({
                'type': 'HIGH_MEMORY_USAGE',
                'severity': 'WARNING',
                'message': f"Memory usage at {metrics['memory_percent']:.1f}%",
                'threshold': f"{self.alert_thresholds['memory_usage'] * 100}%"
            })
        
        if metrics['database_connections'] > self.alert_thresholds['database_connections']:
            alerts.append({
                'type': 'HIGH_DB_CONNECTIONS',
                'severity': 'WARNING',
                'message': f"Database connections: {metrics['database_connections']}",
                'threshold': self.alert_thresholds['database_connections']
            })
        
        for alert in alerts:
            logger.warning(f"ALERT: {alert['type']} - {alert['message']}")
    
    def get_performance_summary(self, hours: int = 24) -> Dict:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_buffer if m.timestamp > cutoff_time]
        
        summary = {
            'time_period': f"Last {hours} hours",
            'total_requests': len([m for m in recent_metrics if m.metric_name == 'api_request']),
            'avg_response_time': 0,
            'error_count': len([m for m in recent_metrics if 'error' in m.metadata.get('status', '')]),
            'resumes_processed': len([m for m in recent_metrics if m.metric_name == 'resume_processing']),
            'matches_generated': sum(m.metadata.get('matches_found', 0) 
                                   for m in recent_metrics if m.metric_name == 'ai_matching'),
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
        }
        
        # Calculate average response time
        api_metrics = [m for m in recent_metrics if m.metric_name == 'api_request']
        if api_metrics:
            summary['avg_response_time'] = sum(m.value for m in api_metrics) / len(api_metrics)
        
        return summary
    
    def get_business_metrics(self) -> Dict:
        """Get business-specific metrics"""
        try:
            # Get metric values safely
            job_count = 0
            matches_count = 0
            resumes_count = 0
            users_count = 0
            
            # Try to get actual values from Prometheus metrics
            try:
                job_count = job_postings_created._value._value
            except:
                job_count = 0
                
            try:
                matches_count = candidate_matches_generated._value._value
            except:
                matches_count = 0
                
            try:
                resumes_count = sum(sample.value for sample in resume_processed_total.collect()[0].samples)
            except:
                resumes_count = 0
                
            try:
                users_count = active_users._value._value
            except:
                users_count = 0
            
            return {
                'total_job_postings': job_count,
                'total_matches_generated': matches_count,
                'total_resumes_processed': resumes_count,
                'current_active_users': users_count,
                'platform_uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
            }
        except Exception as e:
            logger.error(f"Error getting business metrics: {e}")
            return {
                'total_job_postings': 0,
                'total_matches_generated': 0,
                'total_resumes_processed': 0,
                'current_active_users': 0,
                'platform_uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
            }
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return generate_latest()
    
    def health_check(self) -> Dict:
        """Comprehensive health check"""
        system_metrics = self.collect_system_metrics()
        performance_summary = self.get_performance_summary(1)  # Last hour
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': system_metrics['cpu_percent'],
                'memory_percent': system_metrics['memory_percent'],
                'disk_percent': system_metrics['disk_percent']
            },
            'application': {
                'uptime_hours': performance_summary['uptime_hours'],
                'avg_response_time': performance_summary['avg_response_time'],
                'error_rate': performance_summary['error_count'] / max(performance_summary['total_requests'], 1)
            },
            'database': {
                'connections': system_metrics['database_connections'],
                'status': 'connected'
            }
        }
        
        # Determine overall health status
        if (system_metrics['memory_percent'] > 90 or 
            performance_summary['avg_response_time'] > 5.0 or
            health_status['application']['error_rate'] > 0.1):
            health_status['status'] = 'degraded'
        
        return health_status

# Global monitor instance
monitor = AdvancedMonitor()

# Middleware for automatic request monitoring
class MonitoringMiddleware:
    """FastAPI middleware for automatic monitoring"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Process request
            await self.app(scope, receive, send)
            
            # Log metrics
            response_time = time.time() - start_time
            endpoint = scope.get("path", "unknown")
            method = scope.get("method", "unknown")
            
            monitor.log_api_request(endpoint, method, response_time, 200)  # Assume 200 for now
        else:
            await self.app(scope, receive, send)

# Utility functions for easy integration
def log_resume_processing(status: str, processing_time: float, file_size: int):
    """Convenience function for logging resume processing"""
    monitor.log_resume_processing(status, processing_time, file_size)

def log_matching_performance(job_id: int, candidates_processed: int, 
                           matches_found: int, processing_time: float):
    """Convenience function for logging matching performance"""
    monitor.log_matching_performance(job_id, candidates_processed, matches_found, processing_time)

def log_user_activity(user_id: str, action: str, portal_type: str, page: str = None):
    """Convenience function for logging user activity"""
    monitor.log_user_activity(user_id, action, portal_type, page)

def log_error(error_type: str, service: str, error_message: str, 
              stack_trace: str = None, metadata: Dict = None):
    """Convenience function for logging errors"""
    monitor.log_error(error_type, service, error_message, stack_trace, metadata)
