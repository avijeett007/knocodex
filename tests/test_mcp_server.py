#!/usr/bin/env python3
"""
Tests for the MCP Server module
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from knocodex.mcp_server import get_mcp_server, MCPServer
from knocodex.models.mcp_task import MCPServerConfig

class TestMCPServer(unittest.TestCase):
    """Tests for the MCP Server module"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset global server instance to avoid conflicts between tests
        import knocodex.mcp_server
        knocodex.mcp_server._server_instance = None
        
        # Create test config with host="*" to disable TrustedHostMiddleware
        test_config = MCPServerConfig(host="*", auth_enabled=False, rate_limit_enabled=False)
        server = get_mcp_server(test_config)
        self.client = TestClient(server.get_app())
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], "Knocodex MCP Server")
        self.assertIn("version", data)
    
    @patch('knocodex.api.health.get_workflow_engine')
    @patch('knocodex.api.health.get_queue_manager')
    def test_health_endpoint(self, mock_get_queue_manager, mock_get_workflow_engine):
        """Test the basic health endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        self.assertEqual(data["service"], "knocodex-mcp-server")
    
    @patch('knocodex.api.health.get_workflow_engine')
    @patch('knocodex.api.health.get_queue_manager')
    @patch('knocodex.api.health.check_redis_health')
    @patch('knocodex.api.health.check_queue_status')
    def test_detailed_health_endpoint(self, mock_check_queue_status, mock_check_redis_health, 
                                      mock_get_queue_manager, mock_get_workflow_engine):
        """Test the detailed health endpoint"""
        # Mock workflow engine
        mock_workflow = AsyncMock()
        mock_workflow.health_check.return_value = True
        mock_get_workflow_engine.return_value = mock_workflow
        
        # Mock queue manager
        mock_queue_manager = MagicMock()
        mock_get_queue_manager.return_value = mock_queue_manager
        
        # Mock health check responses
        mock_check_redis_health.return_value = {
            "status": "healthy",
            "response_time_ms": 5.0
        }
        mock_check_queue_status.return_value = {
            "status": "healthy",
            "queue_size": 10
        }
        
        response = self.client.get("/health/detailed")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("redis", data)
        self.assertIn("queues", data)
    
    @patch('knocodex.api.health.get_workflow_engine')
    @patch('knocodex.api.health.get_queue_manager')
    def test_readiness_endpoint(self, mock_get_queue_manager, mock_get_workflow_engine):
        """Test the readiness endpoint"""
        # Mock workflow engine
        mock_workflow = AsyncMock()
        mock_workflow.health_check.return_value = None  # No exception means healthy
        mock_get_workflow_engine.return_value = mock_workflow
        
        # Mock queue manager
        mock_queue_manager = MagicMock()
        mock_queue_manager.health_check.return_value = None  # No exception means healthy
        mock_get_queue_manager.return_value = mock_queue_manager
        
        response = self.client.get("/health/readiness")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ready")
    
    def test_liveness_endpoint(self):
        """Test the liveness endpoint"""
        response = self.client.get("/health/liveness")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "alive")
        self.assertIn("uptime", data)
    
    @patch('knocodex.workflow_engine.WorkflowEngine.get_system_metrics')
    def test_metrics_endpoint(self, mock_get_system_metrics):
        """Test the metrics endpoint"""
        from knocodex.models.mcp_task import MetricsResponse
        from datetime import datetime
        
        # Mock the workflow engine's get_system_metrics method directly
        mock_metrics = MetricsResponse(
            total_tasks=100,
            active_tasks=15,
            completed_tasks=85,
            failed_tasks=5,
            queue_size=10,
            worker_count=3,
            average_task_duration=45.0,
            success_rate=85.0,
            last_updated=datetime.utcnow()
        )
        mock_get_system_metrics.return_value = mock_metrics
        
        response = self.client.get("/api/v1/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_tasks"], 100)
        self.assertEqual(data["completed_tasks"], 85)
        self.assertEqual(data["failed_tasks"], 5)
    
    @patch('knocodex.utils.redis_utils.ProjectQueueManager.get_queue_info')
    def test_queue_metrics_endpoint(self, mock_get_queue_info):
        """Test the queue metrics endpoint"""
        # Mock the queue manager's get_queue_info method directly
        mock_get_queue_info.return_value = {
            "size": 10,
            "active": 5,
            "failed": 3,
            "completed": 50,
            "workers": 2
        }
        
        response = self.client.get("/api/v1/metrics/queue")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["queue_size"], 10)
        self.assertEqual(data["active_jobs"], 5)
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = self.client.get("/", headers={"Origin": "http://localhost:3000"})
        self.assertEqual(response.status_code, 200)
        # CORS headers should be present due to middleware
    
    def test_invalid_endpoint(self):
        """Test invalid endpoint returns 404"""
        response = self.client.get("/invalid")
        self.assertEqual(response.status_code, 404)
    
    @patch('knocodex.api.integration.get_config')
    def test_integration_cli_options_endpoint(self, mock_get_config):
        """Test integration CLI options endpoint is accessible through main server"""
        from knocodex.config import Config
        
        # Mock config
        mock_config = Config({})
        mock_get_config.return_value = mock_config
        
        response = self.client.get("/api/v1/cli/options")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("commands", data)
        self.assertIn("config", data)
    
    @patch('knocodex.api.integration.get_workflow_engine')
    @patch('knocodex.api.integration.get_queue_manager')
    def test_integration_health_endpoint(self, mock_get_queue_manager, mock_get_workflow_engine):
        """Test integration health endpoint is accessible through main server"""
        # Mock workflow engine
        mock_workflow = AsyncMock()
        mock_workflow.health_check.return_value = True
        mock_get_workflow_engine.return_value = mock_workflow
        
        # Mock queue manager
        mock_queue_manager = MagicMock()
        mock_get_queue_manager.return_value = mock_queue_manager
        
        response = self.client.get("/api/v1/integration/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)

if __name__ == "__main__":
    unittest.main()