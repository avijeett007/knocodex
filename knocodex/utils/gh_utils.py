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
    """Get GitHub pull requests with enhanced metadata"""
    try:
        cmd = ["gh", "pr", "list", "--json", "number,title,url,state,createdAt,updatedAt,headRefOid,reviews"]
        
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
    """Get a specific GitHub pull request with enhanced metadata"""
    try:
        cmd = ["gh", "pr", "view", str(pr_number), "--json", 
               "number,title,body,url,state,createdAt,updatedAt,headRefOid,additions,deletions,changedFiles,reviews"]
        
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


def get_pr_review_metadata(pr_data):
    """Extract review-relevant metadata from PR data.
    
    Args:
        pr_data: PR data from get_gh_pr() or get_gh_prs()
        
    Returns:
        Dictionary with review metadata including commit SHA and update timestamp
    """
    metadata = {
        'pr_number': pr_data.get('number'),
        'pr_title': pr_data.get('title', ''),
        'commit_sha': pr_data.get('headRefOid', ''),
        'updated_at': pr_data.get('updatedAt', ''),
        'created_at': pr_data.get('createdAt', ''),
        'has_reviews': len(pr_data.get('reviews', [])) > 0
    }
    
    return metadata


def has_knocodex_review(pr_data, bot_username='github-actions[bot]'):
    """Check if a PR already has a knocodex review comment.
    
    Args:
        pr_data: PR data from get_gh_pr()
        bot_username: Username to look for in reviews (default: github-actions[bot])
        
    Returns:
        True if knocodex has already reviewed this PR
    """
    reviews = pr_data.get('reviews', [])
    
    for review in reviews:
        author = review.get('author', {})
        if author and author.get('login') == bot_username:
            # Check if review body contains knocodex signature
            body = review.get('body', '').lower()
            if 'knocodex' in body or 'automated review' in body:
                return True
    
    return False


def filter_prs_for_review(prs_data, pr_review_state=None, review_mode='never_repeat'):
    """Filter PRs to determine which ones need review.
    
    Args:
        prs_data: List of PR data from get_gh_prs()
        pr_review_state: PRReviewState instance for checking review history
        review_mode: Review behavior mode ('never_repeat', 'on_updates', 'manual_only')
        
    Returns:
        List of PRs that need to be reviewed
    """
    prs_to_review = []
    
    for pr_data in prs_data:
        pr_number = pr_data.get('number')
        if not pr_number:
            continue
        
        metadata = get_pr_review_metadata(pr_data)
        
        # Skip if PR already has GitHub reviews (existing behavior)
        if metadata['has_reviews']:
            logger.debug(f"Skipping PR #{pr_number}: already has reviews")
            continue
        
        # If we have review state tracking, use it
        if pr_review_state:
            if pr_review_state.needs_review(
                pr_number=pr_number,
                current_commit_sha=metadata['commit_sha'],
                pr_updated_at=metadata['updated_at'],
                review_mode=review_mode
            ):
                prs_to_review.append(pr_data)
            else:
                logger.debug(f"Skipping PR #{pr_number}: already reviewed by knocodex")
        else:
            # Fallback to existing behavior
            prs_to_review.append(pr_data)
    
    return prs_to_review

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
