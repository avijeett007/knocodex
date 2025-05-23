"""Integration API endpoints for external AI IDE integrations"""

import os
import platform
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from ..workflow_engine import WorkflowEngine
from ..utils.redis_utils import get_project_queue_manager
from ..config import Config

router = APIRouter(prefix="/api/v1", tags=["integration"])


def get_workflow_engine():
    """Dependency to get workflow engine instance"""
    return WorkflowEngine()


def get_queue_manager():
    """Dependency to get queue manager instance"""
    return get_project_queue_manager()


def get_config():
    """Dependency to get config instance"""
    return Config()


@router.get("/cli/options")
async def get_cli_options(
    config: Config = Depends(get_config)
):
    """Get available CLI options and configurations for external integrations"""
    try:
        # Get available CLI commands and options
        cli_options = {
            "commands": {
                "init": {
                    "description": "Initialize knocodex project structure",
                    "options": [
                        {"name": "--project-path", "type": "string", "description": "Path to project root"},
                        {"name": "--template", "type": "string", "description": "Project template to use"},
                        {"name": "--force", "type": "boolean", "description": "Force overwrite existing files"}
                    ]
                },
                "start": {
                    "description": "Start autonomous coding service",
                    "options": [
                        {"name": "--daemon", "type": "boolean", "description": "Run as daemon process"},
                        {"name": "--workers", "type": "integer", "description": "Number of worker processes"},
                        {"name": "--port", "type": "integer", "description": "API server port"}
                    ]
                },
                "stop": {
                    "description": "Stop all services",
                    "options": [
                        {"name": "--force", "type": "boolean", "description": "Force stop all processes"},
                        {"name": "--timeout", "type": "integer", "description": "Timeout in seconds"}
                    ]
                },
                "status": {
                    "description": "Check service status",
                    "options": [
                        {"name": "--detailed", "type": "boolean", "description": "Show detailed status"},
                        {"name": "--json", "type": "boolean", "description": "Output in JSON format"}
                    ]
                },
                "dashboard": {
                    "description": "Start RQ dashboard",
                    "options": [
                        {"name": "--port", "type": "integer", "description": "Dashboard port"},
                        {"name": "--host", "type": "string", "description": "Dashboard host"}
                    ]
                },
                "docs": {
                    "description": "Generate project documentation",
                    "options": [
                        {"name": "--format", "type": "string", "description": "Output format (html, pdf, markdown)"},
                        {"name": "--output", "type": "string", "description": "Output directory"}
                    ]
                }
            },
            "global_options": [
                {"name": "--config", "type": "string", "description": "Configuration file path"},
                {"name": "--verbose", "type": "boolean", "description": "Verbose output"},
                {"name": "--quiet", "type": "boolean", "description": "Suppress output"},
                {"name": "--log-level", "type": "string", "description": "Log level (debug, info, warning, error)"}
            ],
            "environment_variables": [
                {"name": "KNOCODEX_CONFIG", "description": "Path to configuration file"},
                {"name": "KNOCODEX_PROJECT_PATH", "description": "Default project path"},
                {"name": "KNOCODEX_REDIS_URL", "description": "Redis connection URL"},
                {"name": "KNOCODEX_LOG_LEVEL", "description": "Default log level"}
            ],
            "configuration": {
                "config_file_locations": [
                    "~/.knocodex/config.yaml",
                    "./.knocodex/config.yaml",
                    "./knocodex.yaml"
                ],
                "supported_formats": ["yaml", "json", "toml"],
                "schema_version": "1.0"
            },
            "project_structure": {
                "required_directories": [".knocodex", ".knocodex/tasks", ".knocodex/logs"],
                "optional_directories": [".knocodex/templates", ".knocodex/plugins"],
                "config_files": ["config.yaml", "commands.yaml", "templates.yaml"]
            }
        }
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "cli_options": cli_options,
            "system_info": {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "knocodex_version": "1.0.0"  # TODO: Get from setup.py
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get CLI options: {str(e)}"
        )


