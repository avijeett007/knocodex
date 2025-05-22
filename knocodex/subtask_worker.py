#!/usr/bin/env python3
"""
Enhanced Worker process for Knocodex with subtask support

This worker handles both legacy single-task processing and new subtask-based workflows.
"""

import os
import sys
import time
import json
import logging
import subprocess
import importlib.util
from typing import Dict, Optional, List
from pathlib import Path
from redis import Redis
from rq import Worker, Queue

# Add knocodex to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knocodex.models.subtask import Subtask, SubtaskPlan, SubtaskStatus, SubtaskType
from knocodex.workflow_engine import SubtaskWorkflowEngine, WorkflowConfig
from knocodex.utils.redis_utils import SubtaskQueueCoordinator, ProjectQueueManager, TaskLock
from knocodex.project_manager import ProjectManager


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.getcwd(), ".knocodex", "logs", "subtask_worker.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("knocodex.subtask_worker")

# Get project path
project_path = os.getcwd()
knocodex_dir = os.path.join(project_path, ".knocodex")

# Redis connection
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_conn = Redis.from_url(redis_url)

# Initialize workflow engine and project manager
from knocodex.config import Config

# Create a workflow config
workflow_config = WorkflowConfig(
    max_parallel_subtasks=int(os.environ.get("MAX_PARALLEL_SUBTASKS", "3")),
    dependency_timeout_minutes=int(os.environ.get("DEPENDENCY_TIMEOUT_MINUTES", "60")),
    retry_attempts=int(os.environ.get("RETRY_ATTEMPTS", "2"))
)

# Create a config object with the current project path
config = Config(project_path)

# Initialize the workflow engine and project manager with proper parameters
workflow_engine = SubtaskWorkflowEngine(redis_conn, workflow_config)
project_manager = ProjectManager(config, redis_conn)


