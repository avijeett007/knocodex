#!/usr/bin/env python3
"""
Tests for the Metrics API module
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from knocodex.api.metrics import (
    get_system_metrics,
    get_task_statistics,
    update_metrics_for_prometheus,
    router
)

class TestMetricsAPI(unittest.TestCase):
    """Tests for the Metrics API module"""
    
    @patch('knocodex.api.metrics.WorkflowEngine')
    def test_get_system_metrics(self, mock_workflow_class):
        """Test system metrics retrieval"""
        async def async_test():
            # Mock workflow engine
            mock_workflow = MagicMock()
            
            async def mock_get_system_metrics():
                return {
                    "cpu_usage": 45.2,
                    "memory_usage": 512.5,
                    "disk_usage": 75.0,
                    "queue_size": 10,
                    "active_tasks": 3
                }
            
            mock_workflow.get_system_metrics = mock_get_system_metrics
            mock_workflow_class.return_value = mock_workflow
            
            # Run the function
            result = await get_system_metrics(workflow=mock_workflow)
            
            # Check the results
            self.assertEqual(result["cpu_usage"], 45.2)
            self.assertEqual(result["memory_usage"], 512.5)
            self.assertEqual(result["queue_size"], 10)
        
        asyncio.run(async_test())
    
    @patch('knocodex.api.metrics.WorkflowEngine')
    def test_get_task_statistics(self, mock_workflow_class):
        """Test task statistics retrieval"""
        async def async_test():
            # Mock workflow engine
            mock_workflow = MagicMock()
            
            async def mock_get_task_statistics(start_time, end_time):
                return {
                    "task_counts": {"analysis": 10, "implementation": 5},
                    "completion_times": {"avg": 45.5, "median": 40.0},
                    "success_rate": 0.85,
                    "error_distribution": {"timeout": 2, "invalid_input": 1},
                    "throughput": 12.5
                }
            
            mock_workflow.get_task_statistics = mock_get_task_statistics
            mock_workflow_class.return_value = mock_workflow
            
            # Run the function
            result = await get_task_statistics(hours=24, workflow=mock_workflow)
            
            # Check the results
            self.assertIn("time_range", result)
            self.assertEqual(result["time_range"]["hours"], 24)
            self.assertEqual(result["task_counts"]["analysis"], 10)
            self.assertEqual(result["success_rate"], 0.85)
        
        asyncio.run(async_test())
    
    @patch('knocodex.api.metrics.update_system_metrics')
    @patch('knocodex.api.metrics.update_queue_metrics')
    @patch('knocodex.api.metrics.update_redis_metrics')
    @patch('psutil.Process')
    def test_update_metrics_for_prometheus(self, mock_process, mock_redis_metrics, mock_queue_metrics, mock_system_metrics):
        """Test Prometheus metrics update"""
        async def async_test():
            # Mock workflow engine and queue manager
            mock_workflow = MagicMock()
            mock_queue_manager = MagicMock()
            
            # Mock process metrics
            mock_process_instance = MagicMock()
            mock_process_instance.memory_info.return_value.rss = 512 * 1024 * 1024  # 512 MB
            mock_process_instance.cpu_percent.return_value = 45.5
            mock_process.return_value = mock_process_instance
            
            # Mock queue info
            mock_queue_manager.get_queue_info.return_value = {
                "pending": 10,
                "processing": 5,
                "failed": 3
            }
            
            # Mock Redis info
            mock_queue_manager.get_redis_info.return_value = {
                "connected_clients": 15,
                "used_memory": 128 * 1024 * 1024  # 128 MB
            }
            
            # Run the function
            await update_metrics_for_prometheus(mock_workflow, mock_queue_manager)
            
            # Check that metrics were updated
            mock_system_metrics.assert_called_once()
            mock_queue_metrics.assert_called()
            mock_redis_metrics.assert_called_once()
        
        asyncio.run(async_test())
    
    @patch('knocodex.api.metrics.WorkflowEngine')
    def test_get_system_metrics_error(self, mock_workflow_class):
        """Test system metrics handles errors gracefully"""
        async def async_test():
            # Mock workflow engine to raise exception
            mock_workflow = MagicMock()
            mock_workflow.get_system_metrics.side_effect = Exception("Workflow engine error")
            mock_workflow_class.return_value = mock_workflow
            
            # Run the function and check it raises HTTPException
            with self.assertRaises(Exception):
                await get_system_metrics(workflow=mock_workflow)
        
        asyncio.run(async_test())
    
    @patch('knocodex.api.metrics.WorkflowEngine')
    def test_get_task_statistics_with_time_range(self, mock_workflow_class):
        """Test task statistics with custom time range"""
        async def async_test():
            # Mock workflow engine
            mock_workflow = MagicMock()
            
            async def mock_get_task_statistics(start_time, end_time):
                return {
                    "task_counts": {"analysis": 20, "implementation": 15},
                    "completion_times": {"avg": 55.5, "median": 50.0},
                    "success_rate": 0.90,
                    "error_distribution": {"timeout": 1, "network_error": 1},
                    "throughput": 15.5
                }
            
            mock_workflow.get_task_statistics = mock_get_task_statistics
            mock_workflow_class.return_value = mock_workflow
            
            # Run the function with 48 hours
            result = await get_task_statistics(hours=48, workflow=mock_workflow)
            
            # Check the results
            self.assertEqual(result["time_range"]["hours"], 48)
            self.assertEqual(result["task_counts"]["analysis"], 20)
            self.assertEqual(result["success_rate"], 0.90)
        
        asyncio.run(async_test())
    
    def test_update_metrics_error_handling(self):
        """Test metrics update handles errors gracefully"""
        async def async_test():
            # Mock workflow engine and queue manager that raise errors
            mock_workflow = MagicMock()
            mock_queue_manager = MagicMock()
            mock_queue_manager.get_queue_info.side_effect = Exception("Queue error")
            
            # Run the function - should not raise exception
            try:
                await update_metrics_for_prometheus(mock_workflow, mock_queue_manager)
            except Exception as e:
                self.fail(f"update_metrics_for_prometheus raised exception: {e}")
        
        asyncio.run(async_test())

if __name__ == "__main__":
    unittest.main()