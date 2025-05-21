# Core Components

This document provides detailed information about Knocodex's core components, their APIs, and implementation details.

## Component Overview

Knocodex is built with a modular architecture where each component has specific responsibilities:

- **CLI Interface**: User interaction and command processing
- **Agent Manager**: Service orchestration and lifecycle management
- **Configuration System**: Hierarchical configuration management
- **Queue System**: Asynchronous task processing
- **Worker Processes**: Background job execution
- **GitHub Integration**: Issue detection and PR management
- **Claude Integration**: AI-powered code generation

## CLI Interface (`cli.py`)

### Core Commands

The CLI is built using Click and provides a comprehensive command interface:

```python
@click.group()
@click.version_option()
def cli():
    """Knocodex - Autonomous AI-Powered Code Development Platform"""
    pass

@cli.command()
@click.option('--reset', is_flag=True, help='Reset existing configuration')
def init(reset):
    """Initialize Knocodex in the current project"""
    agent = AgentManager()
    agent.initialize_project(reset=reset)

@cli.command()
@click.option('--daemon', is_flag=True, help='Run in daemon mode')
def start(daemon):
    """Start Knocodex services"""
    agent = AgentManager()
    agent.start_services(daemon=daemon)
```

### Command Implementation

Each command follows a consistent pattern:

1. **Initialize Agent Manager**: Create instance with current configuration
2. **Validate Prerequisites**: Check system requirements and dependencies
3. **Execute Action**: Perform the requested operation
4. **Handle Errors**: Provide meaningful error messages and recovery suggestions

### Error Handling

```python
def handle_cli_error(func):
    """Decorator for consistent CLI error handling"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KnocodexError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            sys.exit(1)
    return wrapper
```

## Agent Manager (`agent_manager.py`)

### Class Structure

```python
class AgentManager:
    """Central orchestration for all Knocodex services"""
    
    def __init__(self, config_path=None):
        self.config = Config.load(config_path)
        self.redis_client = None
        self.processes = {}
        self.logger = logging.getLogger(__name__)
    
    def initialize_project(self, reset=False):
        """Initialize .knocodex directory structure"""
        
    def start_services(self, daemon=False):
        """Start all required services"""
        
    def stop_services(self):
        """Stop all running services"""
        
    def get_service_status(self):
        """Get status of all services"""
```

### Service Management

The Agent Manager handles multiple types of services:

#### Redis Service

```python
def _start_redis(self):
    """Start Redis server if not already running"""
    if not self._is_redis_running():
        cmd = ['redis-server', '--daemonize', 'yes']
        subprocess.run(cmd, check=True)
        self._wait_for_redis()

def _is_redis_running(self):
    """Check if Redis is accessible"""
    try:
        client = redis.Redis(**self.config.redis.to_dict())
        client.ping()
        return True
    except redis.ConnectionError:
        return False
```

#### Worker Processes

```python
def _start_workers(self):
    """Start RQ worker processes"""
    for i in range(self.config.queue.max_workers):
        cmd = [
            sys.executable, 
            'templates/worker.py',
            '--queue', self.config.queue.name,
            '--connection', self.config.redis.url
        ]
        
        proc = subprocess.Popen(cmd, cwd=self.project_dir)
        self.processes[f'worker_{i}'] = proc
```

#### Polling Service

```python
def _start_polling(self):
    """Start GitHub issue polling service"""
    cmd = [
        sys.executable,
        'templates/main_loop.py',
        '--config', str(self.config_path)
    ]
    
    proc = subprocess.Popen(cmd, cwd=self.project_dir)
    self.processes['polling'] = proc
```

### MCP Server Integration

```python
def _setup_mcp_servers(self):
    """Configure MCP servers for Claude Code integration"""
    servers_config = {
        'knowledge-graph': {
            'command': 'python',
            'args': ['-m', 'knocodex.mcp.knowledge_graph']
        },
        'github-integration': {
            'command': 'python',
            'args': ['-m', 'knocodex.mcp.github']
        }
    }
    
    # Write MCP configuration
    mcp_config_path = self.project_dir / '.claude' / 'mcp_settings.json'
    with open(mcp_config_path, 'w') as f:
        json.dump({'servers': servers_config}, f, indent=2)
```

