"""Server-Sent Events API endpoints"""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from ..models.mcp_task import TaskEvent, LogEntry
from ..workflow_engine import WorkflowEngine
from ..utils.redis_utils import get_project_queue_manager

router = APIRouter(prefix="/events", tags=["events"])


def get_workflow_engine():
    """Dependency to get workflow engine instance"""
    return WorkflowEngine()


def get_queue_manager():
    """Dependency to get queue manager instance"""
    return get_project_queue_manager()


async def task_event_generator(workflow: WorkflowEngine) -> AsyncGenerator[dict, None]:
    """Generate task events for SSE"""
    try:
        while True:
            # Get latest task events from workflow engine
            events = await workflow.get_task_events()
            
            for event in events:
                yield {
                    "event": event.event_type,
                    "data": json.dumps({
                        "task_id": event.task_id,
                        "timestamp": event.timestamp.isoformat(),
                        "data": event.data
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


@router.get("/tasks")
async def stream_task_events(workflow: WorkflowEngine = Depends(get_workflow_engine)):
    """Stream real-time task events via SSE"""
    return EventSourceResponse(task_event_generator(workflow))


@router.get("/metrics")
async def stream_metrics(workflow: WorkflowEngine = Depends(get_workflow_engine)):
    """Stream real-time metrics via SSE"""
    return EventSourceResponse(metrics_event_generator(workflow))


@router.get("/logs")
async def stream_logs(
    level: str = "INFO",
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Stream real-time logs via SSE"""
    return EventSourceResponse(log_event_generator(workflow, level))


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