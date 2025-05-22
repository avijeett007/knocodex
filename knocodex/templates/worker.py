#!/usr/bin/env python3
"""
Worker process for Knocodex
"""

import os
import sys
import time
import json
import logging
import subprocess
import importlib.util
from pathlib import Path
from redis import Redis
from rq import Worker, Queue

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.getcwd(), ".knocodex", "logs", "worker.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("knocodex.worker")

# Get project path
project_path = os.getcwd()
knocodex_dir = os.path.join(project_path, ".knocodex")

# Redis connection
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
queue_name = os.environ.get("REDIS_QUEUE", "knocodex")
redis_conn = Redis.from_url(redis_url)
queue = Queue(queue_name, connection=redis_conn)

def create_instruction_file(command_type, issue_or_pr_number=None, prompt=None):
    """Create an instruction file for Claude Code"""
    # Create instructions directory if it doesn't exist
    instructions_dir = os.path.join(knocodex_dir, "instructions")
    os.makedirs(instructions_dir, exist_ok=True)
    
    # Create a unique file name
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    file_name = f"{command_type}-{timestamp}.md"
    file_path = os.path.join(instructions_dir, file_name)
    
    # Initialize instructions list
    instructions = []
    
    # Add appropriate instructions based on command type
    if command_type == "analyze-github-issue":
        instructions.append(f"# Analyze GitHub Issue #{issue_or_pr_number}\n")
        instructions.append(f"Please analyze GitHub issue #{issue_or_pr_number} and create a detailed implementation plan.\n")
        instructions.append(f"Use the GitHub CLI to fetch the issue details:\n")
        instructions.append(f"```bash\ngh issue view {issue_or_pr_number} --json number,title,body,labels,assignees\n```\n")
        instructions.append(f"After analyzing the issue, create a detailed plan and save it to:\n")
        instructions.append(f"`.knocodex/tasks/issue-{issue_or_pr_number}-plan.md`\n")
        instructions.append(f"The plan should include:\n")
        instructions.append(f"- Issue summary\n")
        instructions.append(f"- Required changes\n")
        instructions.append(f"- Implementation steps\n")
        instructions.append(f"- Files to be modified\n")
        instructions.append(f"- Testing approach\n")
    
    elif command_type == "implement-github-issue":
        instructions.append(f"# Implement GitHub Issue #{issue_or_pr_number}\n")
        instructions.append(f"Please implement a solution for GitHub issue #{issue_or_pr_number} based on the previously created plan.\n")
        instructions.append(f"First, read the implementation plan:\n")
        instructions.append(f"```bash\ncat .knocodex/tasks/issue-{issue_or_pr_number}-plan.md\n```\n")
        instructions.append(f"Then, create a new branch and implement the solution according to the plan.\n")
        instructions.append(f"Finally, create a pull request with a detailed description of the changes.\n")
    
    elif command_type == "document-project":
        instructions.append(f"# Generate Project Documentation\n")
        instructions.append(f"Please generate comprehensive documentation for this project.\n")
        instructions.append(f"Analyze the project structure and create documentation in the `docs/` directory.\n")
        instructions.append(f"The documentation should include:\n")
        instructions.append(f"- Project overview\n")
        instructions.append(f"- Installation instructions\n")
        instructions.append(f"- Usage guide\n")
        instructions.append(f"- API reference\n")
        instructions.append(f"- Architecture overview\n")
    
    elif command_type == "review-pull-request":
        instructions.append(f"# Review Pull Request #{issue_or_pr_number}\n")
        instructions.append(f"Please review GitHub pull request #{issue_or_pr_number} and provide detailed feedback.\n")
        instructions.append(f"Use the GitHub CLI to fetch the PR details:\n")
        instructions.append(f"```bash\ngh pr view {issue_or_pr_number} --json number,title,body,files,additions,deletions\n```\n")
        instructions.append(f"After reviewing the PR, create a detailed review and save it to:\n")
        instructions.append(f"`.knocodex/reviews/pr-{issue_or_pr_number}-review.md`\n")
        instructions.append(f"Then, post the review as a comment on the PR.\n")
    
    else:
        # Custom command fallback
        instructions.append(f"## Custom Command\n")
        instructions.append(f"Command: {prompt}\n\n")
        instructions.append("Please execute this command and take appropriate actions.\n")
    
    # Write instructions to file
    with open(file_path, 'w') as f:
        f.write('\n'.join(instructions))
    
    return file_path

