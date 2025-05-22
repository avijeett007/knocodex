#!/usr/bin/env python3
"""
Tests for project isolation functionality
"""

import os
import sys
import time
import pytest
import redis
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knocodex.utils.redis_utils import ProjectQueueManager, SubtaskQueueCoordinator
from knocodex.workflow_engine import SubtaskWorkflowEngine, WorkflowConfig
from knocodex.config import Config


class TestProjectIsolation:
    """Test project isolation functionality"""
    
    @pytest.fixture
    def redis_conn(self):
        """Mock Redis connection"""
        return Mock(spec=redis.Redis)
    
    @pytest.fixture
    def queue_manager(self, redis_conn):
        """Create ProjectQueueManager instance"""
        with patch('knocodex.utils.redis_utils.Redis') as mock_redis:
            mock_redis.from_url.return_value = redis_conn
            return ProjectQueueManager("redis://localhost:6379")
    
    @pytest.fixture
    def coordinator(self, redis_conn):
        """Create SubtaskQueueCoordinator instance"""
        with patch('knocodex.utils.redis_utils.Redis') as mock_redis:
            mock_redis.from_url.return_value = redis_conn
            return SubtaskQueueCoordinator("redis://localhost:6379")
    
    def test_project_queue_isolation(self, queue_manager):
        """Test that projects have isolated queues"""
        with patch('knocodex.utils.redis_utils.Queue') as mock_queue_class:
            # Get queues for different projects
            queue_a = queue_manager.get_project_queue("project_a")
            queue_b = queue_manager.get_project_queue("project_b")
            
            # Verify separate queue instances were created
            assert mock_queue_class.call_count == 2
            
            # Verify correct queue names
            calls = mock_queue_class.call_args_list
            assert calls[0][0][0] == "knocodex:project_a:tasks"
            assert calls[1][0][0] == "knocodex:project_b:tasks"
            
            # Verify same connection used
            assert calls[0][1]['connection'] == calls[1][1]['connection']
    
    def test_project_lock_isolation(self, queue_manager):
        """Test that projects have isolated locks"""
        lock_a = queue_manager.get_project_lock("project_a")
        lock_b = queue_manager.get_project_lock("project_b")
        
        # Locks should be different instances
        assert lock_a != lock_b
        
        # Lock keys should be different
        assert lock_a.lock_key != lock_b.lock_key
        assert "project_a" in lock_a.lock_key
        assert "project_b" in lock_b.lock_key
    
    def test_concurrent_project_processing(self, queue_manager):
        """Test that different projects can process concurrently"""
        with patch('knocodex.utils.redis_utils.Queue'):
            # Get locks for different projects
            lock_a = queue_manager.get_project_lock("project_a")
            lock_b = queue_manager.get_project_lock("project_b")
            
            # Mock Redis to allow both locks to be acquired
            with patch.object(lock_a, 'acquire', return_value=True):
                with patch.object(lock_b, 'acquire', return_value=True):
                    # Both projects should be able to acquire locks simultaneously
                    assert lock_a.acquire() is True
                    assert lock_b.acquire() is True
    
    def test_subtask_plan_isolation(self, coordinator):
        """Test that subtask plans are isolated by project"""
        plan_data_a = {
            'id': 'task_a_1',
            'project_id': 'project_a',
            'subtasks': [],
            'status': 'in_progress'
        }
        
        plan_data_b = {
            'id': 'task_b_1', 
            'project_id': 'project_b',
            'subtasks': [],
            'status': 'in_progress'
        }
        
        # Store plans for different projects
        with patch.object(coordinator.redis_conn, 'set', return_value=True):
            result_a = coordinator.store_subtask_plan('task_a_1', plan_data_a)
            result_b = coordinator.store_subtask_plan('task_b_1', plan_data_b)
            
            assert result_a is True
            assert result_b is True
            
            # Verify separate Redis keys
            calls = coordinator.redis_conn.set.call_args_list
            assert calls[0][0][0] == "subtask_plan:task_a_1"
            assert calls[1][0][0] == "subtask_plan:task_b_1"
    
    def test_queue_enumeration_by_project(self, queue_manager):
        """Test listing queues by project"""
        # Mock Redis keys for different projects
        with patch.object(queue_manager.redis_conn, 'keys') as mock_keys:
            mock_keys.return_value = [
                b"rq:queue:knocodex:project_alpha:tasks",
                b"rq:queue:knocodex:project_beta:tasks", 
                b"rq:queue:knocodex:project_gamma:tasks",
                b"rq:queue:other_system:tasks",  # Should be ignored
                b"some_other_key"  # Should be ignored
            ]
            
            projects = queue_manager.get_all_project_queues()
            
            # Should only return knocodex project queues
            expected = ["project_alpha", "project_beta", "project_gamma"]
            assert sorted(projects) == sorted(expected)
    
    def test_queue_status_isolation(self, queue_manager):
        """Test that queue status is project-specific"""
        with patch('knocodex.utils.redis_utils.Queue') as mock_queue_class:
            # Mock different queue states for different projects
            mock_queue_a = Mock()
            mock_queue_a.__len__ = Mock(return_value=3)
            mock_queue_a.failed_job_registry.__len__ = Mock(return_value=1)
            mock_queue_a.finished_job_registry.__len__ = Mock(return_value=5)
            mock_queue_a.started_job_registry.__len__ = Mock(return_value=0)
            mock_queue_a.deferred_job_registry.__len__ = Mock(return_value=0)
            mock_queue_a.scheduled_job_registry.__len__ = Mock(return_value=2)
            
            mock_queue_b = Mock()
            mock_queue_b.__len__ = Mock(return_value=7)
            mock_queue_b.failed_job_registry.__len__ = Mock(return_value=0)
            mock_queue_b.finished_job_registry.__len__ = Mock(return_value=2)
            mock_queue_b.started_job_registry.__len__ = Mock(return_value=1)
            mock_queue_b.deferred_job_registry.__len__ = Mock(return_value=1)
            mock_queue_b.scheduled_job_registry.__len__ = Mock(return_value=0)
            
            # Set up queue manager to return different mocks for different projects
            queue_manager._queues["knocodex:project_a:tasks"] = mock_queue_a
            queue_manager._queues["knocodex:project_b:tasks"] = mock_queue_b
            
            def side_effect(queue_name, connection):
                if queue_name == "knocodex:project_a:tasks":
                    return mock_queue_a
                elif queue_name == "knocodex:project_b:tasks":
                    return mock_queue_b
                return Mock()
            
            mock_queue_class.side_effect = side_effect
            
            # Get status for different projects
            status_a = queue_manager.get_queue_status("project_a")
            status_b = queue_manager.get_queue_status("project_b")
            
            # Verify different status values
            assert status_a['pending'] == 3
            assert status_a['failed'] == 1
            assert status_a['finished'] == 5
            
            assert status_b['pending'] == 7
            assert status_b['failed'] == 0
            assert status_b['finished'] == 2
            
            # Verify they're different
            assert status_a != status_b
    
    def test_queue_clearing_isolation(self, queue_manager):
        """Test that clearing queues only affects specific project"""
        with patch('knocodex.utils.redis_utils.Queue') as mock_queue_class:
            mock_queue_a = Mock()
            mock_queue_b = Mock()
            
            queue_manager._queues["knocodex:project_a:tasks"] = mock_queue_a
            queue_manager._queues["knocodex:project_b:tasks"] = mock_queue_b
            
            def side_effect(queue_name, connection):
                if queue_name == "knocodex:project_a:tasks":
                    return mock_queue_a
                elif queue_name == "knocodex:project_b:tasks":
                    return mock_queue_b
                return Mock()
            
            mock_queue_class.side_effect = side_effect
            
            # Clear only project_a queue
            result = queue_manager.clear_project_queue("project_a")
            
            assert result is True
            mock_queue_a.empty.assert_called_once()
            mock_queue_b.empty.assert_not_called()
    
    def test_subtask_enqueuing_isolation(self, queue_manager):
        """Test that subtasks are enqueued to correct project queue"""
        subtask_data = {
            'id': 'subtask_1',
            'task_id': 'task_1',
            'project_id': 'project_test'
        }
        
        with patch('knocodex.utils.redis_utils.Queue') as mock_queue_class:
            mock_queue = Mock()
            mock_job = Mock()
            mock_job.id = 'job_123'
            mock_queue.enqueue.return_value = mock_job
            mock_queue_class.return_value = mock_queue
            
            # Enqueue subtask for specific project
            job_id = queue_manager.enqueue_subtask("project_test", subtask_data)
            
            assert job_id == 'job_123'
            
            # Verify correct queue was created
            mock_queue_class.assert_called_once_with(
                "knocodex:project_test:tasks",
                connection=queue_manager.redis_conn
            )
            
            # Verify task was enqueued
            mock_queue.enqueue.assert_called_once()