@router.get("/stats/summary")
async def get_stats_summary(
    timeframe: str = Query("24h", description="Time frame: 1h, 6h, 24h, 7d, 30d"),
    include_trends: bool = Query(True, description="Include trend analysis"),
    workflow: WorkflowEngine = Depends(get_workflow_engine),
    queue_manager = Depends(get_queue_manager)
):
    """Get comprehensive system statistics summary for external integrations"""
    try:
        # Parse timeframe
        timeframe_hours = {
            "1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720
        }.get(timeframe, 24)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=timeframe_hours)
        
        # Get various metrics
        system_metrics = await workflow.get_system_metrics()
        enhanced_metrics = await workflow.get_enhanced_metrics()
        task_stats = await workflow.get_task_statistics(start_time, end_time)
        queue_info = queue_manager.get_queue_info()
        worker_info = queue_manager.get_worker_info()
        
        # Calculate summary statistics
        summary = {
            "overview": {
                "timeframe": timeframe,
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours": timeframe_hours
                },
                "last_updated": datetime.utcnow().isoformat()
            },
            "task_summary": {
                "total_tasks": task_stats.get("task_counts", {}).get("total", 0),
                "completed_tasks": task_stats.get("task_counts", {}).get("completed", 0),
                "failed_tasks": task_stats.get("task_counts", {}).get("failed", 0),
                "pending_tasks": task_stats.get("task_counts", {}).get("pending", 0),
                "success_rate": task_stats.get("success_rate", 0.0),
                "average_completion_time": task_stats.get("completion_times", {}).get("average", 0.0),
                "throughput_per_hour": task_stats.get("throughput", 0.0)
            },
            "system_summary": {
                "memory_usage_mb": system_metrics.memory_usage,
                "cpu_usage_percent": system_metrics.cpu_usage,
                "queue_size": queue_info.get("size", 0),
                "active_workers": worker_info.get("active", 0),
                "total_workers": worker_info.get("total", 0),
                "uptime_hours": system_metrics.uptime / 3600 if system_metrics.uptime else 0
            },
            "performance_summary": {
                "completion_rates": enhanced_metrics.get("task_completion_rates", {}),
                "processing_times": enhanced_metrics.get("worker_performance", {}).get("processing_times", {}),
                "queue_health": enhanced_metrics.get("queue_metrics", {}).get("health_score", 100),
                "error_rate": enhanced_metrics.get("error_metrics", {}).get("error_rate", 0.0)
            },
            "alerts": [],
            "health_status": "healthy"
        }
        
        # Generate alerts based on thresholds
        alerts = []
        
        # High failure rate alert
        if summary["task_summary"]["success_rate"] < 0.9:
            alerts.append({
                "type": "warning",
                "message": f"Task success rate is low: {summary['task_summary']['success_rate']:.1%}",
                "severity": "medium"
            })
        
        # High memory usage alert
        if summary["system_summary"]["memory_usage_mb"] > 1000:
            alerts.append({
                "type": "warning", 
                "message": f"High memory usage: {summary['system_summary']['memory_usage_mb']:.1f}MB",
                "severity": "medium"
            })
        
        # No active workers alert
        if summary["system_summary"]["active_workers"] == 0:
            alerts.append({
                "type": "error",
                "message": "No active workers available",
                "severity": "high"
            })
            summary["health_status"] = "degraded"
        
        # Large queue size alert
        if summary["system_summary"]["queue_size"] > 100:
            alerts.append({
                "type": "warning",
                "message": f"Large queue size: {summary['system_summary']['queue_size']} tasks",
                "severity": "medium"
            })
        
        summary["alerts"] = alerts
        
        # Add trends if requested
        if include_trends:
            try:
                # Simple trend calculation (would be more sophisticated in production)
                prev_start = start_time - timedelta(hours=timeframe_hours)
                prev_stats = await workflow.get_task_statistics(prev_start, start_time)
                
                current_throughput = summary["task_summary"]["throughput_per_hour"]
                prev_throughput = prev_stats.get("throughput", 0.0)
                
                summary["trends"] = {
                    "throughput_change": {
                        "current": current_throughput,
                        "previous": prev_throughput,
                        "change_percent": ((current_throughput - prev_throughput) / prev_throughput * 100) if prev_throughput > 0 else 0,
                        "direction": "up" if current_throughput > prev_throughput else "down" if current_throughput < prev_throughput else "stable"
                    },
                    "success_rate_change": {
                        "current": summary["task_summary"]["success_rate"],
                        "previous": prev_stats.get("success_rate", 0.0),
                        "change_percent": ((summary["task_summary"]["success_rate"] - prev_stats.get("success_rate", 0.0)) * 100),
                        "direction": "up" if summary["task_summary"]["success_rate"] > prev_stats.get("success_rate", 0.0) else "down"
                    }
                }
            except Exception:
                summary["trends"] = {"error": "Unable to calculate trends"}
        
        return {
            "status": "success",
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats summary: {str(e)}"
        )