## Configuration System (`config.py`)

### Configuration Hierarchy

```python
class Config:
    """Hierarchical configuration management"""
    
    def __init__(self):
        self.github = GitHubConfig()
        self.redis = RedisConfig()
        self.claude = ClaudeConfig()
        self.queue = QueueConfig()
        self.logging = LoggingConfig()
        self.notifications = NotificationConfig()
    
    @classmethod
    def load(cls, config_path=None):
        """Load configuration from multiple sources"""
        config = cls()
        
        # Load from files (global, then project)
        global_config = cls._load_file(Path.home() / '.knocodex' / 'config.yaml')
        project_config = cls._load_file(config_path or Path('.knocodex/config.yaml'))
        
        # Merge configurations
        merged_config = cls._deep_merge(global_config, project_config)
        
        # Apply environment overrides
        final_config = cls._apply_env_overrides(merged_config)
        
        return cls._from_dict(final_config)
```

### Configuration Validation

```python
def validate(self):
    """Validate configuration values"""
    errors = []
    
    # Validate GitHub configuration
    if not self.github.token:
        errors.append("GitHub token is required")
    
    # Validate Redis configuration
    if not (1 <= self.redis.port <= 65535):
        errors.append(f"Invalid Redis port: {self.redis.port}")
    
    # Validate queue configuration
    if self.queue.max_workers < 1:
        errors.append("At least one worker is required")
    
    if errors:
        raise ConfigValidationError(errors)
```

### Environment Variable Mapping

```python
def _apply_env_overrides(self, config_dict):
    """Apply environment variable overrides"""
    for key, value in os.environ.items():
        if key.startswith('KNOCODEX_'):
            # Convert KNOCODEX_GITHUB__TOKEN to ['github', 'token']
            path = key[9:].lower().split('__')
            self._set_nested_value(config_dict, path, value)
    
    return config_dict
```

## Queue System

### Redis Queue Implementation

```python
from rq import Queue, Job, Worker
import redis

class KnocodexQueue:
    """Wrapper around RQ with Knocodex-specific functionality"""
    
    def __init__(self, config):
        self.redis_conn = redis.Redis(**config.redis.to_dict())
        self.queue = Queue(config.queue.name, connection=self.redis_conn)
        self.config = config
    
    def enqueue_issue_processing(self, issue_number, priority='normal'):
        """Enqueue an issue for processing"""
        job = self.queue.enqueue(
            'knocodex.workers.process_issue',
            issue_number,
            timeout=self.config.claude.timeout,
            retry=Retry(max=self.config.claude.max_retries),
            meta={'priority': priority, 'type': 'issue_processing'}
        )
        return job.id
```

### Job Processing

```python
def process_issue(issue_number):
    """Main job function for processing GitHub issues"""
    from knocodex.github import GitHubClient
    from knocodex.claude import ClaudeExecutor
    
    # Get current job for progress tracking
    job = get_current_job()
    job.meta['stage'] = 'analyzing'
    job.save_meta()
    
    try:
        # Initialize clients
        github = GitHubClient()
        claude = ClaudeExecutor()
        
        # Get issue details
        issue = github.get_issue(issue_number)
        
        # Analyze issue
        job.meta['stage'] = 'planning'
        job.save_meta()
        
        analysis = claude.execute_command(
            'analyze-github-issue',
            {'issue_number': issue_number}
        )
        
        # Implement solution
        job.meta['stage'] = 'implementing'
        job.save_meta()
        
        implementation = claude.execute_command(
            'implement-github-issue',
            {'issue_number': issue_number, 'plan': analysis}
        )
        
        # Create pull request
        job.meta['stage'] = 'creating_pr'
        job.save_meta()
        
        pr = github.create_pull_request(implementation)
        
        job.meta['stage'] = 'completed'
        job.meta['pr_number'] = pr.number
        job.save_meta()
        
        return {
            'status': 'success',
            'pr_number': pr.number,
            'pr_url': pr.html_url
        }
        
    except Exception as e:
        job.meta['stage'] = 'failed'
        job.meta['error'] = str(e)
        job.save_meta()
        raise
```

