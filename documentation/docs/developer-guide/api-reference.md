# API Reference

This document provides comprehensive API documentation for Knocodex's core modules, classes, and functions.

## Table of Contents

- [CLI Module](#cli-module)
- [Agent Manager](#agent-manager)
- [Configuration](#configuration)
- [Queue System](#queue-system)
- [GitHub Integration](#github-integration)
- [Claude Integration](#claude-integration)
- [MCP Server](#mcp-server)
- [Utilities](#utilities)

## CLI Module

### `knocodex.cli`

Main CLI interface using Click framework.

#### Commands

##### `init`

```python
@cli.command()
@click.option('--reset', is_flag=True, help='Reset existing configuration')
def init(reset: bool) -> None:
    """Initialize Knocodex in the current project.
    
    Args:
        reset: Whether to reset existing configuration
        
    Raises:
        KnocodexError: If initialization fails
    """
```

##### `start`

```python
@cli.command()
@click.option('--daemon', is_flag=True, help='Run in daemon mode')
def start(daemon: bool) -> None:
    """Start Knocodex services.
    
    Args:
        daemon: Whether to run in daemon mode
        
    Raises:
        ServiceStartError: If services fail to start
    """
```

##### `stop`

```python
@cli.command()
def stop() -> None:
    """Stop all running Knocodex services.
    
    Raises:
        ServiceStopError: If services fail to stop cleanly
    """
```

##### `status`

```python
@cli.command()
@click.option('--verbose', is_flag=True, help='Show detailed status')
def status(verbose: bool) -> None:
    """Check status of Knocodex services.
    
    Args:
        verbose: Whether to show detailed status information
    """
```

##### `dashboard`

```python
@cli.command()
@click.option('--port', default=9181, help='Dashboard port')
def dashboard(port: int) -> None:
    """Start RQ dashboard for monitoring.
    
    Args:
        port: Port to run dashboard on
    """
```

## Agent Manager

### `knocodex.agent_manager.AgentManager`

Central orchestration class for managing all Knocodex services.

#### Constructor

```python
def __init__(self, config_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize Agent Manager.
    
    Args:
        config_path: Path to configuration file. If None, uses default location.
    """
```

#### Methods

##### `initialize_project`

```python
def initialize_project(self, reset: bool = False) -> None:
    """Initialize project structure and configuration.
    
    Args:
        reset: Whether to reset existing configuration
        
    Raises:
        InitializationError: If project initialization fails
    """
```

##### `start_services`

```python
def start_services(self, daemon: bool = False) -> Dict[str, Any]:
    """Start all required services.
    
    Args:
        daemon: Whether to run services in daemon mode
        
    Returns:
        Dictionary with service status information
        
    Raises:
        ServiceStartError: If any service fails to start
    """
```

##### `stop_services`

```python
def stop_services(self) -> Dict[str, Any]:
    """Stop all running services.
    
    Returns:
        Dictionary with stop operation results
        
    Raises:
        ServiceStopError: If services fail to stop cleanly
    """
```

##### `get_service_status`

```python
def get_service_status(self) -> Dict[str, ServiceStatus]:
    """Get status of all services.
    
    Returns:
        Dictionary mapping service names to their status
    """
```

#### Properties

```python
@property
def redis_client(self) -> redis.Redis:
    """Get Redis client instance."""

@property
def is_running(self) -> bool:
    """Check if services are running."""

@property
def project_dir(self) -> Path:
    """Get project directory path."""
```

## Configuration

### `knocodex.config.Config`

Configuration management with hierarchical loading.

#### Constructor

```python
def __init__(self) -> None:
    """Initialize configuration with defaults."""
```

#### Class Methods

##### `load`

```python
@classmethod
def load(cls, config_path: Optional[Union[str, Path]] = None) -> 'Config':
    """Load configuration from files and environment.
    
    Args:
        config_path: Path to project configuration file
        
    Returns:
        Loaded configuration instance
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
```

#### Methods

##### `validate`

```python
def validate(self) -> List[str]:
    """Validate configuration values.
    
    Returns:
        List of validation errors (empty if valid)
    """
```

##### `to_dict`

```python
def to_dict(self) -> Dict[str, Any]:
    """Convert configuration to dictionary.
    
    Returns:
        Configuration as nested dictionary
    """
```

##### `save`

```python
def save(self, path: Union[str, Path]) -> None:
    """Save configuration to file.
    
    Args:
        path: Path to save configuration to
        
    Raises:
        IOError: If file cannot be written
    """
```

### Configuration Classes

#### `GitHubConfig`

```python
class GitHubConfig:
    """GitHub integration configuration."""
    
    token: str
    owner: str
    repo: str
    issue_label: str = "knocodex-auto"
    poll_interval: int = 300
    max_issues_per_poll: int = 10
    base_branch: str = "main"
```

#### `RedisConfig`

```python
class RedisConfig:
    """Redis connection configuration."""
    
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 30
    socket_keepalive: bool = True
    health_check_interval: int = 30
```

#### `ClaudeConfig`

```python
class ClaudeConfig:
    """Claude Code configuration."""
    
    headless: bool = True
    timeout: int = 3600
    max_retries: int = 3
    retry_delay: int = 30
    model: str = "claude-3-5-sonnet"
    temperature: float = 0.1
```

## Queue System

### `knocodex.queue.KnocodexQueue`

Queue management wrapper around RQ.

#### Constructor

```python
def __init__(self, config: Config) -> None:
    """Initialize queue with configuration.
    
    Args:
        config: Knocodex configuration instance
    """
```

#### Methods

##### `enqueue_issue_processing`

```python
def enqueue_issue_processing(
    self,
    issue_number: int,
    priority: str = 'normal'
) -> str:
    """Enqueue an issue for processing.
    
    Args:
        issue_number: GitHub issue number
        priority: Processing priority ('high', 'normal', 'low')
        
    Returns:
        Job ID for tracking
        
    Raises:
        QueueError: If enqueueing fails
    """
```

##### `get_job_status`

```python
def get_job_status(self, job_id: str) -> JobStatus:
    """Get status of a specific job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status information
        
    Raises:
        JobNotFoundError: If job doesn't exist
    """
```

##### `get_queue_info`

```python
def get_queue_info(self) -> QueueInfo:
    """Get queue statistics and information.
    
    Returns:
        Queue information including length, workers, etc.
    """
```

### Job Functions

#### `process_issue`

```python
def process_issue(issue_number: int) -> Dict[str, Any]:
    """Process a GitHub issue using Claude Code.
    
    Args:
        issue_number: GitHub issue number to process
        
    Returns:
        Processing result with PR information
        
    Raises:
        ProcessingError: If issue processing fails
        GitHubError: If GitHub operations fail
        ClaudeError: If Claude Code execution fails
    """
```

## GitHub Integration

### `knocodex.github.GitHubClient`

GitHub API client with Knocodex-specific functionality.

#### Constructor

```python
def __init__(self, config: Optional[Config] = None) -> None:
    """Initialize GitHub client.
    
    Args:
        config: Configuration instance. Uses loaded config if None.
    """
```

#### Methods

##### `get_issue`

```python
def get_issue(self, issue_number: int) -> github.Issue.Issue:
    """Get a specific issue.
    
    Args:
        issue_number: Issue number to retrieve
        
    Returns:
        GitHub issue object
        
    Raises:
        GitHubError: If issue cannot be retrieved
    """
```

##### `get_labeled_issues`

```python
def get_labeled_issues(
    self,
    label: Optional[str] = None,
    state: str = 'open'
) -> List[github.Issue.Issue]:
    """Get issues with specific label.
    
    Args:
        label: Label to filter by. Uses config default if None.
        state: Issue state ('open', 'closed', 'all')
        
    Returns:
        List of matching issues
    """
```

##### `create_pull_request`

```python
def create_pull_request(
    self,
    title: str,
    body: str,
    head: str,
    base: str = 'main'
) -> github.PullRequest.PullRequest:
    """Create a pull request.
    
    Args:
        title: PR title
        body: PR description
        head: Source branch
        base: Target branch
        
    Returns:
        Created pull request object
        
    Raises:
        GitHubError: If PR creation fails
    """
```

##### `create_branch`

```python
def create_branch(self, branch_name: str, from_branch: str = 'main') -> None:
    """Create a new branch.
    
    Args:
        branch_name: Name for the new branch
        from_branch: Branch to create from
        
    Raises:
        GitHubError: If branch creation fails
    """
```

### Utility Functions

#### `should_process_issue`

```python
def should_process_issue(
    issue: github.Issue.Issue,
    config: Config
) -> bool:
    """Determine if an issue should be processed.
    
    Args:
        issue: GitHub issue to evaluate
        config: Configuration with processing rules
        
    Returns:
        True if issue should be processed, False otherwise
    """
```

## Claude Integration

### `knocodex.claude.ClaudeExecutor`

Execute Claude Code commands in headless mode.

#### Constructor

```python
def __init__(self, config: Optional[Config] = None) -> None:
    """Initialize Claude executor.
    
    Args:
        config: Configuration instance. Uses loaded config if None.
    """
```

#### Methods

##### `execute_command`

```python
def execute_command(
    self,
    command: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute a Claude Code command.
    
    Args:
        command: Command name to execute
        context: Additional context for the command
        
    Returns:
        Command execution result
        
    Raises:
        ClaudeExecutionError: If command execution fails
        TimeoutError: If command times out
    """
```

##### `execute_raw_command`

```python
def execute_raw_command(
    self,
    command_args: List[str],
    timeout: Optional[int] = None
) -> subprocess.CompletedProcess:
    """Execute raw Claude Code command.
    
    Args:
        command_args: Complete command arguments
        timeout: Command timeout in seconds
        
    Returns:
        Subprocess result
        
    Raises:
        ClaudeExecutionError: If execution fails
    """
```

#### Command Templates

##### `register_custom_commands`

```python
def register_custom_commands(commands_dir: Optional[Path] = None) -> None:
    """Register custom Claude commands.
    
    Args:
        commands_dir: Directory containing command templates
        
    Raises:
        IOError: If templates cannot be written
    """
```

## MCP Server

### `knocodex.mcp_server.MCPServer`

FastAPI-based Model Context Protocol (MCP) server providing REST API endpoints for integration monitoring, health checks, and real-time event streaming.

#### Constructor

```python
def __init__(self, config: Optional[Config] = None) -> None:
    """Initialize MCP server with configuration.
    
    Args:
        config: Knocodex configuration instance. Uses loaded config if None.
    """
```

#### REST API Endpoints

##### Health and Status

**GET /api/v1/health**

```python
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check(
    include_details: bool = Query(default=False)
) -> HealthResponse:
    """Comprehensive health check endpoint.
    
    Args:
        include_details: Whether to include detailed component status
        
    Returns:
        HealthResponse with system status information
    """
```

**GET /api/v1/integration/health**

```python
@app.get("/api/v1/integration/health", response_model=IntegrationHealth)
async def get_integration_health() -> IntegrationHealth:
    """Get integration-specific health status.
    
    Returns:
        IntegrationHealth with service integration status
    """
```

##### Metrics and Statistics

**GET /api/v1/metrics**

```python
@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get comprehensive system metrics.
    
    Returns:
        MetricsResponse with performance and usage metrics
    """
```

**GET /api/v1/stats/summary**

```python
@app.get("/api/v1/stats/summary", response_model=SystemStats)
async def get_stats_summary(
    timeframe: str = Query(default="1h", regex="^(1h|24h|7d|30d)$")
) -> SystemStats:
    """Get system statistics summary.
    
    Args:
        timeframe: Time period for statistics (1h, 24h, 7d, 30d)
        
    Returns:
        SystemStats with aggregated statistics
    """
```

##### Configuration and Integration

**GET /api/v1/integration/cli-options**

```python
@app.get("/api/v1/integration/cli-options", response_model=CLIOptions)
async def get_cli_options() -> CLIOptions:
    """Get CLI configuration options.
    
    Returns:
        CLIOptions with available command-line interface options
    """
```

##### Real-time Event Streaming (SSE)

**GET /api/v1/events/stream**

```python
@app.get("/api/v1/events/stream")
async def event_stream(
    request: Request,
    task_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    since: Optional[str] = Query(default=None)
) -> EventSourceResponse:
    """Server-Sent Events stream for real-time updates.
    
    Args:
        request: FastAPI request object
        task_type: Filter by task type (analysis, implementation, review)
        status: Filter by task status (pending, in_progress, completed, failed)
        since: ISO timestamp to filter events from specific time
        
    Returns:
        EventSourceResponse with streaming events
    """
```

#### Response Models

##### `HealthResponse`

```python
class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(description="Overall health status")
    timestamp: datetime = Field(description="Health check timestamp")
    version: str = Field(description="Knocodex version")
    uptime: float = Field(description="Server uptime in seconds")
    components: Optional[Dict[str, ComponentHealth]] = Field(
        description="Detailed component health status"
    )
```

##### `MetricsResponse`

```python
class MetricsResponse(BaseModel):
    """System metrics response model."""
    
    system: SystemMetrics = Field(description="System performance metrics")
    queue: QueueMetrics = Field(description="Queue statistics")
    tasks: TaskMetrics = Field(description="Task execution metrics")
    timestamp: datetime = Field(description="Metrics collection timestamp")
```

##### `IntegrationHealth`

```python
class IntegrationHealth(BaseModel):
    """Integration health status model."""
    
    redis_healthy: bool = Field(description="Redis connection status")
    queue_operational: bool = Field(description="Queue system operational status")
    workflow_engine_status: str = Field(description="Workflow engine status")
    github_integration: bool = Field(description="GitHub API connectivity")
    claude_integration: bool = Field(description="Claude Code availability")
```

##### `CLIOptions`

```python
class CLIOptions(BaseModel):
    """CLI configuration options model."""
    
    available_commands: List[str] = Field(description="Available CLI commands")
    default_config: Dict[str, Any] = Field(description="Default configuration values")
    environment_variables: List[str] = Field(description="Supported environment variables")
    config_file_locations: List[str] = Field(description="Configuration file search paths")
```

#### Event Types

##### `TaskEvent`

```python
class TaskEvent(BaseModel):
    """Task lifecycle event model."""
    
    event_type: str = Field(description="Event type identifier")
    task_id: str = Field(description="Task identifier")
    task_type: str = Field(description="Task type (analysis, implementation, review)")
    status: str = Field(description="Current task status")
    project_name: str = Field(description="Associated project name")
    timestamp: datetime = Field(description="Event timestamp")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional event data")
```

#### Server Lifecycle

##### `start_server`

```python
async def start_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False
) -> None:
    """Start the MCP server.
    
    Args:
        host: Server host address
        port: Server port number
        reload: Enable auto-reload for development
    """
```

##### `stop_server`

```python
async def stop_server() -> None:
    """Gracefully stop the MCP server."""
```

#### Middleware and CORS

The MCP server includes:
- CORS middleware for cross-origin requests
- Request/response logging middleware  
- Error handling middleware for graceful error responses
- Prometheus metrics collection middleware

#### Health Monitoring

The server provides comprehensive health monitoring including:
- Redis connection health checks
- Queue system operational status
- Workflow engine availability
- GitHub API connectivity tests
- Claude Code integration status
- System resource utilization metrics

#### Real-time Updates

Server-Sent Events (SSE) provide real-time streaming of:
- Task status changes
- Queue operations
- System health updates
- Error notifications
- Performance metrics

#### Usage Examples

##### Basic Server Setup

```python
from knocodex.mcp_server import MCPServer
from knocodex.config import Config

# Initialize and start server
config = Config.load()
server = MCPServer(config)
await server.start_server(host="0.0.0.0", port=8080)
```

##### Event Stream Client

```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        "GET", 
        "http://localhost:8080/api/v1/events/stream",
        params={"task_type": "implementation", "status": "in_progress"}
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                print(f"Task update: {event_data}")
```

##### Health Check Integration

```python
import requests

def check_knocodex_health():
    response = requests.get(
        "http://localhost:8080/api/v1/health",
        params={"include_details": True}
    )
    
    if response.status_code == 200:
        health_data = response.json()
        print(f"System status: {health_data['status']}")
        print(f"Uptime: {health_data['uptime']} seconds")
        
        if health_data.get("components"):
            for component, status in health_data["components"].items():
                print(f"{component}: {status['status']}")
```

## Utilities

### System Utils (`knocodex.utils.system_utils`)

#### `check_system_requirements`

```python
def check_system_requirements() -> Dict[str, Dict[str, Any]]:
    """Check if system meets Knocodex requirements.
    
    Returns:
        Dictionary with requirement check results
    """
```

#### `get_system_info`

```python
def get_system_info() -> Dict[str, Any]:
    """Get system information.
    
    Returns:
        System information dictionary
    """
```

#### `find_project_root`

```python
def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find project root directory.
    
    Args:
        start_path: Path to start searching from
        
    Returns:
        Project root path if found, None otherwise
    """
```

### Redis Utils (`knocodex.utils.redis_utils`)

#### `get_redis_connection`

```python
def get_redis_connection(config: Optional[Config] = None) -> redis.Redis:
    """Get Redis connection instance.
    
    Args:
        config: Configuration instance
        
    Returns:
        Connected Redis client
        
    Raises:
        ConnectionError: If Redis is not accessible
    """
```

#### `test_redis_connection`

```python
def test_redis_connection(config: Optional[Config] = None) -> bool:
    """Test Redis connection.
    
    Args:
        config: Configuration instance
        
    Returns:
        True if connection successful, False otherwise
    """
```

### GitHub Utils (`knocodex.utils.gh_utils`)

#### `parse_github_url`

```python
def parse_github_url(url: str) -> Tuple[str, str]:
    """Parse GitHub repository URL.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo)
        
    Raises:
        ValueError: If URL format is invalid
    """
```

#### `format_issue_body`

```python
def format_issue_body(
    issue: github.Issue.Issue,
    include_metadata: bool = True
) -> str:
    """Format issue body for processing.
    
    Args:
        issue: GitHub issue object
        include_metadata: Whether to include issue metadata
        
    Returns:
        Formatted issue body
    """
```

## Exception Classes

### Base Exceptions

```python
class KnocodexError(Exception):
    """Base exception for all Knocodex errors."""
    pass

class ConfigurationError(KnocodexError):
    """Configuration-related errors."""
    pass

class ServiceError(KnocodexError):
    """Service management errors."""
    pass

class ProcessingError(KnocodexError):
    """Issue processing errors."""
    pass
```

### Specific Exceptions

```python
class ServiceStartError(ServiceError):
    """Raised when services fail to start."""
    pass

class ServiceStopError(ServiceError):
    """Raised when services fail to stop."""
    pass

class GitHubError(KnocodexError):
    """GitHub API-related errors."""
    pass

class ClaudeExecutionError(ProcessingError):
    """Claude Code execution errors."""
    pass

class QueueError(KnocodexError):
    """Queue operation errors."""
    pass

class JobNotFoundError(QueueError):
    """Raised when job cannot be found."""
    pass
```

## Type Definitions

### Enums

```python
class ServiceStatus(Enum):
    """Service status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"

class JobStatus(Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Priority(Enum):
    """Task priority enumeration."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
```

### Data Classes

```python
@dataclass
class QueueInfo:
    """Queue information data class."""
    name: str
    length: int
    workers: int
    failed_jobs: int
    scheduled_jobs: int

@dataclass
class JobInfo:
    """Job information data class."""
    id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    meta: Dict[str, Any]
```

## Usage Examples

### Basic Usage

```python
from knocodex import AgentManager, Config

# Initialize and start services
config = Config.load()
agent = AgentManager(config)
agent.start_services()

# Process an issue
from knocodex.queue import KnocodexQueue
queue = KnocodexQueue(config)
job_id = queue.enqueue_issue_processing(123)
```

### Custom Configuration

```python
from knocodex.config import Config, GitHubConfig

# Create custom configuration
config = Config()
config.github = GitHubConfig(
    token="your-token",
    owner="your-org",
    repo="your-repo"
)

config.save('.knocodex/config.yaml')
```

### GitHub Integration

```python
from knocodex.github import GitHubClient

client = GitHubClient()
issues = client.get_labeled_issues("bug")

for issue in issues:
    print(f"Issue #{issue.number}: {issue.title}")
```

This API reference provides comprehensive documentation for all public interfaces in Knocodex. For implementation details and examples, refer to the source code and integration tests.