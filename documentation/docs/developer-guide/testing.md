# Testing Guide

This guide covers the testing strategy, frameworks, and best practices for the Knocodex project. Our testing approach ensures reliability, maintainability, and confidence in the autonomous AI coding platform.

## Testing Philosophy

### Testing Pyramid

Knocodex follows the testing pyramid approach:

```
    /\
   /  \    E2E Tests (Few)
  /____\   Integration Tests (Some)
 /______\  Unit Tests (Many)
```

- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Test component interactions and external services
- **End-to-End Tests**: Test complete workflows and user scenarios

### Test Categories

1. **Unit Tests**: Individual functions and classes
2. **Integration Tests**: Database, Redis, and API interactions
3. **System Tests**: Complete workflows and CLI commands
4. **Performance Tests**: Load testing and benchmarking
5. **Security Tests**: Authentication and authorization

## Test Framework and Tools

### Core Testing Stack

- **pytest**: Primary testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Code coverage reporting
- **pytest-mock**: Mocking and patching
- **pytest-xdist**: Parallel test execution
- **faker**: Test data generation

### Additional Tools

- **tox**: Testing across multiple Python versions
- **hypothesis**: Property-based testing
- **factory_boy**: Test object factories
- **responses**: HTTP request mocking
- **freezegun**: Time-based test mocking

## Test Structure

### Directory Organization

```
tests/
├── __init__.py
├── conftest.py                 # Global pytest configuration
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_agent_manager.py
│   └── utils/
│       ├── test_redis_utils.py
│       └── test_system_utils.py
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_redis_integration.py
│   ├── test_github_integration.py
│   └── test_claude_integration.py
├── system/                     # System/E2E tests
│   ├── __init__.py
│   ├── test_complete_workflow.py
│   └── test_cli_commands.py
├── performance/                # Performance tests
│   ├── __init__.py
│   └── test_load_scenarios.py
├── fixtures/                   # Test data and fixtures
│   ├── __init__.py
│   ├── sample_issues.json
│   ├── sample_config.yaml
│   └── mock_responses/
└── helpers/                    # Test utilities
    ├── __init__.py
    ├── mock_services.py
    └── test_factories.py
```

### Configuration Files

#### pytest.ini
```ini
[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests  
    system: System/E2E tests
    performance: Performance tests
    slow: Slow-running tests
    redis: Tests requiring Redis
    github: Tests requiring GitHub API
    claude: Tests requiring Claude API
filterwarnings =
    error
    ignore::UserWarning
    ignore::DeprecationWarning
```

#### conftest.py
```python
"""Global test configuration and fixtures."""

import asyncio
import os
import pytest
import redis
import tempfile
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

from knocodex.config import Config
from knocodex.agent_manager import AgentManager
from tests.helpers.mock_services import MockGitHubService, MockClaudeService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return Config({
        'github': {
            'token': 'test-token',
            'repo': 'test/repo',
            'polling_interval': 30
        },
        'claude': {
            'api_key': 'test-key',
            'model': 'claude-3-sonnet-20240229'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 15  # Use separate DB for tests
        },
        'logging': {
            'level': 'DEBUG',
            'file': None  # Log to stdout in tests
        }
    })


@pytest.fixture
def redis_client():
    """Create a Redis client for testing."""
    client = redis.Redis(host='localhost', port=6379, db=15)
    yield client
    # Cleanup: flush test database
    client.flushdb()


@pytest.fixture
def mock_github_service():
    """Create a mock GitHub service."""
    return MockGitHubService()


@pytest.fixture
def mock_claude_service():
    """Create a mock Claude service."""
    return MockClaudeService()


@pytest.fixture
def sample_github_issue():
    """Sample GitHub issue data for testing."""
    return {
        'id': 123456789,
        'number': 1,
        'title': 'Add new feature X',
        'body': 'Description of the feature request...',
        'state': 'open',
        'labels': [{'name': 'enhancement'}, {'name': 'knocodex'}],
        'assignee': None,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'html_url': 'https://github.com/test/repo/issues/1'
    }
```

## Unit Testing

### Basic Unit Test Structure

