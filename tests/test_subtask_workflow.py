#!/usr/bin/env python3
"""
Tests for the subtask workflow system
"""

import os
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import redis
from redis import Redis

from knocodex.config import Config
from knocodex.project_manager import ProjectManager, ProjectConfig
from knocodex.workflow_engine import SubtaskWorkflowEngine, WorkflowConfig
from knocodex.models.subtask import Subtask, SubtaskStatus, SubtaskType, SubtaskPlan
from knocodex.utils.redis_utils import SubtaskQueueCoordinator


class TestSubtaskWorkflow(unittest.TestCase):
    """Tests for the subtask workflow system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name)
        
        # Create project structure
        self.knocodex_dir = self.project_path / ".knocodex"
        self.knocodex_dir.mkdir(exist_ok=True)
        
        # Create a mock Redis client
        self.redis_mock = MagicMock(spec=Redis)
        
        # Create config
        self.config = Config(self.project_path)
        
        # Create project manager with mock Redis
        self.project_manager = ProjectManager(self.config, self.redis_mock)
        
        # Create workflow engine with mock Redis
        self.workflow_config = WorkflowConfig(
            max_parallel_subtasks=3,
            dependency_timeout_minutes=60,
            retry_attempts=2
        )
        self.workflow_engine = SubtaskWorkflowEngine(self.redis_mock, self.workflow_config)
        
        # Mock the SubtaskQueueCoordinator
        self.coordinator_mock = MagicMock(spec=SubtaskQueueCoordinator)
        self.workflow_engine.coordinator = self.coordinator_mock
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_create_project(self):
        """Test creating a project"""
        # Mock redis client responses for project creation
        self.redis_mock.exists.return_value = False
        
        # Create a test project
        name = "Test Project"
        repo_url = "https://github.com/test/repo"
        local_path = str(self.project_path / "repo")
        github_token = "mock-token"
        labels = ["test-label"]
        
        with patch.object(self.project_manager, '_save_project_config') as mock_save:
            with patch.object(self.project_manager, '_generate_project_id') as mock_id:
                mock_id.return_value = "test-project"
                result = self.project_manager.create_project(
                    name=name,
                    repository_url=repo_url,
                    local_path=local_path,
                    github_token=github_token,
                    labels=labels
                )
                
                # Verify project was created
                self.assertEqual(result, "test-project")
                mock_save.assert_called_once()
    
    def test_process_github_issue(self):
        """Test processing a GitHub issue"""
        project_id = "test-project"
        
        # Mock issue data
        issue_data = {
            "number": 123,
            "title": "Test Issue",
            "body": "This is a test issue description",
            "labels": [{"name": "test-label"}]
        }
        
        # Mock subtask plan
        mock_plan = SubtaskPlan(
            id="test-plan-id",
            issue_number=123,
            issue_title="Test Issue",
            issue_description="This is a test issue description",
            project_name=project_id,
            branch_name="issue-123",
            subtasks=[]
        )
        
        # Setup mocks
        with patch.object(self.workflow_engine, 'analyzer') as mock_analyzer, \
             patch.object(self.workflow_engine, 'project_manager') as mock_project_manager:
            # Mock the project manager
            mock_project_manager.get_project.return_value = True
            
            # Mock the analyzer to return our test plan
            mock_analyzer.analyze_issue.return_value = mock_plan
            
            # Mock the coordinator
            self.coordinator_mock.store_subtask_plan.return_value = "task-123"
            
            # Call the method under test
            task_id = self.workflow_engine.process_github_issue(project_id, issue_data)
            
            # Verify results
            self.assertEqual(task_id, "task-123")
            mock_analyzer.analyze_issue.assert_called_once_with(issue_data)
            self.coordinator_mock.store_subtask_plan.assert_called_once()
    
    def test_handle_subtask_completion(self):
        """Test handling a completed subtask"""
        task_id = "task-123"
        subtask_id = "subtask-1"
        success = True
        result = {"output": "Completed successfully"}
        
        # Mock the coordinator to avoid store_subtask_result issue
        with patch.object(self.workflow_engine, 'coordinator') as mock_coordinator, \
             patch.object(self.workflow_engine, '_check_and_enqueue_unblocked_subtasks') as mock_check, \
             patch.object(self.workflow_engine, '_is_workflow_complete') as mock_complete, \
             patch.object(self.workflow_engine, '_handle_workflow_completion') as mock_handle:
            
            # Setup mock returns
            mock_complete.return_value = False
            
            # Call the method
            self.workflow_engine.handle_subtask_completion(task_id, subtask_id, success, result)
            
            # Verify correct methods were called
            mock_coordinator.update_subtask_status.assert_called_once_with(
                task_id, subtask_id, SubtaskStatus.COMPLETED
            )
            mock_check.assert_called_once_with(task_id)
            mock_complete.assert_called_once_with(task_id)
    
    def test_check_and_enqueue_unblocked_subtasks(self):
        """Test checking and enqueueing unblocked subtasks"""
        task_id = "task-123"
        
        # Set up mock to return ready subtasks
        ready_subtasks = ["subtask-2", "subtask-3"]
        self.coordinator_mock.get_ready_subtasks.return_value = ready_subtasks
        
        # Call the method under test
        self.workflow_engine._check_and_enqueue_unblocked_subtasks(task_id)
        
        # Verify the coordinator methods were called correctly
        self.coordinator_mock.get_ready_subtasks.assert_called_once_with(task_id)
        self.coordinator_mock.enqueue_ready_subtasks.assert_called_once_with(task_id, ready_subtasks)
    


    def test_is_workflow_complete(self):
        """Test checking if a workflow is complete"""
        task_id = "task-123"
        
        # Create a test plan with some subtasks
        subtasks = [
            Subtask(
                id="subtask-1",
                title="Task 1",
                description="Description 1",
                type=SubtaskType.ANALYSIS,
                status=SubtaskStatus.PENDING
            ),
            Subtask(
                id="subtask-2",
                title="Task 2",
                description="Description 2",
                type=SubtaskType.IMPLEMENTATION,
                status=SubtaskStatus.PENDING
            )
        ]
        
        plan = SubtaskPlan(
            id=task_id,
            issue_number=123,
            issue_title="Test Issue",
            issue_description="This is a test issue",
            project_name="test-project",
            branch_name=f"issue-{task_id}",
            subtasks=subtasks
        )
        
        # Fix for the SKIPPED value issue
        with patch('knocodex.workflow_engine.SubtaskStatus') as mock_status:
            # Create a mock for SubtaskStatus that includes SKIPPED
            mock_status.COMPLETED.value = "completed"
            mock_status.SKIPPED.value = "skipped"
            
            # Mock the coordinator and redis directly
            with patch.object(self.workflow_engine, 'coordinator') as mock_coordinator, \
                 patch.object(self.workflow_engine, 'redis') as mock_redis:
                
                # 1. Test when plan doesn't exist
                mock_coordinator.get_subtask_plan.return_value = None
                result = self.workflow_engine._is_workflow_complete(task_id)
                self.assertFalse(result)
                
                # 2. When plan exists but some subtasks are not complete
                mock_coordinator.get_subtask_plan.return_value = plan
                
                # Mock redis.get to return PENDING for subtask-1
                def mock_redis_get(key):
                    if key == f"subtask_status:{task_id}:subtask-1":
                        return "pending".encode()
                    elif key == f"subtask_status:{task_id}:subtask-2":
                        return "completed".encode()
                    return None
                    
                mock_redis.get.side_effect = mock_redis_get
                result = self.workflow_engine._is_workflow_complete(task_id)
                self.assertFalse(result)
                
                # 3. When all subtasks are complete
                def mock_redis_get_all_complete(key):
                    return "completed".encode()
                    
                mock_redis.get.side_effect = mock_redis_get_all_complete
                result = self.workflow_engine._is_workflow_complete(task_id)
                self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
