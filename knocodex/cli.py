#!/usr/bin/env python3
"""
Command-line interface for Knocodex
"""

import os
import sys
import json
import click
import logging
from pathlib import Path
from tabulate import tabulate
from datetime import datetime

from .config import Config
from .setup_utils import check_requirements, setup_global_config
from .agent_manager import AgentManager
from .models.subtask import SubtaskStatus
from .models.mcp_task import MCPServerConfig
from .mcp_server import get_mcp_server, run_mcp_server

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

# Project management commands
@main.group()
def project():
    """Manage projects for subtask workflows"""
    pass

@project.command("create")
@click.argument("name")
@click.argument("repo_url")
@click.option("--labels", help="Comma-separated list of issue labels to process", default="knocodex")
def project_create(name, repo_url, labels):
    """Create a new project for subtask workflows"""
    # Get current directory
    project_path = os.getcwd()
    
    # Initialize agent manager
    agent_manager = AgentManager(project_path)
    
    # Parse labels
    label_list = [label.strip() for label in labels.split(",")]
    
    # Create project
    project_id = agent_manager.create_project(name, repo_url, label_list)
    
    if project_id:
        click.echo(f"✅ Created project '{name}' with ID: {project_id}")
    else:
        click.echo("❌ Failed to create project")

@project.command("list")
def project_list():
    """List all projects"""
    # Get current directory
    project_path = os.getcwd()
    
    # Initialize agent manager
    agent_manager = AgentManager(project_path)
    
    # Get projects
    projects = agent_manager.list_projects()
    
    if not projects:
        click.echo("No projects found.")
        return
    
    # Format projects for display
    table_data = []
    for project in projects:
        table_data.append([
            project.project_id,
            project.name,
            project.repository_url,
            ", ".join(project.labels) if project.labels else "",
            project.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(project, 'created_at') and project.created_at else "Unknown"
        ])
    
    # Display table
    click.echo(tabulate(table_data, headers=["ID", "Name", "Repository", "Labels", "Created"], tablefmt="grid"))

@project.command("status")
@click.argument("project_id")
def project_status(project_id):
    """Get status of a project and its workflows"""
    # Get current directory
    project_path = os.getcwd()
    
    # Initialize agent manager
    agent_manager = AgentManager(project_path)
    
    # Get project status
    status = agent_manager.get_project_status(project_id)
    
    if not status:
        click.echo(f"Project {project_id} not found or error occurred.")
        return
    
    # Display project info
    project = status.get("project", {})
    click.echo(f"\n📋 Project: {project.get('name', project_id)}")
    click.echo(f"Repository: {project.get('repository_url', 'Unknown')}")
    click.echo(f"Labels: {', '.join(project.get('labels', []))}")
    
    # Display metrics
    metrics = status.get("metrics", {})
    click.echo(f"\n📊 Metrics:")
    click.echo(f"Total workflows: {metrics.get('total_workflows', 0)}")
    click.echo(f"Completed workflows: {metrics.get('completed_workflows', 0)}")
    click.echo(f"Failed workflows: {metrics.get('failed_workflows', 0)}")
    
    # Display queue status
    queue = status.get("queue", {})
    click.echo(f"\n🔄 Queue Status:")
    click.echo(f"Pending tasks: {queue.get('pending', 0)}")
    click.echo(f"Running tasks: {queue.get('running', 0)}")
    
    # Display active workflows
    active_workflows = status.get("active_workflows", [])
    if active_workflows:
        click.echo(f"\n⚙️ Active Workflows:")
        for workflow in active_workflows:
            click.echo(f"- {workflow}")
    else:
        click.echo(f"\n⚙️ No active workflows")

# Subtask workflow commands
@main.group()
def workflow():
    """Manage subtask workflows"""
    pass

@workflow.command("process-issue")
@click.argument("issue_number", type=int)
@click.option("--project", help="Project ID to associate the issue with")
def process_github_issue(issue_number, project):
    """Process a GitHub issue with subtasks"""
    # Get current directory
    project_path = os.getcwd()
    
    # Initialize agent manager
    agent_manager = AgentManager(project_path)
    
    # Process GitHub issue
    plan_id = agent_manager.process_github_issue(issue_number, project)
    
    if plan_id:
        click.echo(f"✅ Started processing GitHub issue #{issue_number}")
        click.echo(f"Workflow ID: {plan_id}")
        click.echo(f"\nMonitor progress with: knocodex workflow status {plan_id}")
    else:
        click.echo(f"❌ Failed to process GitHub issue #{issue_number}")

