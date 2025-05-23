#!/usr/bin/env python3
"""
Tests for the Prometheus utilities module
"""

import unittest
from unittest.mock import patch, MagicMock

from knocodex.utils.prometheus import (
    record_task_metrics,
    record_api_metrics,
    record_sse_connection,
    get_prometheus_metrics,
    get_metrics_content_type
)

class TestPrometheusUtils(unittest.TestCase):
    """Tests for the Prometheus utilities module"""
    
    @patch('knocodex.utils.prometheus.task_counter')
    @patch('knocodex.utils.prometheus.task_duration')
    def test_record_task_metrics(self, mock_duration, mock_counter):
        """Test recording task metrics"""
        # Mock metric instances
        mock_counter_labels = MagicMock()
        mock_duration_labels = MagicMock()
        mock_counter.labels.return_value = mock_counter_labels
        mock_duration.labels.return_value = mock_duration_labels
        
        # Record task metrics
        record_task_metrics("project1", "analysis", "completed", 30.5)
        
        # Verify counter was incremented
        mock_counter.labels.assert_called_with(
            project_id="project1", task_type="analysis", status="completed"
        )
        mock_counter_labels.inc.assert_called_once()
        
        # Verify duration was observed
        mock_duration.labels.assert_called_with(
            project_id="project1", task_type="analysis"
        )
        mock_duration_labels.observe.assert_called_with(30.5)
    
    @patch('knocodex.utils.prometheus.api_requests')
    @patch('knocodex.utils.prometheus.api_duration')
    def test_record_api_request(self, mock_duration, mock_requests):
        """Test recording API request metrics"""
        # Mock metric instances
        mock_requests_labels = MagicMock()
        mock_duration_labels = MagicMock()
        mock_requests.labels.return_value = mock_requests_labels
        mock_duration.labels.return_value = mock_duration_labels
        
        # Record API request
        record_api_metrics("GET", "/health", 200, 0.05)
        
        # Verify counter was incremented
        mock_requests.labels.assert_called_with(
            method="GET", endpoint="/health", status_code=200
        )
        mock_requests_labels.inc.assert_called_once()
        
        # Verify duration was observed
        mock_duration.labels.assert_called_with(
            method="GET", endpoint="/health"
        )
        mock_duration_labels.observe.assert_called_with(0.05)
    
    @patch('knocodex.utils.prometheus.sse_connections')
    def test_record_sse_connection(self, mock_connections):
        """Test recording SSE connection metrics"""
        # Mock gauge instance
        mock_gauge_labels = MagicMock()
        mock_connections.labels.return_value = mock_gauge_labels
        
        # Record SSE connection
        record_sse_connection("tasks", True)
        
        # Verify gauge was incremented
        mock_connections.labels.assert_called_with(event_type="tasks")
        mock_gauge_labels.inc.assert_called_once()
        
        # Test disconnection
        record_sse_connection("tasks", False)
        mock_gauge_labels.dec.assert_called_once()
    
    @patch('knocodex.utils.prometheus.generate_latest')
    @patch('knocodex.utils.prometheus.CONTENT_TYPE_LATEST', "text/plain; version=0.0.4; charset=utf-8")
    def test_get_prometheus_metrics(self, mock_generate):
        """Test getting Prometheus metrics"""
        # Mock prometheus client
        mock_generate.return_value = b"# Prometheus metrics data"
        
        # Get metrics
        content = get_prometheus_metrics()
        content_type = get_metrics_content_type()
        
        # Verify results
        self.assertEqual(content, b"# Prometheus metrics data")
        self.assertEqual(content_type, "text/plain; version=0.0.4; charset=utf-8")
    
    @patch('knocodex.utils.prometheus.task_counter')
    def test_record_task_metrics_error_handling(self, mock_counter):
        """Test task metrics recording handles errors gracefully"""
        # Mock counter to raise exception
        mock_counter.labels.side_effect = Exception("Prometheus error")
        
        # Should not raise exception (metrics errors should be silent)
        try:
            record_task_metrics("project1", "analysis", "completed", 30.5)
        except Exception:
            self.fail("record_task_metrics should handle errors gracefully")
    
    @patch('knocodex.utils.prometheus.api_requests')
    @patch('knocodex.utils.prometheus.api_duration')
    def test_record_api_request_with_none_values(self, mock_duration, mock_requests):
        """Test API request recording with None values"""
        # Mock metric instances
        mock_requests_labels = MagicMock()
        mock_duration_labels = MagicMock()
        mock_requests.labels.return_value = mock_requests_labels
        mock_duration.labels.return_value = mock_duration_labels
        
        # Record API request with None duration (should not call observe)
        record_api_metrics("GET", "/health", 200, None)
        
        # Verify counter was incremented but duration was not observed
        mock_requests.labels.assert_called_with(
            method="GET", endpoint="/health", status_code=200
        )
        mock_requests_labels.inc.assert_called_once()
        
        # Duration should not be observed when None
        mock_duration_labels.observe.assert_not_called()

if __name__ == "__main__":
    unittest.main()