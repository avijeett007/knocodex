#!/usr/bin/env python3
"""
Enhanced main polling loop for Knocodex with subtask workflow support

This script checks for GitHub issues and processes them through the subtask workflow system,
while maintaining backward compatibility with the legacy single-task workflow.
"""

import os
import sys
import time
import json
import logging
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.getcwd(), ".knocodex", "logs", "main_loop.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("knocodex.main_loop")

# Get project path
project_path = os.getcwd()
knocodex_dir = os.path.join(project_path, ".knocodex")

# Load configuration
config_file = os.path.join(knocodex_dir, "config.json")
if not os.path.exists(config_file):
    logger.error(f"Configuration file not found: {config_file}")
    sys.exit(1)

with open(config_file, "r") as f:
    config = json.load(f)

# Get configuration values
github_repo = config.get("github_repo", "")
github_issue_label = config.get("github_issue_label", "knocodex")
polling_interval = config.get("polling_interval", 300)
pr_review_enabled = config.get("pr_review_enabled", True)
use_subtask_workflow = config.get("use_subtask_workflow", True)  # New configuration option

# Try to import the workflow engine and project manager
workflow_engine = None
project_manager = None
queue_coordinator = None

try:
    # Add parent directory to path for imports
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from redis import Redis
    from knocodex.workflow_engine import SubtaskWorkflowEngine, WorkflowConfig
    from knocodex.project_manager import ProjectManager
    from knocodex.utils.redis_utils import SubtaskQueueCoordinator
    
    # Initialize Redis connection
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    redis_conn = Redis.from_url(redis_url)
    
    # Initialize workflow components
    workflow_config = WorkflowConfig()
    workflow_engine = SubtaskWorkflowEngine(redis_conn, workflow_config)
    project_manager = ProjectManager(None, redis_conn)  # We don't have access to Config here
    queue_coordinator = SubtaskQueueCoordinator(redis_url)
    
    logger.info("Initialized subtask workflow engine")
except Exception as e:
    logger.warning(f"Failed to initialize subtask workflow engine: {e}")
    logger.info("Will fallback to legacy single-task workflow")

# Check for worker.py - needed for legacy workflow
worker_file = os.path.join(knocodex_dir, "worker.py")
if not os.path.exists(worker_file):
    logger.warning("Legacy worker script not found. Single-task workflow will not be available.")

