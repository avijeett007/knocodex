"""Server-Sent Events API endpoints"""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from ..models.mcp_task import TaskEvent, LogEntry, TaskStatus, TaskType
from ..workflow_engine import WorkflowEngine
from ..utils.redis_utils import get_project_queue_manager

router = APIRouter(prefix="/events", tags=["events"])


def get_workflow_engine():
    """Dependency to get workflow engine instance"""
    return WorkflowEngine()


def get_queue_manager():
    """Dependency to get queue manager instance"""
    return get_project_queue_manager()


async def task_event_generator(
    workflow: WorkflowEngine,
    project_id: Optional[str] = None,
    task_type: Optional[List[TaskType]] = None,
    status: Optional[List[TaskStatus]] = None,
    since: Optional[datetime] = None
) -> AsyncGenerator[dict, None]:
    """Generate task events for SSE with filtering"""
    try:
        while True:
            # Get latest task events from workflow engine with filters
            events = await workflow.get_task_events(
                project_id=project_id,
                task_type=task_type,
                status=status,
                since=since
            )
            
            for event in events:
                # Additional filtering at event level if needed
                if should_include_event(event, project_id, task_type, status):
                    yield {
                        "event": event.event_type,
                        "data": json.dumps({
                            "task_id": event.task_id,
                            "timestamp": event.timestamp.isoformat(),
                            "data": event.data,
                            "project_id": getattr(event, 'project_id', None),
                            "task_type": getattr(event, 'task_type', None),
                            "status": getattr(event, 'status', None)
                        })
                    }
            
            # Wait before checking for new events
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        # Client disconnected
        pass
    except Exception as e:
        # Send error event
        yield {
            "event": "error",
            "data": json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        }


def should_include_event(
    event: TaskEvent,
    project_id: Optional[str] = None,
    task_type: Optional[List[TaskType]] = None,
    status: Optional[List[TaskStatus]] = None
) -> bool:
    """Check if event should be included based on filters"""
    # Project filter
    if project_id and getattr(event, 'project_id', None) != project_id:
        return False
    
    # Task type filter
    if task_type and getattr(event, 'task_type', None) not in task_type:
        return False
    
    # Status filter
    if status and getattr(event, 'status', None) not in status:
        return False
    
    return True


async def metrics_event_generator(workflow: WorkflowEngine) -> AsyncGenerator[dict, None]:
    """Generate metrics events for SSE"""
    try:
        while True:
            # Get latest metrics from workflow engine
            metrics = await workflow.get_system_metrics()
            
            yield {
                "event": "metrics",
                "data": json.dumps({
                    "total_tasks": metrics.total_tasks,
                    "active_tasks": metrics.active_tasks,
                    "completed_tasks": metrics.completed_tasks,
                    "failed_tasks": metrics.failed_tasks,
                    "queue_size": metrics.queue_size,
                    "worker_count": metrics.worker_count,
                    "average_task_duration": metrics.average_task_duration,
                    "success_rate": metrics.success_rate,
                    "last_updated": metrics.last_updated.isoformat()
                })
            }
            
            # Wait before sending next metrics update
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        # Client disconnected
        pass
    except Exception as e:
        # Send error event
        yield {
            "event": "error",
            "data": json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        }


async def log_event_generator(workflow: WorkflowEngine, level: str = "INFO") -> AsyncGenerator[dict, None]:
    """Generate log events for SSE"""
    try:
        while True:
            # Get latest log entries from workflow engine
            logs = await workflow.get_log_entries(level)
            
            for log_entry in logs:
                yield {
                    "event": "log",
                    "data": json.dumps({
                        "timestamp": log_entry.timestamp.isoformat(),
                        "level": log_entry.level,
                        "logger": log_entry.logger,
                        "message": log_entry.message,
                        "task_id": log_entry.task_id,
                        "worker_id": log_entry.worker_id,
                        "extra": log_entry.extra
                    })
                }
            
            # Wait before checking for new logs
            await asyncio.sleep(2)
            
    except asyncio.CancelledError:
        # Client disconnected
        pass
    except Exception as e:
        # Send error event
        yield {
            "event": "error",
            "data": json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        }


async def filtered_log_event_generator(
    workflow: WorkflowEngine,
    level: str = "INFO",
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    worker_id: Optional[str] = None,
    since: Optional[datetime] = None
) -> AsyncGenerator[dict, None]:
    """Generate filtered log events for SSE"""
    try:
        while True:
            # Get latest log entries from workflow engine with filters
            logs = await workflow.get_log_entries(
                level=level,
                project_id=project_id,
                task_id=task_id,
                worker_id=worker_id,
                since=since
            )
            
            for log_entry in logs:
                yield {
                    "event": "log",
                    "data": json.dumps({
                        "timestamp": log_entry.timestamp.isoformat(),
                        "level": log_entry.level,
                        "logger": log_entry.logger,
                        "message": log_entry.message,
                        "task_id": log_entry.task_id,
                        "worker_id": log_entry.worker_id,
                        "project_id": getattr(log_entry, 'project_id', None),
                        "extra": log_entry.extra
                    })
                }
            
            # Wait before checking for new logs
            await asyncio.sleep(2)
            
    except asyncio.CancelledError:
        # Client disconnected
        pass
    except Exception as e:
        # Send error event
        yield {
            "event": "error",
            "data": json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        }


@router.get("/tasks")
async def stream_task_events(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    task_type: Optional[List[TaskType]] = Query(None, description="Filter by task type"),
    status: Optional[List[TaskStatus]] = Query(None, description="Filter by task status"),
    since: Optional[datetime] = Query(None, description="Filter events since timestamp"),
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Stream real-time task events via SSE with advanced filtering"""
    return EventSourceResponse(
        task_event_generator(workflow, project_id, task_type, status, since)
    )


@router.get("/metrics")
async def stream_metrics(workflow: WorkflowEngine = Depends(get_workflow_engine)):
    """Stream real-time metrics via SSE"""
    return EventSourceResponse(metrics_event_generator(workflow))


@router.get("/logs")
async def stream_logs(
    level: str = Query("INFO", description="Minimum log level to stream"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    worker_id: Optional[str] = Query(None, description="Filter by worker ID"),
    since: Optional[datetime] = Query(None, description="Filter logs since timestamp"),
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Stream real-time logs via SSE with advanced filtering"""
    return EventSourceResponse(
        filtered_log_event_generator(workflow, level, project_id, task_id, worker_id, since)
    )


@router.get("/heartbeat")
async def heartbeat():
    """Simple heartbeat endpoint for SSE connection testing"""
    async def heartbeat_generator():
        try:
            while True:
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "alive"
                    })
                }
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass
    
    return EventSourceResponse(heartbeat_generator())