#!/usr/bin/env python3
"""
Redis utilities for Knocodex
"""

import os
import subprocess
import logging
import time
import platform
import json
from typing import Dict, List, Optional, Any
from redis import Redis
from rq import Queue

logger = logging.getLogger("knocodex.utils.redis_utils")

def check_redis_running():
    """Check if Redis server is running"""
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and "PONG" in result.stdout
    except Exception as e:
        logger.error(f"Failed to check Redis server: {e}")
        return False

def start_redis():
    """Start Redis server"""
    if check_redis_running():
        logger.info("Redis server is already running")
        return True
    
    try:
        if platform.system() == "Darwin":
            subprocess.run(
                ["brew", "services", "start", "redis"],
                check=True,
            )
            logger.info("Redis server started successfully")
            return True
        else:
            logger.error("Automatic starting of Redis is only supported on macOS")
            logger.info("Please start Redis manually")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Redis server: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to start Redis server: {e}")
        return False

def stop_redis():
    """Stop Redis server"""
    if not check_redis_running():
        logger.info("Redis server is not running")
        return True
    
    try:
        if platform.system() == "Darwin":
            subprocess.run(
                ["brew", "services", "stop", "redis"],
                check=True,
            )
            logger.info("Redis server stopped successfully")
            return True
        else:
            logger.error("Automatic stopping of Redis is only supported on macOS")
            logger.info("Please stop Redis manually")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to stop Redis server: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to stop Redis server: {e}")
        return False

def get_redis_queue(redis_url="redis://localhost:6379", queue_name="knocodex"):
    """Get a Redis queue"""
    try:
        redis_conn = Redis.from_url(redis_url)
        queue = Queue(queue_name, connection=redis_conn)
        return queue
    except Exception as e:
        logger.error(f"Failed to get Redis queue: {e}")
        return None

def enqueue_task(queue, func, *args, **kwargs):
    """Enqueue a task in the Redis queue"""
    try:
        job = queue.enqueue(
            func,
            *args,
            **kwargs,
            job_timeout="2h",  # Long timeout for complex tasks
            result_ttl=86400,  # Keep results for 24 hours
            ttl=86400,         # Job can wait in queue for up to 24 hours
        )
        logger.info(f"Enqueued job with ID: {job.id}")
        return job.id
    except Exception as e:
        logger.error(f"Failed to enqueue task: {e}")
        return None


class ProjectQueueManager:
    """
    Manages project-specific Redis queues for subtask processing.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the queue manager."""
        self.redis_url = redis_url
        self.redis_conn = Redis.from_url(redis_url)
        self._queues = {}
    
    def get_project_queue(self, project_name: str) -> Queue:
        """
        Get or create a project-specific queue.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Redis queue for the project
        """
        queue_name = f"knocodex_{project_name}"
        
        if queue_name not in self._queues:
            self._queues[queue_name] = Queue(queue_name, connection=self.redis_conn)
        
        return self._queues[queue_name]
    
    def enqueue_subtask(self, project_name: str, subtask_data: Dict[str, Any]) -> Optional[str]:
        """
        Enqueue a subtask for processing.
        
        Args:
            project_name: Name of the project
            subtask_data: Subtask data dictionary
            
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            queue = self.get_project_queue(project_name)
            job = queue.enqueue(
                'knocodex.subtask_worker.process_subtask',
                subtask_data,
                job_timeout="2h",
                result_ttl=86400,
                ttl=86400
            )
            logger.info(f"Enqueued subtask {subtask_data.get('id')} for project {project_name} with job ID: {job.id}")
            return job.id
        except Exception as e:
            logger.error(f"Failed to enqueue subtask for project {project_name}: {e}")
            return None
    
    def get_queue_status(self, project_name: str) -> Dict[str, int]:
        """
        Get status of a project queue.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dictionary with queue statistics
        """
        try:
            queue = self.get_project_queue(project_name)
            return {
                'pending': len(queue),
                'failed': len(queue.failed_job_registry),
                'finished': len(queue.finished_job_registry),
                'started': len(queue.started_job_registry),
                'deferred': len(queue.deferred_job_registry),
                'scheduled': len(queue.scheduled_job_registry)
            }
        except Exception as e:
            logger.error(f"Failed to get queue status for project {project_name}: {e}")
            return {}
    
    def clear_project_queue(self, project_name: str) -> bool:
        """
        Clear all jobs from a project queue.
        
        Args:
            project_name: Name of the project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            queue = self.get_project_queue(project_name)
            queue.empty()
            logger.info(f"Cleared queue for project {project_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue for project {project_name}: {e}")
            return False
    
    def get_all_project_queues(self) -> List[str]:
        """
        Get names of all project queues.
        
        Returns:
            List of project queue names
        """
        try:
            # Get all keys matching the pattern
            keys = self.redis_conn.keys("rq:queue:knocodex_*")
            project_names = []
            for key in keys:
                # Extract project name from key
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                if key_str.startswith("rq:queue:knocodex_"):
                    project_name = key_str.replace("rq:queue:knocodex_", "")
                    project_names.append(project_name)
            return project_names
        except Exception as e:
            logger.error(f"Failed to get project queue names: {e}")
            return []


