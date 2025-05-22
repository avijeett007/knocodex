# Import and expose subtask model classes
from .subtask import SubtaskStatus, SubtaskType, Subtask, SubtaskPlan

# Define workflow status enum for project_manager.py
from enum import Enum

class WorkflowStatus(Enum):
    """Status of a complete workflow."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
