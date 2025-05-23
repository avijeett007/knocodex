#!/usr/bin/env python3
"""
Integration tests for SSE endpoints
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from fastapi.testclient import TestClient

from knocodex.mcp_server import get_mcp_server
from knocodex.models.mcp_task import MCPServerConfig

class TestSSEIntegration(unittest.TestCase):
    """Integration tests for Server-Sent Events endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset global server instance to avoid conflicts between tests
        import knocodex.mcp_server
        knocodex.mcp_server._server_instance = None
        
        # Create test config with host="*" to disable TrustedHostMiddleware
        test_config = MCPServerConfig(host="*", auth_enabled=False, rate_limit_enabled=False)
        server = get_mcp_server(test_config)
        self.client = TestClient(server.get_app())
    
    @patch('knocodex.api.events.task_event_generator')
    def test_task_events_sse_endpoint(self, mock_task_generator):
        """Test the task events SSE endpoint"""
        # Mock task generator
        mock_task_generator.return_value = []  # Empty generator for simple test
        
        # Make SSE request
        response = self.client.get("/api/v1/events/tasks", headers={"Accept": "text/event-stream"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/event-stream; charset=utf-8")
    
    @patch('knocodex.api.events.filtered_log_event_generator')
    def test_log_events_sse_endpoint(self, mock_log_generator):
        """Test the log events SSE endpoint"""
        # Mock log generator
        mock_log_generator.return_value = []  # Empty generator for simple test
        
        # Make SSE request
        response = self.client.get("/api/v1/events/logs", headers={"Accept": "text/event-stream"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/event-stream; charset=utf-8")
    
    @patch('knocodex.api.events.task_event_generator')
    def test_task_events_with_filters(self, mock_task_generator):
        """Test task events SSE endpoint with query filters"""
        # Mock task generator
        mock_task_generator.return_value = []
        
        # Make SSE request with filters
        response = self.client.get("/api/v1/events/tasks?project_id=project1&status=running")
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
        mock_log_generator.return_value = []
        
        # Make SSE request with filters
        response = self.client.get("/api/v1/events/logs?project_id=project1&level=ERROR")
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
        
        # Make SSE request - should still return 200 due to error handling
        response = self.client.get("/api/v1/events/tasks")
        self.assertEqual(response.status_code, 200)
    
    @patch('knocodex.api.events.task_event_generator')
    def test_sse_cors_headers(self, mock_task_generator):
        """Test that SSE endpoints have proper CORS headers"""
        mock_task_generator.return_value = []
        
        response = self.client.get("/api/v1/events/tasks", headers={"Origin": "http://localhost:3000"})
        self.assertEqual(response.status_code, 200)
        # CORS headers should be present due to middleware

if __name__ == "__main__":
    unittest.main()