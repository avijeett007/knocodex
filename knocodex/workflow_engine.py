"""
Subtask Workflow Engine

This module provides the core orchestration engine for managing subtask-based workflows.
It handles dependency resolution, execution coordination, and branch lifecycle management.
"""

import os
import logging
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis
from rq import Queue

from .models.subtask import Subtask, SubtaskPlan, SubtaskStatus, SubtaskType
from .utils.redis_utils import SubtaskQueueCoordinator, ProjectQueueManager, TaskLock
from .subtask_analyzer import SubtaskAnalyzer
from .project_manager import ProjectManager


@dataclass
class WorkflowConfig:
    """Configuration for workflow engine"""
    max_parallel_subtasks: int = 3
    dependency_timeout_minutes: int = 60
    retry_attempts: int = 2
    branch_cleanup_delay_hours: int = 24


class SubtaskWorkflowEngine:
    """
    Core orchestration engine for subtask-based workflows.
    
    Handles:
    - Dependency resolution and execution order
    - Parallel subtask execution coordination
    - Branch lifecycle management
    - Error handling and retry logic
    - Progress tracking and reporting
    """
    
    def __init__(self, redis_connection=None, config: Optional[WorkflowConfig] = None):
        """Initialize the workflow engine.
        
        Args:
            redis_connection: Redis connection object or URL string
            config: Optional workflow configuration
        """
        # Handle Redis connection
        if redis_connection is None:
            # Default Redis connection
            redis_url = "redis://localhost:6379"
            self.redis = redis.Redis.from_url(redis_url)
        else:
            self.redis = redis_connection
        
        # Initialize configuration
        self.config = config or WorkflowConfig()
        
        # Create Redis URL for components that expect it
        redis_url = "redis://localhost:6379"
        
        # Initialize components
        self.coordinator = SubtaskQueueCoordinator(redis_url)
        self.queue_manager = ProjectQueueManager(redis_url)
        
        # Create a minimal Config object for ProjectManager
        from .config import Config
        config_obj = Config(os.getcwd())
        self.project_manager = ProjectManager(config_obj, self.redis)
        
        self.analyzer = SubtaskAnalyzer()
        self.logger = logging.getLogger(__name__)
        
    def process_github_issue(self, project_id: str, issue_data: Dict) -> str:
        """
        Process a GitHub issue by breaking it into subtasks and orchestrating execution.
        Uses project-specific locking to ensure sequential processing.
        
        Args:
            project_id: Unique identifier for the project
            issue_data: GitHub issue data containing title, body, labels, etc.
            
        Returns:
            task_id: Unique identifier for the generated subtask plan
        """
        self.logger.info(f"Processing GitHub issue for project {project_id}: {issue_data.get('title', 'Unknown')}")
        
        # Acquire project lock to ensure sequential processing
        project_lock = self.queue_manager.get_project_lock(project_id)
        
        if not project_lock.acquire():
            self.logger.warning(f"Could not acquire lock for project {project_id}. Another task is already in progress.")
            raise RuntimeError(f"Project {project_id} is currently processing another task. Please wait.")
        
        try:
            # Ensure project exists and allocate resources
            if not self.project_manager.get_project(project_id):
                self.logger.warning(f"Project {project_id} not found, creating default project")
                self.project_manager.create_project(
                    name=project_id,
                    repository_url=issue_data.get('repository_url', ''),
                    local_path=os.getcwd(),
                    github_token=os.environ.get('GITHUB_TOKEN', ''),
                    labels=['knocodex']
                )
            
            # Allocate resources for this project
            resources = self.project_manager.allocate_resources(project_id)
            self.logger.info(f"Allocated resources for project {project_id}: {resources}")
            
            # Generate subtask plan
            subtask_plan = self.analyzer.analyze_issue(issue_data)
            subtask_plan.project_id = project_id
            
            # Store the plan
            task_id = self.coordinator.store_subtask_plan(subtask_plan.id, {
                'id': subtask_plan.id,
                'project_id': project_id,
                'issue_data': issue_data,
                'subtasks': [subtask.__dict__ for subtask in subtask_plan.subtasks],
                'branch_name': subtask_plan.branch_name,
                'created_at': datetime.now().isoformat(),
                'status': 'in_progress',
                'pr_required': True,
                'pr_created': False
            })
            
            # Initialize all subtasks in Redis
            for subtask in subtask_plan.subtasks:
                subtask.task_id = task_id
                subtask.project_id = project_id
                self.coordinator.update_subtask_status(task_id, subtask.id, SubtaskStatus.PENDING.value)
            
            # Start workflow execution
            self._execute_workflow_with_lock(task_id, project_id, project_lock)
            
            return task_id
            
        except Exception as e:
            # Release lock on any error
            project_lock.release()
            self.logger.error(f"Error processing GitHub issue for project {project_id}: {e}")
            raise
    
    def _execute_workflow_with_lock(self, task_id: str, project_id: str, project_lock: TaskLock) -> None:
        """Execute workflow for a given task ID with project lock management"""
        self.logger.info(f"Starting workflow execution for task {task_id}")
        
        try:
            # Get ready subtasks and enqueue them with project-specific queue
            ready_subtasks = self.coordinator.get_ready_subtasks(task_id)
            
            if ready_subtasks:
                enqueued_count = self.coordinator.enqueue_ready_subtasks(task_id, project_id)
                self.logger.info(f"Enqueued {enqueued_count} ready subtasks for task {task_id}")
            else:
                self.logger.info(f"No ready subtasks found for task {task_id}")
                
        except Exception as e:
            self.logger.error(f"Error executing workflow {task_id}: {e}")
            project_lock.release()
            raise
    
    def _execute_workflow(self, task_id: str, project_id: Optional[str] = None) -> None:
        """Execute workflow for a given task ID (legacy method)"""
        self.logger.info(f"Starting workflow execution for task {task_id}")
        
        # Get ready subtasks and enqueue them
        ready_subtasks = self.coordinator.get_ready_subtasks(task_id)
        
        if ready_subtasks:
            # Use project-specific queue if project_id is provided
            if project_id:
                enqueued_count = self.coordinator.enqueue_ready_subtasks(task_id, project_id)
            else:
                # Fallback to default queue
                enqueued_count = len(ready_subtasks)  # Placeholder
            self.logger.info(f"Enqueued {enqueued_count} ready subtasks for task {task_id}")
        else:
            self.logger.info(f"No ready subtasks found for task {task_id}")
    
    def handle_subtask_completion(self, task_id: str, subtask_id: str, success: bool, result: Optional[Dict] = None) -> None:
        """
        Handle completion of a subtask and trigger next steps.
        
        Args:
            task_id: The parent task ID
            subtask_id: The completed subtask ID
            success: Whether the subtask completed successfully
            result: Optional result data from subtask execution
        """
        self.logger.info(f"Handling subtask completion: {task_id}/{subtask_id}, success={success}")
        
        # Update subtask status
        if success:
            self.coordinator.update_subtask_status(task_id, subtask_id, SubtaskStatus.COMPLETED)
            if result:
                self.coordinator.store_subtask_result(task_id, subtask_id, result)
        else:
            self.coordinator.update_subtask_status(task_id, subtask_id, SubtaskStatus.FAILED)
        
        # Check if this completion unblocks other subtasks
        self._check_and_enqueue_unblocked_subtasks(task_id)
        
        # Check if entire workflow is complete
        if self._is_workflow_complete(task_id):
            self._handle_workflow_completion(task_id)
    
    def _check_and_enqueue_unblocked_subtasks(self, task_id: str) -> None:
        """Check for newly ready subtasks and enqueue them"""
        ready_subtasks = self.coordinator.get_ready_subtasks(task_id)
        
        if ready_subtasks:
            self.coordinator.enqueue_ready_subtasks(task_id, ready_subtasks)
            self.logger.info(f"Enqueued {len(ready_subtasks)} newly ready subtasks for task {task_id}")
    
    def _is_workflow_complete(self, task_id: str) -> bool:
        """Check if all subtasks in workflow are complete"""
        subtask_plan = self.coordinator.get_subtask_plan(task_id)
        if not subtask_plan:
            return False
        
        for subtask in subtask_plan.subtasks:
            status_key = f"subtask_status:{task_id}:{subtask.id}"
            status = self.redis.get(status_key)
            if not status or status.decode() not in [SubtaskStatus.COMPLETED.value, SubtaskStatus.SKIPPED.value]:
                return False
        
        return True
    
    def _handle_workflow_completion(self, task_id: str) -> None:
        """Handle completion of entire workflow and ensure PR creation"""
        self.logger.info(f"Workflow {task_id} completed")
        
        plan_data = self.coordinator.get_subtask_plan(task_id)
        if not plan_data:
            return
        
        project_id = plan_data.get('project_id')
        if not project_id:
            self.logger.error(f"No project_id found for task {task_id}")
            return
        
        # Check if all subtasks succeeded
        all_successful = self.coordinator.is_plan_complete(task_id)
        
        if all_successful and plan_data.get('pr_required', True):
            # Create PR and update plan status
            pr_created = self._create_pull_request(task_id)
            if pr_created:
                # Update plan to mark PR as created
                plan_data['pr_created'] = True
                plan_data['status'] = 'completed'
                self.coordinator.store_subtask_plan(task_id, plan_data)
                
                # Release project lock after successful PR creation
                project_lock = self.queue_manager.get_project_lock(project_id)
                project_lock.release()
                self.logger.info(f"Released project lock for {project_id} after successful completion")
            else:
                self.logger.error(f"Failed to create PR for task {task_id}. Lock retained.")
        else:
            if not all_successful:
                self.logger.warning(f"Workflow {task_id} completed with failures")
                plan_data['status'] = 'failed'
                self.coordinator.store_subtask_plan(task_id, plan_data)
            
            # Release lock even on failure
            if project_id:
                project_lock = self.queue_manager.get_project_lock(project_id)
                project_lock.release()
                self.logger.info(f"Released project lock for {project_id} after workflow completion")
    
    def _create_pull_request(self, task_id: str) -> bool:
        """Create pull request for completed workflow"""
        plan_data = self.coordinator.get_subtask_plan(task_id)
        if not plan_data:
            self.logger.error(f"No plan data found for task {task_id}")
            return False
        
        try:
            # TODO: Implement actual PR creation using GitHub API
            # This would integrate with GitHub API to create a real PR
            self.logger.info(f"Creating pull request for workflow {task_id}")
            
            # Simulate PR creation for now
            # In real implementation, this would:
            # 1. Push branch to remote repository
            # 2. Create PR via GitHub API
            # 3. Set appropriate title, description, labels
            # 4. Return True if successful, False otherwise
            
            branch_name = plan_data.get('branch_name', f"knocodex-task-{task_id}")
            issue_data = plan_data.get('issue_data', {})
            
            pr_title = f"Fix: {issue_data.get('title', 'Automated task completion')}"
            pr_body = f"""
Automated implementation for GitHub issue.

**Original Issue:** {issue_data.get('title', 'Unknown')}

**Task ID:** {task_id}
**Branch:** {branch_name}

This PR was automatically generated by Knocodex workflow engine.
"""
            
            # Mark workflow as PR created
            workflow_status_key = f"workflow_status:{task_id}"
            self.redis.set(workflow_status_key, "pr_created")
            
            self.logger.info(f"Successfully created PR for workflow {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create PR for workflow {task_id}: {e}")
            return False
    
    def get_workflow_status(self, task_id: str) -> Dict:
        """Get current status of workflow"""
        subtask_plan = self.coordinator.get_subtask_plan(task_id)
        if not subtask_plan:
            return {"error": "Workflow not found"}
        
        status_summary = {
            "task_id": task_id,
            "project_id": subtask_plan.project_id,
            "branch_name": subtask_plan.branch_name,
            "total_subtasks": len(subtask_plan.subtasks),
            "subtasks": {}
        }
        
        completed = 0
        failed = 0
        in_progress = 0
        pending = 0
        
        for subtask in subtask_plan.subtasks:
            status_key = f"subtask_status:{task_id}:{subtask.id}"
            status_raw = self.redis.get(status_key)
            status = status_raw.decode() if status_raw else SubtaskStatus.PENDING.value
            
            status_summary["subtasks"][subtask.id] = {
                "title": subtask.title,
                "type": subtask.type.value,
                "status": status,
                "dependencies": subtask.dependencies
            }
            
            if status == SubtaskStatus.COMPLETED.value:
                completed += 1
            elif status == SubtaskStatus.FAILED.value:
                failed += 1
            elif status == SubtaskStatus.IN_PROGRESS.value:
                in_progress += 1
            else:
                pending += 1
        
        status_summary.update({
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "progress_percentage": (completed / len(subtask_plan.subtasks)) * 100
        })
        
        return status_summary
    
    def retry_failed_subtask(self, task_id: str, subtask_id: str) -> bool:
        """Retry a failed subtask"""
        self.logger.info(f"Retrying failed subtask: {task_id}/{subtask_id}")
        
        # Check current status
        status_key = f"subtask_status:{task_id}:{subtask_id}"
        current_status = self.redis.get(status_key)
        
        if not current_status or current_status.decode() != SubtaskStatus.FAILED.value:
            self.logger.warning(f"Cannot retry subtask {subtask_id} - not in failed state")
            return False
        
        # Reset status to pending
        self.coordinator.update_subtask_status(task_id, subtask_id, SubtaskStatus.PENDING)
        
        # Check if it can be enqueued immediately
        self._check_and_enqueue_unblocked_subtasks(task_id)
        
        return True
    
    def cancel_workflow(self, task_id: str) -> bool:
        """Cancel an active workflow"""
        self.logger.info(f"Cancelling workflow {task_id}")
        
        subtask_plan = self.coordinator.get_subtask_plan(task_id)
        if not subtask_plan:
            return False
        
        # Mark all pending/in-progress subtasks as cancelled
        for subtask in subtask_plan.subtasks:
            status_key = f"subtask_status:{task_id}:{subtask.id}"
            current_status = self.redis.get(status_key)
            
            if current_status:
                status = current_status.decode()
                if status in [SubtaskStatus.PENDING.value, SubtaskStatus.IN_PROGRESS.value]:
                    self.coordinator.update_subtask_status(task_id, subtask_id, SubtaskStatus.CANCELLED)
        
        # Mark workflow as cancelled
        workflow_status_key = f"workflow_status:{task_id}"
        self.redis.set(workflow_status_key, "cancelled")
        
        return True
    
    def cleanup_completed_workflows(self, older_than_hours: int = 168) -> int:
        """Clean up completed workflows older than specified hours (default: 1 week)"""
        # TODO: Implement cleanup logic
        # This would remove old workflow data from Redis
        self.logger.info(f"Cleaning up workflows older than {older_than_hours} hours")
        return 0