```python
"""Test module for CLI functionality."""

import pytest
from unittest.mock import Mock, patch, call
from click.testing import CliRunner

from knocodex.cli import cli, start_command, status_command
from knocodex.config import Config, ConfigurationError


class TestCLI:
    """Test cases for CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for CLI tests."""
        config = Mock(spec=Config)
        config.validate.return_value = True
        return config
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'Commands:' in result.output
    
    @patch('knocodex.cli.Config.load')
    def test_start_command_success(self, mock_load_config, runner, mock_config):
        """Test successful start command."""
        mock_load_config.return_value = mock_config
        
        with patch('knocodex.cli.AgentManager') as mock_agent_manager:
            mock_manager = Mock()
            mock_agent_manager.return_value = mock_manager
            mock_manager.start.return_value = True
            
            result = runner.invoke(start_command)
            
            assert result.exit_code == 0
            mock_manager.start.assert_called_once()
    
    @patch('knocodex.cli.Config.load')
    def test_start_command_config_error(self, mock_load_config, runner):
        """Test start command with configuration error."""
        mock_load_config.side_effect = ConfigurationError("Invalid config")
        
        result = runner.invoke(start_command)
        
        assert result.exit_code == 1
        assert "Configuration error" in result.output
    
    def test_status_command(self, runner):
        """Test status command."""
        with patch('knocodex.cli.get_service_status') as mock_status:
            mock_status.return_value = {
                'redis': 'running',
                'worker': 'running',
                'github_poller': 'stopped'
            }
            
            result = runner.invoke(status_command)
            
            assert result.exit_code == 0
            assert 'redis: running' in result.output
            assert 'worker: running' in result.output
```

### Testing Async Code

```python
"""Test async functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from knocodex.agent_manager import AgentManager


class TestAsyncAgentManager:
    """Test async methods in AgentManager."""
    
    @pytest.fixture
    def agent_manager(self, mock_config):
        """Create AgentManager instance."""
        return AgentManager(mock_config)
    
    @pytest.mark.asyncio
    async def test_poll_github_issues(self, agent_manager):
        """Test GitHub issue polling."""
        with patch.object(agent_manager, 'github_client') as mock_client:
            mock_client.get_issues = AsyncMock(return_value=[
                {'id': 1, 'title': 'Test Issue'}
            ])
            
            issues = await agent_manager.poll_github_issues()
            
            assert len(issues) == 1
            assert issues[0]['title'] == 'Test Issue'
            mock_client.get_issues.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_issue_async(self, agent_manager, sample_github_issue):
        """Test async issue processing."""
        with patch.object(agent_manager, 'run_claude_command') as mock_claude:
            mock_claude.return_value = Mock(success=True, output="Success")
            
            result = await agent_manager.process_issue_async(sample_github_issue)
            
            assert result.success is True
            mock_claude.assert_called_once()
```

### Parameterized Tests

```python
"""Parameterized test examples."""

import pytest
from knocodex.utils.system_utils import validate_python_version


class TestSystemUtils:
    """Test system utility functions."""
    
    @pytest.mark.parametrize("version,expected", [
        ("3.8.0", True),
        ("3.9.5", True),
        ("3.10.0", True),
        ("3.7.9", False),
        ("2.7.18", False),
        ("invalid", False),
    ])
    def test_validate_python_version(self, version, expected):
        """Test Python version validation with various inputs."""
        assert validate_python_version(version) == expected
    
    @pytest.mark.parametrize("config,should_raise", [
        ({'github': {'token': 'test'}}, False),
        ({'github': {}}, True),
        ({}, True),
        (None, True),
    ])
    def test_config_validation(self, config, should_raise):
        """Test configuration validation."""
        if should_raise:
            with pytest.raises(ConfigurationError):
                Config(config).validate()
        else:
            # Should not raise
            Config(config).validate()
```

## Integration Testing

### Redis Integration Tests

```python
"""Redis integration tests."""

import pytest
import redis
from rq import Queue, Worker

from knocodex.utils.redis_utils import get_redis_connection, enqueue_issue
from knocodex.tasks import process_github_issue


@pytest.mark.integration
@pytest.mark.redis
class TestRedisIntegration:
    """Test Redis and RQ integration."""
    
    @pytest.fixture
    def redis_connection(self):
        """Create Redis connection for testing."""
        connection = redis.Redis(host='localhost', port=6379, db=15)
        yield connection
        connection.flushdb()  # Clean up after each test
    
    @pytest.fixture
    def test_queue(self, redis_connection):
        """Create test queue."""
        return Queue('test', connection=redis_connection)
    
    def test_redis_connection(self, redis_connection):
        """Test basic Redis connectivity."""
        assert redis_connection.ping() is True
        
        # Test basic operations
        redis_connection.set('test_key', 'test_value')
        assert redis_connection.get('test_key') == b'test_value'
    
    def test_enqueue_issue(self, test_queue, sample_github_issue):
        """Test issue enqueueing."""
        job = enqueue_issue(test_queue, sample_github_issue)
        
        assert job is not None
        assert job.func_name == 'knocodex.tasks.process_github_issue'
        assert job.args[0] == sample_github_issue
    
    def test_worker_processes_job(self, test_queue, redis_connection):
        """Test worker job processing."""
        # Mock the actual processing function
        with patch('knocodex.tasks.process_github_issue') as mock_process:
            mock_process.return_value = {'success': True}
            
            # Enqueue job
            job = test_queue.enqueue(
                'knocodex.tasks.process_github_issue',
                {'id': 123, 'title': 'Test Issue'}
            )
            
            # Process job with worker
            worker = Worker([test_queue], connection=redis_connection)
            worker.work(burst=True)  # Process one job and exit
            
            # Verify job completion
            assert job.is_finished
            assert job.result == {'success': True}
            mock_process.assert_called_once()
```

