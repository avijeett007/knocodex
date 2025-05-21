# Installation Guide for Knocodex

This guide provides step-by-step instructions for installing and setting up Knocodex.

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

## Option 1: Using pip

```bash
# Install Knocodex
pip install knocodex

# Set up Knocodex globally
knocodex setup
```

## Option 2: Installing from source

```bash
# Clone the repository
git clone https://github.com/yourusername/knocodex.git

# Navigate to the directory
cd knocodex

# Install the package in development mode
pip install -e .

# Set up Knocodex globally
knocodex setup
```

## Global Setup

When you run `knocodex setup`, the following steps are performed:

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
