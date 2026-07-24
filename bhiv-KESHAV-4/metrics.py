"""
KESHAV Metrics — Production monitoring and observability

Provides:
- Request metrics (count, latency, errors)
- System metrics (memory, CPU)
- Business metrics (trace_id tracking, severity distribution)
- Health status

Endpoint: GET /metrics (Prometheus format)
"""

import time
from collections import defaultdict
from threading import Lock

_metrics_lock = Lock()
_request_count = 0
_request_errors = 0
_request_latencies: list[float] = []
_severity_counts: dict[str, int] = defaultdict(int)
_trace_ids_processed: set[str] = set()


def record_request_start() -> float:
    """Record request start time."""
    return time.time()


def record_request_success(start_time: float, severity: str, trace_id: str):
    """Record successful request."""
    global _request_count, _request_latencies
    with _metrics_lock:
        _request_count += 1
        _request_latencies.append(time.time() - start_time)
        _severity_counts[severity] += 1
        _trace_ids_processed.add(trace_id)
        
        # Keep only last 1000 latencies
        if len(_request_latencies) > 1000:
            _request_latencies = _request_latencies[-1000:]


def record_request_error(start_time: float):
    """Record failed request."""
    global _request_errors, _request_latencies
    with _metrics_lock:
        _request_errors += 1
        _request_latencies.append(time.time() - start_time)
        
        if len(_request_latencies) > 1000:
            _request_latencies = _request_latencies[-1000:]


def get_metrics() -> dict:
    """Get current metrics snapshot."""
    with _metrics_lock:
        latencies = _request_latencies.copy()
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
        
        return {
            "request_count": _request_count,
            "request_errors": _request_errors,
            "request_success_rate": (
                (_request_count - _request_errors) / _request_count
                if _request_count > 0 else 1.0
            ),
            "avg_latency_seconds": round(avg_latency, 4),
            "p95_latency_seconds": round(p95_latency, 4),
            "p99_latency_seconds": round(p99_latency, 4),
            "severity_distribution": dict(_severity_counts),
            "unique_traces_processed": len(_trace_ids_processed),
        }


def get_prometheus_metrics() -> str:
    """Get metrics in Prometheus format."""
    metrics = get_metrics()
    
    lines = [
        "# HELP keshav_requests_total Total number of requests",
        "# TYPE keshav_requests_total counter",
        f"keshav_requests_total {metrics['request_count']}",
        "",
        "# HELP keshav_request_errors_total Total number of failed requests",
        "# TYPE keshav_request_errors_total counter",
        f"keshav_request_errors_total {metrics['request_errors']}",
        "",
        "# HELP keshav_request_success_rate Request success rate",
        "# TYPE keshav_request_success_rate gauge",
        f"keshav_request_success_rate {metrics['request_success_rate']:.4f}",
        "",
        "# HELP keshav_request_latency_seconds Request latency",
        "# TYPE keshav_request_latency_seconds summary",
        f"keshav_request_latency_seconds{{quantile=\"0.5\"}} {metrics['avg_latency_seconds']}",
        f"keshav_request_latency_seconds{{quantile=\"0.95\"}} {metrics['p95_latency_seconds']}",
        f"keshav_request_latency_seconds{{quantile=\"0.99\"}} {metrics['p99_latency_seconds']}",
        "",
        "# HELP keshav_unique_traces_total Unique trace IDs processed",
        "# TYPE keshav_unique_traces_total counter",
        f"keshav_unique_traces_total {metrics['unique_traces_processed']}",
        "",
    ]
    
    # Severity distribution
    for severity, count in metrics['severity_distribution'].items():
        lines.append(f"keshav_severity_total{{severity=\"{severity}\"}} {count}")
    
    return "\n".join(lines)


def reset_metrics():
    """Reset all metrics (for testing only)."""
    global _request_count, _request_errors, _request_latencies, _severity_counts, _trace_ids_processed
    with _metrics_lock:
        _request_count = 0
        _request_errors = 0
        _request_latencies = []
        _severity_counts.clear()
        _trace_ids_processed.clear()