## Worker Process (`templates/worker.py`)

### Worker Implementation

```python
#!/usr/bin/env python3
"""RQ Worker process for Knocodex"""

import os
import sys
from pathlib import Path
from rq import Worker, Connection
import redis

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from knocodex.config import Config

def main():
    """Main worker entry point"""
    config = Config.load()
    
    # Connect to Redis
    redis_conn = redis.Redis(**config.redis.to_dict())
    
    # Create worker
    worker = Worker(
        [config.queue.name],
        connection=redis_conn,
        name=f'knocodex-worker-{os.getpid()}'
    )
    
    # Start processing
    worker.work()

if __name__ == '__main__':
    main()
```

### Worker Lifecycle

```python
class KnocodexWorker(Worker):
    """Custom worker with Knocodex-specific functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Configure worker-specific logging"""
        self.logger = logging.getLogger(f'knocodex.worker.{self.name}')
        
    def prepare_job(self, job, queue):
        """Prepare environment before job execution"""
        # Set up job-specific environment
        os.environ['KNOCODEX_JOB_ID'] = job.id
        os.environ['KNOCODEX_WORKER_NAME'] = self.name
        
        return super().prepare_job(job, queue)
    
    def handle_job_failure(self, job, *exc_info):
        """Handle job failures with custom logic"""
        self.logger.error(f"Job {job.id} failed: {exc_info[1]}")
        
        # Send notifications
        from knocodex.notifications import notify_job_failure
        notify_job_failure(job, exc_info[1])
        
        return super().handle_job_failure(job, *exc_info)
```

## GitHub Integration

### GitHub Client

```python
from github import Github
from github.GithubException import GithubException

class GitHubClient:
    """GitHub API client with Knocodex-specific functionality"""
    
    def __init__(self, config=None):
        self.config = config or Config.load()
        self.client = Github(self.config.github.token)
        self.repo = self.client.get_repo(
            f"{self.config.github.owner}/{self.config.github.repo}"
        )
    
    def get_labeled_issues(self, label=None):
        """Get issues with specific label"""
        label = label or self.config.github.issue_label
        return self.repo.get_issues(labels=[label], state='open')
    
    def create_pull_request(self, title, body, branch, base='main'):
        """Create a pull request"""
        return self.repo.create_pull(
            title=title,
            body=body,
            head=branch,
            base=base
        )
```

### Issue Processing Logic

```python
def should_process_issue(issue, config):
    """Determine if an issue should be processed"""
    # Check required labels
    issue_labels = {label.name for label in issue.labels}
    
    if config.github.issue_label not in issue_labels:
        return False
    
    # Check exclusion labels
    excluded = set(config.issue_rules.excluded_labels)
    if issue_labels & excluded:
        return False
    
    # Check age limit
    if config.issue_rules.max_age_days:
        age = (datetime.now() - issue.created_at).days
        if age > config.issue_rules.max_age_days:
            return False
    
    return True
```

## Claude Integration

### Claude Executor

```python
import subprocess
import json
from pathlib import Path

class ClaudeExecutor:
    """Execute Claude Code commands in headless mode"""
    
    def __init__(self, config=None):
        self.config = config or Config.load()
        self.timeout = self.config.claude.timeout
        
    def execute_command(self, command, context=None):
        """Execute a Claude Code command"""
        # Prepare command
        cmd = [
            'claude-code',
            '--headless',
            f'/project:{command}'
        ]
        
        # Add context if provided
        if context:
            context_file = Path('.knocodex/tmp/context.json')
            context_file.parent.mkdir(exist_ok=True)
            with open(context_file, 'w') as f:
                json.dump(context, f)
            cmd.extend(['--context', str(context_file)])
        
        # Execute command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=Path.cwd()
            )
            
            if result.returncode != 0:
                raise ClaudeExecutionError(f"Claude command failed: {result.stderr}")
            
            return self._parse_result(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise ClaudeExecutionError(f"Claude command timed out after {self.timeout}s")
```

