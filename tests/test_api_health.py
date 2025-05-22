#!/usr/bin/env python3
"""
Tests for the Health API module
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from knocodex.api.health import (
    get_memory_usage,
    get_cpu_usage,
    get_server_uptime,
    check_redis_health,
    check_queue_status
)

class TestHealthAPI(unittest.TestCase):
    """Tests for the Health API module"""
    
    @patch('psutil.Process')
    @patch('psutil.virtual_memory')
    def test_get_memory_usage(self, mock_virtual_memory, mock_process_class):
        """Test memory usage calculation"""
        # Mock process
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1024*1024*100, vms=1024*1024*150)
        mock_process.memory_percent.return_value = 25.5
        mock_process_class.return_value = mock_process
        
        # Mock virtual memory
        mock_virtual_memory.return_value = MagicMock(
            available=1024*1024*1024*2,  # 2GB
            total=1024*1024*1024*8       # 8GB
        )
        
        # Run the function
        result = get_memory_usage()
        
        # Check the results
        self.assertEqual(result["rss_mb"], 100.0)
        self.assertEqual(result["vms_mb"], 150.0)
        self.assertEqual(result["memory_percent"], 25.5)
        self.assertEqual(result["available_mb"], 2048.0)
        self.assertEqual(result["total_mb"], 8192.0)
    
    @patch('psutil.Process')
    @patch('psutil.cpu_percent')
    @patch('psutil.cpu_count')
    @patch('os.getloadavg')
    def test_get_cpu_usage(self, mock_getloadavg, mock_cpu_count, mock_cpu_percent, mock_process_class):
        """Test CPU usage calculation"""
        # Mock process
        mock_process = MagicMock()
        mock_process.cpu_percent.return_value = 15.5
        mock_process_class.return_value = mock_process
        
        # Mock system functions
        mock_cpu_percent.return_value = 45.2
        mock_cpu_count.return_value = 8
        mock_getloadavg.return_value = (1.2, 1.5, 1.8)
        
        # Run the function
        result = get_cpu_usage()
        
        # Check the results
        self.assertEqual(result["process_cpu_percent"], 15.5)
        self.assertEqual(result["system_cpu_percent"], 45.2)
        self.assertEqual(result["cpu_count"], 8)
        self.assertEqual(result["load_avg"], [1.2, 1.5, 1.8])
    
    def test_get_server_uptime(self):
        """Test server uptime calculation"""
        result = get_server_uptime()
        
        # Check the results
        self.assertIn("started_at", result)
        self.assertIn("uptime_seconds", result)
        self.assertIn("uptime_human", result)
        self.assertIsInstance(result["uptime_seconds"], int)
    
    def test_check_redis_health_success(self):
        """Test Redis health check success"""
        async def async_test():
            # Mock queue manager
            mock_queue_manager = MagicMock()
            mock_queue_manager.health_check.return_value = None  # No exception
            mock_queue_manager.get_redis_info.return_value = {
                "used_memory": 1024000,
                "connected_clients": 5,
                "total_commands_processed": 1000,
                "redis_version": "6.2.0"
            }
            
            # Run the health check
            result = await check_redis_health(mock_queue_manager)
            
            # Check the results
            self.assertEqual(result["status"], "healthy")
            self.assertIn("response_time_ms", result)
            self.assertAlmostEqual(result["memory_usage_mb"], 1.0, places=1)
            self.assertEqual(result["connected_clients"], 5)
            
        asyncio.run(async_test())
    
    def test_check_redis_health_failure(self):
        """Test Redis health check failure"""
        async def async_test():
            # Mock queue manager to raise exception
            mock_queue_manager = MagicMock()
            mock_queue_manager.health_check.side_effect = Exception("Connection failed")
            
            # Run the health check
            result = await check_redis_health(mock_queue_manager)
            
            # Check the results
            self.assertEqual(result["status"], "unhealthy")
            self.assertEqual(result["error"], "Connection failed")
            
        asyncio.run(async_test())
    
    def test_check_queue_status_success(self):
        """Test queue status check success"""
        async def async_test():
            # Mock queue manager
            mock_queue_manager = MagicMock()
            mock_queue_manager.get_queue_info.return_value = {
                "size": 10,
                "active": 2,
                "failed": 1,
                "completed": 50
            }
            mock_queue_manager.get_worker_info.return_value = {
                "total": 3,
                "active": 2,
                "idle": 1
            }
            
            # Run the function
            result = await check_queue_status(mock_queue_manager)
            
            # Check the results
            self.assertEqual(result["status"], "healthy")
            self.assertEqual(result["queue_size"], 10)
            self.assertEqual(result["active_jobs"], 2)
            self.assertEqual(result["total_workers"], 3)
            
        asyncio.run(async_test())
    
    def test_check_queue_status_failure(self):
        """Test queue status check failure"""
        async def async_test():
            # Mock queue manager to raise exception
            mock_queue_manager = MagicMock()
            mock_queue_manager.get_queue_info.side_effect = Exception("Queue unavailable")
            
            # Run the function
            result = await check_queue_status(mock_queue_manager)
            
            # Check the results
            self.assertEqual(result["status"], "unhealthy")
            self.assertEqual(result["error"], "Queue unavailable")
            
        asyncio.run(async_test())

if __name__ == "__main__":
    unittest.main()