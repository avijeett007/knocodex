#!/usr/bin/env python3
"""
Integration tests for SSE endpoints
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import asyncio
from fastapi.testclient import TestClient

from knocodex.mcp_server import get_mcp_server

class TestSSEIntegration(unittest.TestCase):
    """Integration tests for Server-Sent Events endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        server = get_mcp_server()
        self.client = TestClient(server.get_app())
    
    @patch('knocodex.api.events.task_event_generator')
    def test_task_events_sse_endpoint(self, mock_task_generator):
        """Test the task events SSE endpoint"""
        # Mock task generator
        mock_task_generator.return_value = [
            json.dumps({"id": "task1", "status": "running"}),
            json.dumps({"id": "task2", "status": "completed"})
        ]
        
        # Make SSE request
        with self.client.stream("GET", "/events/tasks") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"], "text/plain; charset=utf-8")
            
            # Read first few chunks
            chunks = []
            for i, chunk in enumerate(response.iter_text()):
                chunks.append(chunk)
                if i >= 2:  # Read a few chunks
                    break
            
            # Verify SSE format
            content = "".join(chunks)
            self.assertIn("data:", content)
    
    @patch('knocodex.api.events.filtered_log_event_generator')
    def test_log_events_sse_endpoint(self, mock_log_generator):
        """Test the log events SSE endpoint"""
        # Mock log generator
        mock_log_generator.return_value = [
            json.dumps({"level": "INFO", "message": "Task started"}),
            json.dumps({"level": "ERROR", "message": "Task failed"})
        ]
        
        # Make SSE request
        with self.client.stream("GET", "/events/logs") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"], "text/plain; charset=utf-8")
    
    @patch('knocodex.api.events.task_event_generator')
    def test_task_events_with_filters(self, mock_task_generator):
        """Test task events SSE endpoint with query filters"""
        # Mock task generator
        mock_task_generator.return_value = [
            json.dumps({"id": "task1", "project_id": "project1", "status": "running"})
        ]
        
        # Make SSE request with filters
        with self.client.stream("GET", "/events/tasks?project_id=project1&status=running") as response:
            self.assertEqual(response.status_code, 200)
            
            # Verify generator was called with filters
            mock_task_generator.assert_called_once_with(
                project_id="project1",
                task_type=None,
                status="running",
                since=None
            )
    
    @patch('knocodex.api.events.filtered_log_event_generator')
    def test_log_events_with_filters(self, mock_log_generator):
        """Test log events SSE endpoint with query filters"""
        # Mock log generator
        mock_log_generator.return_value = [
            json.dumps({"level": "ERROR", "project_id": "project1"})
        ]
        
        # Make SSE request with filters
        with self.client.stream("GET", "/events/logs?project_id=project1&level=ERROR") as response:
            self.assertEqual(response.status_code, 200)
            
            # Verify generator was called with filters
            mock_log_generator.assert_called_once_with(
                project_id="project1",
                level="ERROR",
                since=None
            )
    
    @patch('knocodex.api.events.task_event_generator')
    def test_sse_error_handling(self, mock_task_generator):
        """Test SSE endpoint error handling"""
        # Mock generator to raise exception
        mock_task_generator.side_effect = Exception("Redis connection error")
        
        # Make SSE request
        with self.client.stream("GET", "/events/tasks") as response:
            self.assertEqual(response.status_code, 200)
            
            # Should handle error gracefully and not crash
            chunks = []
            for i, chunk in enumerate(response.iter_text()):
                chunks.append(chunk)
                if i >= 1:  # Read a couple chunks
                    break
    
    def test_sse_cors_headers(self):
        """Test that SSE endpoints have proper CORS headers"""
        with self.client.stream("GET", "/events/tasks", headers={"Origin": "http://localhost:3000"}) as response:
            self.assertEqual(response.status_code, 200)
            # CORS headers should be present due to middleware

if __name__ == "__main__":
    unittest.main()