### Custom Commands

```python
def register_custom_commands():
    """Register custom Claude commands"""
    commands_dir = Path('.claude/commands')
    commands_dir.mkdir(parents=True, exist_ok=True)
    
    # Default commands
    commands = {
        'analyze-github-issue': ANALYZE_ISSUE_TEMPLATE,
        'implement-github-issue': IMPLEMENT_ISSUE_TEMPLATE,
        'document-project': DOCUMENT_PROJECT_TEMPLATE,
        'review-pull-request': REVIEW_PR_TEMPLATE,
    }
    
    for name, template in commands.items():
        command_file = commands_dir / f'{name}.md'
        if not command_file.exists():
            command_file.write_text(template)
```

## Utility Components

### Setup Utils (`setup_utils.py`)

```python
def create_project_structure(project_dir):
    """Create the .knocodex directory structure"""
    dirs_to_create = [
        '.knocodex',
        '.knocodex/tasks',
        '.knocodex/logs',
        '.knocodex/tmp',
        '.claude',
        '.claude/commands',
    ]
    
    for dir_path in dirs_to_create:
        full_path = project_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

def setup_virtual_environment(project_dir):
    """Set up Python virtual environment"""
    venv_path = project_dir / '.knocodex' / 'venv'
    
    if not venv_path.exists():
        subprocess.run([
            sys.executable, '-m', 'venv', 
            str(venv_path)
        ], check=True)
    
    # Install requirements
    pip_path = venv_path / 'bin' / 'pip'
    requirements = project_dir / 'requirements.txt'
    
    if requirements.exists():
        subprocess.run([
            str(pip_path), 'install', '-r', 
            str(requirements)
        ], check=True)
```

### System Utils (`utils/system_utils.py`)

```python
def check_system_requirements():
    """Check if system meets Knocodex requirements"""
    requirements = {
        'python': check_python_version,
        'redis': check_redis_available,
        'claude': check_claude_code_cli,
        'git': check_git_available,
    }
    
    results = {}
    for name, checker in requirements.items():
        try:
            results[name] = checker()
        except Exception as e:
            results[name] = {'status': 'error', 'message': str(e)}
    
    return results

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version < (3, 8):
        raise SystemRequirementError(
            f"Python 3.8+ required, found {version.major}.{version.minor}"
        )
    
    return {
        'status': 'ok',
        'version': f"{version.major}.{version.minor}.{version.micro}"
    }
```

## Component Testing

### Unit Testing Framework

```python
import pytest
from unittest.mock import Mock, patch
from knocodex.agent_manager import AgentManager

class TestAgentManager:
    """Test suite for Agent Manager component"""
    
    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.redis.host = 'localhost'
        config.redis.port = 6379
        return config
    
    @pytest.fixture
    def agent_manager(self, mock_config):
        with patch('knocodex.agent_manager.Config.load', return_value=mock_config):
            return AgentManager()
    
    def test_initialize_project(self, agent_manager, tmp_path):
        """Test project initialization"""
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            agent_manager.initialize_project()
            
            assert (tmp_path / '.knocodex').exists()
            assert (tmp_path / '.knocodex' / 'config.yaml').exists()
    
    @patch('subprocess.Popen')
    def test_start_services(self, mock_popen, agent_manager):
        """Test service startup"""
        mock_popen.return_value.pid = 1234
        
        agent_manager.start_services()
        
        assert len(agent_manager.processes) > 0
        mock_popen.assert_called()
```

This comprehensive overview covers all the core components of Knocodex, their interactions, and implementation details. Each component is designed to be modular, testable, and maintainable.