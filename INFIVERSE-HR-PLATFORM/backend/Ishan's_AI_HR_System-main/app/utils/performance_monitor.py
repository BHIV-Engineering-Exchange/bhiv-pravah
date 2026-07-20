import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int
    response_time_ms: float

class PerformanceMonitor:
    """Monitor system performance and API response times"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.response_times = deque(maxlen=100)
        self.error_counts = {"5min": 0, "1hour": 0, "24hour": 0}
        self.request_counts = {"5min": 0, "1hour": 0, "24hour": 0}
        self.monitoring_active = False
        self._monitor_thread = None
        self._lock = threading.Lock()
        
    def start_monitoring(self, interval_seconds: int = 30):
        """Start performance monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval_seconds,), 
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Performance monitoring started (interval: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metric = self._collect_metrics()
                with self._lock:
                    self.metrics_history.append(metric)
                
                # Check for performance issues
                self._check_performance_alerts(metric)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
            
            time.sleep(interval_seconds)
    
    def _collect_metrics(self) -> PerformanceMetric:
        """Collect current system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        
        # Disk usage
        disk = psutil.disk_usage('.')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # Network connections (approximate active connections)
        connections = len(psutil.net_connections(kind='inet'))
        
        # Average response time from recent requests
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
        
        return PerformanceMetric(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_usage_percent=disk_usage_percent,
            active_connections=connections,
            response_time_ms=avg_response_time
        )
    
    def record_request(self, response_time_ms: float, is_error: bool = False):
        """Record API request metrics"""
        with self._lock:
            self.response_times.append(response_time_ms)
            
            # Update request counts
            for period in self.request_counts:
                self.request_counts[period] += 1
            
            # Update error counts
            if is_error:
                for period in self.error_counts:
                    self.error_counts[period] += 1
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics available"}
        
        latest = self.metrics_history[-1]
        
        # Calculate averages over different periods
        now = datetime.now()
        metrics_5min = [m for m in self.metrics_history if now - m.timestamp <= timedelta(minutes=5)]
        metrics_1hour = [m for m in self.metrics_history if now - m.timestamp <= timedelta(hours=1)]
        
        def avg_metric(metrics_list, attr):
            if not metrics_list:
                return 0
            return sum(getattr(m, attr) for m in metrics_list) / len(metrics_list)
        
        return {
            "timestamp": latest.timestamp.isoformat(),
            "current": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_used_mb": latest.memory_used_mb,
                "disk_usage_percent": latest.disk_usage_percent,
                "active_connections": latest.active_connections,
                "response_time_ms": latest.response_time_ms
            },
            "averages": {
                "5min": {
                    "cpu_percent": avg_metric(metrics_5min, 'cpu_percent'),
                    "memory_percent": avg_metric(metrics_5min, 'memory_percent'),
                    "response_time_ms": avg_metric(metrics_5min, 'response_time_ms')
                },
                "1hour": {
                    "cpu_percent": avg_metric(metrics_1hour, 'cpu_percent'),
                    "memory_percent": avg_metric(metrics_1hour, 'memory_percent'),
                    "response_time_ms": avg_metric(metrics_1hour, 'response_time_ms')
                }
            },
            "request_stats": {
                "total_requests_5min": self.request_counts["5min"],
                "total_errors_5min": self.error_counts["5min"],
                "error_rate_5min": (self.error_counts["5min"] / max(1, self.request_counts["5min"])) * 100
            }
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and health status"""
        metrics = self.get_current_metrics()
        
        if metrics.get("status") == "no_data":
            return metrics
        
        current = metrics["current"]
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if current["cpu_percent"] > 80:
            health_status = "warning"
            issues.append("High CPU usage")
        
        if current["memory_percent"] > 85:
            health_status = "critical" if health_status != "critical" else health_status
            issues.append("High memory usage")
        
        if current["disk_usage_percent"] > 90:
            health_status = "critical"
            issues.append("Low disk space")
        
        if current["response_time_ms"] > 1000:
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append("Slow response times")
        
        error_rate = metrics["request_stats"]["error_rate_5min"]
        if error_rate > 10:
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append("High error rate")
        
        return {
            "health_status": health_status,
            "issues": issues,
            "metrics": metrics,
            "recommendations": self._get_recommendations(current, issues)
        }
    
    def _get_recommendations(self, current: Dict[str, Any], issues: List[str]) -> List[str]:
        """Get performance improvement recommendations"""
        recommendations = []
        
        if "High CPU usage" in issues:
            recommendations.append("Consider scaling horizontally or optimizing CPU-intensive operations")
        
        if "High memory usage" in issues:
            recommendations.append("Review memory usage patterns and consider increasing available RAM")
        
        if "Low disk space" in issues:
            recommendations.append("Clean up old log files and consider expanding storage")
        
        if "Slow response times" in issues:
            recommendations.append("Optimize database queries and consider caching frequently accessed data")
        
        if "High error rate" in issues:
            recommendations.append("Review error logs and fix underlying issues causing failures")
        
        return recommendations
    
    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check for performance alerts and log warnings"""
        if metric.cpu_percent > 90:
            logger.warning(f"Critical CPU usage: {metric.cpu_percent:.1f}%")
        
        if metric.memory_percent > 90:
            logger.warning(f"Critical memory usage: {metric.memory_percent:.1f}%")
        
        if metric.disk_usage_percent > 95:
            logger.critical(f"Critical disk usage: {metric.disk_usage_percent:.1f}%")
        
        if metric.response_time_ms > 2000:
            logger.warning(f"Slow response time: {metric.response_time_ms:.1f}ms")
    
    def get_historical_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical performance data"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        historical_metrics = [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "response_time_ms": m.response_time_ms,
                "active_connections": m.active_connections
            }
            for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        return historical_metrics
    
    def reset_counters(self):
        """Reset request and error counters"""
        with self._lock:
            self.request_counts = {"5min": 0, "1hour": 0, "24hour": 0}
            self.error_counts = {"5min": 0, "1hour": 0, "24hour": 0}
            self.response_times.clear()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Middleware for FastAPI to track request performance
class PerformanceMiddleware:
    """FastAPI middleware to track request performance"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Record response time and status
                response_time_ms = (time.time() - start_time) * 1000
                status_code = message.get("status", 200)
                is_error = status_code >= 400
                
                performance_monitor.record_request(response_time_ms, is_error)
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)