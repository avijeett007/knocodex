"""Prometheus metrics integration"""

from datetime import datetime
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


# Task metrics
task_counter = Counter(
    'mcp_tasks_total',
    'Total number of MCP tasks',
    ['project_id', 'task_type', 'status']
)

task_duration = Histogram(
    'mcp_task_duration_seconds',
    'Task execution duration in seconds',
    ['project_id', 'task_type']
)

# API metrics
api_requests = Counter(
    'mcp_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_duration = Histogram(
    'mcp_api_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# SSE metrics
sse_connections = Gauge(
    'mcp_sse_connections_active',
    'Number of active SSE connections',
    ['event_type']
)

sse_messages = Counter(
    'mcp_sse_messages_total',
    'Total SSE messages sent',
    ['event_type']
)

# System metrics
system_memory = Gauge(
    'mcp_system_memory_mb',
    'System memory usage in MB',
    ['type']
)

system_cpu = Gauge(
    'mcp_system_cpu_percent',
    'System CPU usage percentage'
)

# Queue metrics
queue_size = Gauge(
    'mcp_queue_size',
    'Number of items in queue',
    ['queue_name']
)

queue_processing_time = Histogram(
    'mcp_queue_processing_seconds',
    'Queue item processing time',
    ['queue_name']
)

# Redis metrics
redis_connections = Gauge(
    'mcp_redis_connections',
    'Number of Redis connections'
)

redis_memory = Gauge(
    'mcp_redis_memory_mb',
    'Redis memory usage in MB'
)

redis_operations = Counter(
    'mcp_redis_operations_total',
    'Total Redis operations',
    ['operation']
)


def record_task_metrics(
    project_id: str,
    task_type: str,
    status: str,
    duration_seconds: float = None
):
    """Record task-related metrics"""
    try:
        task_counter.labels(
            project_id=project_id,
            task_type=task_type,
            status=status
        ).inc()
        
        if duration_seconds is not None:
            task_duration.labels(
                project_id=project_id,
                task_type=task_type
            ).observe(duration_seconds)
    except Exception:
        # Silently ignore metrics errors to prevent breaking application flow
        pass


def record_api_metrics(
    method: str,
    endpoint: str,
    status_code: int,
    duration_seconds: float
):
    """Record API request metrics"""
    api_requests.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code
    ).inc()
    
    if duration_seconds is not None:
        api_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration_seconds)


def record_sse_connection(event_type: str, connected: bool):
    """Record SSE connection metrics"""
    if connected:
        sse_connections.labels(event_type=event_type).inc()
    else:
        sse_connections.labels(event_type=event_type).dec()


def record_sse_message(event_type: str):
    """Record SSE message sent"""
    sse_messages.labels(event_type=event_type).inc()


def update_system_metrics(memory_mb: float, cpu_percent: float):
    """Update system metrics"""
    system_memory.labels(type='process').set(memory_mb)
    system_cpu.set(cpu_percent)


def update_queue_metrics(queue_name: str, size: int):
    """Update queue metrics"""
    queue_size.labels(queue_name=queue_name).set(size)


def record_queue_processing(queue_name: str, duration_seconds: float):
    """Record queue processing time"""
    queue_processing_time.labels(queue_name=queue_name).observe(duration_seconds)


def update_redis_metrics(connections: int, memory_mb: float):
    """Update Redis metrics"""
    redis_connections.set(connections)
    redis_memory.set(memory_mb)


def record_redis_operation(operation: str):
    """Record Redis operation"""
    redis_operations.labels(operation=operation).inc()


def get_prometheus_metrics() -> str:
    """Get Prometheus metrics in text format"""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get Prometheus metrics content type"""
    return CONTENT_TYPE_LATEST


class MetricsCollector:
    """Centralized metrics collection"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    def collect_task_metrics(self, tasks: list) -> Dict[str, Any]:
        """Collect task-related metrics"""
        metrics = {
            "total_tasks": len(tasks),
            "tasks_by_status": {},
            "tasks_by_type": {},
            "tasks_by_project": {}
        }
        
        for task in tasks:
            # Count by status
            status = task.get('status', 'unknown')
            metrics["tasks_by_status"][status] = metrics["tasks_by_status"].get(status, 0) + 1
            
            # Count by type
            task_type = task.get('task_type', 'unknown')
            metrics["tasks_by_type"][task_type] = metrics["tasks_by_type"].get(task_type, 0) + 1
            
            # Count by project
            project_id = task.get('project_id', 'unknown')
            metrics["tasks_by_project"][project_id] = metrics["tasks_by_project"].get(project_id, 0) + 1
        
        return metrics
    
    def collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.utcnow().isoformat()
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()