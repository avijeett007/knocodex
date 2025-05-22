"""
Subtask analyzer for breaking down GitHub issues into manageable subtasks.
"""
import re
from typing import List, Dict, Any, Optional
from .models.subtask import Subtask, SubtaskPlan, SubtaskType
from .utils.gh_utils import get_issue_details


class SubtaskAnalyzer:
    """
    Analyzes GitHub issues and breaks them down into subtasks.
    """
    
    def __init__(self):
        """Initialize the subtask analyzer."""
        self.subtask_patterns = {
            'feature': [
                SubtaskType.BRANCH,
                SubtaskType.ANALYSIS,
                SubtaskType.IMPLEMENTATION,
                SubtaskType.TESTING,
                SubtaskType.DOCUMENTATION,
                SubtaskType.COMMIT,
                SubtaskType.PULL_REQUEST
            ],
            'bug': [
                SubtaskType.BRANCH,
                SubtaskType.ANALYSIS,
                SubtaskType.IMPLEMENTATION,
                SubtaskType.TESTING,
                SubtaskType.COMMIT,
                SubtaskType.PULL_REQUEST
            ],
            'documentation': [
                SubtaskType.BRANCH,
                SubtaskType.ANALYSIS,
                SubtaskType.DOCUMENTATION,
                SubtaskType.COMMIT,
                SubtaskType.PULL_REQUEST
            ],
            'refactor': [
                SubtaskType.BRANCH,
                SubtaskType.ANALYSIS,
                SubtaskType.IMPLEMENTATION,
                SubtaskType.TESTING,
                SubtaskType.DOCUMENTATION,
                SubtaskType.COMMIT,
                SubtaskType.PULL_REQUEST
            ]
        }
    
    def analyze_issue(self, issue_number: int, project_name: str) -> SubtaskPlan:
        """
        Analyze a GitHub issue and create a subtask plan.
        
        Args:
            issue_number: GitHub issue number
            project_name: Name of the project
            
        Returns:
            SubtaskPlan with breakdown of subtasks
        """
        # Get issue details from GitHub
        issue_data = get_issue_details(issue_number)
        
        # Create the subtask plan
        plan = SubtaskPlan(
            issue_number=issue_number,
            issue_title=issue_data.get('title', ''),
            issue_description=issue_data.get('body', ''),
            project_name=project_name,
            branch_name=self._generate_branch_name(issue_number, issue_data.get('title', ''))
        )
        
        # Determine issue type from labels or content
        issue_type = self._determine_issue_type(issue_data)
        
        # Generate subtasks based on issue type
        subtasks = self._generate_subtasks(issue_data, issue_type, plan.branch_name)
        
        # Add subtasks to plan with proper dependencies
        for i, subtask in enumerate(subtasks):
            if i > 0:
                # Each subtask depends on the previous one
                subtask.dependencies = [subtasks[i-1].id]
            plan.add_subtask(subtask)
        
        return plan
    
    def _determine_issue_type(self, issue_data: Dict[str, Any]) -> str:
        """
        Determine the type of issue based on labels and content.
        
        Args:
            issue_data: GitHub issue data
            
        Returns:
            Issue type string
        """
        labels = [label.get('name', '').lower() for label in issue_data.get('labels', [])]
        title = issue_data.get('title', '').lower()
        body = issue_data.get('body', '').lower()
        
        # Check labels first
        if any(label in ['bug', 'fix', 'hotfix'] for label in labels):
            return 'bug'
        elif any(label in ['documentation', 'docs'] for label in labels):
            return 'documentation'
        elif any(label in ['refactor', 'refactoring', 'cleanup'] for label in labels):
            return 'refactor'
        elif any(label in ['feature', 'enhancement', 'new'] for label in labels):
            return 'feature'
        
        # Check title and body content
        if any(keyword in title or keyword in body for keyword in ['bug', 'fix', 'error', 'issue']):
            return 'bug'
        elif any(keyword in title or keyword in body for keyword in ['documentation', 'docs', 'readme']):
            return 'documentation'
        elif any(keyword in title or keyword in body for keyword in ['refactor', 'cleanup', 'improve']):
            return 'refactor'
        else:
            return 'feature'  # Default to feature
    
    def _generate_branch_name(self, issue_number: int, title: str) -> str:
        """
        Generate a branch name for the issue.
        
        Args:
            issue_number: GitHub issue number
            title: Issue title
            
        Returns:
            Branch name string
        """
        # Clean up the title for branch name
        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        clean_title = re.sub(r'\s+', '-', clean_title.strip())
        clean_title = clean_title.lower()[:50]  # Limit length
        
        return f"feature/issue-{issue_number}-{clean_title}"
    
    def _generate_subtasks(self, issue_data: Dict[str, Any], issue_type: str, branch_name: str) -> List[Subtask]:
        """
        Generate subtasks based on issue type and content.
        
        Args:
            issue_data: GitHub issue data
            issue_type: Type of issue
            branch_name: Branch name for the issue
            
        Returns:
            List of subtasks
        """
        subtasks = []
        subtask_types = self.subtask_patterns.get(issue_type, self.subtask_patterns['feature'])
        
        for subtask_type in subtask_types:
            subtask = self._create_subtask_for_type(subtask_type, issue_data, branch_name)
            subtasks.append(subtask)
        
        return subtasks
    
    def _create_subtask_for_type(self, subtask_type: SubtaskType, issue_data: Dict[str, Any], branch_name: str) -> Subtask:
        """
        Create a subtask for a specific type.
        
        Args:
            subtask_type: Type of subtask
            issue_data: GitHub issue data
            branch_name: Branch name for the issue
            
        Returns:
            Subtask instance
        """
        issue_title = issue_data.get('title', '')
        issue_body = issue_data.get('body', '')
        issue_number = issue_data.get('number', 0)
        
        subtask_templates = {
            SubtaskType.BRANCH: {
                'title': f'Create branch for issue #{issue_number}',
                'description': f'Create and checkout branch {branch_name}',
                'context': {'branch_name': branch_name}
            },
            SubtaskType.ANALYSIS: {
                'title': f'Analyze requirements for: {issue_title}',
                'description': f'Understand the requirements and create implementation plan for: {issue_title}',
                'context': {
                    'issue_title': issue_title,
                    'issue_body': issue_body,
                    'analysis_focus': 'requirements, dependencies, implementation approach'
                }
            },
            SubtaskType.IMPLEMENTATION: {
                'title': f'Implement solution for: {issue_title}',
                'description': f'Write code to implement the solution for: {issue_title}',
                'context': {
                    'issue_title': issue_title,
                    'issue_body': issue_body,
                    'implementation_focus': 'core functionality, error handling, integration'
                }
            },
            SubtaskType.TESTING: {
                'title': f'Add tests for: {issue_title}',
                'description': f'Write comprehensive tests for the implementation of: {issue_title}',
                'context': {
                    'issue_title': issue_title,
                    'testing_focus': 'unit tests, integration tests, edge cases'
                }
            },
            SubtaskType.DOCUMENTATION: {
                'title': f'Update documentation for: {issue_title}',
                'description': f'Update relevant documentation for changes made for: {issue_title}',
                'context': {
                    'issue_title': issue_title,
                    'documentation_focus': 'API docs, README, code comments'
                }
            },
            SubtaskType.COMMIT: {
                'title': f'Commit changes for issue #{issue_number}',
                'description': f'Create commit with all changes for: {issue_title}',
                'context': {
                    'issue_number': issue_number,
                    'issue_title': issue_title,
                    'commit_message_template': f'feat: {issue_title}'
                }
            },
            SubtaskType.PULL_REQUEST: {
                'title': f'Create pull request for issue #{issue_number}',
                'description': f'Create pull request with detailed description for: {issue_title}',
                'context': {
                    'issue_number': issue_number,
                    'issue_title': issue_title,
                    'branch_name': branch_name,
                    'pr_template': 'fixes #{}, description, testing notes'
                }
            }
        }
        
        template = subtask_templates.get(subtask_type, {
            'title': f'Execute {subtask_type.value} for: {issue_title}',
            'description': f'Execute {subtask_type.value} subtask for: {issue_title}',
            'context': {'issue_title': issue_title}
        })
        
        return Subtask(
            type=subtask_type,
            title=template['title'],
            description=template['description'],
            context=template['context']
        )
    
    def enhance_subtasks_with_content_analysis(self, plan: SubtaskPlan) -> None:
        """
        Enhance subtasks with more detailed analysis based on issue content.
        
        Args:
            plan: SubtaskPlan to enhance
        """
        issue_body = plan.issue_description.lower()
        
        # Look for specific requirements or mentions
        file_mentions = re.findall(r'`([^`]*\.[a-z]+)`', plan.issue_description)
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', plan.issue_description, re.DOTALL)
        
        # Enhance implementation subtask with file information
        for subtask in plan.subtasks:
            if subtask.type == SubtaskType.IMPLEMENTATION:
                if file_mentions:
                    subtask.context['mentioned_files'] = file_mentions
                if code_blocks:
                    subtask.context['code_examples'] = code_blocks
            elif subtask.type == SubtaskType.ANALYSIS:
                # Add complexity indicators
                complexity_indicators = []
                if 'database' in issue_body or 'db' in issue_body:
                    complexity_indicators.append('database_changes')
                if 'api' in issue_body or 'endpoint' in issue_body:
                    complexity_indicators.append('api_changes')
                if 'ui' in issue_body or 'frontend' in issue_body:
                    complexity_indicators.append('frontend_changes')
                if 'test' in issue_body:
                    complexity_indicators.append('testing_required')
                
                subtask.context['complexity_indicators'] = complexity_indicators
    
    def create_minimal_subtask_plan(self, issue_number: int, project_name: str, subtask_types: List[SubtaskType]) -> SubtaskPlan:
        """
        Create a minimal subtask plan with specific subtask types.
        
        Args:
            issue_number: GitHub issue number
            project_name: Name of the project
            subtask_types: List of subtask types to include
            
        Returns:
            SubtaskPlan with specified subtasks
        """
        issue_data = get_issue_details(issue_number)
        
        plan = SubtaskPlan(
            issue_number=issue_number,
            issue_title=issue_data.get('title', ''),
            issue_description=issue_data.get('body', ''),
            project_name=project_name,
            branch_name=self._generate_branch_name(issue_number, issue_data.get('title', ''))
        )
        
        subtasks = []
        for subtask_type in subtask_types:
            subtask = self._create_subtask_for_type(subtask_type, issue_data, plan.branch_name)
            subtasks.append(subtask)
        
        # Add dependencies (each subtask depends on previous)
        for i, subtask in enumerate(subtasks):
            if i > 0:
                subtask.dependencies = [subtasks[i-1].id]
            plan.add_subtask(subtask)
        
        return plan