### GitHub API Integration Tests

```python
"""GitHub API integration tests."""

import pytest
import responses
from unittest.mock import patch

from knocodex.utils.gh_utils import GitHubClient, GitHubAPIError


@pytest.mark.integration
@pytest.mark.github
class TestGitHubIntegration:
    """Test GitHub API integration."""
    
    @pytest.fixture
    def github_client(self):
        """Create GitHub client for testing."""
        return GitHubClient(token='test-token', repo='test/repo')
    
    @responses.activate
    def test_get_issues_success(self, github_client):
        """Test successful issue retrieval."""
        # Mock GitHub API response
        responses.add(
            responses.GET,
            'https://api.github.com/repos/test/repo/issues',
            json=[
                {
                    'id': 1,
                    'number': 1,
                    'title': 'Test Issue',
                    'state': 'open',
                    'labels': [{'name': 'knocodex'}]
                }
            ],
            status=200
        )
        
        issues = github_client.get_issues(labels=['knocodex'])
        
        assert len(issues) == 1
        assert issues[0]['title'] == 'Test Issue'
    
    @responses.activate
    def test_get_issues_api_error(self, github_client):
        """Test GitHub API error handling."""
        responses.add(
            responses.GET,
            'https://api.github.com/repos/test/repo/issues',
            json={'message': 'API rate limit exceeded'},
            status=403
        )
        
        with pytest.raises(GitHubAPIError) as exc_info:
            github_client.get_issues()
        
        assert 'rate limit' in str(exc_info.value).lower()
    
    @responses.activate
    def test_create_pull_request(self, github_client):
        """Test pull request creation."""
        responses.add(
            responses.POST,
            'https://api.github.com/repos/test/repo/pulls',
            json={
                'id': 1,
                'number': 1,
                'title': 'Test PR',
                'html_url': 'https://github.com/test/repo/pull/1'
            },
            status=201
        )
        
        pr_data = {
            'title': 'Test PR',
            'body': 'Test pull request',
            'head': 'feature-branch',
            'base': 'main'
        }
        
        pr = github_client.create_pull_request(pr_data)
        
        assert pr['number'] == 1
        assert pr['title'] == 'Test PR'
```

## System Testing

### End-to-End Workflow Tests

```python
"""End-to-end system tests."""

import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch

from knocodex.cli import cli
from click.testing import CliRunner


@pytest.mark.system
class TestCompleteWorkflow:
    """Test complete Knocodex workflows."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test-project"
            project_dir.mkdir()
            
            # Create basic project structure
            (project_dir / "README.md").write_text("# Test Project")
            (project_dir / ".git").mkdir()
            
            yield project_dir
    
    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()
    
    def test_init_workflow(self, runner, temp_project):
        """Test project initialization workflow."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'])
            
            assert result.exit_code == 0
            assert Path('.knocodex').exists()
            assert Path('.knocodex/config.yaml').exists()
            assert Path('.claude/commands').exists()
    
    @patch('knocodex.agent_manager.subprocess.run')
    def test_issue_processing_workflow(self, mock_subprocess, runner, sample_github_issue):
        """Test complete issue processing workflow."""
        # Mock Claude Code execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Issue processed successfully"
        
        with patch('knocodex.utils.gh_utils.GitHubClient') as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.get_issues.return_value = [sample_github_issue]
            mock_instance.create_pull_request.return_value = {
                'number': 1,
                'html_url': 'https://github.com/test/repo/pull/1'
            }
            
            # Start the service (in test mode)
            result = runner.invoke(cli, ['start', '--test-mode'])
            
            # Verify successful execution
            assert result.exit_code == 0
            mock_instance.get_issues.assert_called()
            mock_subprocess.assert_called()
```

### Performance Testing

