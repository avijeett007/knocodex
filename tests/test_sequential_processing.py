#!/usr/bin/env python3
"""
Tests for sequential processing and task locking functionality
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

from knocodex.utils.redis_utils import TaskLock, ProjectQueueManager, SubtaskQueueCoordinator
from knocodex.workflow_engine import SubtaskWorkflowEngine, WorkflowConfig
from knocodex.models.subtask import SubtaskStatus, SubtaskType


class TestTaskLock:
    """Test task locking functionality"""
    
    @pytest.fixture
    def redis_conn(self):
        """Mock Redis connection"""
        return Mock(spec=redis.Redis)
    
    @pytest.fixture
    def task_lock(self, redis_conn):
        """Create a TaskLock instance"""
        return TaskLock(redis_conn, "test_project", timeout=60)
    
    def test_lock_initialization(self, task_lock, redis_conn):
        """Test lock initialization"""
        assert task_lock.redis_conn == redis_conn
        assert task_lock.lock_key == "task_lock:test_project"
        assert task_lock.timeout == 60
        assert task_lock.acquired is False
    
    def test_acquire_lock_success(self, task_lock, redis_conn):
        """Test successful lock acquisition"""
        redis_conn.set.return_value = True
        
        result = task_lock.acquire()
        
        assert result is True
        assert task_lock.acquired is True
        redis_conn.set.assert_called_once_with(
            "task_lock:test_project",
            "locked",
            nx=True,
            ex=60
        )
    
    def test_acquire_lock_failure(self, task_lock, redis_conn):
        """Test failed lock acquisition"""
        redis_conn.set.return_value = False
        
        result = task_lock.acquire()
        
        assert result is False
        assert task_lock.acquired is False
    
    def test_release_lock_success(self, task_lock, redis_conn):
        """Test successful lock release"""
        task_lock.acquired = True
        redis_conn.delete.return_value = 1
        
        result = task_lock.release()
        
        assert result is True
        assert task_lock.acquired is False
        redis_conn.delete.assert_called_once_with("task_lock:test_project")
    
    def test_release_lock_not_acquired(self, task_lock):
        """Test releasing lock that wasn't acquired"""
        result = task_lock.release()
        assert result is True
    
    def test_is_locked_true(self, task_lock, redis_conn):
        """Test checking if lock is held"""
        redis_conn.exists.return_value = 1
        
        result = task_lock.is_locked()
        
        assert result is True
        redis_conn.exists.assert_called_once_with("task_lock:test_project")
    
    def test_is_locked_false(self, task_lock, redis_conn):
        """Test checking if lock is not held"""
        redis_conn.exists.return_value = 0
        
        result = task_lock.is_locked()
        
        assert result is False
    
    def test_context_manager_success(self, task_lock, redis_conn):
        """Test context manager with successful lock acquisition"""
        redis_conn.set.return_value = True
        redis_conn.delete.return_value = 1
        
        with task_lock:
            assert task_lock.acquired is True
        
        assert task_lock.acquired is False
    
    def test_context_manager_failure(self, task_lock, redis_conn):
        """Test context manager with failed lock acquisition"""
        redis_conn.set.return_value = False
        
        with pytest.raises(RuntimeError, match="Failed to acquire lock"):
            with task_lock:
                pass


