# Development Setup

This guide will help you set up a complete development environment for Knocodex. Follow these steps to get started with contributing to the project.

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows with WSL2
- **Python**: 3.8 or higher (3.9+ recommended)
- **Redis**: 6.0 or higher
- **Git**: Latest version
- **Node.js**: 16+ (for documentation development)

### Required Accounts

- **GitHub Account**: For code contributions and issue tracking
- **Claude AI Account**: For AI agent integration
- **Redis Cloud** (optional): For cloud-based Redis instances

## Environment Setup

### 1. Clone the Repository

```bash
# Clone your fork of the repository
git clone https://github.com/YOUR_USERNAME/knocodex.git
cd knocodex

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/knocodex.git

# Verify remotes
git remote -v
```

### 2. Python Environment

#### Using pyenv (Recommended)

```bash
# Install pyenv (macOS)
brew install pyenv

# Install pyenv (Linux)
curl https://pyenv.run | bash

# Install Python 3.9
pyenv install 3.9.16
pyenv local 3.9.16

# Verify Python version
python --version
```

#### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Activate virtual environment (Windows)
venv\Scripts\activate

# Verify activation
which python  # Should point to venv/bin/python
```

### 3. Install Dependencies

#### Core Dependencies

```bash
# Install core requirements
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

#### Development Tools

```bash
# Install development tools
pip install \
    black \
    isort \
    flake8 \
    mypy \
    pytest \
    pytest-cov \
    pytest-asyncio \
    pre-commit
```

### 4. Redis Setup

#### Local Redis Installation

**macOS (using Homebrew):**
```bash
brew install redis
brew services start redis

# Verify Redis is running
redis-cli ping  # Should return PONG
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping  # Should return PONG
```

**Docker (Alternative):**
```bash
# Run Redis in Docker
docker run -d \
    --name redis-dev \
    -p 6379:6379 \
    redis:7-alpine

# Verify connection
docker exec -it redis-dev redis-cli ping
```

#### Redis Configuration

Create a development Redis configuration:

```bash
# Create Redis config directory
mkdir -p ~/.knocodex/redis

# Create development Redis config
cat > ~/.knocodex/redis/redis-dev.conf << EOF
# Redis development configuration
port 6379
bind 127.0.0.1
dir ~/.knocodex/redis/
dbfilename dump-dev.rdb
logfile ~/.knocodex/redis/redis-dev.log
loglevel notice

# Development-specific settings
save 900 1
save 300 10
save 60 10000
EOF

# Start Redis with custom config
redis-server ~/.knocodex/redis/redis-dev.conf
```

### 5. Claude Code CLI Setup

#### Installation

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verify installation
claude-code --version
```

#### Configuration

```bash
# Initialize Claude Code in project
cd /path/to/knocodex
claude-code init

# Configure API key (interactive)
claude-code config

# Or set environment variable
export ANTHROPIC_API_KEY="your-api-key-here"
```

#### Custom Commands Setup

```bash
# Create Claude commands directory
mkdir -p .claude/commands

