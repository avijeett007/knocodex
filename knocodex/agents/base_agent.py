"""Base agent class for AI coding assistants."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class TaskResult:
    """Result of an agent task execution."""
    success: bool
    output: str
    error: Optional[str] = None
    files_modified: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class IssueAnalysis:
    """Analysis result for a GitHub issue."""
    summary: str
    complexity: str
    affected_files: List[str]
    implementation_plan: str
    subtasks: List[str]
    estimated_time: Optional[str] = None


class BaseAgent(ABC):
    """Abstract base class for AI coding assistants."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the agent with configuration."""
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def analyze_issue(self, issue: Dict[str, Any]) -> TaskResult:
        """Analyze a GitHub issue and create implementation plan.
        
        Args:
            issue: GitHub issue data containing title, body, labels, etc.
            
        Returns:
            TaskResult with analysis details and implementation plan.
        """
        pass
    
    @abstractmethod
    def implement_solution(self, issue: Dict[str, Any], plan: str) -> TaskResult:
        """Implement a solution based on the issue and plan.
        
        Args:
            issue: GitHub issue data
            plan: Implementation plan from analyze_issue
            
        Returns:
            TaskResult with implementation details and modified files.
        """
        pass
    
    @abstractmethod
    def generate_docs(self, files: List[str], context: str = "") -> TaskResult:
        """Generate documentation for specified files.
        
        Args:
            files: List of file paths to document
            context: Additional context or requirements
            
        Returns:
            TaskResult with generated documentation.
        """
        pass
    
    @abstractmethod
    def review_pr(self, pr_data: Dict[str, Any]) -> TaskResult:
        """Review a pull request and provide feedback.
        
        Args:
            pr_data: Pull request data including diff, description, etc.
            
        Returns:
            TaskResult with review comments and suggestions.
        """
        pass
    
    def validate_config(self) -> bool:
        """Validate agent configuration.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        return True
    
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities.
        
        Returns:
            List of capability names.
        """
        return [
            "analyze_issue",
            "implement_solution", 
            "generate_docs",
            "review_pr"
        ]
    
    def health_check(self) -> bool:
        """Check if agent is healthy and ready to work.
        
        Returns:
            True if agent is healthy, False otherwise.
        """
        return self.validate_config()