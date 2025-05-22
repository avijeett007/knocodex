#!/usr/bin/env python3
"""
Test PR polling deduplication functionality
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from knocodex.utils.gh_utils import (
    get_pr_review_metadata,
    has_knocodex_review,
    filter_prs_for_review
)
from knocodex.models.pr_review_state import PRReviewState


class TestPRMetadataExtraction(unittest.TestCase):
    """Test PR metadata extraction functions"""
    
    def test_get_pr_review_metadata(self):
        """Test extracting metadata from PR data"""
        pr_data = {
            'number': 123,
            'title': 'Test PR',
            'headRefOid': 'abc123def456',
            'updatedAt': '2024-01-01T12:00:00Z',
            'createdAt': '2024-01-01T10:00:00Z',
            'reviews': [{'author': {'login': 'reviewer1'}}]
        }
        
        metadata = get_pr_review_metadata(pr_data)
        
        self.assertEqual(metadata['pr_number'], 123)
        self.assertEqual(metadata['pr_title'], 'Test PR')
        self.assertEqual(metadata['commit_sha'], 'abc123def456')
        self.assertEqual(metadata['updated_at'], '2024-01-01T12:00:00Z')
        self.assertTrue(metadata['has_reviews'])
    
    def test_get_pr_review_metadata_missing_fields(self):
        """Test metadata extraction with missing fields"""
        pr_data = {
            'number': 123
        }
        
        metadata = get_pr_review_metadata(pr_data)
        
        self.assertEqual(metadata['pr_number'], 123)
        self.assertEqual(metadata['pr_title'], '')
        self.assertEqual(metadata['commit_sha'], '')
        self.assertEqual(metadata['updated_at'], '')
        self.assertFalse(metadata['has_reviews'])
    
    def test_has_knocodex_review_no_reviews(self):
        """Test knocodex review detection with no reviews"""
        pr_data = {'reviews': []}
        
        self.assertFalse(has_knocodex_review(pr_data))
    
    def test_has_knocodex_review_found(self):
        """Test knocodex review detection when found"""
        pr_data = {
            'reviews': [
                {
                    'author': {'login': 'github-actions[bot]'},
                    'body': 'This is an automated review by knocodex'
                }
            ]
        }
        
        self.assertTrue(has_knocodex_review(pr_data))
    
    def test_has_knocodex_review_different_bot(self):
        """Test knocodex review detection with different bot"""
        pr_data = {
            'reviews': [
                {
                    'author': {'login': 'some-other-bot'},
                    'body': 'This is a review by another bot'
                }
            ]
        }
        
        self.assertFalse(has_knocodex_review(pr_data))


class TestPRFiltering(unittest.TestCase):
    """Test PR filtering for review"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "test_pr_state.json")
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_filter_prs_no_state_tracking(self):
        """Test PR filtering without state tracking"""
        prs_data = [
            {
                'number': 123,
                'title': 'PR without reviews',
                'reviews': []
            },
            {
                'number': 456,
                'title': 'PR with reviews',
                'reviews': [{'author': {'login': 'reviewer1'}}]
            }
        ]
        
        filtered = filter_prs_for_review(prs_data)
        
        # Should only return PR without reviews
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['number'], 123)
    
    def test_filter_prs_with_state_tracking_never_repeat(self):
        """Test PR filtering with state tracking in never_repeat mode"""
        pr_review_state = PRReviewState(self.storage_path)
        
        # Record a completed review for PR 123
        pr_review_state.record_review_start(123, "Test PR", "abc123", "2024-01-01T11:00:00Z")
        pr_review_state.record_review_completion(123, success=True)
        
        prs_data = [
            {
                'number': 123,
                'title': 'Already reviewed PR',
                'headRefOid': 'abc123',
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            },
            {
                'number': 456,
                'title': 'New PR',
                'headRefOid': 'def456',
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            }
        ]
        
        filtered = filter_prs_for_review(
            prs_data, 
            pr_review_state=pr_review_state,
            review_mode="never_repeat"
        )
        
        # Should only return new PR
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['number'], 456)
    
    def test_filter_prs_with_state_tracking_on_updates(self):
        """Test PR filtering with state tracking in on_updates mode"""
        pr_review_state = PRReviewState(self.storage_path)
        
        # Record a completed review for PR 123
        pr_review_state.record_review_start(123, "Test PR", "abc123", "2024-01-01T11:00:00Z")
        pr_review_state.record_review_completion(123, success=True)
        
        prs_data = [
            {
                'number': 123,
                'title': 'PR with same commit',
                'headRefOid': 'abc123',
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            },
            {
                'number': 123,
                'title': 'PR with updated commit',
                'headRefOid': 'xyz789',  # Different commit
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            },
            {
                'number': 456,
                'title': 'New PR',
                'headRefOid': 'def456',
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            }
        ]
        
        # Test with same commit (should be filtered out)
        filtered = filter_prs_for_review(
            prs_data[:1], 
            pr_review_state=pr_review_state,
            review_mode="on_updates"
        )
        self.assertEqual(len(filtered), 0)
        
        # Test with updated commit (should be included)
        filtered = filter_prs_for_review(
            prs_data[1:2], 
            pr_review_state=pr_review_state,
            review_mode="on_updates"
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['headRefOid'], 'xyz789')
        
        # Test with new PR (should be included)
        filtered = filter_prs_for_review(
            prs_data[2:], 
            pr_review_state=pr_review_state,
            review_mode="on_updates"
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['number'], 456)
    
    def test_filter_prs_manual_only_mode(self):
        """Test PR filtering in manual_only mode"""
        pr_review_state = PRReviewState(self.storage_path)
        
        prs_data = [
            {
                'number': 123,
                'title': 'PR in manual mode',
                'headRefOid': 'abc123',
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            }
        ]
        
        filtered = filter_prs_for_review(
            prs_data, 
            pr_review_state=pr_review_state,
            review_mode="manual_only"
        )
        
        # Should return empty in manual_only mode
        self.assertEqual(len(filtered), 0)
    
    def test_filter_prs_with_existing_reviews(self):
        """Test that PRs with existing reviews are always filtered out"""
        pr_review_state = PRReviewState(self.storage_path)
        
        prs_data = [
            {
                'number': 123,
                'title': 'PR with GitHub reviews',
                'headRefOid': 'abc123',
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': [{'author': {'login': 'human-reviewer'}}]
            }
        ]
        
        filtered = filter_prs_for_review(
            prs_data, 
            pr_review_state=pr_review_state,
            review_mode="never_repeat"
        )
        
        # Should be filtered out due to existing reviews
        self.assertEqual(len(filtered), 0)