# Copy Knocodex custom commands
cp -r knocodex/templates/commands/* .claude/commands/

# Verify commands are available
claude-code --list-commands
```

### 6. Environment Configuration

#### Create Development Configuration

```bash
# Create .env file for development
cat > .env << EOF
# Knocodex Development Configuration

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# GitHub Configuration
GITHUB_TOKEN=your-github-token-here
GITHUB_REPO=your-username/your-repo
GITHUB_POLLING_INTERVAL=30

# Claude Configuration
ANTHROPIC_API_KEY=your-claude-api-key-here
CLAUDE_MODEL=claude-3-sonnet-20240229

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FILE=.knocodex/logs/knocodex-dev.log

# Development Mode
DEBUG=true
ENVIRONMENT=development
EOF

# Make sure .env is in .gitignore
echo ".env" >> .gitignore
```

#### Create Development Directories

```bash
# Create necessary directories
mkdir -p .knocodex/{logs,tasks,temp}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p docs/examples

# Set up logging
touch .knocodex/logs/knocodex-dev.log
```

### 7. Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files (optional)
pre-commit run --all-files
```

#### Pre-commit Configuration

The project includes a `.pre-commit-config.yaml` file:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-redis, types-requests]
```

## Development Workflow

### 1. Initial Setup Verification

```bash
# Run setup verification script
python -m knocodex.scripts.verify_setup

# Or manually verify components
python -c "import redis; print('Redis OK')"
python -c "from rq import Queue; print('RQ OK')"
python -c "import click; print('Click OK')"
```

### 2. Start Development Services

#### Terminal 1: Redis Server
```bash
# Start Redis with development config
redis-server ~/.knocodex/redis/redis-dev.conf
```

#### Terminal 2: RQ Worker
```bash
# Activate virtual environment
source venv/bin/activate

# Start development worker
python -m knocodex.worker --queue development --burst
```

#### Terminal 3: Development Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start Knocodex in development mode
export DEBUG=true
python -m knocodex.cli status
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=knocodex --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run tests with live Redis (integration tests)
pytest tests/integration/ --redis-url=redis://localhost:6379/15
```

### 4. Code Quality Checks

```bash
# Format code
black knocodex/ tests/

# Sort imports
isort knocodex/ tests/

# Lint code
flake8 knocodex/ tests/

# Type checking
mypy knocodex/

# Run all quality checks
make quality  # If Makefile is available
```

## IDE Setup

### VS Code Configuration

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".mypy_cache": true,
        ".pytest_cache": true
    }
}
```

Create `.vscode/launch.json` for debugging:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Knocodex CLI",
            "type": "python",
            "request": "launch",
            "module": "knocodex.cli",
            "args": ["status"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        },
        {
            "name": "RQ Worker",
            "type": "python",
            "request": "launch",
            "module": "knocodex.worker",
            "args": ["--queue", "development"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        }
    ]
}
```

### PyCharm Configuration

1. **Interpreter Setup**:
   - File → Settings → Project → Python Interpreter
   - Add Local Interpreter → Existing environment
   - Select `venv/bin/python`

2. **Code Style**:
   - File → Settings → Tools → External Tools
   - Add Black formatter configuration
   - Add isort configuration

3. **Run Configurations**:
   - Create run configuration for `knocodex.cli`
   - Create run configuration for `knocodex.worker`

## Documentation Development

### Setup Docusaurus

```bash
# Navigate to documentation directory
cd documentation

# Install Node.js dependencies
npm install

# Start development server
npm run start

# Build documentation
npm run build

# Deploy to GitHub Pages
npm run deploy
```

### Writing Documentation

- Follow the [Contributing Guidelines](contributing.md) for documentation standards
- Use Markdown with Docusaurus-specific features
- Test all code examples
- Include screenshots for UI features

## Debugging

### Common Development Issues

#### Redis Connection Errors

```bash
# Check Redis status
redis-cli ping

# Check Redis logs
tail -f ~/.knocodex/redis/redis-dev.log

# Test connection from Python
python -c "import redis; r = redis.Redis(); print(r.ping())"
```

#### Python Environment Issues

```bash
# Verify virtual environment
which python
pip list

# Recreate virtual environment if needed
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Claude Code CLI Issues

```bash
# Verify installation
claude-code --version

# Check configuration
claude-code config --show

# Test API connection
claude-code api test
```

### Debug Mode

Enable debug mode for verbose logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python -m knocodex.cli --verbose status
```

## Performance Optimization

### Development Performance

1. **Redis Optimization**:
   - Use local Redis instance
   - Adjust save settings for development
   - Use separate database for tests

2. **Python Optimization**:
   - Use `asyncio` for concurrent operations
   - Cache expensive computations
   - Profile code with `cProfile`

3. **Testing Optimization**:
   - Use pytest fixtures for setup/teardown
   - Mock external services
   - Run tests in parallel with `pytest-xdist`

## Troubleshooting

### Environment Issues

| Issue | Solution |
|-------|----------|
| Python version conflicts | Use pyenv to manage Python versions |
| Redis connection refused | Ensure Redis server is running |
| Import errors | Verify virtual environment activation |
| Permission errors | Check file permissions and ownership |

### Getting Help

- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Ask questions and share ideas
- **Discord**: Join the developer community
- **Documentation**: Check the troubleshooting guide

## Next Steps

After completing the development setup:

1. Read the [Architecture Overview](architecture.md)
2. Study the [Core Components](core-components.md)
3. Check out [Contributing Guidelines](contributing.md)
4. Start with a beginner-friendly issue labeled `good-first-issue`

Happy coding! 🚀