class SubtaskQueueCoordinator:
    """
    Coordinates subtask processing across multiple queues.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the coordinator."""
        self.redis_url = redis_url
        self.redis_conn = Redis.from_url(redis_url)
        self.queue_manager = ProjectQueueManager(redis_url)
    
    def store_subtask_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> bool:
        """
        Store a subtask plan in Redis.
        
        Args:
            plan_id: Unique plan identifier
            plan_data: Plan data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"subtask_plan:{plan_id}"
            self.redis_conn.set(key, json.dumps(plan_data), ex=86400)  # Expire after 24 hours
            logger.info(f"Stored subtask plan {plan_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store subtask plan {plan_id}: {e}")
            return False
    
    def get_subtask_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a subtask plan from Redis.
        
        Args:
            plan_id: Unique plan identifier
            
        Returns:
            Plan data dictionary or None if not found
        """
        try:
            key = f"subtask_plan:{plan_id}"
            data = self.redis_conn.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get subtask plan {plan_id}: {e}")
            return None
    
    def update_subtask_status(self, plan_id: str, subtask_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """
        Update the status of a subtask in the plan.
        
        Args:
            plan_id: Unique plan identifier
            subtask_id: Subtask identifier
            status: New status
            error_message: Optional error message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            plan_data = self.get_subtask_plan(plan_id)
            if not plan_data:
                logger.error(f"Subtask plan {plan_id} not found")
                return False
            
            # Find and update the subtask
            for subtask in plan_data.get('subtasks', []):
                if subtask['id'] == subtask_id:
                    subtask['status'] = status
                    subtask['updated_at'] = time.time()
                    if error_message:
                        subtask['error_message'] = error_message
                    break
            else:
                logger.error(f"Subtask {subtask_id} not found in plan {plan_id}")
                return False
            
            # Store the updated plan
            return self.store_subtask_plan(plan_id, plan_data)
        except Exception as e:
            logger.error(f"Failed to update subtask status: {e}")
            return False
    
    def get_ready_subtasks(self, plan_id: str) -> List[Dict[str, Any]]:
        """
        Get subtasks that are ready to be processed.
        
        Args:
            plan_id: Unique plan identifier
            
        Returns:
            List of ready subtasks
        """
        try:
            plan_data = self.get_subtask_plan(plan_id)
            if not plan_data:
                return []
            
            subtasks = plan_data.get('subtasks', [])
            completed_ids = {s['id'] for s in subtasks if s['status'] == 'completed'}
            ready_subtasks = []
            
            for subtask in subtasks:
                if subtask['status'] == 'pending':
                    # Check if all dependencies are completed
                    dependencies = subtask.get('dependencies', [])
                    if all(dep_id in completed_ids for dep_id in dependencies):
                        ready_subtasks.append(subtask)
            
            return ready_subtasks
        except Exception as e:
            logger.error(f"Failed to get ready subtasks for plan {plan_id}: {e}")
            return []
    
    def enqueue_ready_subtasks(self, plan_id: str, project_name: str) -> int:
        """
        Enqueue all ready subtasks for processing.
        
        Args:
            plan_id: Unique plan identifier
            project_name: Name of the project
            
        Returns:
            Number of tasks enqueued
        """
        try:
            ready_subtasks = self.get_ready_subtasks(plan_id)
            enqueued_count = 0
            
            for subtask in ready_subtasks:
                # Add plan_id to subtask context for tracking
                subtask['plan_id'] = plan_id
                subtask['project_name'] = project_name
                
                job_id = self.queue_manager.enqueue_subtask(project_name, subtask)
                if job_id:
                    # Update subtask status to in_progress
                    self.update_subtask_status(plan_id, subtask['id'], 'in_progress')
                    enqueued_count += 1
            
            logger.info(f"Enqueued {enqueued_count} ready subtasks for plan {plan_id}")
            return enqueued_count
        except Exception as e:
            logger.error(f"Failed to enqueue ready subtasks for plan {plan_id}: {e}")
            return 0
    
    def is_plan_complete(self, plan_id: str) -> bool:
        """
        Check if all subtasks in a plan are complete.
        
        Args:
            plan_id: Unique plan identifier
            
        Returns:
            True if all subtasks are complete, False otherwise
        """
        try:
            plan_data = self.get_subtask_plan(plan_id)
            if not plan_data:
                return False
            
            subtasks = plan_data.get('subtasks', [])
            return all(s['status'] == 'completed' for s in subtasks)
        except Exception as e:
            logger.error(f"Failed to check if plan {plan_id} is complete: {e}")
            return False