class TestProjectQueueManager:
    """Test project-specific queue management"""
    
    @pytest.fixture
    def redis_conn(self):
        """Mock Redis connection"""
        return Mock(spec=redis.Redis)
    
    @pytest.fixture 
    def queue_manager(self, redis_conn):
        """Create a ProjectQueueManager instance"""
        with patch('knocodex.utils.redis_utils.Redis') as mock_redis:
            mock_redis.from_url.return_value = redis_conn
            return ProjectQueueManager("redis://localhost:6379")
    
    def test_get_project_queue(self, queue_manager):
        """Test getting project-specific queue"""
        with patch('knocodex.utils.redis_utils.Queue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue_class.return_value = mock_queue
            
            queue = queue_manager.get_project_queue("test_project")
            
            assert queue == mock_queue
            mock_queue_class.assert_called_once_with(
                "knocodex:test_project:tasks",
                connection=queue_manager.redis_conn
            )
    
    def test_get_project_lock(self, queue_manager):
        """Test getting project lock"""
        lock = queue_manager.get_project_lock("test_project")
        
        assert isinstance(lock, TaskLock)
        assert lock.lock_key == "task_lock:project:test_project:processing"
    
    def test_queue_status(self, queue_manager):
        """Test getting queue status"""
        with patch('knocodex.utils.redis_utils.Queue') as mock_queue_class:
            mock_queue = Mock()
            mock_queue.__len__ = Mock(return_value=5)
            mock_queue.failed_job_registry.__len__ = Mock(return_value=1)
            mock_queue.finished_job_registry.__len__ = Mock(return_value=3)
            mock_queue.started_job_registry.__len__ = Mock(return_value=2)
            mock_queue.deferred_job_registry.__len__ = Mock(return_value=0)
            mock_queue.scheduled_job_registry.__len__ = Mock(return_value=1)
            
            mock_queue_class.return_value = mock_queue
            queue_manager._queues["knocodex:test_project:tasks"] = mock_queue
            
            status = queue_manager.get_queue_status("test_project")
            
            expected = {
                'pending': 5,
                'failed': 1,
                'finished': 3,
                'started': 2,
                'deferred': 0,
                'scheduled': 1
            }
            assert status == expected


class TestSequentialProcessing:
    """Test sequential processing workflow"""
    
    @pytest.fixture
    def redis_conn(self):
        """Mock Redis connection"""
        return Mock(spec=redis.Redis)
    
    @pytest.fixture
    def workflow_engine(self, redis_conn):
        """Create WorkflowEngine instance"""
        config = WorkflowConfig()
        with patch('knocodex.config.Config'):
            with patch('knocodex.project_manager.ProjectManager'):
                return SubtaskWorkflowEngine(redis_conn, config)
    
    def test_concurrent_issue_processing_blocked(self, workflow_engine):
        """Test that concurrent issue processing is blocked"""
        issue_data = {
            "title": "Test Issue",
            "body": "Test issue body",
            "number": 1
        }
        
        # Mock the project lock acquisition
        with patch.object(workflow_engine.queue_manager, 'get_project_lock') as mock_get_lock:
            mock_lock = Mock()
            mock_lock.acquire.return_value = False  # Lock acquisition fails
            mock_get_lock.return_value = mock_lock
            
            # First call should fail due to lock
            with pytest.raises(RuntimeError, match="Project test_project is currently processing another task"):
                workflow_engine.process_github_issue("test_project", issue_data)
    
    def test_sequential_issue_processing_success(self, workflow_engine):
        """Test successful sequential issue processing"""
        issue_data = {
            "title": "Test Issue",
            "body": "Test issue body", 
            "number": 1
        }
        
        # Mock successful processing
        with patch.object(workflow_engine.queue_manager, 'get_project_lock') as mock_get_lock:
            with patch.object(workflow_engine.project_manager, 'get_project', return_value=Mock()):
                with patch.object(workflow_engine.project_manager, 'allocate_resources', return_value={}):
                    with patch.object(workflow_engine.analyzer, 'analyze_issue') as mock_analyze:
                        with patch.object(workflow_engine.coordinator, 'store_subtask_plan', return_value="task_123"):
                            with patch.object(workflow_engine.coordinator, 'update_subtask_status'):
                                with patch.object(workflow_engine, '_execute_workflow_with_lock'):
                                    
                                    mock_lock = Mock()
                                    mock_lock.acquire.return_value = True
                                    mock_get_lock.return_value = mock_lock
                                    
                                    # Mock subtask plan
                                    mock_plan = Mock()
                                    mock_plan.id = "task_123"
                                    mock_plan.project_id = "test_project"
                                    mock_plan.subtasks = []
                                    mock_analyze.return_value = mock_plan
                                    
                                    result = workflow_engine.process_github_issue("test_project", issue_data)
                                    
                                    assert result == "task_123"
                                    mock_lock.acquire.assert_called_once()
    
    def test_lock_cleanup_on_error(self, workflow_engine):
        """Test that project lock is released on error"""
        issue_data = {
            "title": "Test Issue",
            "body": "Test issue body",
            "number": 1
        }
        
        with patch.object(workflow_engine.queue_manager, 'get_project_lock') as mock_get_lock:
            mock_lock = Mock()
            mock_lock.acquire.return_value = True
            mock_get_lock.return_value = mock_lock
            
            # Mock an error during processing
            with patch.object(workflow_engine.project_manager, 'get_project', side_effect=Exception("Test error")):
                
                with pytest.raises(Exception, match="Test error"):
                    workflow_engine.process_github_issue("test_project", issue_data)
                
                # Lock should be released on error
                mock_lock.release.assert_called_once()


class TestProjectIsolation:
    """Test project isolation functionality"""
    
    @pytest.fixture
    def queue_manager(self):
        """Create ProjectQueueManager instance"""
        with patch('knocodex.utils.redis_utils.Redis'):
            return ProjectQueueManager("redis://localhost:6379")
    
    def test_separate_project_queues(self, queue_manager):
        """Test that different projects get separate queues"""
        with patch('knocodex.utils.redis_utils.Queue') as mock_queue_class:
            queue1 = queue_manager.get_project_queue("project1")
            queue2 = queue_manager.get_project_queue("project2")
            
            # Should create different queue names
            assert mock_queue_class.call_count == 2
            calls = mock_queue_class.call_args_list
            assert calls[0][0][0] == "knocodex:project1:tasks"
            assert calls[1][0][0] == "knocodex:project2:tasks"
    
    def test_separate_project_locks(self, queue_manager):
        """Test that different projects get separate locks"""
        lock1 = queue_manager.get_project_lock("project1")
        lock2 = queue_manager.get_project_lock("project2")
        
        assert lock1.lock_key != lock2.lock_key
        assert "project1" in lock1.lock_key
        assert "project2" in lock2.lock_key
    
    def test_project_queue_names(self, queue_manager):
        """Test project queue naming convention"""
        with patch.object(queue_manager.redis_conn, 'keys') as mock_keys:
            mock_keys.return_value = [
                b"rq:queue:knocodex:project1:tasks",
                b"rq:queue:knocodex:project2:tasks",
                b"rq:queue:other_queue"
            ]
            
            projects = queue_manager.get_all_project_queues()
            
            assert "project1" in projects
            assert "project2" in projects
            assert len(projects) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])