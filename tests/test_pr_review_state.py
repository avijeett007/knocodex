#!/usr/bin/env python3
"""
Test PR review state management functionality
"""

import os
import json
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from knocodex.models.pr_review_state import PRReviewState, PRReviewRecord
from knocodex.storage.pr_state_store import PRStateStore


class TestPRReviewRecord(unittest.TestCase):
    """Test PRReviewRecord dataclass"""
    
    def test_pr_review_record_creation(self):
        """Test creating a PR review record"""
        record = PRReviewRecord(
            pr_number=123,
            pr_title="Test PR",
            reviewed_at="2024-01-01T12:00:00Z",
            last_commit_sha="abc123",
            pr_updated_at="2024-01-01T11:00:00Z",
            review_status="completed"
        )
        
        self.assertEqual(record.pr_number, 123)
        self.assertEqual(record.pr_title, "Test PR")
        self.assertEqual(record.review_status, "completed")
        self.assertIsNone(record.review_comment_id)


class TestPRStateStore(unittest.TestCase):
    """Test PR state store functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "test_pr_state.json")
        self.store = PRStateStore(self.storage_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_store(self):
        """Test empty store behavior"""
        record = self.store.get_review_record(123)
        self.assertIsNone(record)
        
        records = self.store.get_all_records()
        self.assertEqual(len(records), 0)
    
    def test_save_and_get_record(self):
        """Test saving and retrieving a record"""
        record = PRReviewRecord(
            pr_number=123,
            pr_title="Test PR",
            reviewed_at="2024-01-01T12:00:00Z",
            last_commit_sha="abc123",
            pr_updated_at="2024-01-01T11:00:00Z",
            review_status="completed"
        )
        
        self.store.save_review_record(record)
        
        retrieved = self.store.get_review_record(123)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.pr_number, 123)
        self.assertEqual(retrieved.pr_title, "Test PR")
        self.assertEqual(retrieved.review_status, "completed")
    
    def test_cleanup_closed_prs(self):
        """Test cleanup of closed PRs"""
        # Add some records
        records = [
            PRReviewRecord(
                pr_number=123,
                pr_title="Open PR 1",
                reviewed_at="2024-01-01T12:00:00Z",
                last_commit_sha="abc123",
                pr_updated_at="2024-01-01T11:00:00Z",
                review_status="completed"
            ),
            PRReviewRecord(
                pr_number=456,
                pr_title="Open PR 2", 
                reviewed_at="2024-01-01T12:00:00Z",
                last_commit_sha="def456",
                pr_updated_at="2024-01-01T11:00:00Z",
                review_status="completed"
            ),
            PRReviewRecord(
                pr_number=789,
                pr_title="Closed PR",
                reviewed_at="2024-01-01T12:00:00Z",
                last_commit_sha="ghi789",
                pr_updated_at="2024-01-01T11:00:00Z",
                review_status="completed"
            )
        ]
        
        for record in records:
            self.store.save_review_record(record)
        
        # Cleanup with only PRs 123 and 456 open
        removed_count = self.store.cleanup_closed_prs([123, 456])
        
        self.assertEqual(removed_count, 1)
        self.assertIsNotNone(self.store.get_review_record(123))
        self.assertIsNotNone(self.store.get_review_record(456))
        self.assertIsNone(self.store.get_review_record(789))


class TestPRReviewState(unittest.TestCase):
    """Test PR review state management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "test_pr_state.json")
        self.state = PRReviewState(self.storage_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_has_been_reviewed_empty(self):
        """Test has_been_reviewed with empty state"""
        self.assertFalse(self.state.has_been_reviewed(123))
    
    def test_has_been_reviewed_after_completion(self):
        """Test has_been_reviewed after completing a review"""
        # Record a review start
        self.state.record_review_start(
            pr_number=123,
            pr_title="Test PR",
            commit_sha="abc123",
            pr_updated_at="2024-01-01T11:00:00Z"
        )
        
        # Should not be considered reviewed yet
        self.assertFalse(self.state.has_been_reviewed(123))
        
        # Complete the review
        self.state.record_review_completion(123, success=True)
        
        # Now should be considered reviewed
        self.assertTrue(self.state.has_been_reviewed(123))
    
    def test_needs_review_never_repeat_mode(self):
        """Test needs_review with never_repeat mode"""
        # New PR should need review
        self.assertTrue(self.state.needs_review(
            pr_number=123,
            current_commit_sha="abc123",
            pr_updated_at="2024-01-01T11:00:00Z",
            review_mode="never_repeat"
        ))
        
        # Record and complete a review
        self.state.record_review_start(123, "Test PR", "abc123", "2024-01-01T11:00:00Z")
        self.state.record_review_completion(123, success=True)
        
        # Same PR should not need review again in never_repeat mode
        self.assertFalse(self.state.needs_review(
            pr_number=123,
            current_commit_sha="abc123",
            pr_updated_at="2024-01-01T11:00:00Z",
            review_mode="never_repeat"
        ))
    
    def test_needs_review_on_updates_mode(self):
        """Test needs_review with on_updates mode"""
        # Record and complete a review
        self.state.record_review_start(123, "Test PR", "abc123", "2024-01-01T11:00:00Z")
        self.state.record_review_completion(123, success=True)
        
        # Same commit should not need review
        self.assertFalse(self.state.needs_review(
            pr_number=123,
            current_commit_sha="abc123",
            pr_updated_at="2024-01-01T11:00:00Z",
            review_mode="on_updates"
        ))
        
        # Different commit should need review
        self.assertTrue(self.state.needs_review(
            pr_number=123,
            current_commit_sha="def456",
            pr_updated_at="2024-01-01T11:00:00Z",
            review_mode="on_updates"
        ))
    
    def test_needs_review_manual_only_mode(self):
        """Test needs_review with manual_only mode"""
        # Should never need review in manual_only mode
        self.assertFalse(self.state.needs_review(
            pr_number=123,
            current_commit_sha="abc123",
            pr_updated_at="2024-01-01T11:00:00Z",
            review_mode="manual_only"
        ))
    
    def test_needs_review_failed_review(self):
        """Test needs_review after a failed review"""
        # Record a failed review
        self.state.record_review_start(123, "Test PR", "abc123", "2024-01-01T11:00:00Z")
        self.state.record_review_completion(123, success=False)
        
        # Should need review again after failure
        self.assertTrue(self.state.needs_review(
            pr_number=123,
            current_commit_sha="abc123",
            pr_updated_at="2024-01-01T11:00:00Z",
            review_mode="never_repeat"
        ))
    
    def test_get_stats(self):
        """Test getting review statistics"""
        # Add some records with different statuses
        records = [
            (123, True),   # completed
            (456, False),  # failed
            (789, True),   # completed
        ]
        
        for pr_number, success in records:
            self.state.record_review_start(pr_number, f"PR {pr_number}", "abc123", "2024-01-01T11:00:00Z")
            self.state.record_review_completion(pr_number, success)
        
        # Add one in-progress record
        self.state.record_review_start(999, "In Progress PR", "abc123", "2024-01-01T11:00:00Z")
        
        stats = self.state.get_stats()
        
        self.assertEqual(stats['total_reviews'], 4)
        self.assertEqual(stats['completed_reviews'], 2)
        self.assertEqual(stats['failed_reviews'], 1)
        self.assertEqual(stats['in_progress_reviews'], 1)


if __name__ == '__main__':
    unittest.main()