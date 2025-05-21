# API Reference

This document provides comprehensive API documentation for Knocodex's core modules, classes, and functions.

## Table of Contents

- [CLI Module](#cli-module)
- [Agent Manager](#agent-manager)
- [Configuration](#configuration)
- [Queue System](#queue-system)
- [GitHub Integration](#github-integration)
- [Claude Integration](#claude-integration)
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