class TestPRStateIntegration(unittest.TestCase):
    """Test integration of PR state with filtering logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "test_pr_state.json")
        self.pr_review_state = PRReviewState(self.storage_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow_simulation(self):
        """Test a full workflow simulation"""
        # Simulate first polling cycle - should find 2 PRs to review
        prs_cycle1 = [
            {
                'number': 123,
                'title': 'New Feature PR',
                'headRefOid': 'abc123',
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            },
            {
                'number': 456,
                'title': 'Bug Fix PR',
                'headRefOid': 'def456',
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            }
        ]
        
        filtered = filter_prs_for_review(
            prs_cycle1,
            pr_review_state=self.pr_review_state,
            review_mode="never_repeat"
        )
        
        self.assertEqual(len(filtered), 2)
        
        # Simulate processing the PRs
        for pr in filtered:
            pr_number = pr['number']
            commit_sha = pr['headRefOid']
            updated_at = pr['updatedAt']
            
            self.pr_review_state.record_review_start(
                pr_number, pr['title'], commit_sha, updated_at
            )
            self.pr_review_state.record_review_completion(pr_number, success=True)
        
        # Simulate second polling cycle - should find no new PRs to review
        prs_cycle2 = prs_cycle1  # Same PRs
        
        filtered = filter_prs_for_review(
            prs_cycle2,
            pr_review_state=self.pr_review_state,
            review_mode="never_repeat"
        )
        
        self.assertEqual(len(filtered), 0)
        
        # Simulate third polling cycle with updated PR - should find 1 PR in on_updates mode
        prs_cycle3 = [
            {
                'number': 123,
                'title': 'New Feature PR',
                'headRefOid': 'abc456',  # Updated commit
                'updatedAt': '2024-01-01T12:00:00Z',
                'reviews': []
            },
            {
                'number': 456,
                'title': 'Bug Fix PR',
                'headRefOid': 'def456',  # Same commit
                'updatedAt': '2024-01-01T11:00:00Z',
                'reviews': []
            }
        ]
        
        filtered = filter_prs_for_review(
            prs_cycle3,
            pr_review_state=self.pr_review_state,
            review_mode="on_updates"
        )
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['number'], 123)
        self.assertEqual(filtered[0]['headRefOid'], 'abc456')


if __name__ == '__main__':
    unittest.main()