@router.get("/integration/health")
async def get_integration_health(
    include_details: bool = Query(True, description="Include detailed health information"),
    workflow: WorkflowEngine = Depends(get_workflow_engine),
    queue_manager = Depends(get_queue_manager)
):
    """Comprehensive health check endpoint for external integrations"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "knocodex-mcp-server",
            "version": "1.0.0",  # TODO: Get from setup.py
            "integration_ready": True
        }
        
        # Core service checks
        services_status = {}
        overall_healthy = True
        
        # Check workflow engine
        try:
            await workflow.health_check()
            services_status["workflow_engine"] = {
                "status": "healthy",
                "response_time_ms": 0  # Would measure actual response time
            }
        except Exception as e:
            services_status["workflow_engine"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_healthy = False
        
        # Check Redis/Queue system
        try:
            queue_manager.health_check()
            redis_info = queue_manager.get_redis_info()
            services_status["redis"] = {
                "status": "healthy",
                "version": redis_info.get("redis_version", "unknown"),
                "connected_clients": redis_info.get("connected_clients", 0),
                "memory_usage_mb": redis_info.get("used_memory", 0) / 1024 / 1024
            }
        except Exception as e:
            services_status["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_healthy = False
        
        # Check worker availability
        try:
            worker_info = queue_manager.get_worker_info()
            worker_status = "healthy" if worker_info.get("total", 0) > 0 else "warning"
            if worker_info.get("total", 0) == 0:
                overall_healthy = False
                
            services_status["workers"] = {
                "status": worker_status,
                "total": worker_info.get("total", 0),
                "active": worker_info.get("active", 0),
                "idle": worker_info.get("idle", 0)
            }
        except Exception as e:
            services_status["workers"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_healthy = False
        
        # Check file system access
        try:
            test_file = "/tmp/.knocodex_integration_health_check"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            services_status["filesystem"] = {"status": "healthy"}
        except Exception as e:
            services_status["filesystem"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_healthy = False
        
        # Set overall status
        if not overall_healthy:
            health_data["status"] = "degraded"
            health_data["integration_ready"] = False
        
        health_data["services"] = services_status
        
        # Add detailed information if requested
        if include_details:
            try:
                system_metrics = await workflow.get_system_metrics()
                queue_info = queue_manager.get_queue_info()
                
                health_data["details"] = {
                    "system": {
                        "memory_usage_mb": system_metrics.memory_usage,
                        "cpu_usage_percent": system_metrics.cpu_usage,
                        "uptime_seconds": system_metrics.uptime,
                        "platform": platform.system(),
                        "python_version": platform.python_version()
                    },
                    "queues": {
                        "pending_tasks": queue_info.get("size", 0),
                        "active_jobs": queue_info.get("active", 0),
                        "failed_jobs": queue_info.get("failed", 0),
                        "completed_jobs": queue_info.get("completed", 0)
                    },
                    "api": {
                        "endpoints_available": [
                            "/api/v1/cli/options",
                            "/api/v1/stats/summary", 
                            "/api/v1/integration/health",
                            "/events/metrics",
                            "/tasks",
                            "/health",
                            "/metrics"
                        ],
                        "sse_enabled": True,
                        "authentication": "none"  # TODO: Update when auth is implemented
                    },
                    "capabilities": {
                        "task_management": True,
                        "real_time_metrics": True,
                        "batch_processing": True,
                        "error_tracking": True,
                        "performance_monitoring": True,
                        "external_integrations": True
                    }
                }
            except Exception as e:
                health_data["details"] = {
                    "error": f"Unable to gather detailed information: {str(e)}"
                }
        
        # Set appropriate status code
        status_code = 200 if health_data["status"] == "healthy" else 503
        
        return health_data
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "integration_ready": False
            }
        )