def create_subtask_instruction_file(subtask: Subtask, task_id: str, project_id: str) -> str:
    """Create instruction file for a specific subtask"""
    instructions_dir = os.path.join(knocodex_dir, "instructions")
    os.makedirs(instructions_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    file_name = f"subtask-{task_id}-{subtask.id}-{timestamp}.md"
    file_path = os.path.join(instructions_dir, file_name)
    
    instructions = []
    
    # Add header
    instructions.append(f"# Subtask: {subtask.title}\n")
    instructions.append(f"**Task ID:** {task_id}")
    instructions.append(f"**Project ID:** {project_id}")
    instructions.append(f"**Subtask ID:** {subtask.id}")
    instructions.append(f"**Type:** {subtask.type.value}")
    instructions.append(f"**Priority:** {subtask.priority}\n")
    
    # Add description
    if subtask.description:
        instructions.append(f"## Description\n{subtask.description}\n")
    
    # Add dependencies info
    if subtask.dependencies:
        instructions.append("## Dependencies")
        instructions.append("This subtask depends on the following subtasks being completed:")
        for dep in subtask.dependencies:
            instructions.append(f"- {dep}")
        instructions.append("")
    
    # Add type-specific instructions
    if subtask.type == SubtaskType.ANALYZE:
        instructions.extend([
            "## Instructions",
            "Perform analysis as described. Create detailed documentation of findings.",
            "Save analysis results in a structured format for use by subsequent subtasks.",
            "Focus on understanding the problem space and identifying key requirements."
        ])
    
    elif subtask.type == SubtaskType.IMPLEMENT:
        instructions.extend([
            "## Instructions", 
            "Implement the functionality as described.",
            "Follow existing code patterns and conventions.",
            "Write clean, well-documented code.",
            "Ensure the implementation is testable."
        ])
    
    elif subtask.type == SubtaskType.TEST:
        instructions.extend([
            "## Instructions",
            "Create comprehensive tests for the implemented functionality.",
            "Include unit tests, integration tests as appropriate.",
            "Ensure tests follow existing test patterns.",
            "Run tests to verify they pass."
        ])
    
    elif subtask.type == SubtaskType.REFACTOR:
        instructions.extend([
            "## Instructions",
            "Refactor the code as described while maintaining functionality.",
            "Improve code quality, readability, and maintainability.",
            "Ensure all existing tests continue to pass.",
            "Update documentation if necessary."
        ])
    
    elif subtask.type == SubtaskType.DOCUMENTATION:
        instructions.extend([
            "## Instructions",
            "Create or update documentation as described.",
            "Ensure documentation is clear, comprehensive, and follows project conventions.",
            "Include code examples where appropriate.",
            "Update any related documentation that may be affected."
        ])
    
    elif subtask.type == SubtaskType.REVIEW:
        instructions.extend([
            "## Instructions",
            "Review the specified code, implementation, or documentation.",
            "Provide constructive feedback and suggestions for improvement.",
            "Check for potential issues, bugs, or improvements.",
            "Document review findings clearly."
        ])
    
    else:  # SETUP or unknown
        instructions.extend([
            "## Instructions",
            "Complete the setup or configuration task as described.",
            "Ensure the setup is properly documented.",
            "Verify the setup works as expected."
        ])
    
    # Add context and constraints
    instructions.extend([
        "",
        "## Context",
        f"This subtask is part of a larger workflow (Task ID: {task_id}).",
        "Focus only on the specific requirements of this subtask.",
        "The results of this subtask may be used by other subtasks in the workflow.",
        "",
        "## Success Criteria",
        "- Complete the subtask requirements as described",
        "- Ensure your changes integrate well with the existing codebase", 
        "- Document any important decisions or findings",
        "- Leave the codebase in a clean, working state"
    ])
    
    # Write instructions to file
    with open(file_path, 'w') as f:
        f.write('\n'.join(instructions))
    
    return file_path


def run_claude_code_for_subtask(subtask: Subtask, task_id: str, project_id: str) -> Dict:
    """Run Claude Code for a specific subtask"""
    claude_path = os.environ.get('CLAUDE_CODE_PATH', 'claude')
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(knocodex_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create instruction file for the subtask
    instruction_file = create_subtask_instruction_file(subtask, task_id, project_id)
    
    logger.info(f"Running Claude Code for subtask {subtask.id} of task {task_id}")
    logger.info(f"Instruction file: {instruction_file}")
    
    # Prepare Claude Code command
    file_prompt = f"Read and execute the instructions in this file: {instruction_file}"
    command = [claude_path, '-p', file_prompt, '--dangerously-skip-permissions']
    
    # Execute with retries
    max_retries = workflow_config.retry_attempts
    retries = 0
    
    while retries <= max_retries:
        try:
            logger.info(f"Executing subtask {subtask.id} (attempt {retries + 1}/{max_retries + 1})")
            
            if retries > 0:
                logger.info(f"Retry attempt {retries} of {max_retries}")
            
            # Run Claude Code
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            
            # Success!
            return {
                'success': True,
                'stdout': process.stdout,
                'stderr': process.stderr,
                'subtask_id': subtask.id,
                'task_id': task_id,
                'instruction_file': instruction_file,
                'retries': retries
            }
        
        except subprocess.CalledProcessError as e:
            stderr_output = e.stderr if hasattr(e, 'stderr') else str(e)
            stdout_output = e.stdout if hasattr(e, 'stdout') else ''
            
            logger.error(f"Subtask {subtask.id} execution failed (attempt {retries+1}/{max_retries+1}):")
            logger.error(f"Exit code: {e.returncode}")
            logger.error(f"Error: {stderr_output}")
            
            retries += 1
            
            if retries <= max_retries:
                logger.info(f"Waiting 10 seconds before retry...")
                time.sleep(10)
            else:
                logger.error(f"Max retries reached for subtask {subtask.id}")
                return {
                    'success': False,
                    'stdout': stdout_output,
                    'stderr': stderr_output,
                    'subtask_id': subtask.id,
                    'task_id': task_id,
                    'instruction_file': instruction_file,
                    'retries': retries,
                    'error': 'Max retries exceeded'
                }
        
        except Exception as e:
            logger.error(f"Unexpected error during subtask {subtask.id} execution: {e}")
            
            retries += 1
            
            if retries <= max_retries:
                logger.info(f"Waiting 10 seconds before retry...")
                time.sleep(10)
            else:
                logger.error(f"Max retries reached for subtask {subtask.id}")
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': str(e),
                    'subtask_id': subtask.id,
                    'task_id': task_id,
                    'instruction_file': instruction_file,
                    'retries': retries,
                    'error': 'Unexpected error'
                }


def execute_subtask(subtask_data: Dict) -> Dict:
    """Execute a single subtask with project lock verification"""
    try:
        # Parse subtask data
        task_id = subtask_data['task_id']
        subtask_id = subtask_data['subtask_id']
        project_id = subtask_data.get('project_id', 'default')
        
        logger.info(f"Starting execution of subtask {subtask_id} for task {task_id}")
        
        # Initialize queue manager and check project lock
        queue_manager = ProjectQueueManager(redis_url)
        project_lock = queue_manager.get_project_lock(project_id)
        
        # Verify the lock is held (should be held by the workflow that scheduled this task)
        if not project_lock.is_locked():
            error_msg = f"Project lock not held for {project_id}. Task {task_id} may have been abandoned."
            logger.warning(error_msg)
            # Continue execution but log the warning
        
        # Get subtask details from Redis
        coordinator = SubtaskQueueCoordinator(redis_url)
        subtask_plan = coordinator.get_subtask_plan(task_id)
        
        if not subtask_plan:
            error_msg = f"Subtask plan not found for task {task_id}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Find the specific subtask
        subtask = None
        subtasks = subtask_plan.get('subtasks', [])
        for st_data in subtasks:
            if st_data.get('id') == subtask_id:
                # Convert dict to Subtask object if needed
                if isinstance(st_data, dict):
                    subtask = Subtask(
                        id=st_data['id'],
                        title=st_data.get('title', ''),
                        description=st_data.get('description', ''),
                        type=SubtaskType(st_data.get('type', 'implement')),
                        dependencies=st_data.get('dependencies', []),
                        priority=st_data.get('priority', 'medium')
                    )
                else:
                    subtask = st_data
                break
        
        if not subtask:
            error_msg = f"Subtask {subtask_id} not found in plan for task {task_id}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Mark subtask as in progress
        coordinator.update_subtask_status(task_id, subtask_id, SubtaskStatus.IN_PROGRESS.value)
        
        # Execute the subtask
        result = run_claude_code_for_subtask(subtask, task_id, project_id)
        
        # Handle result and notify workflow engine
        if result['success']:
            workflow_engine.handle_subtask_completion(task_id, subtask_id, True, result)
            logger.info(f"Subtask {subtask_id} completed successfully")
        else:
            workflow_engine.handle_subtask_completion(task_id, subtask_id, False, result)
            logger.error(f"Subtask {subtask_id} failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    except Exception as e:
        error_msg = f"Error executing subtask: {str(e)}"
        logger.error(error_msg)
        
        # Try to mark subtask as failed if we have the IDs
        try:
            if 'task_id' in subtask_data and 'subtask_id' in subtask_data:
                coordinator = SubtaskQueueCoordinator(redis_url)
                coordinator.update_subtask_status(
                    subtask_data['task_id'], 
                    subtask_data['subtask_id'], 
                    SubtaskStatus.FAILED.value
                )
                workflow_engine.handle_subtask_completion(
                    subtask_data['task_id'], 
                    subtask_data['subtask_id'], 
                    False, 
                    {'error': error_msg}
                )
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup after subtask error: {cleanup_error}")
        
        return {'success': False, 'error': error_msg}


def process_github_issue_with_subtasks(issue_data: Dict, project_id: str = "default") -> Dict:
    """Process a GitHub issue using the new subtask-based workflow"""
    try:
        logger.info(f"Processing GitHub issue with subtasks for project {project_id}")
        
        # Use workflow engine to process the issue
        task_id = workflow_engine.process_github_issue(project_id, issue_data)
        
        logger.info(f"Created subtask workflow with task ID: {task_id}")
        
        return {
            'success': True,
            'task_id': task_id,
            'message': f"Started subtask workflow for issue processing"
        }
    
    except Exception as e:
        error_msg = f"Error processing GitHub issue with subtasks: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}


# Legacy functions from original worker for backward compatibility
def create_instruction_file(command_type, issue_or_pr_number=None, prompt=None):
    """Legacy function - create an instruction file for Claude Code"""
    # Import the function from the original worker
    from knocodex.templates.worker import create_instruction_file as legacy_create_instruction_file
    return legacy_create_instruction_file(command_type, issue_or_pr_number, prompt)


def run_claude_code_headless(prompt, allowed_tools=None):
    """Legacy function - run Claude Code in headless mode"""
    from knocodex.templates.worker import run_claude_code_headless as legacy_run_claude_code_headless
    return legacy_run_claude_code_headless(prompt, allowed_tools)


def process_github_issue(issue_number):
    """Legacy function - process a GitHub issue using old workflow"""
    from knocodex.templates.worker import process_github_issue as legacy_process_github_issue
    return legacy_process_github_issue(issue_number)


if __name__ == "__main__":
    logger.info("Starting enhanced subtask worker process")
    
    # Get queue configuration
    project_id = os.environ.get("PROJECT_ID", "default")
    
    # Initialize queue manager for project-specific queues
    queue_manager = ProjectQueueManager(redis_url)
    
    # Use project-specific queue
    if project_id != "default":
        queue = queue_manager.get_project_queue(project_id)
        logger.info(f"Using project-specific queue for project: {project_id}")
    else:
        # Fallback to default queue naming for backward compatibility
        queue_name = os.environ.get("REDIS_QUEUE", "knocodex:default:tasks")
        queue = Queue(queue_name, connection=redis_conn)
        logger.info(f"Using default queue: {queue_name}")
    
    # Create worker
    worker = Worker([queue], connection=redis_conn)
    
    logger.info(f"Worker listening on queue: {queue.name}")
    logger.info(f"Project ID: {project_id}")
    logger.info(f"Worker will respect project locks for sequential processing")
    
    # Start processing
    worker.work()