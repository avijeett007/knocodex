"""
Subtask data models for the Knocodex workflow system.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


class SubtaskType(Enum):
    """Types of subtasks in the workflow."""
    BRANCH = "branch"
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"


class SubtaskStatus(Enum):
    """Status of subtask execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Subtask:
    """
    Represents a single subtask in the workflow.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: SubtaskType = SubtaskType.ANALYSIS
    title: str = ""
    description: str = ""
    status: SubtaskStatus = SubtaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def start(self) -> None:
        """Mark subtask as started."""
        self.status = SubtaskStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Mark subtask as completed."""
        self.status = SubtaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def fail(self, error_message: str) -> None:
        """Mark subtask as failed with error message."""
        self.status = SubtaskStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now()
    
    def block(self) -> None:
        """Mark subtask as blocked."""
        self.status = SubtaskStatus.BLOCKED
        self.updated_at = datetime.now()
    
    def can_retry(self) -> bool:
        """Check if subtask can be retried."""
        return self.retry_count < self.max_retries
    
    def increment_retry(self) -> None:
        """Increment retry count and reset status to pending."""
        self.retry_count += 1
        self.status = SubtaskStatus.PENDING
        self.error_message = None
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subtask to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'dependencies': self.dependencies,
            'context': self.context,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subtask':
        """Create subtask from dictionary."""
        subtask = cls(
            id=data['id'],
            type=SubtaskType(data['type']),
            title=data['title'],
            description=data['description'],
            status=SubtaskStatus(data['status']),
            dependencies=data['dependencies'],
            context=data['context'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )
        
        if data.get('started_at'):
            subtask.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            subtask.completed_at = datetime.fromisoformat(data['completed_at'])
        
        return subtask


@dataclass
class SubtaskPlan:
    """
    Represents a complete plan for processing a GitHub issue with subtasks.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issue_number: int = 0
    issue_title: str = ""
    issue_description: str = ""
    project_name: str = ""
    branch_name: str = ""
    subtasks: List[Subtask] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    
    def add_subtask(self, subtask: Subtask) -> None:
        """Add a subtask to the plan."""
        self.subtasks.append(subtask)
        self.updated_at = datetime.now()
    
    def get_subtask_by_id(self, subtask_id: str) -> Optional[Subtask]:
        """Get subtask by ID."""
        for subtask in self.subtasks:
            if subtask.id == subtask_id:
                return subtask
        return None
    
    def get_ready_subtasks(self) -> List[Subtask]:
        """Get subtasks that are ready to be executed (no pending dependencies)."""
        ready_subtasks = []
        completed_ids = {s.id for s in self.subtasks if s.status == SubtaskStatus.COMPLETED}
        
        for subtask in self.subtasks:
            if subtask.status == SubtaskStatus.PENDING:
                # Check if all dependencies are completed
                if all(dep_id in completed_ids for dep_id in subtask.dependencies):
                    ready_subtasks.append(subtask)
        
        return ready_subtasks
    
    def get_blocked_subtasks(self) -> List[Subtask]:
        """Get subtasks that are blocked by failed dependencies."""
        blocked_subtasks = []
        failed_ids = {s.id for s in self.subtasks if s.status == SubtaskStatus.FAILED}
        
        for subtask in self.subtasks:
            if subtask.status == SubtaskStatus.PENDING:
                # Check if any dependency has failed
                if any(dep_id in failed_ids for dep_id in subtask.dependencies):
                    blocked_subtasks.append(subtask)
        
        return blocked_subtasks
    
    def is_complete(self) -> bool:
        """Check if all subtasks are completed."""
        return all(s.status == SubtaskStatus.COMPLETED for s in self.subtasks)
    
    def has_failed_subtasks(self) -> bool:
        """Check if any subtasks have failed."""
        return any(s.status == SubtaskStatus.FAILED for s in self.subtasks)
    
    def get_progress(self) -> Dict[str, int]:
        """Get progress statistics."""
        total = len(self.subtasks)
        completed = sum(1 for s in self.subtasks if s.status == SubtaskStatus.COMPLETED)
        failed = sum(1 for s in self.subtasks if s.status == SubtaskStatus.FAILED)
        in_progress = sum(1 for s in self.subtasks if s.status == SubtaskStatus.IN_PROGRESS)
        pending = sum(1 for s in self.subtasks if s.status == SubtaskStatus.PENDING)
        blocked = sum(1 for s in self.subtasks if s.status == SubtaskStatus.BLOCKED)
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'in_progress': in_progress,
            'pending': pending,
            'blocked': blocked,
            'completion_percentage': (completed / total * 100) if total > 0 else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for serialization."""
        return {
            'id': self.id,
            'issue_number': self.issue_number,
            'issue_title': self.issue_title,
            'issue_description': self.issue_description,
            'project_name': self.project_name,
            'branch_name': self.branch_name,
            'subtasks': [s.to_dict() for s in self.subtasks],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubtaskPlan':
        """Create plan from dictionary."""
        plan = cls(
            id=data['id'],
            issue_number=data['issue_number'],
            issue_title=data['issue_title'],
            issue_description=data['issue_description'],
            project_name=data['project_name'],
            branch_name=data['branch_name'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            status=data['status']
        )
        
        for subtask_data in data['subtasks']:
            plan.subtasks.append(Subtask.from_dict(subtask_data))
        
        return plan