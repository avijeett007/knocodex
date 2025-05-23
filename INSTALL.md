# Installation Guide for Knocodex

This guide provides comprehensive instructions for installing and setting up Knocodex in various Python environments.

## Prerequisites

Knocodex currently requires:

- **Operating System**: macOS (with Homebrew)
- **Dependencies**:
  - Node.js and npm (for Claude Code CLI)
  - Python 3.6+
  - Git and GitHub CLI
  - Redis

## Installation Methods

There are two ways to install Knocodex:

1. **Using pip** (Recommended)
2. **Installing from source**

## Option 1: Using pip (Recommended)

```bash
# Install Knocodex
pip install knocodex

# Set up Knocodex globally
knocodex setup
```

## Option 2: Installing from source

```bash
# Clone the repository
git clone https://github.com/avijeett007/knocodex.git

# Navigate to the directory
cd knocodex

# Install the package in development mode
pip install -e .

# Set up Knocodex globally
knocodex setup
```

## Global Setup

When you run `knocodex setup`, the following steps are performed:

1. Creates a global `.knocodex` directory in your home folder
2. Sets up global configuration
3. Checks for dependencies like Redis, GitHub CLI
4. Configures access to AI models (Claude, OpenAI, etc.)

## Project-Specific Setup

After installing Knocodex globally, you need to initialize it in each project where you want to use it:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialize Knocodex in this project
knocodex init
```

The `knocodex init` command performs these important steps:

1. Creates a `.knocodex` directory in your project (automatically added to `.gitignore`)
2. Sets up project-specific configuration
3. **Creates a dedicated virtual environment** in `.knocodex/venv`
4. Installs all required dependencies in this isolated environment, including:
   - Redis client libraries
   - RQ (Redis Queue) and dashboard
   - FastAPI, Uvicorn, and SSE-Starlette for MCP server
   - Pydantic and other required dependencies
5. Configures command files for interaction with AI agents

> **Note:** The project-specific virtual environment ensures that Knocodex works consistently regardless of your global Python environment (conda, venv, uv, etc.)

## Starting Knocodex

After initializing, you can start Knocodex:

```bash
knocodex start
```

This command launches several components:
1. Redis server (if not already running)
2. Worker process for handling tasks
3. Subtask worker for workflow management
4. RQ dashboard for monitoring
5. Main polling loop for checking GitHub issues/PRs

## Stopping Knocodex

```bash
knocodex stop
```

## Troubleshooting

### Missing Dependency Errors

If you encounter errors about missing Python modules like:

```
ModuleNotFoundError: No module named 'pydantic'
```

Try these steps:

1. **Reinitialize the project**:
   ```bash
   knocodex stop
   rm -rf .knocodex/venv  # Remove the existing virtual environment
   knocodex init           # Recreate with all dependencies
   knocodex start
   ```

2. **Install missing dependencies manually**:
   ```bash
   .knocodex/venv/bin/pip install pydantic fastapi uvicorn sse-starlette
   ```

3. **Install knocodex in development mode in the virtual environment**:
   ```bash
   .knocodex/venv/bin/pip install -e .
   ```

### PR Review Issues

If Knocodex repeatedly reviews the same PR:

1. Ensure PR review state storage is configured:
   ```bash
   mkdir -p .knocodex/state
   echo '{}' > .knocodex/state/pr_review_state.json
   ```

2. Update your configuration to set the PR state storage path:
   ```python
   python -c "import json; config = json.load(open('.knocodex/config.json')); config['pr_state_storage_path'] = '.knocodex/state/pr_review_state.json'; json.dump(config, open('.knocodex/config.json', 'w'), indent=2)"
   ```

3. Restart Knocodex:
   ```bash
   knocodex stop && knocodex start
   ```

### Environment Compatibility

Knocodex is designed to work consistently across different Python environments:

1. Check for required dependencies
2. Install missing dependencies (GitHub CLI, Redis, Claude Code)
3. Set up GitHub authentication
4. Configure Claude MCP servers
5. Create a global configuration file

## Project Setup

After installing Knocodex, you need to set up each project to use it:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialize the project
knocodex init
```

This will:
- Create necessary directories (.knocodex, .claude/commands)
- Set up a Python virtual environment
- Create configuration files
- Configure custom Claude commands
- Import MCP servers from Claude Desktop

## Configuration

Knocodex uses two levels of configuration:

1. **Global Configuration**: Stored in `~/.knocodex/config.json`
2. **Project Configuration**: Stored in `.knocodex/config.json` in your project directory

You can edit these files to customize the behavior of Knocodex.

## Usage

Once you have set up Knocodex, you can use the following commands:

```bash
# Start the autonomous agent
knocodex start

# Stop the autonomous agent
knocodex stop

# Check the status of the agent
knocodex status

# Generate project documentation
knocodex docs

# Start the RQ dashboard
knocodex dashboard
```

## Troubleshooting

If you encounter any issues during installation or setup:

1. Make sure all prerequisites are installed
2. Check the logs in `.knocodex/logs/`
3. Try running the commands with verbose output: `knocodex --verbose [command]`
4. If Redis fails to start, try starting it manually: `brew services start redis`
5. If GitHub authentication fails, try authenticating manually: `gh auth login`

For more detailed information, see the [README.md](README.md) file.
