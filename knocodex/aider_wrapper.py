"""
Aider Wrapper Module

This module provides specialized wrapper functions for aider operations,
complementing the generic AI backend abstraction layer.
"""

import os
import subprocess
import tempfile
import json
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AiderWrapper:
    """Specialized wrapper for aider operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('aider_model', 'gemini-exp')
        self.api_key = self._get_api_key()
        self.auto_commits = config.get('aider_auto_commits', True)
        self.stream = config.get('aider_stream', False)
        self.verbose = config.get('aider_verbose', False)
        
    def _get_api_key(self) -> Optional[str]:
        """Get the appropriate API key based on model."""
        if 'gemini' in self.model.lower():
            return self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        elif 'gpt' in self.model.lower() or 'openai' in self.model.lower():
            return self.config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        elif 'claude' in self.model.lower():
            return self.config.get('anthropic_api_key') or os.getenv('ANTHROPIC_API_KEY')
        else:
            return self.config.get('aider_api_key')
    
    def _build_command(self, message: str, files: Optional[List[str]] = None, 
                      additional_args: Optional[List[str]] = None) -> List[str]:
        """Build aider command with proper arguments."""
        cmd_args = [
            'aider',
            '--model', self.model,
            '--message', message
        ]
        
        # Stream settings
        if not self.stream:
            cmd_args.append('--no-stream')
        
        # Auto-commit settings
        if self.auto_commits:
            cmd_args.append('--yes')
        else:
            cmd_args.append('--no-auto-commits')
        
        # Verbose output
        if self.verbose:
            cmd_args.append('--verbose')
        
        # Add additional arguments
        if additional_args:
            cmd_args.extend(additional_args)
        
        # Add files
        if files:
            cmd_args.extend(files)
        
        return cmd_args
    
    def _execute_command(self, cmd_args: List[str], timeout: int = 600) -> Dict[str, Any]:
        """Execute aider command and return result."""
        try:
            # Set up environment with API key
            env = os.environ.copy()
            if self.api_key:
                if 'gemini' in self.model.lower():
                    env['GEMINI_API_KEY'] = self.api_key
                elif 'gpt' in self.model.lower():
                    env['OPENAI_API_KEY'] = self.api_key
                elif 'claude' in self.model.lower():
                    env['ANTHROPIC_API_KEY'] = self.api_key
            
            logger.info(f"Executing aider command: {' '.join(cmd_args[:5])}...")
            
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=os.getcwd()
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Aider command timed out after {timeout} seconds")
            return {
                'success': False,
                'output': '',
                'error': f'Command timed out after {timeout} seconds',
                'return_code': -1
            }
        except Exception as e:
            logger.error(f"Error executing aider command: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }
    
    def analyze_github_issue(self, issue_content: str, project_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze a GitHub issue and create implementation plan."""
        message = f"""
        Analyze this GitHub issue and create a detailed implementation plan:
        
        {issue_content}
        
        Please provide:
        1. Summary of the issue
        2. Technical requirements
        3. Files that need to be modified
        4. Step-by-step implementation plan
        5. Testing approach
        """
        
        cmd_args = self._build_command(
            message=message,
            files=project_files,
            additional_args=['--no-auto-commits']  # Don't commit during analysis
        )
        
        return self._execute_command(cmd_args, timeout=300)
    
    def implement_github_issue(self, plan: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Implement solution based on the provided plan."""
        message = f"""
        Implement the following plan:
        
        {plan}
        
        Please:
        1. Follow the implementation plan exactly
        2. Ensure code follows project conventions
        3. Add appropriate error handling
        4. Include docstrings and comments where needed
        5. Ensure all imports are correct
        """
        
        cmd_args = self._build_command(
            message=message,
            files=files
        )
        
        return self._execute_command(cmd_args, timeout=900)  # 15 minutes for implementation
    
    def review_pull_request(self, files: List[str]) -> Dict[str, Any]:
        """Review code changes in pull request."""
        message = """
        Review these code changes and provide feedback on:
        1. Code quality and best practices
        2. Potential bugs or issues
        3. Security considerations
        4. Performance implications
        5. Suggestions for improvement
        """
        
        cmd_args = self._build_command(
            message=message,
            files=files,
            additional_args=['--no-auto-commits']  # Don't commit during review
        )
        
        return self._execute_command(cmd_args, timeout=300)
    
    def document_project(self, files: List[str]) -> Dict[str, Any]:
        """Generate documentation for project files."""
        message = """
        Generate comprehensive documentation for this project including:
        1. README.md updates if needed
        2. Docstrings for functions and classes
        3. API documentation
        4. Usage examples
        5. Configuration documentation
        """
        
        cmd_args = self._build_command(
            message=message,
            files=files
        )
        
        return self._execute_command(cmd_args, timeout=600)
    
    def fix_code_issues(self, error_message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fix code issues based on error message."""
        message = f"""
        Fix the following code issues:
        
        {error_message}
        
        Please:
        1. Identify the root cause of the issue
        2. Implement a proper fix
        3. Ensure the fix doesn't break existing functionality
        4. Add tests if appropriate
        """
        
        cmd_args = self._build_command(
            message=message,
            files=files
        )
        
        return self._execute_command(cmd_args, timeout=600)
    
    def refactor_code(self, refactor_instructions: str, files: List[str]) -> Dict[str, Any]:
        """Refactor code according to instructions."""
        message = f"""
        Refactor the code according to these instructions:
        
        {refactor_instructions}
        
        Please:
        1. Maintain existing functionality
        2. Improve code structure and readability
        3. Follow project conventions
        4. Update tests if necessary
        """
        
        cmd_args = self._build_command(
            message=message,
            files=files
        )
        
        return self._execute_command(cmd_args, timeout=900)
    
    def create_tests(self, test_instructions: str, files: List[str]) -> Dict[str, Any]:
        """Create tests for specified files."""
        message = f"""
        Create comprehensive tests based on these instructions:
        
        {test_instructions}
        
        Please:
        1. Create unit tests for all functions
        2. Include edge cases and error conditions
        3. Follow project testing conventions
        4. Ensure tests are maintainable
        """
        
        cmd_args = self._build_command(
            message=message,
            files=files
        )
        
        return self._execute_command(cmd_args, timeout=600)
    
    def check_availability(self) -> Dict[str, Any]:
        """Check if aider is available and properly configured."""
        try:
            # Check if aider is installed
            result = subprocess.run(['aider', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    'available': False,
                    'error': 'Aider not installed or not in PATH'
                }
            
            # Check if API key is configured
            if not self.api_key:
                return {
                    'available': False,
                    'error': f'API key not configured for model {self.model}'
                }
            
            # Test API connection with a simple query
            test_cmd = self._build_command(
                message="Test connection - just respond with 'OK'",
                additional_args=['--no-auto-commits', '--dry-run']
            )
            
            test_result = self._execute_command(test_cmd, timeout=30)
            
            return {
                'available': test_result['success'],
                'version': result.stdout.strip(),
                'model': self.model,
                'error': test_result.get('error') if not test_result['success'] else None
            }
            
        except FileNotFoundError:
            return {
                'available': False,
                'error': 'Aider command not found'
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def list_supported_models(self) -> List[str]:
        """Get list of supported models."""
        try:
            result = subprocess.run(['aider', '--models'], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse the output to extract model names
                models = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('Available'):
                        models.append(line.split()[0])  # Get first word (model name)
                return models
            else:
                return []
        except Exception:
            return []