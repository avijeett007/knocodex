"""Metrics and monitoring API endpoints"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from ..models.mcp_task import MetricsResponse
from ..workflow_engine import WorkflowEngine
from ..utils.redis_utils import get_project_queue_manager

router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_workflow_engine():
    """Dependency to get workflow engine instance"""
    return WorkflowEngine()


def get_queue_manager():
    """Dependency to get queue manager instance"""
    return get_project_queue_manager()


@router.get("", response_model=MetricsResponse)
async def get_system_metrics(
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get current system metrics"""
    try:
        metrics = await workflow.get_system_metrics()
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/queue")
async def get_queue_metrics(
    queue_manager = Depends(get_queue_manager)
):
    """Get Redis queue metrics"""
    try:
        # Get queue statistics
        queue_info = queue_manager.get_queue_info()
        
        return {
            "queue_size": queue_info.get("size", 0),
            "active_jobs": queue_info.get("active", 0),
            "failed_jobs": queue_info.get("failed", 0),
            "completed_jobs": queue_info.get("completed", 0),
            "workers": queue_info.get("workers", 0),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue metrics: {str(e)}")


@router.get("/tasks/statistics")
async def get_task_statistics(
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get task statistics for a specific time range"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        stats = await workflow.get_task_statistics(start_time, end_time)
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "task_counts": stats.get("task_counts", {}),
            "completion_times": stats.get("completion_times", {}),
            "success_rate": stats.get("success_rate", 0.0),
            "error_distribution": stats.get("error_distribution", {}),
            "throughput": stats.get("throughput", 0.0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task statistics: {str(e)}")


@router.get("/workers")
async def get_worker_metrics(
    queue_manager = Depends(get_queue_manager)
):
    """Get worker metrics and status"""
    try:
        worker_info = queue_manager.get_worker_info()
        
        return {
            "total_workers": worker_info.get("total", 0),
            "active_workers": worker_info.get("active", 0),
            "idle_workers": worker_info.get("idle", 0),
            "busy_workers": worker_info.get("busy", 0),
            "workers": worker_info.get("workers", []),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker metrics: {str(e)}")


@router.get("/health")
async def health_check(
    workflow: WorkflowEngine = Depends(get_workflow_engine),
    queue_manager = Depends(get_queue_manager)
):
    """System health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # Check workflow engine health
        try:
            await workflow.health_check()
            health_status["services"]["workflow_engine"] = "healthy"
        except Exception as e:
            health_status["services"]["workflow_engine"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check Redis connection
        try:
            queue_manager.health_check()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check worker availability
        try:
            worker_info = queue_manager.get_worker_info()
            if worker_info.get("total", 0) > 0:
                health_status["services"]["workers"] = "healthy"
            else:
                health_status["services"]["workers"] = "no workers available"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["services"]["workers"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Determine overall status code
        status_code = 200 if health_status["status"] == "healthy" else 503
        
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )