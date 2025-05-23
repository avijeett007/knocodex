"""
Tests for MCP integration API endpoints
"""

import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from knocodex.api.integration import router
from knocodex.models.mcp_task import TaskStatus, TaskType, TaskPriority
from knocodex.config import Config


class BaseIntegrationAPITest(unittest.TestCase):
    """Base test class with common setup"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test FastAPI app with integration router
        self.app = FastAPI()
        self.app.include_router(router, prefix="/api/v1")
        self.client = TestClient(self.app)
        
        # Mock configuration
        self.mock_config = {
            "agent_type": "claude",
            "ai_backend": "claude-code",
            "redis_url": "redis://localhost:6379",
            "github_issue_label": "knocodx",
            "claude_code_path": "/usr/local/bin/claude-code",
            "gh_path": "/usr/local/bin/gh",
            "sequential_processing": True,
            "enforce_pr_creation": True,
            "max_parallel_subtasks": 3,
            "task_lock_timeout": 3600,
            "claude_model": "claude-3-5-sonnet-20241022",
            "mcp_server": {
                "enabled": True,
                "host": "localhost",
                "port": 8080,
                "cors_origins": ["*"],
                "auth_enabled": False,
                "max_connections": 100,
                "sse_heartbeat_interval": 30,
                "metrics_retention_days": 7,
                "rate_limit_enabled": True,
                "rate_limit_requests": 100,
                "log_level": "INFO"
            },
            "integration": {
                "enabled": True,
                "cli_commands_enabled": True,
                "stats_enabled": True,
                "health_checks_enabled": True,
                "allowed_origins": ["*"],
                "api_key_required": False,
                "api_keys": [],
                "rate_limit_per_minute": 60,
                "cache_ttl_seconds": 300
            }
        }
        
        # Mock workflow engine
        self.mock_workflow_engine = Mock()
        self.mock_workflow_engine.get_task_stats = AsyncMock(return_value={
            "total": 100,
            "pending": 5,
            "queued": 2,
            "running": 3,
            "completed": 85,
            "failed": 5,
            "cancelled": 0
        })
        self.mock_workflow_engine.get_performance_metrics = AsyncMock(return_value={
            "avg_task_duration": 45.5,
            "success_rate": 85.0,
            "throughput_per_hour": 12.5,
            "queue_wait_time": 2.3
        })
        self.mock_workflow_engine.is_healthy = AsyncMock(return_value=True)
        self.mock_workflow_engine.get_active_workflows = AsyncMock(return_value=3)
        self.mock_workflow_engine.get_pending_tasks_count = AsyncMock(return_value=5)
        
        # Mock queue manager
        self.mock_queue_manager = Mock()
        self.mock_queue_manager.get_queue_stats = AsyncMock(return_value={
            "size": 7,
            "processing": 3,
            "failed": 1,
            "retry_count": 2
        })
        self.mock_queue_manager.get_worker_stats = AsyncMock(return_value={
            "active": 3,
            "idle": 1,
            "busy": 2,
            "total": 4
        })
        self.mock_queue_manager.is_healthy = AsyncMock(return_value=True)


class TestCLIOptionsEndpoint(BaseIntegrationAPITest):
    """Tests for CLI options endpoint"""
    
    def test_get_cli_options_success(self):
        """Test successful CLI options retrieval"""
        with patch('knocodex.api.integration.get_config', return_value=self.mock_config):
            response = self.client.get("/api/v1/cli/options")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("commands", data)
        self.assertIn("options", data)
        self.assertIn("environment_variables", data)
        self.assertIn("project_structure", data)
        self.assertIn("integrations", data)
        
        # Verify specific commands
        commands = data["commands"]
        self.assertIn("analyze-github-issue", commands)
        self.assertIn("implement-github-issue", commands)
        self.assertIn("document-project", commands)
        self.assertIn("review-pull-request", commands)
        
        # Verify command structure
        analyze_cmd = commands["analyze-github-issue"]
        self.assertIn("description", analyze_cmd)
        self.assertIn("required_params", analyze_cmd)
        self.assertIn("optional_params", analyze_cmd)
        self.assertIn("issue_url", analyze_cmd["required_params"])
        
        # Verify options
        options = data["options"]
        self.assertIn("project_path", options)
        self.assertIn("agent_type", options)
        self.assertEqual(options["agent_type"]["default"], "claude")
        
        # Verify environment variables
        env_vars = data["environment_variables"]
        self.assertIn("ANTHROPIC_API_KEY", env_vars)
        self.assertIn("GITHUB_TOKEN", env_vars)
        
        # Verify project structure
        structure = data["project_structure"]
        self.assertIn("required_directories", structure)
        self.assertIn("config_files", structure)
        self.assertIn(".knocodx", structure["required_directories"])
        self.assertIn(".knocodx/config.json", structure["config_files"])


class TestStatsEndpoint(BaseIntegrationAPITest):
    """Tests for statistics summary endpoint"""
    
    def test_get_stats_summary_success(self):
        """Test successful stats retrieval"""
        with patch('knocodex.api.integration.get_workflow_engine', return_value=self.mock_workflow_engine), \
             patch('knocodx.api.integration.get_queue_manager', return_value=self.mock_queue_manager), \
             patch('psutil.cpu_percent', return_value=25.4), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('time.time', return_value=1642248600.0):
            
            # Mock system metrics
            mock_memory.return_value.percent = 68.2
            mock_disk.return_value.percent = 45.1
            
            response = self.client.get("/api/v1/stats/summary")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("timestamp", data)
        self.assertIn("tasks", data)
        self.assertIn("performance", data)
        self.assertIn("system", data)
        self.assertIn("queue", data)
        self.assertIn("workers", data)
        self.assertIn("trends", data)
        self.assertIn("alerts", data)
        
        # Verify task stats
        tasks = data["tasks"]
        self.assertEqual(tasks["total"], 100)
        self.assertEqual(tasks["pending"], 5)
        self.assertEqual(tasks["completed"], 85)
        self.assertEqual(tasks["failed"], 5)
        
        # Verify performance metrics
        performance = data["performance"]
        self.assertEqual(performance["avg_task_duration"], 45.5)
        self.assertEqual(performance["success_rate"], 85.0)
        
        # Verify system metrics
        system = data["system"]
        self.assertEqual(system["cpu_usage"], 25.4)
        self.assertEqual(system["memory_usage"], 68.2)
        self.assertEqual(system["disk_usage"], 45.1)
        
        # Verify queue stats
        queue = data["queue"]
        self.assertEqual(queue["size"], 7)
        self.assertEqual(queue["processing"], 3)
        
        # Verify worker stats
        workers = data["workers"]
        self.assertEqual(workers["active"], 3)
        self.assertEqual(workers["total"], 4)
    
    def test_get_stats_summary_with_timeframe(self):
        """Test stats retrieval with custom timeframe"""
        with patch('knocodex.api.integration.get_workflow_engine', return_value=self.mock_workflow_engine), \
             patch('knocodx.api.integration.get_queue_manager', return_value=self.mock_queue_manager), \
             patch('psutil.cpu_percent', return_value=25.4), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value.percent = 68.2
            mock_disk.return_value.percent = 45.1
            
            response = self.client.get("/api/v1/stats/summary?timeframe=1h&include_trends=false")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should still have trends even when include_trends=false (mock data)
        self.assertIn("trends", data)
    
    def test_get_stats_summary_invalid_timeframe(self):
        """Test stats retrieval with invalid timeframe"""
        response = self.client.get("/api/v1/stats/summary?timeframe=invalid")
        
        self.assertEqual(response.status_code, 422)  # Validation error


class TestIntegrationHealthEndpoint(BaseIntegrationAPITest):
    """Tests for integration health endpoint"""
    
    def test_get_integration_health_success(self):
        """Test successful health check"""
        with patch('knocodex.api.integration.get_workflow_engine', return_value=self.mock_workflow_engine), \
             patch('knocodx.api.integration.get_queue_manager', return_value=self.mock_queue_manager), \
             patch('redis.Redis') as mock_redis_class, \
             patch('time.time', return_value=1642248600.0), \
             patch('platform.platform', return_value='Darwin-23.5.0'), \
             patch('platform.node', return_value='knocodx-server'):
            
            # Mock Redis connection
            mock_redis = Mock()
            mock_redis.ping.return_value = True
            mock_redis_class.return_value = mock_redis
            
            response = self.client.get("/api/v1/integration/health")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("status", data)
        self.assertIn("timestamp", data)
        self.assertIn("services", data)
        self.assertIn("capabilities", data)
        self.assertIn("version", data)
        self.assertIn("uptime_seconds", data)
        self.assertIn("system_info", data)
        self.assertIn("integration_ready", data)
        
        # Verify overall status
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["integration_ready"])
        
        # Verify services
        services = data["services"]
        self.assertIn("redis", services)
        self.assertIn("workflow_engine", services)
        self.assertIn("claude_api", services)
        
        # Verify Redis service
        redis_service = services["redis"]
        self.assertEqual(redis_service["status"], "healthy")
        self.assertIn("response_time_ms", redis_service)
        
        # Verify workflow engine service
        workflow_service = services["workflow_engine"]
        self.assertEqual(workflow_service["status"], "healthy")
        self.assertEqual(workflow_service["active_workflows"], 3)
        self.assertEqual(workflow_service["pending_tasks"], 5)
        
        # Verify capabilities
        capabilities = data["capabilities"]
        expected_capabilities = [
            "task_management",
            "workflow_execution", 
            "sse_streaming",
            "health_monitoring",
            "metrics_collection",
            "github_integration",
            "claude_integration"
        ]
        for capability in expected_capabilities:
            self.assertIn(capability, capabilities)
        
        # Verify system info
        system_info = data["system_info"]
        self.assertIn("python_version", system_info)
        self.assertIn("fastapi_version", system_info)
        self.assertIn("platform", system_info)
        self.assertIn("hostname", system_info)
    
    def test_get_integration_health_without_details(self):
        """Test health check without detailed information"""
        with patch('knocodex.api.integration.get_workflow_engine', return_value=self.mock_workflow_engine), \
             patch('knocodx.api.integration.get_queue_manager', return_value=self.mock_queue_manager), \
             patch('redis.Redis') as mock_redis_class:
            
            mock_redis = Mock()
            mock_redis.ping.return_value = True
            mock_redis_class.return_value = mock_redis
            
            response = self.client.get("/api/v1/integration/health?include_details=false")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should still include system_info even when include_details=false
        self.assertIn("system_info", data)
    
    def test_get_integration_health_redis_failure(self):
        """Test health check with Redis failure"""
        with patch('knocodex.api.integration.get_workflow_engine', return_value=self.mock_workflow_engine), \
             patch('knocodx.api.integration.get_queue_manager', return_value=self.mock_queue_manager), \
             patch('redis.Redis') as mock_redis_class:
            
            # Mock Redis connection failure
            mock_redis = Mock()
            mock_redis.ping.side_effect = Exception("Connection failed")
            mock_redis_class.return_value = mock_redis
            
            response = self.client.get("/api/v1/integration/health")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should report unhealthy status
        self.assertEqual(data["status"], "degraded")
        self.assertFalse(data["integration_ready"])
        
        # Redis service should be marked as unhealthy
        services = data["services"]
        self.assertEqual(services["redis"]["status"], "unhealthy")
    
    def test_get_integration_health_workflow_failure(self):
        """Test health check with workflow engine failure"""
        # Create unhealthy workflow engine
        unhealthy_workflow = Mock()
        unhealthy_workflow.is_healthy = AsyncMock(return_value=False)
        unhealthy_workflow.get_active_workflows = AsyncMock(return_value=0)
        unhealthy_workflow.get_pending_tasks_count = AsyncMock(return_value=0)
        
        with patch('knocodx.api.integration.get_workflow_engine', return_value=unhealthy_workflow), \
             patch('knocodx.api.integration.get_queue_manager', return_value=self.mock_queue_manager), \
             patch('redis.Redis') as mock_redis_class:
            
            mock_redis = Mock()
            mock_redis.ping.return_value = True
            mock_redis_class.return_value = mock_redis
            
            response = self.client.get("/api/v1/integration/health")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should report degraded status
        self.assertEqual(data["status"], "degraded")
        
        # Workflow engine should be marked as unhealthy
        services = data["services"]
        self.assertEqual(services["workflow_engine"]["status"], "unhealthy")


class TestIntegrationEndpointErrors(BaseIntegrationAPITest):
    """Tests for error handling in integration endpoints"""
    
    def test_cli_options_config_error(self):
        """Test CLI options endpoint with config error"""
        with patch('knocodx.api.integration.get_config', side_effect=Exception("Config error")):
            response = self.client.get("/api/v1/cli/options")
            
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Config error", data["message"])
    
    def test_stats_summary_workflow_error(self):
        """Test stats endpoint with workflow engine error"""
        error_workflow = Mock()
        error_workflow.get_task_stats = AsyncMock(side_effect=Exception("Workflow error"))
        
        with patch('knocodx.api.integration.get_workflow_engine', return_value=error_workflow):
            response = self.client.get("/api/v1/stats/summary")
            
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Workflow error", data["message"])
    
    def test_health_check_exception(self):
        """Test health endpoint with unexpected exception"""
        with patch('knocodx.api.integration.get_workflow_engine', side_effect=Exception("Unexpected error")):
            response = self.client.get("/api/v1/integration/health")
            
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Unexpected error", data["message"])


class TestIntegrationModels(unittest.TestCase):
    """Tests for integration data models"""
    
    def test_integration_config_model(self):
        """Test IntegrationConfig model validation"""
        from knocodx.models.mcp_task import IntegrationConfig
        
        # Valid config
        config = IntegrationConfig(
            enabled=True,
            cli_commands_enabled=True,
            stats_enabled=True,
            health_checks_enabled=True,
            allowed_origins=["https://example.com"],
            api_key_required=True,
            api_keys=["key1", "key2"],
            rate_limit_per_minute=30,
            cache_ttl_seconds=600
        )
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.rate_limit_per_minute, 30)
        self.assertEqual(len(config.api_keys), 2)
    
    def test_system_stats_model(self):
        """Test SystemStats model validation"""
        from knocodx.models.mcp_task import SystemStats
        
        stats = SystemStats(
            timestamp=datetime.now(),
            tasks={"total": 100, "completed": 90},
            performance={"avg_duration": 45.5},
            system={"cpu": 25.0},
            queue={"size": 5},
            workers={"active": 3},
            trends={"completion_rate": [90, 91, 92]},
            alerts=[{"type": "warning", "message": "High load"}]
        )
        
        self.assertEqual(stats.tasks["total"], 100)
        self.assertEqual(stats.performance["avg_duration"], 45.5)
        self.assertEqual(len(stats.alerts), 1)
    
    def test_integration_health_model(self):
        """Test IntegrationHealth model validation"""
        from knocodx.models.mcp_task import IntegrationHealth
        
        health = IntegrationHealth(
            status="healthy",
            timestamp=datetime.now(),
            services={"redis": {"status": "healthy"}},
            capabilities=["task_management"],
            version="1.0.0",
            uptime_seconds=3600,
            system_info={"python": "3.11"},
            integration_ready=True
        )
        
        self.assertEqual(health.status, "healthy")
        self.assertTrue(health.integration_ready)
        self.assertEqual(len(health.capabilities), 1)
    
    def test_cli_options_model(self):
        """Test CLIOptions model validation"""
        from knocodx.models.mcp_task import CLIOptions
        
        options = CLIOptions(
            commands={"test": {"description": "Test command"}},
            options={"verbose": {"type": "boolean"}},
            environment_variables={"API_KEY": "Required"},
            project_structure={"dirs": [".knocodx"]},
            integrations={"vscode": {"extension": "knocodx"}}
        )
        
        self.assertIn("test", options.commands)
        self.assertIn("verbose", options.options)
        self.assertIn("API_KEY", options.environment_variables)


if __name__ == "__main__":
    unittest.main()