def run_claude_code_headless(prompt, allowed_tools=None):
    """Run Claude Code in headless mode with the given prompt"""
    claude_path = os.environ.get('CLAUDE_CODE_PATH', 'claude')
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(knocodex_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Parse the command/prompt and prepare execution
    try:
        # Check if the prompt starts with a custom command
        if prompt.startswith('/project:'):
            parts = prompt.split(' ')
            if len(parts) >= 1:
                command_with_prefix = parts[0]
                command_type = command_with_prefix.replace('/project:', '')
                
                if len(parts) >= 2:
                    issue_or_pr_number = parts[1]
            
            # Create instruction file for different commands
            if command_type in ['analyze-github-issue', 'implement-github-issue', 'document-project', 'review-pull-request']:
                instruction_file = create_instruction_file(command_type, issue_or_pr_number)
            else:
                # Fallback for unknown custom commands
                command_type = 'custom-command'
                instruction_file = create_instruction_file(command_type, prompt=prompt)
        
            logger.info(f"Running Claude Code with file-based instructions for: {command_type}")
            logger.info(f"Instruction file: {instruction_file}")
            
            # Run Claude in print mode with the instruction file
            file_prompt = f"Read and execute the instructions in this file: {instruction_file}"
            command = [claude_path, '-p', file_prompt, '--dangerously-skip-permissions']
            
            # Keep the allowed_tools parameter in context variable but don't use it in command
            # We're always using dangerously-skip-permissions now by user request
        else:
            # Direct execution of prompt
            command = [claude_path, '-p', prompt, '--dangerously-skip-permissions']
            command_type = 'direct-prompt'
            instruction_file = None
            
            # Always use dangerously-skip-permissions for reliable execution
    except Exception as e:
        logger.error(f"Failed to prepare Claude Code execution: {e}")
        return {
            'success': False,
            'stderr': str(e),
            'command_type': 'unknown',
            'instruction_file': None,
            'retries': 0
        }
    
    # Execute Claude Code with retries
    max_retries = 3
    retries = 0
    
    while retries <= max_retries:
        try:
            logger.info(f"Running Claude Code with command: {' '.join(command)}")
            if retries > 0:
                logger.info(f"Retry attempt {retries} of {max_retries}")
                
            # Run the command and capture output
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            
            stdout = process.stdout
            stderr = process.stderr
            
            # Success! Return the result
            return {
                'success': True,
                'stdout': stdout,
                'stderr': stderr,
                'command_type': command_type,
                'instruction_file': instruction_file,
                'retries': retries
            }
                
        except subprocess.CalledProcessError as e:
            stderr_output = e.stderr if hasattr(e, 'stderr') else str(e)
            stdout_output = e.stdout if hasattr(e, 'stdout') else ''
            
            logger.error(f"Claude Code execution failed (attempt {retries+1}/{max_retries+1}):")
            logger.error(f"Exit code: {e.returncode}")
            logger.error(f"Error: {stderr_output}")
            
            # Increment retry counter
            retries += 1
            
            if retries <= max_retries:
                logger.info(f"Waiting 10 seconds before retry...")
                time.sleep(10)
            else:
                logger.error(f"Max retries reached. Giving up.")
                return {
                    'success': False,
                    'stdout': stdout_output,
                    'stderr': stderr_output,
                    'command_type': command_type,
                    'instruction_file': instruction_file,
                    'retries': retries
                }
        
        except Exception as e:
            logger.error(f"Unexpected error during Claude Code execution: {e}")
            
            # Increment retry counter
            retries += 1
            
            if retries <= max_retries:
                logger.info(f"Waiting 10 seconds before retry...")
                time.sleep(10)
            else:
                logger.error(f"Max retries reached. Giving up.")
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': str(e),
                    'command_type': command_type,
                    'instruction_file': instruction_file,
                    'retries': retries
                }

def process_github_issue(issue_number):
    """Process a GitHub issue"""
    logger.info(f"Processing GitHub issue #{issue_number}")
    
    # Create a lock file to prevent duplicate processing
    lock_dir = os.path.join(knocodex_dir, "locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_file = os.path.join(lock_dir, f"issue-{issue_number}.lock")
    
    if os.path.exists(lock_file):
        logger.info(f"Issue #{issue_number} is already being processed")
        return {
            'success': False,
            'error': 'Issue is already being processed'
        }
    
    # Create the lock file
    with open(lock_file, 'w') as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"Processing started: {timestamp}\n")
    
    try:
        # Step 1: Analyze the issue and create a plan
        analyze_prompt = f"/project:analyze-github-issue {issue_number}"
        
        result = run_claude_code_headless(
            analyze_prompt,
            "Bash(gh:*) Edit Run"
        )
        
        if not result['success']:
            logger.error(f"Failed to analyze issue #{issue_number}")
            # Don't remove lock file here - keep it as a record of failure
            return {
                'success': False,
                'stage': 'analyze',
                'error': result['stderr']
            }
        
        logger.info(f"Successfully analyzed issue #{issue_number}")
        
        # Update lock file to indicate progress
        with open(lock_file, 'a') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Analysis completed: {timestamp}\n")
        
        # Step 2: Implement the solution
        implement_prompt = f"/project:implement-github-issue {issue_number}"
        
        result = run_claude_code_headless(
            implement_prompt,
            "Bash(gh:*,git:*) Edit Run Test"
        )
        
        if not result['success']:
            logger.error(f"Failed to implement solution for issue #{issue_number}")
            # Update lock file with failure information
            with open(lock_file, 'a') as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Implementation failed: {timestamp}\n")
            
            return {
                'success': False,
                'stage': 'implement',
                'error': result['stderr']
            }
        
        logger.info(f"Successfully implemented solution for issue #{issue_number}")
        
        # Update lock file to indicate completion
        with open(lock_file, 'a') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Implementation completed: {timestamp}\n")
        
        return {
            'success': True,
            'stage': 'complete',
            'message': f"Successfully processed issue #{issue_number}"
        }
    
    except Exception as e:
        logger.error(f"Error processing issue #{issue_number}: {e}")
        
        # Update lock file with error information
        with open(lock_file, 'a') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Error: {timestamp} - {str(e)}\n")
        
        return {
            'success': False,
            'stage': 'unknown',
            'error': str(e)
        }

