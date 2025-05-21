# Installation

This guide covers the complete installation process for Knocodex, including all prerequisites and setup steps.

## Prerequisites

Before installing Knocodex, ensure you have the following:

### System Requirements

- **Python 3.8+**: Knocodex is built with Python and requires version 3.8 or higher
- **Redis Server**: Required for the task queue system
- **Git**: For repository management and pull request creation
- **Claude Code CLI**: The AI coding assistant that powers Knocodex

### GitHub Setup

- GitHub repository with appropriate permissions
- GitHub Personal Access Token with the following scopes:
  - `repo` (full repository access)
  - `workflow` (if using GitHub Actions)

## Installation Steps

### 1. Install Python Dependencies

```bash
# Install Knocodex
pip install knocodex

# Or for development
pip install knocodex[dev]
```

### 2. Install Redis

#### macOS (using Homebrew)
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Docker
```bash
docker run -d -p 6379:6379 redis:alpine
```

### 3. Install Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

### 4. Verify Installation

```bash
# Check Knocodex installation
knocodex --version

# Check Redis connection
redis-cli ping

# Check Claude Code
claude-code --version
```

## Project Setup

### 1. Initialize Knocodex in Your Project

Navigate to your project directory and run:

```bash
cd your-project
knocodex init
```

This creates the `.knocodex/` directory with:
- Configuration files
- Task storage
- Log directories
- Python virtual environment

### 2. Configure GitHub Integration

Edit `.knocodex/config.yaml`:

```yaml
github:
  token: "your-github-token"
  owner: "your-github-username"
  repo: "your-repository-name"
  issue_label: "knocodex-auto"
  poll_interval: 300  # seconds

redis:
  host: "localhost"
  port: 6379
  db: 0

claude:
  headless: true
  timeout: 3600  # seconds
```

### 3. Set Up GitHub Token

Create a `.env` file in your project root:

```bash
GITHUB_TOKEN=your_github_personal_access_token
```

Or set the environment variable:

```bash
export GITHUB_TOKEN=your_github_personal_access_token
```

## Verification

Test your installation:

```bash
# Check service status
knocodex status

# Start services
knocodex start

# Verify all components are running
knocodex dashboard
```

## Troubleshooting Installation

### Common Issues

**Redis Connection Error**
```bash
# Check if Redis is running
redis-cli ping
# Should return "PONG"

# Start Redis if not running
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux
```

**Python Dependencies**
```bash
# Create virtual environment
python -m venv .knocodex/venv
source .knocodex/venv/bin/activate
pip install -r requirements.txt
```

**GitHub API Issues**
- Verify your token has correct permissions
- Check rate limits: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit`

**Claude Code CLI Not Found**
```bash
# Reinstall Claude Code
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code
```

## Next Steps

- [Configure Knocodex](configuration.md)
- [Learn Basic Usage](usage.md)
- [Set Up Issue Management](issue-management.md)