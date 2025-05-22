"""Metrics and monitoring API endpoints"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Response
from ..models.mcp_task import MetricsResponse
from ..workflow_engine import WorkflowEngine
from ..utils.redis_utils import get_project_queue_manager
from ..utils.prometheus import (
    get_prometheus_metrics, get_metrics_content_type,
    metrics_collector, update_system_metrics, update_queue_metrics,
    update_redis_metrics
)

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


@router.get("/prometheus")
async def get_prometheus_metrics_endpoint(
    workflow: WorkflowEngine = Depends(get_workflow_engine),
    queue_manager = Depends(get_queue_manager)
):
    """Export metrics in Prometheus format"""
    try:
        # Update metrics before export
        await update_metrics_for_prometheus(workflow, queue_manager)
        
        # Get Prometheus formatted metrics
        metrics_data = get_prometheus_metrics()
        
        return Response(
            content=metrics_data,
            media_type=get_metrics_content_type()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export Prometheus metrics: {str(e)}"
        )


@router.get("/analytics")
async def get_analytics_metrics(
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get advanced analytics metrics"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get comprehensive analytics
        analytics = await workflow.get_analytics_metrics(start_time, end_time)
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "task_analytics": analytics.get("task_analytics", {}),
            "performance_analytics": analytics.get("performance_analytics", {}),
            "error_analytics": analytics.get("error_analytics", {}),
            "usage_analytics": analytics.get("usage_analytics", {}),
            "trends": analytics.get("trends", {}),
            "predictions": analytics.get("predictions", {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics metrics: {str(e)}"
        )


@router.get("/performance")
async def get_performance_metrics(
    include_history: bool = Query(False, description="Include performance history"),
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get detailed performance metrics"""
    try:
        performance_data = await workflow.get_performance_metrics(include_history)
        
        return {
            "current": performance_data.get("current", {}),
            "averages": performance_data.get("averages", {}),
            "percentiles": performance_data.get("percentiles", {}),
            "bottlenecks": performance_data.get("bottlenecks", []),
            "recommendations": performance_data.get("recommendations", []),
            "history": performance_data.get("history", []) if include_history else None,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/usage")
async def get_usage_statistics(
    days: int = Query(7, ge=1, le=30, description="Time range in days"),
    breakdown: str = Query("daily", description="Breakdown type: hourly, daily, weekly"),
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get usage statistics and trends"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        usage_stats = await workflow.get_usage_statistics(start_time, end_time, breakdown)
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days,
                "breakdown": breakdown
            },
            "usage_data": usage_stats.get("usage_data", []),
            "summary": usage_stats.get("summary", {}),
            "trends": usage_stats.get("trends", {}),
            "peak_usage": usage_stats.get("peak_usage", {}),
            "projections": usage_stats.get("projections", {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage statistics: {str(e)}"
        )


async def update_metrics_for_prometheus(
    workflow: WorkflowEngine,
    queue_manager
):
    """Update metrics for Prometheus export"""
    try:
        # Update system metrics
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        update_system_metrics(memory_mb, cpu_percent)
        
        # Update queue metrics
        queue_info = queue_manager.get_queue_info()
        for queue_name, size in queue_info.items():
            if isinstance(size, int):
                update_queue_metrics(queue_name, size)
        
        # Update Redis metrics
        redis_info = queue_manager.get_redis_info()
        connections = redis_info.get("connected_clients", 0)
        memory_mb = redis_info.get("used_memory", 0) / 1024 / 1024
        update_redis_metrics(connections, memory_mb)
        
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error updating metrics for Prometheus: {e}")