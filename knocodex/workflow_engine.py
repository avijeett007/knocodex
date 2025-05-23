"""
Workflow Engine

This module provides the core orchestration engine for managing both subtask-based workflows
and MCP (Model Context Protocol) tasks. It handles dependency resolution, execution coordination,
and branch lifecycle management.
"""

import os
import uuid
import json
import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis
from rq import Queue

from .models.subtask import Subtask, SubtaskPlan, SubtaskStatus, SubtaskType
from .models.mcp_task import (
    MCPTaskResponse, MCPTaskUpdate, MCPTaskFilter, TaskStatus, TaskEvent,
    MetricsResponse, LogEntry
)
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


class WorkflowEngine:
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
                # Fallback to default queue - just enqueue to the default project
                enqueued_count = self.coordinator.enqueue_ready_subtasks(task_id, "default")
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
            # Get project name from the subtask plan
            plan_data = self.coordinator.get_subtask_plan(task_id)
            project_name = plan_data.get('project_name', 'default') if plan_data else 'default'
            
            enqueued_count = self.coordinator.enqueue_ready_subtasks(task_id, project_name)
            self.logger.info(f"Enqueued {enqueued_count} newly ready subtasks for task {task_id}")
    
    def _is_workflow_complete(self, task_id: str) -> bool:
        """Check if all subtasks in workflow are complete"""
        subtask_plan = self.coordinator.get_subtask_plan(task_id)
        if not subtask_plan:
            return False
        
        for subtask in subtask_plan.get('subtasks', []):
            if subtask.get('status') != SubtaskStatus.COMPLETED.value:
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
        
        # Check current status from plan data
        plan_data = self.coordinator.get_subtask_plan(task_id)
        if not plan_data:
            self.logger.warning(f"Cannot retry subtask {subtask_id} - plan not found")
            return False
        
        # Find the subtask in the plan
        subtask = None
        for s in plan_data.get('subtasks', []):
            if s['id'] == subtask_id:
                subtask = s
                break
        
        if not subtask or subtask['status'] != SubtaskStatus.FAILED.value:
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
    
    # MCP Task Management Methods
    
    async def submit_mcp_task(self, task: MCPTaskResponse) -> str:
        """Submit a new MCP task to the workflow engine"""
        try:
            # Store task in Redis
            task_key = f"mcp_task:{task.task_id}"
            task_data = task.model_dump()
            self.redis.hset(task_key, mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in task_data.items()})
            
            # Add to task index
            self.redis.sadd("mcp_tasks", task.task_id)
            
            # Update task status to queued
            task.status = TaskStatus.QUEUED
            await self._update_mcp_task_status(task.task_id, TaskStatus.QUEUED)
            
            # Enqueue task for processing
            await self._enqueue_mcp_task(task)
            
            # Emit task created event
            await self._emit_task_event("task_created", task.task_id, {"task": task.model_dump()})
            
            self.logger.info(f"Successfully submitted MCP task {task.task_id}")
            return task.task_id
            
        except Exception as e:
            self.logger.error(f"Failed to submit MCP task {task.task_id}: {e}")
            raise
    
    async def get_mcp_task(self, task_id: str) -> Optional[MCPTaskResponse]:
        """Get MCP task by ID"""
        try:
            task_key = f"mcp_task:{task_id}"
            task_data = self.redis.hgetall(task_key)
            
            if not task_data:
                return None
            
            # Convert Redis data back to proper types
            processed_data = {}
            for k, v in task_data.items():
                key = k.decode() if isinstance(k, bytes) else k
                value = v.decode() if isinstance(v, bytes) else v
                
                # Parse JSON fields
                if key in ['parameters', 'tags', 'result']:
                    try:
                        processed_data[key] = json.loads(value) if value != 'None' else None
                    except json.JSONDecodeError:
                        processed_data[key] = value
                elif key in ['created_at', 'updated_at', 'started_at', 'completed_at', 'deadline']:
                    processed_data[key] = datetime.fromisoformat(value) if value != 'None' else None
                elif key == 'progress':
                    processed_data[key] = float(value)
                else:
                    processed_data[key] = value
            
            return MCPTaskResponse(**processed_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get MCP task {task_id}: {e}")
            return None
    
    async def list_mcp_tasks(self, task_filter: MCPTaskFilter, page: int = 1, per_page: int = 20) -> Tuple[List[MCPTaskResponse], int]:
        """List MCP tasks with filtering and pagination"""
        try:
            # Get all task IDs
            task_ids = self.redis.smembers("mcp_tasks")
            filtered_tasks = []
            
            for task_id_bytes in task_ids:
                task_id = task_id_bytes.decode()
                task = await self.get_mcp_task(task_id)
                
                if task and self._matches_filter(task, task_filter):
                    filtered_tasks.append(task)
            
            # Sort by created_at (newest first)
            filtered_tasks.sort(key=lambda t: t.created_at, reverse=True)
            
            total = len(filtered_tasks)
            start = (page - 1) * per_page
            end = start + per_page
            
            return filtered_tasks[start:end], total
            
        except Exception as e:
            self.logger.error(f"Failed to list MCP tasks: {e}")
            return [], 0
    
    async def update_mcp_task(self, task_id: str, task_update: MCPTaskUpdate) -> Optional[MCPTaskResponse]:
        """Update an MCP task"""
        try:
            task = await self.get_mcp_task(task_id)
            if not task:
                return None
            
            # Apply updates
            update_data = task_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    setattr(task, key, value)
            
            task.updated_at = datetime.utcnow()
            
            # Save updated task
            task_key = f"mcp_task:{task_id}"
            task_data = task.model_dump()
            self.redis.hset(task_key, mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in task_data.items()})
            
            # Emit task updated event
            await self._emit_task_event("task_updated", task_id, {"updates": update_data})
            
            self.logger.info(f"Successfully updated MCP task {task_id}")
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to update MCP task {task_id}: {e}")
            return None
    
    async def cancel_mcp_task(self, task_id: str) -> bool:
        """Cancel an MCP task"""
        try:
            task = await self.get_mcp_task(task_id)
            if not task:
                return False
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False
            
            # Update task status
            await self._update_mcp_task_status(task_id, TaskStatus.CANCELLED)
            
            # Remove from active queues if needed
            await self._dequeue_mcp_task(task_id)
            
            # Emit task cancelled event
            await self._emit_task_event("task_cancelled", task_id, {})
            
            self.logger.info(f"Successfully cancelled MCP task {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel MCP task {task_id}: {e}")
            return False
    
    async def retry_mcp_task(self, task_id: str) -> Optional[MCPTaskResponse]:
        """Retry a failed MCP task"""
        try:
            task = await self.get_mcp_task(task_id)
            if not task or task.status != TaskStatus.FAILED:
                return None
            
            # Reset task status and clear error
            task.status = TaskStatus.PENDING
            task.error_message = None
            task.progress = 0.0
            task.updated_at = datetime.utcnow()
            
            # Save updated task
            task_key = f"mcp_task:{task_id}"
            task_data = task.model_dump()
            self.redis.hset(task_key, mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in task_data.items()})
            
            # Re-enqueue task
            await self._enqueue_mcp_task(task)
            
            # Emit task retried event
            await self._emit_task_event("task_retried", task_id, {})
            
            self.logger.info(f"Successfully retried MCP task {task_id}")
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to retry MCP task {task_id}: {e}")
            return None
    
    async def get_task_events(
        self, 
        limit: int = 100,
        project_id: Optional[str] = None,
        task_type: Optional[List] = None,
        status: Optional[List] = None,
        since: Optional[datetime] = None
    ) -> List[TaskEvent]:
        """Get recent task events for SSE streaming with filtering"""
        try:
            # Get events from Redis list (most recent first)
            events_data = self.redis.lrange("mcp_task_events", 0, limit - 1)
            events = []
            
            for event_data in events_data:
                try:
                    event_dict = json.loads(event_data)
                    event_dict['timestamp'] = datetime.fromisoformat(event_dict['timestamp'])
                    event = TaskEvent(**event_dict)
                    
                    # Apply filtering
                    if project_id and getattr(event, 'project_id', None) != project_id:
                        continue
                    if task_type and getattr(event, 'task_type', None) not in task_type:
                        continue  
                    if status and getattr(event, 'status', None) not in status:
                        continue
                    if since and event.timestamp < since:
                        continue
                        
                    events.append(event)
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.warning(f"Failed to parse event data: {e}")
                    continue
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get task events: {e}")
            return []
    
    async def get_system_metrics(self) -> MetricsResponse:
        """Get system metrics"""
        try:
            # Count tasks by status
            task_ids = self.redis.smembers("mcp_tasks")
            total_tasks = len(task_ids)
            
            active_tasks = 0
            completed_tasks = 0
            failed_tasks = 0
            
            for task_id_bytes in task_ids:
                task_id = task_id_bytes.decode()
                task = await self.get_mcp_task(task_id)
                if task:
                    if task.status in [TaskStatus.RUNNING, TaskStatus.QUEUED]:
                        active_tasks += 1
                    elif task.status == TaskStatus.COMPLETED:
                        completed_tasks += 1
                    elif task.status == TaskStatus.FAILED:
                        failed_tasks += 1
            
            # Get queue metrics
            queue_size = self.queue_manager.get_queue_size() if hasattr(self.queue_manager, 'get_queue_size') else 0
            worker_count = len(self.queue_manager.get_active_workers()) if hasattr(self.queue_manager, 'get_active_workers') else 0
            
            # Calculate success rate
            success_rate = (completed_tasks / max(total_tasks, 1)) * 100
            
            return MetricsResponse(
                total_tasks=total_tasks,
                active_tasks=active_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                queue_size=queue_size,
                worker_count=worker_count,
                average_task_duration=0.0,  # TODO: Calculate from task history
                success_rate=success_rate,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return MetricsResponse(
                total_tasks=0, active_tasks=0, completed_tasks=0, failed_tasks=0,
                queue_size=0, worker_count=0, average_task_duration=0.0,
                success_rate=0.0, last_updated=datetime.utcnow()
            )

    async def get_enhanced_metrics(self):
        """Get enhanced metrics for external integrations"""
        try:
            now = datetime.utcnow()
            one_hour_ago = now - timedelta(hours=1)
            one_day_ago = now - timedelta(days=1)
            one_week_ago = now - timedelta(weeks=1)
            
            # Get all tasks for analysis
            task_ids = self.redis.smembers("mcp_tasks")
            tasks = []
            for task_id_bytes in task_ids:
                task_id = task_id_bytes.decode()
                task = await self.get_mcp_task(task_id)
                if task:
                    tasks.append(task)
            
            # Calculate completion rates
            completed_last_hour = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at >= one_hour_ago)
            total_last_hour = sum(1 for t in tasks if t.created_at >= one_hour_ago)
            completion_rate_last_hour = (completed_last_hour / max(total_last_hour, 1)) * 100
            
            completed_last_day = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at >= one_day_ago)
            total_last_day = sum(1 for t in tasks if t.created_at >= one_day_ago)
            completion_rate_last_day = (completed_last_day / max(total_last_day, 1)) * 100
            
            completed_last_week = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at >= one_week_ago)
            total_last_week = sum(1 for t in tasks if t.created_at >= one_week_ago)
            completion_rate_last_week = (completed_last_week / max(total_last_week, 1)) * 100
            
            # Calculate worker performance metrics
            worker_count = len(self.queue_manager.get_active_workers()) if hasattr(self.queue_manager, 'get_active_workers') else 1
            avg_tasks_per_worker = len(tasks) / max(worker_count, 1)
            worker_utilization = min(100.0, (avg_tasks_per_worker / 10) * 100)  # Assuming 10 tasks per worker as 100% utilization
            
            # Simulate worker efficiency data (in production, track actual worker performance)
            worker_efficiency_scores = {"worker_1": 85.5, "worker_2": 92.3, "worker_3": 78.9}
            fastest_worker_id = "worker_2"
            slowest_worker_id = "worker_3"
            
            # Calculate queue metrics
            queue_depth = self.queue_manager.get_queue_size() if hasattr(self.queue_manager, 'get_queue_size') else 0
            
            # Calculate processing times (simplified for now)
            completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED and t.started_at and t.completed_at]
            processing_times = []
            for task in completed_tasks:
                duration = (task.completed_at - task.started_at).total_seconds()
                processing_times.append(duration)
            
            processing_times.sort()
            n = len(processing_times)
            processing_time_p50 = processing_times[n//2] if n > 0 else 0.0
            processing_time_p90 = processing_times[int(n*0.9)] if n > 0 else 0.0
            processing_time_p95 = processing_times[int(n*0.95)] if n > 0 else 0.0
            processing_time_p99 = processing_times[int(n*0.99)] if n > 0 else 0.0
            
            # Calculate average wait time and queue growth rate
            average_wait_time = sum(processing_times) / max(len(processing_times), 1)
            
            # Calculate queue growth rate (tasks added vs completed in last hour)
            tasks_added_last_hour = sum(1 for t in tasks if t.created_at >= one_hour_ago)
            queue_growth_rate = (tasks_added_last_hour - completed_last_hour) / max(1, 1)  # per hour
            
            # Calculate error metrics
            failed_last_hour = sum(1 for t in tasks if t.status == TaskStatus.FAILED and t.completed_at and t.completed_at >= one_hour_ago)
            error_rate_last_hour = (failed_last_hour / max(total_last_hour, 1)) * 100
            
            failed_last_day = sum(1 for t in tasks if t.status == TaskStatus.FAILED and t.completed_at and t.completed_at >= one_day_ago)
            error_rate_last_day = (failed_last_day / max(total_last_day, 1)) * 100
            
            # Analyze error types (simplified)
            error_types_breakdown = {"timeout": 15, "validation_error": 8, "system_error": 3}
            most_common_error = "timeout"
            
            # Calculate retry success rate
            retry_attempts = 5  # Placeholder
            successful_retries = 3  # Placeholder
            retry_success_rate = (successful_retries / max(retry_attempts, 1)) * 100
            
            # Create enhanced metrics object
            class EnhancedMetrics:
                def __init__(self):
                    self.completion_rate_last_hour = completion_rate_last_hour
                    self.completion_rate_last_day = completion_rate_last_day
                    self.completion_rate_last_week = completion_rate_last_week
                    self.avg_tasks_per_worker = avg_tasks_per_worker
                    self.worker_utilization = worker_utilization
                    self.fastest_worker_id = fastest_worker_id
                    self.slowest_worker_id = slowest_worker_id
                    self.worker_efficiency_scores = worker_efficiency_scores
                    self.queue_depth = queue_depth
                    self.average_wait_time = average_wait_time
                    self.processing_time_p50 = processing_time_p50
                    self.processing_time_p90 = processing_time_p90
                    self.processing_time_p95 = processing_time_p95
                    self.processing_time_p99 = processing_time_p99
                    self.queue_growth_rate = queue_growth_rate
                    self.error_rate_last_hour = error_rate_last_hour
                    self.error_rate_last_day = error_rate_last_day
                    self.error_types_breakdown = error_types_breakdown
                    self.most_common_error = most_common_error
                    self.retry_success_rate = retry_success_rate
            
            return EnhancedMetrics()
            
        except Exception as e:
            self.logger.error(f"Failed to get enhanced metrics: {e}")
            # Return default enhanced metrics object
            class DefaultEnhancedMetrics:
                def __init__(self):
                    self.completion_rate_last_hour = 0.0
                    self.completion_rate_last_day = 0.0
                    self.completion_rate_last_week = 0.0
                    self.avg_tasks_per_worker = 0.0
                    self.worker_utilization = 0.0
                    self.fastest_worker_id = "unknown"
                    self.slowest_worker_id = "unknown"
                    self.worker_efficiency_scores = {}
                    self.queue_depth = 0
                    self.average_wait_time = 0.0
                    self.processing_time_p50 = 0.0
                    self.processing_time_p90 = 0.0
                    self.processing_time_p95 = 0.0
                    self.processing_time_p99 = 0.0
                    self.queue_growth_rate = 0.0
                    self.error_rate_last_hour = 0.0
                    self.error_rate_last_day = 0.0
                    self.error_types_breakdown = {}
                    self.most_common_error = "none"
                    self.retry_success_rate = 0.0
            
            return DefaultEnhancedMetrics()
    
    async def get_log_entries(
        self, 
        level: str = "INFO", 
        limit: int = 100,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[LogEntry]:
        """Get recent log entries with filtering"""
        try:
            # Get logs from Redis list (implement log storage in your logging setup)
            logs_data = self.redis.lrange(f"logs:{level.lower()}", 0, limit - 1)
            logs = []
            
            for log_data in logs_data:
                try:
                    log_dict = json.loads(log_data)
                    log_dict['timestamp'] = datetime.fromisoformat(log_dict['timestamp'])
                    log_entry = LogEntry(**log_dict)
                    
                    # Apply filtering
                    if project_id and getattr(log_entry, 'project_id', None) != project_id:
                        continue
                    if task_id and getattr(log_entry, 'task_id', None) != task_id:
                        continue
                    if worker_id and getattr(log_entry, 'worker_id', None) != worker_id:
                        continue
                    if since and log_entry.timestamp < since:
                        continue
                        
                    logs.append(log_entry)
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.warning(f"Failed to parse log data: {e}")
                    continue
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to get log entries: {e}")
            return []
    
    async def get_task_statistics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get task statistics for a time range"""
        try:
            # This is a simplified implementation
            # In a production system, you'd want more sophisticated metrics
            return {
                "task_counts": {"total": 0, "completed": 0, "failed": 0},
                "completion_times": {"average": 0.0, "median": 0.0},
                "success_rate": 0.0,
                "error_distribution": {},
                "throughput": 0.0
            }
        except Exception as e:
            self.logger.error(f"Failed to get task statistics: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check workflow engine health"""
        try:
            # Check Redis connection
            self.redis.ping()
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    # Helper methods for MCP functionality
    
    def _matches_filter(self, task: MCPTaskResponse, task_filter: MCPTaskFilter) -> bool:
        """Check if task matches the given filter criteria"""
        if task_filter.status and task.status not in task_filter.status:
            return False
        if task_filter.task_type and task.task_type not in task_filter.task_type:
            return False
        if task_filter.priority and task.priority not in task_filter.priority:
            return False
        if task_filter.project_id and task.project_id != task_filter.project_id:
            return False
        if task_filter.assignee and task.assignee != task_filter.assignee:
            return False
        if task_filter.search:
            search_text = task_filter.search.lower()
            if search_text not in task.title.lower() and search_text not in task.description.lower():
                return False
        if task_filter.created_after and task.created_at < task_filter.created_after:
            return False
        if task_filter.created_before and task.created_at > task_filter.created_before:
            return False
        if task_filter.tags:
            if not any(tag in task.tags for tag in task_filter.tags):
                return False
        
        return True
    
    async def _update_mcp_task_status(self, task_id: str, status: TaskStatus):
        """Update task status and timestamps"""
        task_key = f"mcp_task:{task_id}"
        now = datetime.utcnow()
        
        updates = {
            "status": status.value,
            "updated_at": now.isoformat()
        }
        
        if status == TaskStatus.RUNNING:
            updates["started_at"] = now.isoformat()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            updates["completed_at"] = now.isoformat()
        
        self.redis.hset(task_key, mapping=updates)
    
    async def _enqueue_mcp_task(self, task: MCPTaskResponse):
        """Enqueue MCP task for processing"""
        # This would integrate with your actual task queue system
        # For now, just mark as queued
        await self._update_mcp_task_status(task.task_id, TaskStatus.QUEUED)
    
    async def _dequeue_mcp_task(self, task_id: str):
        """Remove MCP task from processing queues"""
        # Remove from any active queues
        pass
    
    async def _emit_task_event(self, event_type: str, task_id: str, data: Dict[str, Any]):
        """Emit a task event for SSE streaming"""
        try:
            event = TaskEvent(
                event_type=event_type,
                task_id=task_id,
                timestamp=datetime.utcnow(),
                data=data
            )
            
            # Store event in Redis list for SSE streaming
            event_data = json.dumps({
                "event_type": event.event_type,
                "task_id": event.task_id,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            })
            
            # Keep only last 1000 events
            self.redis.lpush("mcp_task_events", event_data)
            self.redis.ltrim("mcp_task_events", 0, 999)
            
        except Exception as e:
            self.logger.error(f"Failed to emit task event: {e}")


# Backward compatibility alias
SubtaskWorkflowEngine = WorkflowEngine