def update_project_documentation():
    """Update project documentation"""
    logger.info("Updating project documentation")
    
    try:
        # Run the document-project command
        result = run_claude_code_headless(
            "/project:document-project",
            "Bash Edit Run"
        )
        
        if not result['success']:
            logger.error("Failed to update project documentation")
            return {
                'success': False,
                'error': result['stderr']
            }
        
        logger.info("Successfully updated project documentation")
        return {
            'success': True,
            'message': "Successfully updated project documentation"
        }
    
    except Exception as e:
        logger.error(f"Error updating project documentation: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def review_pull_request(pr_number):
    """Review a pull request with state tracking"""
    logger.info(f"Reviewing pull request #{pr_number}")
    
    # Create a lock file to prevent duplicate processing
    lock_dir = os.path.join(knocodex_dir, "locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_file = os.path.join(lock_dir, f"pr-{pr_number}.lock")
    
    if os.path.exists(lock_file):
        logger.info(f"PR #{pr_number} is already being reviewed")
        return {
            'success': False,
            'error': 'PR is already being reviewed'
        }
    
    # Create the lock file
    with open(lock_file, 'w') as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"Review started: {timestamp}\n")
    
    # Initialize PR review state tracking
    pr_review_state = None
    try:
        # Load configuration
        config_file = os.path.join(knocodex_dir, "config.json")
        config = {}
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
        
        pr_state_storage_path = config.get("pr_state_storage_path")
        
        # Import PR review state management
        sys.path.insert(0, os.path.join(project_path, "knocodex"))
        from models.pr_review_state import PRReviewState
        
        pr_review_state = PRReviewState(pr_state_storage_path)
        logger.info("Initialized PR review state tracking")
    except ImportError as e:
        logger.warning(f"Could not import PR review state management: {e}")
    except Exception as e:
        logger.warning(f"Error initializing PR review state: {e}")
    
    try:
        # Run the review-pull-request command
        result = run_claude_code_headless(
            f"/project:review-pull-request {pr_number}",
            "Bash(gh:*) Edit Run"
        )
        
        if not result['success']:
            logger.error(f"Failed to review pull request #{pr_number}")
            
            # Record failed review in state if available
            if pr_review_state:
                pr_review_state.record_review_completion(pr_number, success=False)
            
            # Update lock file with failure information
            with open(lock_file, 'a') as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Review failed: {timestamp}\n")
            
            return {
                'success': False,
                'error': result['stderr']
            }
        
        logger.info(f"Successfully reviewed pull request #{pr_number}")
        
        # Record successful review in state if available
        if pr_review_state:
            # TODO: Extract comment ID from GitHub CLI response if needed
            pr_review_state.record_review_completion(pr_number, success=True)
        
        # Update lock file to indicate completion
        with open(lock_file, 'a') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Review completed: {timestamp}\n")
        
        # Remove lock file after successful completion
        try:
            os.remove(lock_file)
        except OSError:
            pass  # Lock file removal is not critical
        
        return {
            'success': True,
            'message': f"Successfully reviewed pull request #{pr_number}"
        }
    
    except Exception as e:
        logger.error(f"Error reviewing pull request #{pr_number}: {e}")
        
        # Record failed review in state if available
        if pr_review_state:
            pr_review_state.record_review_completion(pr_number, success=False)
        
        # Update lock file with error information
        with open(lock_file, 'a') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Error: {timestamp} - {str(e)}\n")
        
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    logger.info("Starting worker process")
    
    # In RQ 2.3.3, the Connection context manager was removed
    # Worker now directly uses the connection from the queue
    worker = Worker([queue], connection=redis_conn)
    worker.work()
