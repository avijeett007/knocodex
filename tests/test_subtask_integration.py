#!/usr/bin/env python3
"""
Integration test for the subtask workflow system

This test verifies the actual functionality of the subtask workflow
rather than just testing method call patterns.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import redis
import time
from redis import Redis

from knocodex.config import Config
from knocodex.project_manager import ProjectManager, ProjectConfig
from knocodex.workflow_engine import SubtaskWorkflowEngine, WorkflowConfig
from knocodex.models.subtask import Subtask, SubtaskStatus, SubtaskType, SubtaskPlan
from knocodex.utils.redis_utils import SubtaskQueueCoordinator


class TestSubtaskIntegration(unittest.TestCase):
    """Integration test for the subtask workflow system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name)
        
        # Create project structure
        self.knocodex_dir = self.project_path / ".knocodex"
        self.knocodex_dir.mkdir(exist_ok=True)
        
        # Create an in-memory Redis for testing
        self.redis_mock = MagicMock(spec=Redis)
        
        # Mock Redis get and set operations to use a dictionary
        self.redis_storage = {}
        
        def mock_set(key, value, *args, **kwargs):
            self.redis_storage[key] = value
            return True
            
        def mock_get(key):
            if key in self.redis_storage:
                return self.redis_storage[key]
            return None
            
        def mock_exists(key):
            return key in self.redis_storage
            
        def mock_keys(pattern):
            import fnmatch
            matches = []
            for key in self.redis_storage.keys():
                if isinstance(key, bytes):
                    key_str = key.decode('utf-8')
                else:
                    key_str = str(key)
                if fnmatch.fnmatch(key_str, pattern):
                    matches.append(key)
            return matches
        
        self.redis_mock.set.side_effect = mock_set
        self.redis_mock.get.side_effect = mock_get
        self.redis_mock.exists.side_effect = mock_exists
        self.redis_mock.keys.side_effect = mock_keys
        
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
        
        # Create the SubtaskQueueCoordinator with a patched constructor
        with patch('redis.Redis.from_url', return_value=self.redis_mock):
            self.coordinator = SubtaskQueueCoordinator("redis://localhost:6379")
        
        # Set the coordinator on the workflow engine
        self.workflow_engine.coordinator = self.coordinator
        
        # Mock the queue enqueue operation to return a valid job ID
        mock_job = MagicMock()
        mock_job.id = "job-123"
        self.coordinator.queue_manager.enqueue_subtask = MagicMock(return_value="job-123")
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_end_to_end_workflow(self):
        """Test a complete subtask workflow from start to finish"""
        # Mock the GitHub operations
        with patch('subprocess.run') as mock_run, \
             patch('os.chdir') as mock_chdir:
            
            # Configure the mock to return success for any subprocess call
            mock_run.return_value = Mock(returncode=0, stdout="Success")
            
            # Step 1: Create a project
            project_id = "test-project"
            project_name = "Test Project"
            repo_url = "https://github.com/test/repo"
            local_path = str(self.project_path / "repo")
            github_token = "mock-token"
            labels = ["test-label"]
            
            # Create the project directly in the project manager
            self.project_manager.projects[project_id] = ProjectConfig(
                project_id=project_id,
                name=project_name,
                repository_url=repo_url,
                local_path=local_path,
                github_token=github_token,
                labels=labels
            )
            
            # Step 2: Create a mock issue
            issue_data = {
                "number": 123,
                "title": "Test Issue",
                "body": "This is a test issue that should be processed with subtasks",
                "labels": [{"name": "test-label"}]
            }
            
            # Step 3: Create a subtask plan for the issue
            subtasks = [
                Subtask(
                    id="subtask-1",
                    title="Analyze Issue",
                    description="Analyze the GitHub issue",
                    type=SubtaskType.ANALYSIS,
                    status=SubtaskStatus.PENDING,
                    dependencies=[]
                ),
                Subtask(
                    id="subtask-2",
                    title="Implement Feature",
                    description="Implement the requested feature",
                    type=SubtaskType.IMPLEMENTATION,
                    status=SubtaskStatus.PENDING,
                    dependencies=["subtask-1"]
                ),
                Subtask(
                    id="subtask-3",
                    title="Write Tests",
                    description="Write tests for the feature",
                    type=SubtaskType.TESTING,
                    status=SubtaskStatus.PENDING,
                    dependencies=["subtask-2"]
                ),
                Subtask(
                    id="subtask-4",
                    title="Create PR",
                    description="Create a pull request with the changes",
                    type=SubtaskType.PULL_REQUEST,
                    status=SubtaskStatus.PENDING,
                    dependencies=["subtask-3"]
                )
            ]
            
            task_id = f"task-{issue_data['number']}"
            subtask_plan = SubtaskPlan(
                id=task_id,
                issue_number=issue_data["number"],
                issue_title=issue_data["title"],
                issue_description=issue_data["body"],
                project_name=project_id,
                branch_name=f"issue-{issue_data['number']}",
                subtasks=subtasks
            )
            
            # Store the plan using the coordinator
            # Convert the SubtaskPlan to a dictionary for storage
            plan_dict = {
                "issue_number": subtask_plan.issue_number,
                "issue_title": subtask_plan.issue_title,
                "issue_description": subtask_plan.issue_description,
                "project_name": subtask_plan.project_name,
                "branch_name": subtask_plan.branch_name,
                "subtasks": [s.__dict__ for s in subtask_plan.subtasks],
                "created_at": subtask_plan.created_at.isoformat(),
                "updated_at": subtask_plan.updated_at.isoformat(),
                "status": subtask_plan.status
            }
            self.coordinator.store_subtask_plan(task_id, plan_dict)
            
            # Step 4: Initialize the workflow
            self.workflow_engine._execute_workflow(task_id, project_id)
            
            # Verify that the first subtask (with no dependencies) was enqueued
            # After enqueuing, it should change from pending to in_progress
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_1 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-1')
            self.assertEqual(subtask_1['status'], SubtaskStatus.IN_PROGRESS.value)
            
            # Step 5: Complete the first subtask
            self.workflow_engine.handle_subtask_completion(
                task_id, "subtask-1", True, {"output": "Analysis complete"}
            )
            
            # Verify the first subtask is marked as completed
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_1 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-1')
            self.assertEqual(subtask_1['status'], SubtaskStatus.COMPLETED.value)
            
            # Verify that the second subtask (dependent on first) is now enqueued and in progress
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_2 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-2')
            self.assertEqual(subtask_2['status'], SubtaskStatus.IN_PROGRESS.value)
            
            # Step 6: Complete the second subtask
            self.workflow_engine.handle_subtask_completion(
                task_id, "subtask-2", True, {"output": "Implementation complete"}
            )
            
            # Verify the second subtask is marked as completed
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_2 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-2')
            self.assertEqual(subtask_2['status'], SubtaskStatus.COMPLETED.value)
            
            # Verify that the third subtask is now enqueued and in progress
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_3 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-3')
            self.assertEqual(subtask_3['status'], SubtaskStatus.IN_PROGRESS.value)
            
            # Step 7: Complete the third subtask
            self.workflow_engine.handle_subtask_completion(
                task_id, "subtask-3", True, {"output": "Tests complete"}
            )
            
            # Verify the third subtask is marked as completed
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_3 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-3')
            self.assertEqual(subtask_3['status'], SubtaskStatus.COMPLETED.value)
            
            # Verify that the fourth subtask is now enqueued and in progress
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_4 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-4')
            self.assertEqual(subtask_4['status'], SubtaskStatus.IN_PROGRESS.value)
            
            # Step 8: Complete the final subtask
            with patch.object(self.workflow_engine, '_handle_workflow_completion') as mock_completion:
                self.workflow_engine.handle_subtask_completion(
                    task_id, "subtask-4", True, {"output": "PR created"}
                )
                
                # Verify the fourth subtask is marked as completed
                plan_data = self.coordinator.get_subtask_plan(task_id)
                subtask_4 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-4')
                self.assertEqual(subtask_4['status'], SubtaskStatus.COMPLETED.value)
                
                # Verify that the workflow is marked as complete
                self.assertTrue(self.workflow_engine._is_workflow_complete(task_id))
                
                # Verify that workflow completion handler was called
                mock_completion.assert_called_once_with(task_id)
    
    def test_failed_subtask_handling(self):
        """Test handling of a failed subtask in the workflow"""
        # Mock the GitHub operations
        with patch('subprocess.run') as mock_run, \
             patch('os.chdir') as mock_chdir:
            
            # Configure the mock to return success for any subprocess call
            mock_run.return_value = Mock(returncode=0, stdout="Success")
            
            # Create a project
            project_id = "test-project"
            self.project_manager.projects[project_id] = ProjectConfig(
                project_id=project_id,
                name="Test Project",
                repository_url="https://github.com/test/repo",
                local_path=str(self.project_path / "repo"),
                github_token="mock-token",
                labels=["test-label"]
            )
            
            # Create a subtask plan with dependencies
            task_id = "task-456"
            subtasks = [
                Subtask(
                    id="subtask-1",
                    title="Analyze Issue",
                    description="Analyze the GitHub issue",
                    type=SubtaskType.ANALYSIS,
                    status=SubtaskStatus.PENDING,
                    dependencies=[]
                ),
                Subtask(
                    id="subtask-2",
                    title="Implement Feature",
                    description="Implement the requested feature",
                    type=SubtaskType.IMPLEMENTATION,
                    status=SubtaskStatus.PENDING,
                    dependencies=["subtask-1"]
                )
            ]
            
            subtask_plan = SubtaskPlan(
                id=task_id,
                issue_number=456,
                issue_title="Test Issue with Failure",
                issue_description="This is a test issue that will have a failed subtask",
                project_name=project_id,
                branch_name=f"issue-456",
                subtasks=subtasks
            )
            
            # Store the plan
            # Convert the SubtaskPlan to a dictionary for storage
            plan_dict = {
                "issue_number": subtask_plan.issue_number,
                "issue_title": subtask_plan.issue_title,
                "issue_description": subtask_plan.issue_description,
                "project_name": subtask_plan.project_name,
                "branch_name": subtask_plan.branch_name,
                "subtasks": [s.__dict__ for s in subtask_plan.subtasks],
                "created_at": subtask_plan.created_at.isoformat(),
                "updated_at": subtask_plan.updated_at.isoformat(),
                "status": subtask_plan.status
            }
            self.coordinator.store_subtask_plan(task_id, plan_dict)
            
            # Initialize the workflow
            self.workflow_engine._execute_workflow(task_id, project_id)
            
            # Verify the first subtask was enqueued (changed to in_progress)
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_1 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-1')
            self.assertEqual(subtask_1['status'], SubtaskStatus.IN_PROGRESS.value)
            
            # Fail the first subtask
            self.workflow_engine.handle_subtask_completion(
                task_id, "subtask-1", False, {"error": "Analysis failed"}
            )
            
            # Verify the subtask is marked as failed
            plan_data = self.coordinator.get_subtask_plan(task_id)
            subtask_1 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-1')
            self.assertEqual(subtask_1['status'], SubtaskStatus.FAILED.value)
            
            # Verify no new subtasks are ready (since the dependency failed)
            ready_subtasks = self.coordinator.get_ready_subtasks(task_id)
            self.assertEqual(len(ready_subtasks), 0)
            
            # Retry the failed subtask
            with patch.object(self.workflow_engine, '_check_and_enqueue_unblocked_subtasks') as mock_check:
                self.workflow_engine.retry_failed_subtask(task_id, "subtask-1")
                
                # Verify the subtask is reset to pending
                plan_data = self.coordinator.get_subtask_plan(task_id)
                subtask_1 = next(s for s in plan_data['subtasks'] if s['id'] == 'subtask-1')
                self.assertEqual(subtask_1['status'], SubtaskStatus.PENDING.value)
                
                # Verify that the unblocked subtasks check was triggered
                mock_check.assert_called_once_with(task_id)


if __name__ == "__main__":
    unittest.main()
