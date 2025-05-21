#!/usr/bin/env python3
"""
Command-line interface for Knocodex
"""

import os
import sys
import click
import logging
from pathlib import Path

from .config import Config
from .setup_utils import check_requirements, setup_global_config
from .agent_manager import AgentManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("knocodex")

# Create a Click group for commands
@click.group()
@click.version_option()
def main():
    """Knocodex - An open-source Python library for autonomous coding with AI agents"""
    pass

@main.command()
@click.option("--agent", type=click.Choice(["claude", "aider"]), default="claude", 
              help="The agent to use (aider support is coming soon)")
def setup(agent):
    """Set up Knocodex globally"""
    click.echo("Setting up Knocodex globally...")
    
    # Check requirements
    check_requirements()
    
    # Set up global configuration
    setup_global_config(agent)
    
    click.echo("Knocodex setup complete!")

@main.command()
@click.option("--agent", type=click.Choice(["claude", "aider"]), default=None, 
              help="Override the agent to use (defaults to global config)")
def init(agent):
    """Initialize a project for Knocodex"""
    click.echo("Initializing project for Knocodex...")
    
    # Get the project path
    project_path = os.getcwd()
    
    # Create agent manager
    agent_manager = AgentManager(project_path)
    
    # Initialize the project
    agent_manager.init_project(agent)
    
    # Import MCP servers from Claude Desktop if using Claude
    if agent_manager.agent_type == "claude":
        agent_manager.import_mcp_servers()
    
    click.echo("Project initialization complete!")

@main.command()
def start():
    """Start the autonomous agent"""
    click.echo("Starting Knocodex autonomous agent...")
    
    # Get the project path
    project_path = os.getcwd()
    
    # Create agent manager
    agent_manager = AgentManager(project_path)
    
    # Start the agent
    agent_manager.start()
    
    click.echo("Knocodex agent started!")

@main.command()
def stop():
    """Stop the autonomous agent"""
    click.echo("Stopping Knocodex autonomous agent...")
    
    # Get the project path
    project_path = os.getcwd()
    
    # Create agent manager
    agent_manager = AgentManager(project_path)
    
    # Stop the agent
    agent_manager.stop()
    
    click.echo("Knocodex agent stopped!")

@main.command()
def status():
    """Check the status of the autonomous agent"""
    click.echo("Checking Knocodex agent status...")
    
    # Get the project path
    project_path = os.getcwd()
    
    # Create agent manager
    agent_manager = AgentManager(project_path)
    
    # Get the status
    status = agent_manager.status()
    
    # Display the status
    click.echo(f"Agent type: {status['agent_type']}")
    click.echo(f"Worker running: {'Yes' if status['worker_running'] else 'No'}")
    click.echo(f"Redis running: {'Yes' if status['redis_running'] else 'No'}")
    click.echo(f"Dashboard running: {'Yes' if status['dashboard_running'] else 'No'}")

@main.command()
def docs():
    """Generate project documentation"""
    click.echo("Generating project documentation...")
    
    # Get the project path
    project_path = os.getcwd()
    
    # Create agent manager
    agent_manager = AgentManager(project_path)
    
    # Generate documentation
    agent_manager.generate_docs()
    
    click.echo("Documentation generation complete!")

@main.command()
def dashboard():
    """Start the RQ dashboard"""
    click.echo("Starting RQ dashboard...")
    
    # Get the project path
    project_path = os.getcwd()
    
    # Create agent manager
    agent_manager = AgentManager(project_path)
    
    # Start the dashboard
    agent_manager.start_dashboard()
    
    click.echo("Dashboard started at http://localhost:9181")

if __name__ == "__main__":
    main()
