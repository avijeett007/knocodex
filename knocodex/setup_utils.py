#!/usr/bin/env python3
"""
Setup utilities for Knocodex
"""

import os
import sys
import shutil
import subprocess
import logging
import platform
from pathlib import Path

from .config import Config

logger = logging.getLogger("knocodex.setup_utils")

def check_requirements():
    """Check if all requirements are met"""
    requirements_met = True
    
    # Check operating system
    if platform.system() != "Darwin":
        logger.warning("Knocodex is currently only fully supported on macOS")
        logger.warning("Some features may not work on other operating systems")
    
    # Check for brew on macOS
    if platform.system() == "Darwin" and shutil.which("brew") is None:
        logger.error("Homebrew is not installed")
        logger.info("Please install Homebrew from https://brew.sh/")
        requirements_met = False
    
    # Check for Python 3
    if shutil.which("python3") is None:
        logger.error("Python 3 is not installed")
        logger.info("Please install Python 3")
        requirements_met = False
    
    # Check for GitHub CLI
    if shutil.which("gh") is None:
        logger.warning("GitHub CLI is not installed")
        logger.info("We will attempt to install it during setup")
    else:
        # Check GitHub authentication
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.warning("Not authenticated with GitHub")
                logger.info("You will need to authenticate with GitHub during setup")
        except Exception as e:
            logger.warning(f"Failed to check GitHub authentication: {e}")
    
    # Check for Claude Code
    if shutil.which("claude") is None:
        logger.warning("Claude Code is not installed")
        logger.info("We will attempt to install it during setup")
    
    # Check for Redis
    if shutil.which("redis-cli") is None:
        logger.warning("Redis is not installed")
        logger.info("We will attempt to install it during setup")
    else:
        # Check if Redis server is running
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0 or "PONG" not in result.stdout:
                logger.warning("Redis server is not running")
                logger.info("We will attempt to start it during setup")
        except Exception as e:
            logger.warning(f"Failed to check Redis server: {e}")
    
    return requirements_met

def install_dependencies():
    """Install all required dependencies"""
    # Install GitHub CLI if not present
    if shutil.which("gh") is None:
        logger.info("Installing GitHub CLI...")
        if platform.system() == "Darwin":
            try:
                subprocess.run(["brew", "install", "gh"], check=True)
                logger.info("GitHub CLI installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install GitHub CLI: {e}")
                logger.info("Please install GitHub CLI manually: brew install gh")
        else:
            logger.error("Automatic installation of GitHub CLI is only supported on macOS")
            logger.info("Please install GitHub CLI manually: https://cli.github.com/")
    
    # Install Redis if not present
    if shutil.which("redis-cli") is None:
        logger.info("Installing Redis...")
        if platform.system() == "Darwin":
            try:
                subprocess.run(["brew", "install", "redis"], check=True)
                subprocess.run(["brew", "services", "start", "redis"], check=True)
                logger.info("Redis installed and started successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install Redis: {e}")
                logger.info("Please install Redis manually: brew install redis")
        else:
            logger.error("Automatic installation of Redis is only supported on macOS")
            logger.info("Please install Redis manually: https://redis.io/download")
    else:
        # Start Redis if not running
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0 or "PONG" not in result.stdout:
                logger.info("Starting Redis server...")
                if platform.system() == "Darwin":
                    subprocess.run(["brew", "services", "start", "redis"], check=True)
                    logger.info("Redis server started successfully")
                else:
                    logger.error("Automatic starting of Redis is only supported on macOS")
                    logger.info("Please start Redis manually")
        except Exception as e:
            logger.warning(f"Failed to start Redis server: {e}")
    
    # Install Claude Code if not present
    if shutil.which("claude") is None:
        logger.info("Installing Claude Code...")
        try:
            subprocess.run(["npm", "install", "-g", "@anthropic-ai/claude-code"], check=True)
            logger.info("Claude Code installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Claude Code: {e}")
            logger.info("Please install Claude Code manually: npm install -g @anthropic-ai/claude-code")

def setup_github_auth():
    """Set up GitHub authentication"""
    # Check if already authenticated
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            logger.info("Already authenticated with GitHub")
            return True
    except Exception as e:
        logger.warning(f"Failed to check GitHub authentication: {e}")
    
    # Authenticate with GitHub
    logger.info("Authenticating with GitHub...")
    logger.info("This is needed for Knocodex to interact with GitHub issues and PRs")
    logger.info("All operations are performed locally on your machine")
    
    try:
        subprocess.run(["gh", "auth", "login"], check=True)
        logger.info("GitHub authentication successful")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to authenticate with GitHub: {e}")
        logger.info("Please authenticate with GitHub manually: gh auth login")
        return False

def setup_global_config(agent_type="claude"):
    """Set up the global configuration"""
    # Install dependencies
    install_dependencies()
    
    # Set up GitHub authentication
    setup_github_auth()
    
    # Create config manager
    config = Config()
    
    # Create global config
    config.create_global_config()
    
    # Update global config with paths
    updates = {
        "agent_type": agent_type,
        "claude_code_path": shutil.which("claude") or "",
        "gh_path": shutil.which("gh") or "",
    }
    
    # Update global config
    config.update_global_config(updates)
    
    # If using Claude, set up MCP servers
    if agent_type == "claude":
        setup_claude_mcp_servers()
    
    logger.info("Global configuration setup complete")

def setup_claude_mcp_servers():
    """Set up Claude MCP servers"""
    # Check if Claude is installed
    if shutil.which("claude") is None:
        logger.error("Claude Code is not installed")
        logger.info("Please install Claude Code: npm install -g @anthropic-ai/claude-code")
        return False
    
    # Check if already set up
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
        if "autonomous_coding" in result.stdout:
            logger.info("MCP servers already set up")
            return True
    except Exception as e:
        logger.warning(f"Failed to check MCP servers: {e}")
    
    # We'll set up MCP servers during project initialization
    logger.info("MCP servers will be set up during project initialization")
    return True
