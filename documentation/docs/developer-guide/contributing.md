# Contributing to Knocodex

Welcome to Knocodex! We're excited to have you contribute to this autonomous AI-powered coding platform. This guide will help you get started with contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful**: Treat all contributors with respect and kindness
- **Be inclusive**: Welcome newcomers and help them learn
- **Be constructive**: Provide helpful feedback and suggestions
- **Be professional**: Focus on the code and technical discussions

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8+ installed
- Redis server running
- Git configured with your GitHub account
- Basic understanding of async programming and queue systems

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/knocodex.git
   cd knocodex
   ```

3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/knocodex.git
   ```

### Development Setup

Follow the [Development Setup](development-setup.md) guide to set up your local development environment.

## Development Workflow

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature branches (e.g., `feature/github-integration`)
- **bugfix/**: Bug fix branches (e.g., `bugfix/redis-connection`)
- **hotfix/**: Critical fixes for production

### Creating a Feature Branch

```bash
# Update your local develop branch
git checkout develop
git pull upstream develop

# Create a new feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Commit your changes
git add .
git commit -m "Add: implement your feature"

# Push to your fork
git push origin feature/your-feature-name
```

### Keeping Your Branch Updated

```bash
# Fetch upstream changes
git fetch upstream

# Rebase your branch on latest develop
git rebase upstream/develop

# Force push if necessary (be careful!)
git push --force-with-lease origin feature/your-feature-name
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some additional conventions:

#### Import Organization
```python
# Standard library imports
import os
import sys
from typing import Optional, Dict, List

# Third-party imports
import click
import redis
from rq import Queue

# Local imports
from knocodex.config import Config
from knocodex.utils.redis_utils import get_redis_connection
```

#### Function Documentation
```python
def process_github_issue(issue_data: Dict, config: Config) -> bool:
    """
    Process a single GitHub issue through the Knocodex pipeline.
    
    Args:
        issue_data: Dictionary containing GitHub issue information
        config: Knocodex configuration object
        
    Returns:
        bool: True if issue was processed successfully, False otherwise
        
    Raises:
        RedisConnectionError: If Redis connection fails
        ConfigurationError: If configuration is invalid
    """
    pass
```

#### Error Handling
```python
# Use specific exception types
try:
    result = risky_operation()
except RedisConnectionError as e:
    logger.error(f"Redis connection failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return False
```

#### Logging
```python
import logging

logger = logging.getLogger(__name__)

def example_function():
    logger.info("Starting operation")
    try:
        # Do something
        logger.debug("Operation details")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
```

### Code Quality Tools

We use several tools to maintain code quality:

#### Black (Code Formatting)
```bash
black knocodex/ tests/
```

#### isort (Import Sorting)
```bash
isort knocodex/ tests/
```

#### flake8 (Linting)
```bash
flake8 knocodex/ tests/
```

#### mypy (Type Checking)
```bash
mypy knocodex/
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run quality checks:

```bash
pip install pre-commit
pre-commit install
```

## Testing Guidelines

### Test Organization

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test data and fixtures
└── conftest.py     # pytest configuration
```

### Writing Tests

#### Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch

from knocodex.agent_manager import AgentManager
from knocodex.config import Config

class TestAgentManager:
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.github_token = "test-token"
        config.github_repo = "test/repo"
        return config
    
    @pytest.fixture
    def agent_manager(self, mock_config):
        return AgentManager(mock_config)
    
    def test_initialization(self, agent_manager, mock_config):
        assert agent_manager.config == mock_config
        assert agent_manager.github_client is not None
    
    @patch('knocodex.agent_manager.subprocess.run')
    def test_run_claude_command(self, mock_subprocess, agent_manager):
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Success"
        
        result = agent_manager.run_claude_command("test command")
        
        assert result.success is True
        assert result.output == "Success"
```

#### Integration Test Example
```python
import pytest
import redis
from rq import Queue

from knocodex.worker import create_worker
from knocodex.config import Config

@pytest.mark.integration
class TestWorkerIntegration:
    @pytest.fixture
    def redis_connection(self):
        # Use test Redis database
        return redis.Redis(host='localhost', port=6379, db=15)
    
    @pytest.fixture
    def test_queue(self, redis_connection):
        return Queue('test', connection=redis_connection)
    
    def test_worker_processes_job(self, test_queue, redis_connection):
        # Enqueue a test job
        job = test_queue.enqueue('knocodex.tasks.process_issue', {'id': 123})
        
        # Process the job
        worker = create_worker([test_queue])
        worker.work(burst=True)
        
        # Verify job completion
        assert job.is_finished
        assert job.result is not None
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=knocodex --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_agent_manager.py

# Run with verbose output
pytest -v
```

## Pull Request Process

### Before Submitting

1. **Run tests**: Ensure all tests pass
   ```bash
   pytest
   ```

2. **Run quality checks**: Format and lint your code
   ```bash
   black knocodex/ tests/
   isort knocodex/ tests/
   flake8 knocodex/ tests/
   mypy knocodex/
   ```

3. **Update documentation**: Update relevant documentation
4. **Write tests**: Add tests for new functionality

### Pull Request Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows the style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented where necessary
- [ ] Documentation updated
- [ ] No breaking changes introduced

## Related Issues
Closes #[issue_number]
```

### Review Process

1. **Automated checks**: CI/CD pipeline runs tests and quality checks
2. **Code review**: At least one maintainer reviews the PR
3. **Testing**: Manual testing of new functionality
4. **Documentation**: Ensure documentation is updated
5. **Merge**: PR is merged by maintainer

## Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g., macOS, Ubuntu]
- Python version: [e.g., 3.9.0]
- Knocodex version: [e.g., 1.0.0]

**Additional Context**
Any other context about the problem.
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
A clear description of the feature.

**Use Case**
Describe the use case and why this feature would be valuable.

**Proposed Solution**
If you have ideas on how to implement this feature.

**Additional Context**
Any other context or screenshots.
```

## Documentation

### Writing Documentation

- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Link to related documentation
- Test all code examples

### Documentation Structure

```
docs/
├── user-guide/      # End-user documentation
├── developer-guide/ # Developer documentation
├── api/            # API reference
└── examples/       # Code examples and tutorials
```

### Docusaurus Commands

```bash
# Start development server
npm run start

# Build documentation
npm run build

# Deploy to GitHub Pages
npm run deploy
```

## Getting Help

- **Discord**: Join our Discord server for real-time chat
- **GitHub Discussions**: For general questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Email**: Contact maintainers at contributors@knocodex.dev

## Recognition

Contributors are recognized in:
- **CONTRIBUTORS.md**: Listed in the contributors file
- **Release notes**: Major contributions highlighted
- **Documentation**: Author attribution where appropriate

Thank you for contributing to Knocodex! 🚀