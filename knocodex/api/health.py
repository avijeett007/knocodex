"""Enhanced health monitoring API endpoints"""

import asyncio
import os
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from ..workflow_engine import WorkflowEngine
from ..utils.redis_utils import get_project_queue_manager

router = APIRouter(prefix="/health", tags=["health"])

# Server start time for uptime calculation
SERVER_START_TIME = datetime.utcnow()


def get_workflow_engine():
    """Dependency to get workflow engine instance"""
    return WorkflowEngine()


def get_queue_manager():
    """Dependency to get queue manager instance"""
    return get_project_queue_manager()


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage statistics"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "memory_percent": memory_percent,
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "total_mb": psutil.virtual_memory().total / 1024 / 1024
        }
    except Exception:
        return {"error": "Unable to get memory info"}


def get_cpu_usage() -> Dict[str, float]:
    """Get current CPU usage statistics"""
    try:
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=0.1)
        system_cpu = psutil.cpu_percent(interval=0.1)
        
        return {
            "process_cpu_percent": cpu_percent,
            "system_cpu_percent": system_cpu,
            "cpu_count": psutil.cpu_count(),
            "load_avg": list(os.getloadavg()) if hasattr(os, 'getloadavg') else None
        }
    except Exception:
        return {"error": "Unable to get CPU info"}


def get_server_uptime() -> Dict[str, str]:
    """Get server uptime information"""
    uptime_delta = datetime.utcnow() - SERVER_START_TIME
    return {
        "started_at": SERVER_START_TIME.isoformat(),
        "uptime_seconds": int(uptime_delta.total_seconds()),
        "uptime_human": str(uptime_delta)
    }


async def check_redis_health(queue_manager) -> Dict[str, any]:
    """Check Redis connection and performance"""
    try:
        start_time = datetime.utcnow()
        
        # Test Redis connectivity
        queue_manager.health_check()
        
        # Measure response time
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Get Redis info
        redis_info = queue_manager.get_redis_info()
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "memory_usage_mb": redis_info.get("used_memory", 0) / 1024 / 1024,
            "connected_clients": redis_info.get("connected_clients", 0),
            "total_commands_processed": redis_info.get("total_commands_processed", 0),
            "version": redis_info.get("redis_version", "unknown")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_queue_status(queue_manager) -> Dict[str, any]:
    """Check queue status and performance"""
    try:
        queue_info = queue_manager.get_queue_info()
        worker_info = queue_manager.get_worker_info()
        
        return {
            "status": "healthy",
            "queue_size": queue_info.get("size", 0),
            "active_jobs": queue_info.get("active", 0),
            "failed_jobs": queue_info.get("failed", 0),
            "completed_jobs": queue_info.get("completed", 0),
            "total_workers": worker_info.get("total", 0),
            "active_workers": worker_info.get("active", 0),
            "idle_workers": worker_info.get("idle", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def measure_endpoint_response_times() -> Dict[str, float]:
    """Measure response times for key endpoints"""
    response_times = {}
    
    try:
        # Test workflow engine response time
        start_time = datetime.utcnow()
        workflow = WorkflowEngine()
        await workflow.health_check()
        response_times["workflow_engine_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
    except Exception:
        response_times["workflow_engine_ms"] = -1
    
    return response_times


@router.get("")
async def basic_health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "knocodex-mcp-server"
    }


@router.get("/detailed")
async def detailed_health_check(
    workflow: WorkflowEngine = Depends(get_workflow_engine),
    queue_manager = Depends(get_queue_manager)
):
    """Detailed health check with comprehensive system information"""
    try:
        # Gather all health information
        redis_health = await check_redis_health(queue_manager)
        queue_status = await check_queue_status(queue_manager)
        response_times = await measure_endpoint_response_times()
        
        # Determine overall status
        overall_status = "healthy"
        if (redis_health.get("status") != "healthy" or 
            queue_status.get("status") != "healthy"):
            overall_status = "degraded"
        
        health_data = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "knocodex-mcp-server",
            "uptime": get_server_uptime(),
            "system": {
                "memory": get_memory_usage(),
                "cpu": get_cpu_usage(),
                "response_times": response_times
            },
            "redis": redis_health,
            "queues": queue_status,
            "workflow_engine": {
                "status": "healthy" if await workflow.health_check() else "unhealthy"
            }
        }
        
        # Set appropriate HTTP status code
        status_code = 200 if overall_status == "healthy" else 503
        
        return health_data
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/readiness")
async def readiness_check(
    workflow: WorkflowEngine = Depends(get_workflow_engine),
    queue_manager = Depends(get_queue_manager)
):
    """Kubernetes-style readiness probe"""
    try:
        # Check if service is ready to accept traffic
        await workflow.health_check()
        queue_manager.health_check()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/liveness")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": get_server_uptime()
    }


@router.get("/dependencies")
async def dependencies_check(
    workflow: WorkflowEngine = Depends(get_workflow_engine),
    queue_manager = Depends(get_queue_manager)
):
    """Check status of all external dependencies"""
    dependencies = {}
    
    # Check Redis
    try:
        queue_manager.health_check()
        dependencies["redis"] = {
            "status": "healthy",
            "response_time_ms": (await check_redis_health(queue_manager)).get("response_time_ms", 0)
        }
    except Exception as e:
        dependencies["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check workflow engine
    try:
        await workflow.health_check()
        dependencies["workflow_engine"] = {"status": "healthy"}
    except Exception as e:
        dependencies["workflow_engine"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check file system access
    try:
        test_file = "/tmp/.knocodex_health_check"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        dependencies["filesystem"] = {"status": "healthy"}
    except Exception as e:
        dependencies["filesystem"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Determine overall status
    all_healthy = all(dep.get("status") == "healthy" for dep in dependencies.values())
    overall_status = "healthy" if all_healthy else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": dependencies
    }