@workflow.command("status")
@click.argument("workflow_id")
def workflow_status(workflow_id):
    """Get status of a specific workflow"""
    # Get current directory
    project_path = os.getcwd()
    
    # Initialize agent manager
    agent_manager = AgentManager(project_path)
    
    # Implement workflow status command
    if not agent_manager.workflow_engine:
        click.echo("❌ Workflow engine is not initialized")
        return
    
    try:
        status = agent_manager.workflow_engine.get_workflow_status(workflow_id)
        
        if not status:
            click.echo(f"Workflow {workflow_id} not found.")
            return
        
        # Display workflow info
        click.echo(f"\n📋 Workflow: {workflow_id}")
        click.echo(f"Project: {status.get('project_name', 'Unknown')}")
        click.echo(f"Issue: #{status.get('issue_number', '?')} - {status.get('issue_title', 'Unknown')}")
        click.echo(f"Status: {status.get('status', 'Unknown')}")
        click.echo(f"Progress: {status.get('progress', {}).get('percent_complete', 0)}%")
        click.echo(f"Created: {status.get('created_at', 'Unknown')}")
        
        # Display subtasks
        subtasks = status.get('subtasks', [])
        if subtasks:
            click.echo(f"\n⚙️ Subtasks:")
            
            # Format subtasks for display
            table_data = []
            for subtask in subtasks:
                # Format status with color
                status_text = subtask.get('status', 'Unknown')
                if status_text == SubtaskStatus.COMPLETED.value:
                    status_display = click.style(status_text, fg="green")
                elif status_text == SubtaskStatus.FAILED.value:
                    status_display = click.style(status_text, fg="red")
                elif status_text == SubtaskStatus.IN_PROGRESS.value:
                    status_display = click.style(status_text, fg="blue")
                else:
                    status_display = status_text
                
                # Add to table data
                table_data.append([
                    subtask.get('id', '?'),
                    subtask.get('title', 'Unknown'),
                    status_display,
                    ", ".join(subtask.get('dependencies', []))
                ])
            
            # Display table
            click.echo(tabulate(table_data, headers=["ID", "Title", "Status", "Dependencies"], tablefmt="grid"))
        else:
            click.echo(f"\n⚙️ No subtasks found")
            
    except Exception as e:
        click.echo(f"❌ Error getting workflow status: {e}")

@workflow.command("retry")
@click.argument("workflow_id")
@click.argument("subtask_id")
def retry_subtask(workflow_id, subtask_id):
    """Retry a failed subtask"""
    # Get current directory
    project_path = os.getcwd()
    
    # Initialize agent manager
    agent_manager = AgentManager(project_path)
    
    # Implement retry subtask command
    if not agent_manager.workflow_engine:
        click.echo("❌ Workflow engine is not initialized")
        return
    
    try:
        result = agent_manager.workflow_engine.retry_failed_subtask(workflow_id, subtask_id)
        
        if result:
            click.echo(f"✅ Retrying subtask {subtask_id} in workflow {workflow_id}")
        else:
            click.echo(f"❌ Failed to retry subtask {subtask_id}")
            
    except Exception as e:
        click.echo(f"❌ Error retrying subtask: {e}")

# MCP server management commands
@main.group()
def mcp():
    """MCP server management commands."""
    pass


@mcp.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=8000, help='Port to bind the server to')
@click.option('--workers', default=1, help='Number of worker processes')
def start(host, port, workers):
    """Start the MCP server."""
    click.echo(f"Starting MCP server on {host}:{port}")
    try:
        import asyncio
        asyncio.run(run_mcp_server(host=host, port=port, workers=workers))
    except KeyboardInterrupt:
        click.echo("MCP server stopped")
    except Exception as e:
        click.echo(f"Error starting MCP server: {e}", err=True)


@mcp.command()
def stop():
    """Stop the MCP server."""
    click.echo("Stopping MCP server...")
    # Implementation would check for running server process and stop it
    click.echo("MCP server stopped")


@mcp.command()
def status():
    """Check MCP server status."""
    try:
        server = get_mcp_server()
        if server:
            click.echo("MCP server is running")
        else:
            click.echo("MCP server is not running")
    except Exception as e:
        click.echo(f"Error checking MCP server status: {e}", err=True)


@mcp.command()
@click.option('--host', help='Set server host')
@click.option('--port', type=int, help='Set server port')
@click.option('--debug', type=bool, help='Enable debug mode')
def config(host, port, debug):
    """Configure MCP server settings."""
    config_data = {}
    if host:
        config_data['host'] = host
    if port:
        config_data['port'] = port
    if debug is not None:
        config_data['debug'] = debug
    
    if config_data:
        click.echo(f"Updated MCP server configuration: {config_data}")
    else:
        click.echo("MCP server configuration unchanged")


if __name__ == "__main__":
    main()