# Try to import tasks from worker.py
try:
    # Add knocodex directory to path
    sys.path.insert(0, knocodex_dir)
    
    # Import worker module
    spec = importlib.util.spec_from_file_location("worker", worker_file)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    
    # Create tasks module
    tasks_file = os.path.join(knocodex_dir, "tasks.py")
    
    with open(tasks_file, "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Tasks for Knocodex
\"\"\"

import os
import sys
import logging
from worker import process_github_issue, review_pull_request, update_project_documentation

logger = logging.getLogger("knocodex.tasks")
""")
    
    # Make tasks.py executable
    os.chmod(tasks_file, 0o755)
    
    # Import tasks module
    import tasks
    logger.info("Imported tasks module")
except Exception as e:
    logger.warning(f"Failed to import tasks: {e}")
    
    # Create placeholder functions for tasks module
    class tasks:
        @staticmethod
        def process_github_issue(issue_number):
            logger.error("Tasks module not initialized. Cannot process GitHub issue.")
            return False
        
        @staticmethod
        def review_pull_request(pr_number):
            logger.error("Tasks module not initialized. Cannot review pull request.")
            return False
        
        @staticmethod
        def update_project_documentation():
            logger.error("Tasks module not initialized. Cannot update project documentation.")
            return False


def check_github_issues():
    """Check for GitHub issues with the specified label"""
    logger.info("Checking for GitHub issues with label: %s", github_issue_label)
    
    try:
        # Get list of open issues with the specified label
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", github_repo, "--label", github_issue_label, "--state", "open", "--json", "number,title"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        issues = json.loads(result.stdout)
        
        if not issues:
            logger.info("No open issues found with label: %s", github_issue_label)
            return
        
        logger.info("Found %d open issues with label: %s", len(issues), github_issue_label)
        
        for issue in issues:
            issue_number = issue["number"]
            issue_title = issue["title"]
            
            # Check if issue is already being processed
            issue_lock_file = os.path.join(knocodex_dir, "locks", f"issue-{issue_number}.lock")
            if os.path.exists(issue_lock_file):
                logger.info("Issue #%d is already being processed", issue_number)
                continue
            
            # Create lock file
            os.makedirs(os.path.dirname(issue_lock_file), exist_ok=True)
            with open(issue_lock_file, "w") as f:
                f.write(str(datetime.now()))
            
            logger.info("Processing GitHub issue #%d: %s", issue_number, issue_title)
            
            # Process issue with subtask workflow if available, otherwise use legacy workflow
            if use_subtask_workflow and workflow_engine:
                try:
                    # Get full issue data
                    result = subprocess.run(
                        ["gh", "issue", "view", str(issue_number), "--json", "number,title,body,labels"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    issue_data = json.loads(result.stdout)
                    
                    # Get project ID (use "default" if no projects are configured)
                    project_id = "default"
                    if project_manager:
                        projects = project_manager.list_projects()
                        if projects:
                            project_id = projects[0]
                    
                    # Process the issue with subtasks
                    plan_id = workflow_engine.process_github_issue(project_id, issue_data)
                    logger.info(f"Started processing GitHub issue {issue_number} with subtask plan ID {plan_id}")
                except Exception as e:
                    logger.error(f"Failed to process issue with subtask workflow: {e}")
                    logger.info("Falling back to legacy workflow")
                    
                    # Fallback to legacy workflow
                    tasks.process_github_issue(issue_number)
            else:
                # Use legacy workflow
                tasks.process_github_issue(issue_number)
    except Exception as e:
        logger.error("Failed to check GitHub issues: %s", e)


def check_github_prs():
    """Check for GitHub PRs that need review"""
    if not pr_review_enabled:
        logger.info("PR review is disabled")
        return
    
    logger.info("Checking for GitHub PRs that need review")
    
    try:
        # Get list of open PRs
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", github_repo, "--state", "open", "--json", "number,title,reviews"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        prs = json.loads(result.stdout)
        
        if not prs:
            logger.info("No open PRs found")
            return
        
        logger.info("Found %d open PRs", len(prs))
        
        for pr in prs:
            pr_number = pr["number"]
            pr_title = pr["title"]
            reviews = pr.get("reviews", [])
            
            # Check if PR has already been reviewed
            review_count = len(reviews)
            if review_count > 0:
                logger.info("PR #%d already has %d reviews", pr_number, review_count)
                continue
            
            # Check if PR is already being reviewed
            pr_lock_file = os.path.join(knocodex_dir, "locks", f"pr-{pr_number}.lock")
            if os.path.exists(pr_lock_file):
                logger.info("PR #%d is already being reviewed", pr_number)
                continue
            
            # Create lock file
            os.makedirs(os.path.dirname(pr_lock_file), exist_ok=True)
            with open(pr_lock_file, "w") as f:
                f.write(str(datetime.now()))
            
            logger.info("Reviewing GitHub PR #%d: %s", pr_number, pr_title)
            
            # Review PR
            tasks.review_pull_request(pr_number)
    except Exception as e:
        logger.error("Failed to check GitHub PRs: %s", e)


def check_active_workflows():
    """Check and update status of active subtask workflows"""
    if not use_subtask_workflow or not workflow_engine or not queue_coordinator:
        return
    
    logger.info("Checking active subtask workflows")
    
    try:
        # This function would need to be implemented in the workflow engine
        # to get all active workflows and check their status
        active_workflows = []  # workflow_engine.get_active_workflows()
        
        if not active_workflows:
            logger.info("No active workflows found")
            return
        
        logger.info(f"Found {len(active_workflows)} active workflows")
        
        for workflow_id in active_workflows:
            # Check if any subtasks are ready to be processed
            try:
                # Get project ID for this workflow
                project_id = "default"  # This would need to be retrieved from the workflow
                
                # Check for and enqueue ready subtasks
                num_enqueued = queue_coordinator.enqueue_ready_subtasks(workflow_id, project_id)
                
                if num_enqueued > 0:
                    logger.info(f"Enqueued {num_enqueued} ready subtasks for workflow {workflow_id}")
                
                # Check if workflow is complete
                if queue_coordinator.is_plan_complete(workflow_id):
                    logger.info(f"Workflow {workflow_id} is complete")
                    
                    # Perform workflow completion actions
                    # This would need to be implemented in the workflow engine
                    # workflow_engine.finalize_workflow(workflow_id)
            except Exception as e:
                logger.error(f"Error processing workflow {workflow_id}: {e}")
    except Exception as e:
        logger.error(f"Failed to check active workflows: {e}")


def clean_old_locks():
    """Clean up old lock files"""
    locks_dir = os.path.join(knocodex_dir, "locks")
    if not os.path.exists(locks_dir):
        return
    
    try:
        # Get current time
        now = datetime.now()
        
        # Get list of lock files
        lock_files = os.listdir(locks_dir)
        
        for lock_file in lock_files:
            lock_file_path = os.path.join(locks_dir, lock_file)
            
            # Get lock file creation time
            with open(lock_file_path, "r") as f:
                try:
                    created_time = datetime.fromisoformat(f.read().strip())
                except:
                    # If parsing fails, use file modification time
                    created_time = datetime.fromtimestamp(os.path.getmtime(lock_file_path))
            
            # Check if lock file is older than 24 hours
            if now - created_time > timedelta(hours=24):
                logger.info("Removing old lock file: %s", lock_file)
                os.remove(lock_file_path)
    except Exception as e:
        logger.error("Failed to clean old locks: %s", e)


def main_loop():
    """Main polling loop"""
    try:
        while True:
            logger.info("Starting polling loop")
            
            # Clean old locks
            clean_old_locks()
            
            # Check GitHub issues
            check_github_issues()
            
            # Check GitHub PRs
            check_github_prs()
            
            # Check active workflows
            check_active_workflows()
            
            # Update project documentation once per day
            if datetime.now().hour == 2:  # 2 AM
                tasks.update_project_documentation()
            
            logger.info("Sleeping for %d seconds", polling_interval)
            time.sleep(polling_interval)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error("Error in main loop: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Starting enhanced main polling loop with subtask workflow support")
    main_loop()
