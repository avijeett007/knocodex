"""PR Review State Management Module.

This module provides functionality to track which PRs have been reviewed
by knocodex to prevent duplicate reviews.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from ..storage.pr_state_store import PRStateStore


@dataclass
class PRReviewRecord:
    """Represents a record of a PR review by knocodex."""
    pr_number: int
    pr_title: str
    reviewed_at: str
    last_commit_sha: str
    pr_updated_at: str
    review_status: str  # 'completed', 'failed', 'skipped'
    review_comment_id: Optional[int] = None


class PRReviewState:
    """Manages the state of PR reviews to prevent duplicates."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize PR review state manager.
        
        Args:
            storage_path: Optional path to store review state data.
                        Defaults to .knocodex/pr_review_state.json
        """
        if storage_path is None:
            storage_path = os.path.join('.knocodex', 'pr_review_state.json')
        
        self.store = PRStateStore(storage_path)
    
    def has_been_reviewed(self, pr_number: int) -> bool:
        """Check if a PR has already been reviewed by knocodex.
        
        Args:
            pr_number: GitHub PR number
            
        Returns:
            True if PR has been reviewed, False otherwise
        """
        record = self.store.get_review_record(pr_number)
        return record is not None and record.review_status == 'completed'
    
    def needs_review(self, pr_number: int, current_commit_sha: str, 
                    pr_updated_at: str, review_mode: str = 'never_repeat') -> bool:
        """Determine if a PR needs to be reviewed.
        
        Args:
            pr_number: GitHub PR number
            current_commit_sha: Current HEAD commit SHA of the PR
            pr_updated_at: ISO timestamp when PR was last updated
            review_mode: Review behavior mode ('never_repeat', 'on_updates', 'manual_only')
            
        Returns:
            True if PR needs review, False otherwise
        """
        if review_mode == 'manual_only':
            return False
        
        record = self.store.get_review_record(pr_number)
        
        # If never reviewed, needs review
        if record is None:
            return True
        
        # If previous review failed, needs review
        if record.review_status != 'completed':
            return True
        
        # If review mode is never_repeat and already reviewed, skip
        if review_mode == 'never_repeat':
            return False
        
        # If review mode is on_updates, check for updates
        if review_mode == 'on_updates':
            # Check if commit SHA changed
            if record.last_commit_sha != current_commit_sha:
                return True
            
            # Check if PR was updated after last review
            try:
                last_review = datetime.fromisoformat(record.reviewed_at.replace('Z', '+00:00'))
                pr_update = datetime.fromisoformat(pr_updated_at.replace('Z', '+00:00'))
                return pr_update > last_review
            except (ValueError, AttributeError):
                # If can't parse dates, err on side of reviewing
                return True
        
        return False
    
    def record_review_start(self, pr_number: int, pr_title: str, 
                           commit_sha: str, pr_updated_at: str) -> None:
        """Record that a PR review has started.
        
        Args:
            pr_number: GitHub PR number
            pr_title: PR title
            commit_sha: Current HEAD commit SHA
            pr_updated_at: ISO timestamp when PR was last updated
        """
        record = PRReviewRecord(
            pr_number=pr_number,
            pr_title=pr_title,
            reviewed_at=datetime.now(timezone.utc).isoformat(),
            last_commit_sha=commit_sha,
            pr_updated_at=pr_updated_at,
            review_status='in_progress'
        )
        self.store.save_review_record(record)
    
    def record_review_completion(self, pr_number: int, success: bool, 
                                comment_id: Optional[int] = None) -> None:
        """Record that a PR review has completed.
        
        Args:
            pr_number: GitHub PR number
            success: Whether the review completed successfully
            comment_id: Optional GitHub comment ID for the review
        """
        record = self.store.get_review_record(pr_number)
        if record is None:
            # This shouldn't happen, but handle gracefully
            return
        
        record.review_status = 'completed' if success else 'failed'
        record.reviewed_at = datetime.now(timezone.utc).isoformat()
        if comment_id:
            record.review_comment_id = comment_id
        
        self.store.save_review_record(record)
    
    def get_review_record(self, pr_number: int) -> Optional[PRReviewRecord]:
        """Get the review record for a PR.
        
        Args:
            pr_number: GitHub PR number
            
        Returns:
            PRReviewRecord if found, None otherwise
        """
        return self.store.get_review_record(pr_number)
    
    def get_all_reviewed_prs(self) -> List[PRReviewRecord]:
        """Get all PR review records.
        
        Returns:
            List of all PR review records
        """
        return self.store.get_all_records()
    
    def cleanup_closed_prs(self, open_pr_numbers: List[int]) -> int:
        """Clean up review records for PRs that are no longer open.
        
        Args:
            open_pr_numbers: List of currently open PR numbers
            
        Returns:
            Number of records cleaned up
        """
        return self.store.cleanup_closed_prs(open_pr_numbers)
    
    def clear_all_records(self) -> None:
        """Clear all review records. Use with caution."""
        self.store.clear_all_records()
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about PR reviews.
        
        Returns:
            Dictionary with review statistics
        """
        records = self.get_all_reviewed_prs()
        stats = {
            'total_reviews': len(records),
            'completed_reviews': len([r for r in records if r.review_status == 'completed']),
            'failed_reviews': len([r for r in records if r.review_status == 'failed']),
            'in_progress_reviews': len([r for r in records if r.review_status == 'in_progress'])
        }
        return stats