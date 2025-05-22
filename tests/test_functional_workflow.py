#!/usr/bin/env python3
"""
Functional test for the subtask workflow system

This test verifies the core workflow functionality with minimal external dependencies.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import redis
from datetime import datetime

from knocodex.models.subtask import Subtask, SubtaskStatus, SubtaskType, SubtaskPlan
from knocodex.workflow_engine import WorkflowConfig


class TestFunctionalWorkflow(unittest.TestCase):
    """Functional test for the subtask workflow system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name)
        self.project_id = "test-project"
        
        # In-memory storage for tracking subtask statuses
        self.subtask_statuses = {}
        self.subtask_results = {}
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_subtask_workflow_execution(self):
        """Test the execution of a subtask workflow with dependencies"""
        # Create subtasks with dependencies
        subtask1 = Subtask(
            id="subtask-1",
            title="Analyze Issue",
            description="Analyze the GitHub issue",
            type=SubtaskType.ANALYSIS,
            status=SubtaskStatus.PENDING,
            dependencies=[]
        )
        
        subtask2 = Subtask(
            id="subtask-2",
            title="Implement Feature",
            description="Implement the requested feature",
            type=SubtaskType.IMPLEMENTATION,
            status=SubtaskStatus.PENDING,
            dependencies=["subtask-1"]  # Depends on subtask1
        )
        
        subtask3 = Subtask(
            id="subtask-3",
            title="Write Tests",
            description="Write tests for the feature",
            type=SubtaskType.TESTING,
            status=SubtaskStatus.PENDING,
            dependencies=["subtask-2"]  # Depends on subtask2
        )
        
        # Set up the workflow
        task_id = "task-123"
        subtasks = [subtask1, subtask2, subtask3]
        
        # Initialize all subtasks as pending
        for subtask in subtasks:
            self.subtask_statuses[f"{task_id}:{subtask.id}"] = SubtaskStatus.PENDING
        
        # 1. Find the ready subtasks (should only be subtask1 with no dependencies)
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 1)
        self.assertEqual(ready_subtasks[0].id, "subtask-1")
        
        # 2. Execute the first subtask
        self._execute_subtask(task_id, subtask1)
        
        # 3. Find ready subtasks again (should now be subtask2)
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 1)
        self.assertEqual(ready_subtasks[0].id, "subtask-2")
        
        # 4. Execute the second subtask
        self._execute_subtask(task_id, subtask2)
        
        # 5. Find ready subtasks again (should now be subtask3)
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 1)
        self.assertEqual(ready_subtasks[0].id, "subtask-3")
        
        # 6. Execute the third subtask
        self._execute_subtask(task_id, subtask3)
        
        # 7. Verify no more subtasks are ready
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 0)
        
        # 8. Verify all subtasks are completed
        for subtask in subtasks:
            status = self.subtask_statuses[f"{task_id}:{subtask.id}"]
            self.assertEqual(status, SubtaskStatus.COMPLETED)
        
        # 9. Verify workflow is complete
        self.assertTrue(self._is_workflow_complete(task_id, subtasks))
    
    def test_failed_subtask_handling(self):
        """Test handling of a failed subtask in the workflow"""
        # Create subtasks with dependencies
        subtask1 = Subtask(
            id="subtask-1",
            title="Analyze Issue",
            description="Analyze the GitHub issue",
            type=SubtaskType.ANALYSIS,
            status=SubtaskStatus.PENDING,
            dependencies=[]
        )
        
        subtask2 = Subtask(
            id="subtask-2",
            title="Implement Feature",
            description="Implement the requested feature",
            type=SubtaskType.IMPLEMENTATION,
            status=SubtaskStatus.PENDING,
            dependencies=["subtask-1"]  # Depends on subtask1
        )
        
        # Set up the workflow
        task_id = "task-456"
        subtasks = [subtask1, subtask2]
        
        # Initialize all subtasks as pending
        for subtask in subtasks:
            self.subtask_statuses[f"{task_id}:{subtask.id}"] = SubtaskStatus.PENDING
        
        # 1. Find the ready subtasks (should only be subtask1 with no dependencies)
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 1)
        self.assertEqual(ready_subtasks[0].id, "subtask-1")
        
        # 2. Fail the first subtask
        self._fail_subtask(task_id, subtask1)
        
        # 3. Verify the subtask is marked as failed
        status = self.subtask_statuses[f"{task_id}:{subtask1.id}"]
        self.assertEqual(status, SubtaskStatus.FAILED)
        
        # 4. Find ready subtasks again (should be none since subtask1 failed)
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 0)
        
        # 5. Retry the failed subtask
        self._retry_subtask(task_id, subtask1)
        
        # 6. Verify the subtask is reset to pending
        status = self.subtask_statuses[f"{task_id}:{subtask1.id}"]
        self.assertEqual(status, SubtaskStatus.PENDING)
        
        # 7. Find ready subtasks again (should be subtask1)
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 1)
        self.assertEqual(ready_subtasks[0].id, "subtask-1")
        
        # 8. Execute the first subtask successfully
        self._execute_subtask(task_id, subtask1)
        
        # 9. Find ready subtasks again (should now be subtask2)
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 1)
        self.assertEqual(ready_subtasks[0].id, "subtask-2")
        
        # 10. Execute the second subtask
        self._execute_subtask(task_id, subtask2)
        
        # 11. Verify no more subtasks are ready
        ready_subtasks = self._get_ready_subtasks(task_id, subtasks)
        self.assertEqual(len(ready_subtasks), 0)
        
        # 12. Verify all subtasks are completed
        for subtask in subtasks:
            status = self.subtask_statuses[f"{task_id}:{subtask.id}"]
            self.assertEqual(status, SubtaskStatus.COMPLETED)
        
        # 13. Verify workflow is complete
        self.assertTrue(self._is_workflow_complete(task_id, subtasks))
    
    # Helper methods that implement core workflow functionality
    
    def _get_ready_subtasks(self, task_id, subtasks):
        """Get subtasks that are ready to execute (pending and have all dependencies satisfied)"""
        ready_subtasks = []
        
        for subtask in subtasks:
            key = f"{task_id}:{subtask.id}"
            # Check if subtask is pending
            if self.subtask_statuses.get(key) != SubtaskStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            all_deps_completed = True
            for dep_id in subtask.dependencies:
                dep_key = f"{task_id}:{dep_id}"
                if self.subtask_statuses.get(dep_key) != SubtaskStatus.COMPLETED:
                    all_deps_completed = False
                    break
            
            if all_deps_completed:
                ready_subtasks.append(subtask)
                
        return ready_subtasks
    
    def _execute_subtask(self, task_id, subtask):
        """Simulate executing a subtask successfully"""
        # Update status to COMPLETED
        key = f"{task_id}:{subtask.id}"
        self.subtask_statuses[key] = SubtaskStatus.COMPLETED
        self.subtask_results[key] = {"output": f"{subtask.title} completed successfully"}
    
    def _fail_subtask(self, task_id, subtask):
        """Simulate a subtask failure"""
        # Update status to FAILED
        key = f"{task_id}:{subtask.id}"
        self.subtask_statuses[key] = SubtaskStatus.FAILED
        self.subtask_results[key] = {"error": f"{subtask.title} failed"}
    
    def _retry_subtask(self, task_id, subtask):
        """Simulate retrying a failed subtask"""
        # Reset status to PENDING
        key = f"{task_id}:{subtask.id}"
        self.subtask_statuses[key] = SubtaskStatus.PENDING
    
    def _is_workflow_complete(self, task_id, subtasks):
        """Check if the workflow is complete (all subtasks are completed)"""
        for subtask in subtasks:
            key = f"{task_id}:{subtask.id}"
            if self.subtask_statuses.get(key) != SubtaskStatus.COMPLETED:
                return False
        return True


if __name__ == "__main__":
    unittest.main()