```python
"""Performance tests."""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from knocodex.agent_manager import AgentManager


@pytest.mark.performance
class TestPerformance:
    """Performance test cases."""
    
    def test_config_loading_performance(self, temp_dir):
        """Test configuration loading performance."""
        # Create large config file
        config_file = Path(temp_dir) / "config.yaml"
        large_config = {
            'github': {'token': 'test' * 1000},
            'data': {f'key_{i}': f'value_{i}' for i in range(1000)}
        }
        
        start_time = time.time()
        config = Config.from_file(config_file)
        load_time = time.time() - start_time
        
        # Should load within reasonable time
        assert load_time < 1.0  # Less than 1 second
        assert config is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_issue_processing(self, mock_config):
        """Test concurrent issue processing performance."""
        agent_manager = AgentManager(mock_config)
        
        # Create multiple test issues
        issues = [
            {'id': i, 'title': f'Issue {i}'}
            for i in range(10)
        ]
        
        with patch.object(agent_manager, 'process_issue_async') as mock_process:
            mock_process.return_value = Mock(success=True)
            
            start_time = time.time()
            
            # Process issues concurrently
            tasks = [
                agent_manager.process_issue_async(issue)
                for issue in issues
            ]
            results = await asyncio.gather(*tasks)
            
            processing_time = time.time() - start_time
            
            # Should process all issues
            assert len(results) == 10
            assert all(result.success for result in results)
            
            # Should be faster than sequential processing
            assert processing_time < 5.0  # Less than 5 seconds for 10 issues
    
    def test_redis_throughput(self, redis_client):
        """Test Redis operation throughput."""
        operations = 1000
        
        start_time = time.time()
        
        # Perform many Redis operations
        for i in range(operations):
            redis_client.set(f'key_{i}', f'value_{i}')
            redis_client.get(f'key_{i}')
        
        total_time = time.time() - start_time
        ops_per_second = (operations * 2) / total_time  # 2 ops per iteration
        
        # Should achieve reasonable throughput
        assert ops_per_second > 1000  # At least 1000 ops/second
```

## Testing Best Practices

### Test Organization

1. **Group Related Tests**: Use classes to group related test methods
2. **Clear Naming**: Use descriptive test method names
3. **One Assertion Per Test**: Focus on a single behavior
4. **Arrange-Act-Assert**: Structure tests clearly

### Fixture Best Practices

```python
@pytest.fixture(scope="session")
def expensive_resource():
    """Session-scoped fixture for expensive setup."""
    resource = create_expensive_resource()
    yield resource
    cleanup_expensive_resource(resource)

@pytest.fixture
def isolated_resource():
    """Function-scoped fixture for test isolation."""
    resource = create_resource()
    yield resource
    cleanup_resource(resource)

@pytest.fixture(params=[1, 2, 3])
def parametrized_fixture(request):
    """Parametrized fixture for multiple test scenarios."""
    return create_resource_with_param(request.param)
```

### Mocking Guidelines

```python
# Good: Mock at the boundary
@patch('knocodex.utils.gh_utils.requests.get')
def test_github_api_call(self, mock_get):
    mock_get.return_value.json.return_value = {'data': 'test'}
    # Test implementation

# Better: Use dependency injection
def test_github_client_with_injection(self):
    mock_session = Mock()
    client = GitHubClient(session=mock_session)
    # Test implementation
```

### Data-Driven Testing

```python
@pytest.mark.parametrize("input_data,expected", [
    pytest.param(
        {'valid': True, 'data': 'test'}, 
        'success',
        id="valid_input"
    ),
    pytest.param(
        {'valid': False}, 
        'error',
        id="invalid_input"
    ),
])
def test_data_processing(self, input_data, expected):
    result = process_data(input_data)
    assert result.status == expected
```

## Continuous Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=knocodex
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
      env:
        REDIS_URL: redis://localhost:6379/15
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

### Quality Gates

```yaml
# .github/workflows/quality.yml  
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install black isort flake8 mypy
    
    - name: Check code formatting
      run: black --check knocodex/ tests/
    
    - name: Check import sorting
      run: isort --check-only knocodex/ tests/
    
    - name: Lint code
      run: flake8 knocodex/ tests/
    
    - name: Type checking
      run: mypy knocodex/
```

## Test Maintenance

### Regular Test Hygiene

1. **Remove Obsolete Tests**: Clean up tests for removed features
2. **Update Test Data**: Keep fixtures current with real data
3. **Review Test Coverage**: Ensure adequate coverage for new code
4. **Optimize Slow Tests**: Profile and optimize long-running tests

### Test Documentation

```python
class TestComplexWorkflow:
    """
    Test complex workflow scenarios.
    
    This test class covers the end-to-end workflow of:
    1. Issue detection and parsing
    2. Code generation via Claude
    3. Pull request creation
    4. Feedback incorporation
    
    Prerequisites:
    - Redis server running on localhost:6379
    - Mock GitHub API responses configured
    - Test project structure in place
    """
    
    def test_workflow_with_feedback_loop(self):
        """
        Test the complete workflow including feedback incorporation.
        
        Scenario:
        1. Process initial issue
        2. Generate code solution
        3. Receive review feedback
        4. Incorporate feedback
        5. Update pull request
        
        Expected: Successfully updated PR with incorporated feedback
        """
        # Test implementation...
```

Happy testing! 🧪