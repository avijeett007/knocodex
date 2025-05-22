#!/usr/bin/env python3
"""
Configuration management for Knocodex
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("knocodex.config")

class Config:
    """Configuration manager for Knocodex"""
    
    def __init__(self, project_path=None):
        """Initialize the configuration manager"""
        self.home_dir = Path.home()
        self.global_config_dir = self.home_dir / ".knocodex"
        self.global_config_file = self.global_config_dir / "config.json"
        
        # Project-specific configuration
        self.project_path = Path(project_path) if project_path else None
        self.project_config_dir = self.project_path / ".knocodex" if self.project_path else None
        self.project_config_file = self.project_config_dir / "config.json" if self.project_config_dir else None
        
        # Base directory for project manager - needed for subtask workflows
        self.base_dir = self.global_config_dir
        if self.project_path:
            self.base_dir = self.project_path
        
        # Default global configuration
        self.default_global_config = {
            "agent_type": "claude",  # Default agent type (claude or aider)
            "ai_backend": "claude-code",  # AI backend (claude-code or aider)
            "redis_url": "redis://localhost:6379",
            "redis_queue": "knocodex",
            "polling_interval": 300,  # 5 minutes
            "github_issue_label": "knocodex",
            "claude_code_path": "",  # Will be set during setup
            "gh_path": "",  # Will be set during setup
            # Claude Code configuration
            "claude_api_key": "",  # Will be set from environment
            "claude_model": "claude-3-5-sonnet-20241022",
            # Aider configuration
            "aider_model": "gemini-exp",
            "aider_auto_commits": True,
            "aider_stream": False,
            "aider_verbose": False,
            # API keys for different models
            "gemini_api_key": "",  # Will be set from environment
            "openai_api_key": "",  # Will be set from environment
            "anthropic_api_key": "",  # Will be set from environment
        }
        
        # Default project configuration
        self.default_project_config = {
            "agent_type": None,  # Will inherit from global config if None
            "github_repo": "",  # Will be set during init
            "github_issue_label": "knocodex",
            "polling_interval": 300,  # 5 minutes
            "pr_review_enabled": True,
            "pr_auto_review": True,
            "pr_auto_review_delay": 300,  # 5 minutes
        }
    
    def create_global_config(self):
        """Create the global configuration directory and file"""
        # Create the global config directory if it doesn't exist
        self.global_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the global config file if it doesn't exist
        if not self.global_config_file.exists():
            with open(self.global_config_file, "w") as f:
                json.dump(self.default_global_config, f, indent=2)
            logger.info(f"Created global config file at {self.global_config_file}")
        
        return self.global_config_file
    
    def get_global_config(self):
        """Get the global configuration"""
        if not self.global_config_file.exists():
            self.create_global_config()
        
        with open(self.global_config_file, "r") as f:
            config = json.load(f)
        
        return config
    
    def update_global_config(self, updates):
        """Update the global configuration"""
        config = self.get_global_config()
        config.update(updates)
        
        with open(self.global_config_file, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Updated global config file at {self.global_config_file}")
        return config
    
    def create_project_config(self):
        """Create the project configuration directory and file"""
        if not self.project_path:
            raise ValueError("Project path not set")
        
        # Create the project config directory if it doesn't exist
        self.project_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the project config file if it doesn't exist
        if not self.project_config_file.exists():
            # Get the global config to inherit from
            global_config = self.get_global_config()
            
            # Create the project config
            project_config = self.default_project_config.copy()
            project_config["agent_type"] = global_config["agent_type"]
            
            # Try to get the GitHub repo from the git config
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "config", "--get", "remote.origin.url"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    repo_url = result.stdout.strip()
                    # Extract the username/repo from the URL
                    if "github.com" in repo_url:
                        if repo_url.startswith("git@github.com:"):
                            # SSH URL format: git@github.com:username/repo.git
                            repo = repo_url.split("git@github.com:")[1].split(".git")[0]
                        else:
                            # HTTPS URL format: https://github.com/username/repo.git
                            repo = repo_url.split("github.com/")[1].split(".git")[0]
                        
                        project_config["github_repo"] = repo
            except Exception as e:
                logger.warning(f"Failed to get GitHub repo from git config: {e}")
            
            with open(self.project_config_file, "w") as f:
                json.dump(project_config, f, indent=2)
            
            logger.info(f"Created project config file at {self.project_config_file}")
        
        return self.project_config_file
    
    def get_project_config(self):
        """Get the project configuration"""
        if not self.project_path:
            raise ValueError("Project path not set")
        
        if not self.project_config_file.exists():
            self.create_project_config()
        
        with open(self.project_config_file, "r") as f:
            config = json.load(f)
        
        # If agent_type is None, inherit from global config
        if config["agent_type"] is None:
            global_config = self.get_global_config()
            config["agent_type"] = global_config["agent_type"]
        
        return config
    
    def update_project_config(self, updates):
        """Update the project configuration"""
        if not self.project_path:
            raise ValueError("Project path not set")
        
        config = self.get_project_config()
        config.update(updates)
        
        with open(self.project_config_file, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Updated project config file at {self.project_config_file}")
        return config