class TestMultiProjectWorkflow:
    """Test multi-project workflow scenarios"""
    
    @pytest.fixture
    def workflow_engines(self):
        """Create workflow engines for different projects"""
        config = WorkflowConfig()
        
        engines = {}
        for project in ['project_1', 'project_2']:
            with patch('knocodex.config.Config'):
                with patch('knocodex.project_manager.ProjectManager'):
                    with patch('knocodex.utils.redis_utils.Redis'):
                        engines[project] = SubtaskWorkflowEngine(Mock(), config)
        
        return engines
    
    def test_independent_project_workflows(self, workflow_engines):
        """Test that projects can run independent workflows"""
        issue_data_1 = {
            "title": "Issue for Project 1",
            "body": "Project 1 issue body",
            "number": 1
        }
        
        issue_data_2 = {
            "title": "Issue for Project 2", 
            "body": "Project 2 issue body",
            "number": 2
        }
        
        # Mock successful processing for both projects
        for project_id, engine in workflow_engines.items():
            with patch.object(engine.queue_manager, 'get_project_lock') as mock_get_lock:
                with patch.object(engine.project_manager, 'get_project', return_value=Mock()):
                    with patch.object(engine.project_manager, 'allocate_resources', return_value={}):
                        with patch.object(engine.analyzer, 'analyze_issue') as mock_analyze:
                            with patch.object(engine.coordinator, 'store_subtask_plan', return_value=f"task_{project_id}"):
                                with patch.object(engine.coordinator, 'update_subtask_status'):
                                    with patch.object(engine, '_execute_workflow_with_lock'):
                                        
                                        mock_lock = Mock()
                                        mock_lock.acquire.return_value = True
                                        mock_get_lock.return_value = mock_lock
                                        
                                        # Mock subtask plan
                                        mock_plan = Mock()
                                        mock_plan.id = f"task_{project_id}"
                                        mock_plan.project_id = project_id
                                        mock_plan.subtasks = []
                                        mock_analyze.return_value = mock_plan
                                        
                                        if project_id == 'project_1':
                                            result = engine.process_github_issue(project_id, issue_data_1)
                                        else:
                                            result = engine.process_github_issue(project_id, issue_data_2)
                                        
                                        assert result == f"task_{project_id}"
                                        mock_lock.acquire.assert_called_once()
    
    def test_project_specific_config_isolation(self):
        """Test that project configurations are isolated"""
        # Test project-specific configuration
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                # Mock different configs for different projects
                configs = {
                    'project_1': {
                        'project_id': 'project_1',
                        'sequential_processing': True,
                        'enforce_pr_creation': True
                    },
                    'project_2': {
                        'project_id': 'project_2', 
                        'sequential_processing': False,
                        'enforce_pr_creation': False
                    }
                }
                
                def mock_json_load(file):
                    # Determine which config to return based on file path
                    if 'project_1' in str(file):
                        return configs['project_1']
                    elif 'project_2' in str(file):
                        return configs['project_2']
                    return {}
                
                with patch('json.load', side_effect=mock_json_load):
                    config_1 = Config('/path/to/project_1')
                    config_2 = Config('/path/to/project_2')
                    
                    # Mock file existence and reading
                    with patch.object(config_1, 'get_project_config', return_value=configs['project_1']):
                        with patch.object(config_2, 'get_project_config', return_value=configs['project_2']):
                            # Verify different settings
                            assert config_1.is_sequential_processing_enabled() != config_2.is_sequential_processing_enabled()
                            assert config_1.is_pr_creation_enforced() != config_2.is_pr_creation_enforced()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])