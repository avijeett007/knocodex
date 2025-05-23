"""MCP Task Models

This module defines data models for MCP (Model Context Protocol) tasks
that can be submitted through the MCP server API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task type enumeration"""
    ANALYZE_ISSUE = "analyze_issue"
    IMPLEMENT_ISSUE = "implement_issue"
    REVIEW_PR = "review_pr"
    DOCUMENT_PROJECT = "document_project"
    CUSTOM_COMMAND = "custom_command"


class TaskPriority(str, Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MCPTaskRequest(BaseModel):
    """Request model for creating new MCP tasks"""
    model_config = ConfigDict(extra="forbid")
    
    task_type: TaskType = Field(..., description="Type of task to execute")
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str = Field(..., min_length=1, description="Detailed task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task-specific parameters")
    tags: List[str] = Field(default_factory=list, description="Task tags for organization")
    project_id: Optional[str] = Field(default=None, description="Project identifier")
    assignee: Optional[str] = Field(default=None, description="Task assignee")
    deadline: Optional[datetime] = Field(default=None, description="Task deadline")


class MCPTaskUpdate(BaseModel):
    """Request model for updating existing MCP tasks"""
    model_config = ConfigDict(extra="forbid")
    
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1)
    priority: Optional[TaskPriority] = Field(default=None)
    parameters: Optional[Dict[str, Any]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    assignee: Optional[str] = Field(default=None)
    deadline: Optional[datetime] = Field(default=None)


class MCPTaskResponse(BaseModel):
    """Response model for MCP tasks"""
    model_config = ConfigDict(from_attributes=True)
    
    task_id: str = Field(..., description="Unique task identifier")
    task_type: TaskType = Field(..., description="Type of task")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    status: TaskStatus = Field(..., description="Current task status")
    priority: TaskPriority = Field(..., description="Task priority")
    parameters: Dict[str, Any] = Field(..., description="Task parameters")
    tags: List[str] = Field(..., description="Task tags")
    project_id: Optional[str] = Field(..., description="Project identifier")
    assignee: Optional[str] = Field(..., description="Task assignee")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(..., description="Task start timestamp")
    completed_at: Optional[datetime] = Field(..., description="Task completion timestamp")
    deadline: Optional[datetime] = Field(..., description="Task deadline")
    error_message: Optional[str] = Field(..., description="Error message if task failed")
    result: Optional[Dict[str, Any]] = Field(..., description="Task execution result")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Task progress percentage")


class MCPTaskListResponse(BaseModel):
    """Response model for listing MCP tasks"""
    tasks: List[MCPTaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Tasks per page")
    pages: int = Field(..., description="Total number of pages")


class TaskEvent(BaseModel):
    """Model for task events sent via SSE"""
    event_type: str = Field(..., description="Event type (task_created, task_updated, etc.)")
    task_id: str = Field(..., description="Task identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event data")


class MCPTaskFilter(BaseModel):
    """Model for filtering tasks"""
    model_config = ConfigDict(extra="forbid")
    
    status: Optional[List[TaskStatus]] = Field(default=None, description="Filter by status")
    task_type: Optional[List[TaskType]] = Field(default=None, description="Filter by type")
    priority: Optional[List[TaskPriority]] = Field(default=None, description="Filter by priority")
    project_id: Optional[str] = Field(default=None, description="Filter by project")
    assignee: Optional[str] = Field(default=None, description="Filter by assignee")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    created_after: Optional[datetime] = Field(default=None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(default=None, description="Filter by creation date")
    search: Optional[str] = Field(default=None, description="Search in title and description")


class MCPServerConfig(BaseModel):
    """MCP Server configuration model"""
    enabled: bool = Field(default=True, description="Enable MCP server")
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, ge=1, le=65535, description="Server port")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    auth_enabled: bool = Field(default=False, description="Enable authentication")
    auth_secret: Optional[str] = Field(default=None, description="Authentication secret")
    max_connections: int = Field(default=100, ge=1, description="Maximum concurrent connections")
    sse_heartbeat_interval: int = Field(default=30, ge=5, description="SSE heartbeat interval in seconds")
    metrics_retention_days: int = Field(default=7, ge=1, description="Metrics retention period")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, ge=1, description="Requests per minute")
    log_level: str = Field(default="INFO", description="Logging level")


class MetricsResponse(BaseModel):
    """Response model for system metrics"""
    total_tasks: int = Field(..., description="Total number of tasks")
    active_tasks: int = Field(..., description="Currently active tasks")
    completed_tasks: int = Field(..., description="Completed tasks")
    failed_tasks: int = Field(..., description="Failed tasks")
    queue_size: int = Field(..., description="Current queue size")
    worker_count: int = Field(..., description="Active worker count")
    average_task_duration: float = Field(..., description="Average task duration in seconds")
    success_rate: float = Field(..., description="Task success rate percentage")
    last_updated: datetime = Field(..., description="Metrics last updated timestamp")


class LogEntry(BaseModel):
    """Model for log entries"""
    timestamp: datetime = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level")
    logger: str = Field(..., description="Logger name")
    message: str = Field(..., description="Log message")
    task_id: Optional[str] = Field(default=None, description="Associated task ID")
    worker_id: Optional[str] = Field(default=None, description="Worker ID")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Additional log data")


class IntegrationConfig(BaseModel):
    """Configuration model for external integrations"""
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(default=True, description="Enable integration endpoints")
    cli_commands_enabled: bool = Field(default=True, description="Enable CLI command integration")
    stats_enabled: bool = Field(default=True, description="Enable statistics endpoints")
    health_checks_enabled: bool = Field(default=True, description="Enable health check endpoints")
    allowed_origins: List[str] = Field(default=["*"], description="Allowed origins for integration requests")
    api_key_required: bool = Field(default=False, description="Require API key for integration endpoints")
    api_keys: List[str] = Field(default_factory=list, description="Valid API keys for integration")
    rate_limit_per_minute: int = Field(default=60, ge=1, description="Rate limit for integration endpoints")
    cache_ttl_seconds: int = Field(default=300, ge=60, description="Cache TTL for expensive operations")


class SystemStats(BaseModel):
    """Model for comprehensive system statistics"""
    timestamp: datetime = Field(..., description="Statistics timestamp")
    tasks: Dict[str, int] = Field(..., description="Task statistics by status")
    performance: Dict[str, float] = Field(..., description="Performance metrics")
    system: Dict[str, Any] = Field(..., description="System resource metrics")
    queue: Dict[str, int] = Field(..., description="Queue statistics")
    workers: Dict[str, int] = Field(..., description="Worker statistics")
    trends: Optional[Dict[str, List[float]]] = Field(default=None, description="Trend data")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="System alerts")


class IntegrationHealth(BaseModel):
    """Model for integration health status"""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    services: Dict[str, Dict[str, Any]] = Field(..., description="Individual service health")
    capabilities: List[str] = Field(..., description="Available capabilities")
    version: str = Field(..., description="System version")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    system_info: Optional[Dict[str, Any]] = Field(default=None, description="Detailed system information")
    integration_ready: bool = Field(..., description="Ready for external integrations")


class CLIOptions(BaseModel):
    """Model for CLI configuration options"""
    commands: Dict[str, Dict[str, Any]] = Field(..., description="Available CLI commands")
    options: Dict[str, Dict[str, Any]] = Field(..., description="Global CLI options")
    environment_variables: Dict[str, str] = Field(..., description="Required environment variables")
    project_structure: Dict[str, Any] = Field(..., description="Expected project structure")
    integrations: Dict[str, Dict[str, Any]] = Field(..., description="Integration-specific options")