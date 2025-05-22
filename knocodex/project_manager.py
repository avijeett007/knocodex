"""
Project isolation and management system for Knocodex.
Handles project-specific queues, configuration, and resource management.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import redis
from redis import Redis
import logging

from .config import Config
from .models import SubtaskStatus, WorkflowStatus

logger = logging.getLogger(__name__)

@dataclass
class ProjectConfig:
    """Configuration for a specific project."""
    project_id: str
    name: str
    repository_url: str
    local_path: str
    github_token: str
    labels: List[str]
    max_concurrent_workflows: int = 3
    max_concurrent_subtasks: int = 10
    queue_priority: int = 1
    auto_merge_enabled: bool = False
    notification_settings: Dict = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.notification_settings is None:
            self.notification_settings = {
                'slack_webhook': None,
                'email_recipients': [],
                'discord_webhook': None
            }
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class ProjectMetrics:
    """Metrics tracking for project performance."""
    project_id: str
    total_issues_processed: int = 0
    total_subtasks_completed: int = 0
    total_subtasks_failed: int = 0
    average_completion_time: float = 0.0
    success_rate: float = 0.0
    active_workflows: int = 0
    queue_depth: int = 0
    last_activity: Optional[datetime] = None
    
class ProjectManager:
    """Manages project isolation, configuration, and resource allocation."""
    
    def __init__(self, config=None, redis_client=None):
        """
        Initialize the project manager.
        
        Args:
            config: Optional Config object or string path to config directory
            redis_client: Optional Redis client instance or Redis URL string
        """
        self.config = config
        
        # Handle Redis connection initialization
        if redis_client is None:
            # Default Redis connection
            redis_url = "redis://localhost:6379"
            self.redis = Redis.from_url(redis_url)
        elif isinstance(redis_client, str):
            # Redis URL string
            self.redis = Redis.from_url(redis_client)
        else:
            # Redis connection object
            self.redis = redis_client
        
        self.projects: Dict[str, ProjectConfig] = {}
        self.metrics: Dict[str, ProjectMetrics] = {}
        self._load_projects()
        
    def create_project(self, 
                      name: str,
                      repository_url: str,
                      local_path: str,
                      github_token: str,
                      labels: List[str],
                      **kwargs) -> str:
        """Create a new project configuration."""
        project_id = self._generate_project_id(name, repository_url)
        
        project_config = ProjectConfig(
            project_id=project_id,
            name=name,
            repository_url=repository_url,
            local_path=local_path,
            github_token=github_token,
            labels=labels,
            **kwargs
        )
        
        self.projects[project_id] = project_config
        self.metrics[project_id] = ProjectMetrics(project_id=project_id)
        
        # Create project-specific Redis queues
        self._setup_project_queues(project_id)
        
        # Save project configuration
        self._save_project_config(project_config)
        
        logger.info(f"Created project {name} with ID {project_id}")
        return project_id
    
    def get_project(self, project_id: str) -> Optional[ProjectConfig]:
        """Get project configuration by ID."""
        return self.projects.get(project_id)
    
    def list_projects(self) -> List[ProjectConfig]:
        """List all configured projects."""
        return list(self.projects.values())
    
    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project configuration."""
        if project_id not in self.projects:
            return False
            
        project = self.projects[project_id]
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.now()
        self._save_project_config(project)
        
        logger.info(f"Updated project {project_id}")
        return True
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and clean up its resources."""
        if project_id not in self.projects:
            return False
        
        # Clean up Redis queues
        self._cleanup_project_queues(project_id)
        
        # Remove from memory
        del self.projects[project_id]
        if project_id in self.metrics:
            del self.metrics[project_id]
        
        # Remove config file
        config_path = self._get_project_config_path(project_id)
        if config_path.exists():
            config_path.unlink()
        
        logger.info(f"Deleted project {project_id}")
        return True
    
    def get_project_queue_name(self, project_id: str, queue_type: str = "default") -> str:
        """Get the Redis queue name for a project."""
        return f"knocodex:project:{project_id}:{queue_type}"
    
    def get_project_metrics(self, project_id: str) -> Optional[ProjectMetrics]:
        """Get project performance metrics."""
        if project_id not in self.metrics:
            return None
        
        # Update real-time metrics
        self._update_project_metrics(project_id)
        return self.metrics[project_id]
    
    def allocate_resources(self, project_id: str) -> Dict[str, int]:
        """Allocate resources for a project based on priority and current load."""
        if project_id not in self.projects:
            return {}
        
        project = self.projects[project_id]
        metrics = self.get_project_metrics(project_id)
        
        # Calculate available slots based on current load
        total_projects = len(self.projects)
        base_allocation = max(1, 10 // total_projects)  # Base allocation per project
        
        # Adjust based on priority and current load
        priority_multiplier = project.queue_priority
        load_factor = 1.0 - (metrics.queue_depth / 100.0) if metrics else 1.0
        
        allocated_workflows = min(
            project.max_concurrent_workflows,
            int(base_allocation * priority_multiplier * load_factor)
        )
        
        allocated_subtasks = min(
            project.max_concurrent_subtasks,
            int(base_allocation * 2 * priority_multiplier * load_factor)
        )
        
        return {
            'max_workflows': allocated_workflows,
            'max_subtasks': allocated_subtasks,
            'queue_priority': project.queue_priority
        }
    
    def can_start_workflow(self, project_id: str) -> bool:
        """Check if a project can start a new workflow."""
        if project_id not in self.projects:
            return False
        
        metrics = self.get_project_metrics(project_id)
        allocation = self.allocate_resources(project_id)
        
        return metrics.active_workflows < allocation['max_workflows']
    
    def register_workflow_start(self, project_id: str, workflow_id: str):
        """Register the start of a new workflow."""
        if project_id in self.metrics:
            self.metrics[project_id].active_workflows += 1
            self.metrics[project_id].last_activity = datetime.now()
        
        # Store workflow-project mapping in Redis
        self.redis.hset(
            "knocodex:workflow_projects",
            workflow_id,
            project_id
        )
    
    def register_workflow_completion(self, project_id: str, workflow_id: str):
        """Register the completion of a workflow."""
        if project_id in self.metrics:
            self.metrics[project_id].active_workflows = max(
                0, self.metrics[project_id].active_workflows - 1
            )
            self.metrics[project_id].total_issues_processed += 1
            self.metrics[project_id].last_activity = datetime.now()
        
        # Remove workflow-project mapping
        self.redis.hdel("knocodex:workflow_projects", workflow_id)
    
    def register_subtask_completion(self, project_id: str, success: bool):
        """Register the completion of a subtask."""
        if project_id not in self.metrics:
            return
        
        if success:
            self.metrics[project_id].total_subtasks_completed += 1
        else:
            self.metrics[project_id].total_subtasks_failed += 1
        
        # Update success rate
        total = (self.metrics[project_id].total_subtasks_completed + 
                self.metrics[project_id].total_subtasks_failed)
        if total > 0:
            self.metrics[project_id].success_rate = (
                self.metrics[project_id].total_subtasks_completed / total * 100
            )
    
    def get_next_project_for_processing(self) -> Optional[str]:
        """Get the next project that should be processed based on priority and load."""
        eligible_projects = []
        
        for project_id, project in self.projects.items():
            if self.can_start_workflow(project_id):
                metrics = self.get_project_metrics(project_id)
                queue_depth = self._get_queue_depth(project_id)
                
                if queue_depth > 0:  # Has pending work
                    score = project.queue_priority * queue_depth
                    eligible_projects.append((project_id, score))
        
        if not eligible_projects:
            return None
        
        # Sort by score (priority * queue depth) descending
        eligible_projects.sort(key=lambda x: x[1], reverse=True)
        return eligible_projects[0][0]
    
    def _generate_project_id(self, name: str, repository_url: str) -> str:
        """Generate a unique project ID."""
        combined = f"{name}:{repository_url}"
        return hashlib.md5(combined.encode()).hexdigest()[:8]
    
    def _setup_project_queues(self, project_id: str):
        """Set up Redis queues for a project."""
        queue_names = [
            self.get_project_queue_name(project_id, "issues"),
            self.get_project_queue_name(project_id, "subtasks"),
            self.get_project_queue_name(project_id, "notifications")
        ]
        
        for queue_name in queue_names:
            # Initialize queue with empty list if it doesn't exist
            if not self.redis.exists(queue_name):
                self.redis.rpush(queue_name, "init")
                self.redis.rpop(queue_name)  # Remove init item
    
    def _cleanup_project_queues(self, project_id: str):
        """Clean up Redis queues for a project."""
        queue_pattern = f"knocodex:project:{project_id}:*"
        for key in self.redis.scan_iter(match=queue_pattern):
            self.redis.delete(key)
    
    def _get_queue_depth(self, project_id: str) -> int:
        """Get the current queue depth for a project."""
        queue_name = self.get_project_queue_name(project_id, "issues")
        return self.redis.llen(queue_name)
    
    def _update_project_metrics(self, project_id: str):
        """Update real-time metrics for a project."""
        if project_id not in self.metrics:
            return
        
        metrics = self.metrics[project_id]
        metrics.queue_depth = self._get_queue_depth(project_id)
        
        # Get active workflows count from Redis
        workflow_pattern = f"knocodex:workflow:*:project:{project_id}"
        active_count = len(list(self.redis.scan_iter(match=workflow_pattern)))
        metrics.active_workflows = active_count
    
    def _save_project_config(self, project: ProjectConfig):
        """Save project configuration to disk."""
        config_path = self._get_project_config_path(project.project_id)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = asdict(project)
        # Convert datetime objects to ISO strings
        for key, value in config_data.items():
            if isinstance(value, datetime):
                config_data[key] = value.isoformat()
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def _load_projects(self):
        """Load project configurations from disk."""
        projects_dir = self._get_projects_dir()
        if not projects_dir.exists():
            return
        
        for config_file in projects_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Convert ISO strings back to datetime objects
                for key in ['created_at', 'updated_at']:
                    if key in config_data and config_data[key]:
                        config_data[key] = datetime.fromisoformat(config_data[key])
                
                project = ProjectConfig(**config_data)
                self.projects[project.project_id] = project
                self.metrics[project.project_id] = ProjectMetrics(
                    project_id=project.project_id
                )
                
            except Exception as e:
                logger.error(f"Failed to load project config {config_file}: {e}")
    
    def _get_projects_dir(self) -> Path:
        """Get the projects configuration directory."""
        return Path(self.config.base_dir) / "projects"
    
    def _get_project_config_path(self, project_id: str) -> Path:
        """Get the path to a project's configuration file."""
        return self._get_projects_dir() / f"{project_id}.json"