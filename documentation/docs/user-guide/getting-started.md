# Getting Started

Welcome to Knocodex, the autonomous AI-powered code development platform! This guide will help you get up and running with Knocodex quickly.

## What is Knocodex?

Knocodex is an autonomous coding system that uses AI agents (Claude Code) to automatically process GitHub issues, implement solutions, and create pull requests. It's designed to streamline your development workflow by handling routine coding tasks while you focus on higher-level architecture and decision-making.

## Key Features

- **Autonomous Issue Processing**: Automatically detects and processes GitHub issues labeled for automation
- **AI-Powered Implementation**: Uses Claude Code to analyze, plan, and implement solutions
- **Queue-Based Architecture**: Reliable task processing using Redis queues
- **Custom Commands**: Specialized Claude commands for different types of work
- **Monitoring Dashboard**: Real-time monitoring of task processing

## Quick Start

1. **Install Knocodex**
   ```bash
   pip install knocodex
   ```

2. **Initialize Your Project**
   ```bash
   cd your-project
   knocodex init
   ```

3. **Configure GitHub Integration**
   Set up your GitHub token and repository settings in `.knocodex/config.yaml`

4. **Start the Service**
   ```bash
   knocodex start
   ```

5. **Monitor Progress**
   ```bash
   knocodex dashboard
   ```

## How It Works

1. **Issue Detection**: Knocodex monitors your GitHub repository for issues with specific labels
2. **Analysis**: When an issue is detected, Claude Code analyzes it and creates an implementation plan
3. **Implementation**: The AI agent implements the solution following the plan
4. **Pull Request**: A pull request is automatically created with the implementation
5. **Review**: You review and merge the pull request as needed

## Next Steps

- [Complete Installation Guide](installation.md)
- [Configuration Options](configuration.md)
- [Usage Examples](usage.md)
- [Issue Management](issue-management.md)

## Need Help?

If you encounter any issues or have questions:
- Check the [Troubleshooting Guide](troubleshooting.md)
- Read the [Developer Documentation](../developer-guide/architecture.md)
- Create an issue in our GitHub repository