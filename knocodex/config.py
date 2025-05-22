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
            # Workflow Configuration
            "sequential_processing": True,  # Enable sequential task processing
            "enforce_pr_creation": True,  # Mandate PR creation after task completion
            "max_parallel_subtasks": 3,  # Max parallel subtasks within a task
            "task_lock_timeout": 3600,  # Task lock timeout in seconds (1 hour)
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
            # PR review behavior configuration
            "pr_review_mode": "never_repeat",  # never_repeat, on_updates, manual_only
            "pr_state_storage_path": None,  # Path for PR state storage (default: .knocodex/pr_review_state.json)
            "pr_update_detection_enabled": True,  # Enable PR update detection
            # Project-specific workflow settings
            "project_id": "",  # Unique project identifier
            "sequential_processing": None,  # Inherit from global if None
            "enforce_pr_creation": None,  # Inherit from global if None
            "max_parallel_subtasks": None,  # Inherit from global if None
            "task_lock_timeout": None,  # Inherit from global if None
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
        """Get the project configuration with global inheritance"""
        if not self.project_path:
            raise ValueError("Project path not set")
        
        if not self.project_config_file.exists():
            self.create_project_config()
        
        with open(self.project_config_file, "r") as f:
            config = json.load(f)
        
        # Inherit from global config for None values
        global_config = self.get_global_config()
        
        # List of keys that should inherit from global config if None
        inherit_keys = [
            "agent_type",
            "sequential_processing", 
            "enforce_pr_creation",
            "max_parallel_subtasks",
            "task_lock_timeout"
        ]
        
        for key in inherit_keys:
            if config.get(key) is None and key in global_config:
                config[key] = global_config[key]
        
        # Set project_id based on project path if not set
        if not config.get("project_id") and self.project_path:
            config["project_id"] = self.project_path.name
        
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
    
    def get_redis_queue_name(self, project_id: str = None) -> str:
        """Get the Redis queue name for a project"""
        if project_id:
            return f"knocodex:{project_id}:tasks"
        
        # Get project_id from config
        try:
            config = self.get_project_config()
            project_id = config.get("project_id", "default")
            return f"knocodex:{project_id}:tasks"
        except:
            # Fallback to default queue naming
            return "knocodex:default:tasks"
    
    def is_sequential_processing_enabled(self) -> bool:
        """Check if sequential processing is enabled"""
        try:
            config = self.get_project_config()
            return config.get("sequential_processing", True)
        except:
            global_config = self.get_global_config()
            return global_config.get("sequential_processing", True)
    
    def is_pr_creation_enforced(self) -> bool:
        """Check if PR creation is enforced"""
        try:
            config = self.get_project_config()
            return config.get("enforce_pr_creation", True)
        except:
            global_config = self.get_global_config()
            return global_config.get("enforce_pr_creation", True)
