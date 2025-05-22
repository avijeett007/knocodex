#!/usr/bin/env python3
"""
GitHub utilities for Knocodex
"""

import os
import subprocess
import logging
import json
from pathlib import Path

logger = logging.getLogger("knocodex.utils.gh_utils")

def check_gh_auth():
    """Check if GitHub CLI is authenticated"""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to check GitHub authentication: {e}")
        return False

def get_gh_issues(repo=None, label=None, state="open", limit=10):
    """Get GitHub issues"""
    try:
        cmd = ["gh", "issue", "list", "--json", "number,title,url,labels,state,createdAt"]
        
        if repo:
            cmd.extend(["--repo", repo])
        
        if label:
            cmd.extend(["--label", label])
        
        cmd.extend(["--state", state, "--limit", str(limit)])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get GitHub issues: {e}")
        logger.error(f"Error output: {e.stderr}")
        return []
    except Exception as e:
        logger.error(f"Failed to get GitHub issues: {e}")
        return []

def get_gh_issue(issue_number, repo=None):
    """Get a specific GitHub issue"""
    try:
        cmd = ["gh", "issue", "view", str(issue_number), "--json", "number,title,body,url,labels,state,createdAt"]
        
        if repo:
            cmd.extend(["--repo", repo])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get GitHub issue {issue_number}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Failed to get GitHub issue {issue_number}: {e}")
        return None

def comment_on_issue(issue_number, comment, repo=None):
    """Comment on a GitHub issue"""
    try:
        cmd = ["gh", "issue", "comment", str(issue_number), "--body", comment]
        
        if repo:
            cmd.extend(["--repo", repo])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        logger.info(f"Commented on issue {issue_number}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to comment on issue {issue_number}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to comment on issue {issue_number}: {e}")
        return False

def create_pr(title, body, base_branch="main", repo=None):
    """Create a GitHub pull request"""
    try:
        cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base_branch]
        
        if repo:
            cmd.extend(["--repo", repo])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        logger.info(f"Created PR: {title}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create PR: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Failed to create PR: {e}")
        return None

def get_gh_prs(repo=None, state="open", limit=10):
    """Get GitHub pull requests"""
    try:
        cmd = ["gh", "pr", "list", "--json", "number,title,url,state,createdAt"]
        
        if repo:
            cmd.extend(["--repo", repo])
        
        cmd.extend(["--state", state, "--limit", str(limit)])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get GitHub PRs: {e}")
        logger.error(f"Error output: {e.stderr}")
        return []
    except Exception as e:
        logger.error(f"Failed to get GitHub PRs: {e}")
        return []

def get_gh_pr(pr_number, repo=None):
    """Get a specific GitHub pull request"""
    try:
        cmd = ["gh", "pr", "view", str(pr_number), "--json", "number,title,body,url,state,createdAt,additions,deletions,changedFiles"]
        
        if repo:
            cmd.extend(["--repo", repo])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get GitHub PR {pr_number}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Failed to get GitHub PR {pr_number}: {e}")
        return None

def comment_on_pr(pr_number, comment, repo=None):
    """Comment on a GitHub pull request"""
    try:
        cmd = ["gh", "pr", "comment", str(pr_number), "--body", comment]
        
        if repo:
            cmd.extend(["--repo", repo])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        logger.info(f"Commented on PR #{pr_number}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to comment on PR #{pr_number}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to comment on PR {pr_number}: {e}")
        return False

def get_issue_details(issue_number, repo=None):
    """Get detailed information about a GitHub issue
    
    This function fetches comprehensive details about a GitHub issue,
    including its title, body, labels, assignees, and other metadata.
    
    Args:
        issue_number: The issue number to get details for
        repo: Optional repository in the format 'owner/repo'
        
    Returns:
        Dict with issue details or None if an error occurs
    """
    try:
        cmd = ["gh", "issue", "view", str(issue_number), 
               "--json", "number,title,body,labels,assignees,milestone,state,createdAt,updatedAt,comments"]
        
        if repo:
            cmd.extend(["--repo", repo])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        
        issue_data = json.loads(result.stdout)
        logger.info(f"Retrieved details for issue #{issue_number}")
        return issue_data
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get details for issue #{issue_number}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response for issue #{issue_number}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to get details for issue #{issue_number}: {e}")
        return None
