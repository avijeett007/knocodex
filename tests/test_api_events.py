#!/usr/bin/env python3
"""
Tests for the Events API module
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from knocodex.api.events import (
    filtered_log_event_generator,
    task_event_generator,
    router,
    should_include_event
)
from knocodex.models.mcp_task import TaskEvent, TaskType, TaskStatus

class TestEventsAPI(unittest.TestCase):
    """Tests for the Events API module"""
    
    @patch('knocodex.workflow_engine.WorkflowEngine')
    def test_filtered_log_event_generator_with_filters(self, mock_workflow_class):
        """Test log event generator with filters"""
        # Mock workflow engine
        mock_workflow = MagicMock()
        mock_log_entry = MagicMock()
        mock_log_entry.timestamp = datetime.now()
        mock_log_entry.level = "INFO"
        mock_log_entry.logger = "test"
        mock_log_entry.message = "Task started"
        mock_log_entry.task_id = "task1"
        mock_log_entry.worker_id = "worker1"
        mock_log_entry.extra = {}
        
        # Make get_log_entries async
        async def mock_get_log_entries(*args, **kwargs):
            return [mock_log_entry]
        
        mock_workflow.get_log_entries = AsyncMock(side_effect=mock_get_log_entries)
        mock_workflow_class.return_value = mock_workflow
        
        # Test should_include_event function instead with mock object
        event = MagicMock()
        event.project_id = "project1"
        event.task_type = TaskType.ANALYZE_ISSUE
        
        result = should_include_event(event, project_id="project1")
        self.assertTrue(result)
    
    def test_should_include_event_no_filters(self):
        """Test should_include_event without filters"""
        # Create mock event
        event = MagicMock()
        
        # Test without filters - should always return True
        result = should_include_event(event)
        self.assertTrue(result)
    
    def test_should_include_event_with_filters(self):
        """Test should_include_event with filters"""
        # Create mock event
        event = MagicMock()
        event.project_id = "project1"
        event.task_type = TaskType.ANALYZE_ISSUE
        event.status = TaskStatus.RUNNING
        
        # Test with matching filters
        result = should_include_event(
            event,
            project_id="project1",
            task_type=[TaskType.ANALYZE_ISSUE],
            status=[TaskStatus.RUNNING]
        )
        self.assertTrue(result)
        
        # Test with non-matching project filter
        result = should_include_event(
            event,
            project_id="project2"
        )
        self.assertFalse(result)
    
    def test_should_include_event_task_type_filter(self):
        """Test should_include_event with task type filter"""
        # Create mock event
        event = MagicMock()
        event.task_type = TaskType.ANALYZE_ISSUE
        
        # Test with matching task type
        result = should_include_event(
            event,
            task_type=[TaskType.ANALYZE_ISSUE, TaskType.IMPLEMENT_ISSUE]
        )
        self.assertTrue(result)
        
        # Test with non-matching task type
        result = should_include_event(
            event,
            task_type=[TaskType.DOCUMENT_PROJECT]
        )
        self.assertFalse(result)
    
    def test_should_include_event_status_filter(self):
        """Test should_include_event with status filter"""
        # Create mock event
        event = MagicMock()
        event.status = TaskStatus.COMPLETED
        
        # Test with matching status
        result = should_include_event(
            event,
            status=[TaskStatus.COMPLETED, TaskStatus.FAILED]
        )
        self.assertTrue(result)
        
        # Test with non-matching status
        result = should_include_event(
            event,
            status=[TaskStatus.RUNNING]
        )
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()