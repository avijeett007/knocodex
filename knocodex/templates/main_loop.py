#!/usr/bin/env python3
"""
Main polling loop for Knocodex
"""

import os
import sys
import time
import json
import logging
import subprocess
import importlib.util
from pathlib import Path

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

# Check for worker.py first - it's needed by tasks.py
worker_file = os.path.join(knocodex_dir, "worker.py")
if not os.path.exists(worker_file):
    logger.error("Worker script not found. Please run 'knocodex init' first to initialize the project properly.")
    sys.exit(1)

# Import tasks module
sys.path.append(knocodex_dir)

# First check if tasks.py exists, if not create it
tasks_file = os.path.join(knocodex_dir, "tasks.py")
if not os.path.exists(tasks_file):
    logger.info("Creating tasks.py file")
    
    tasks_content = """import os
import sys
import time
from redis import Redis
from rq import Queue

# Redis connection
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
queue_name = os.environ.get('REDIS_QUEUE', 'knocodex')
redis_conn = Redis.from_url(redis_url)
queue = Queue(queue_name, connection=redis_conn)

# Safely import from worker - add appropriate path first
worker_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(worker_path)

# Define placeholder functions in case imports fail
def process_github_issue(issue_number):
    '''Process a GitHub issue'''
    raise NotImplementedError("Worker module not properly loaded")

def update_project_documentation():
    '''Update project documentation'''
    raise NotImplementedError("Worker module not properly loaded")

def review_pull_request(pr_number):
    '''Review a pull request'''
    raise NotImplementedError("Worker module not properly loaded")

# Try to import the actual implementations
try:
    from worker import process_github_issue, update_project_documentation, review_pull_request
    print("Successfully imported worker functions")
except ImportError as e:
    print(f"Warning: Could not import from worker: {e}")
    # Continue with placeholder functions

def enqueue_process_github_issue(issue_number):
    '''Add a GitHub issue processing task to the queue'''
    job = queue.enqueue(
        process_github_issue,
        issue_number,
        job_timeout='2h',  # Long timeout for complex issues
        result_ttl=86400,  # Keep results for 24 hours
        ttl=86400          # Job can wait in queue for up to 24 hours
    )
    return job.id

def enqueue_update_documentation():
    '''Add a documentation update task to the queue'''
    job = queue.enqueue(
        update_project_documentation,
        job_timeout='1h',
        result_ttl=86400,
        ttl=86400
    )
    return job.id

def enqueue_review_pull_request(pr_number):
    '''Add a PR review task to the queue'''
    job = queue.enqueue(
        review_pull_request,
        pr_number,
        job_timeout='1h',
        result_ttl=86400,
        ttl=86400
    )
    return job.id
"""
    
    with open(tasks_file, "w") as f:
        f.write(tasks_content)
    
    logger.info("Created tasks.py file")

# Try to import the tasks module
try:
    from tasks import enqueue_process_github_issue, enqueue_review_pull_request
    logger.info("Successfully imported tasks module")
except ImportError as e:
    logger.error(f"Failed to import tasks module: {e}")
    sys.exit(1)

def check_github_issues():
    """Check for GitHub issues with the specified label"""
    logger.info(f"Checking for GitHub issues with label: {github_issue_label}")
    
    try:
        # Get issues with the specified label
        cmd = ["gh", "issue", "list", "--json", "number,title,url,labels", "--label", github_issue_label, "--state", "open"]
        
        if github_repo:
            cmd.extend(["--repo", github_repo])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issues = json.loads(result.stdout)
        
        if not issues:
            logger.info("No issues found with the specified label")
            return
        
        logger.info(f"Found {len(issues)} issues with label: {github_issue_label}")
        
        # Process each issue
        for issue in issues:
            issue_number = issue["number"]
            issue_title = issue["title"]
            
            # Check if the issue is already being processed
            lock_file = os.path.join(knocodex_dir, "locks", f"issue-{issue_number}.lock")
            if os.path.exists(lock_file):
                logger.info(f"Issue #{issue_number} is already being processed")
                continue
            
            # Enqueue the issue for processing
            logger.info(f"Enqueuing issue #{issue_number}: {issue_title}")
            job_id = enqueue_process_github_issue(issue_number)
            logger.info(f"Enqueued job with ID: {job_id}")
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check GitHub issues: {e}")
        logger.error(f"Error output: {e.stderr}")
    except Exception as e:
        logger.error(f"Error checking GitHub issues: {e}")

def check_github_prs():
    """Check for GitHub PRs that need review"""
    if not pr_review_enabled:
        logger.info("PR review is disabled")
        return
    
    logger.info("Checking for GitHub PRs that need review")
    
    try:
        # Get open PRs
        cmd = ["gh", "pr", "list", "--json", "number,title,url,reviewDecision,reviews", "--state", "open"]
        
        if github_repo:
            cmd.extend(["--repo", github_repo])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        prs = json.loads(result.stdout)
        
        if not prs:
            logger.info("No open PRs found")
            return
        
        logger.info(f"Found {len(prs)} open PRs")
        
        # Process each PR
        for pr in prs:
            pr_number = pr["number"]
            pr_title = pr["title"]
            review_decision = pr.get("reviewDecision")
            reviews = pr.get("reviews", [])
            
            # Check if the PR needs review
            if review_decision == "APPROVED":
                logger.info(f"PR #{pr_number} is already approved")
                continue
            
            if len(reviews) > 0:
                logger.info(f"PR #{pr_number} already has reviews")
                continue
            
            # Check if the PR is already being reviewed
            lock_file = os.path.join(knocodex_dir, "locks", f"pr-{pr_number}.lock")
            if os.path.exists(lock_file):
                logger.info(f"PR #{pr_number} is already being reviewed")
                continue
            
            # Enqueue the PR for review
            logger.info(f"Enqueuing PR #{pr_number} for review: {pr_title}")
            job_id = enqueue_review_pull_request(pr_number)
            logger.info(f"Enqueued job with ID: {job_id}")
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check GitHub PRs: {e}")
        logger.error(f"Error output: {e.stderr}")
    except Exception as e:
        logger.error(f"Error checking GitHub PRs: {e}")

def main_loop():
    """Main polling loop"""
    logger.info(f"Starting main loop with polling interval of {polling_interval} seconds")
    
    while True:
        try:
            # Check for GitHub issues
            check_github_issues()
            
            # Check for GitHub PRs that need review
            if pr_review_enabled:
                check_github_prs()
            
            # Sleep for the polling interval
            logger.info(f"Sleeping for {polling_interval} seconds...")
            time.sleep(polling_interval)
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, exiting...")
            break
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.info(f"Sleeping for {polling_interval} seconds before retrying...")
            time.sleep(polling_interval)

if __name__ == "__main__":
    logger.info("Starting main polling loop")
    main_loop()
