"""
AI Backend Abstraction Layer

This module provides a unified interface for different AI coding backends,
allowing seamless switching between Claude Code and Aider.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
import subprocess
import os

logger = logging.getLogger(__name__)


class AIBackend(ABC):
    """Abstract base class for AI coding backends."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__.lower().replace("backend", "").replace("wrapper", "")
    
    @abstractmethod
    def execute_command(self, command: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute a command using the AI backend."""
        pass
    
    @abstractmethod
    def analyze_issue(self, issue_content: str) -> Dict[str, Any]:
        """Analyze a GitHub issue and create an implementation plan."""
        pass
    
    @abstractmethod
    def implement_solution(self, plan: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Implement a solution based on the provided plan."""
        pass
    
    @abstractmethod
    def review_code(self, files: List[str]) -> Dict[str, Any]:
        """Review code changes and provide feedback."""
        pass
    
    @abstractmethod
    def generate_documentation(self, files: List[str]) -> Dict[str, Any]:
        """Generate documentation for the specified files."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available and properly configured."""
        pass


class ClaudeCodeBackend(AIBackend):
    """Claude Code backend implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('claude_api_key') or os.getenv('ANTHROPIC_API_KEY')
        self.model = config.get('claude_model', 'claude-3-5-sonnet-20241022')
    
    def execute_command(self, command: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute a Claude Code command."""
        try:
            cmd_args = ['claude-code']
            if files:
                cmd_args.extend(['--files'] + files)
            cmd_args.append(command)
            
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'backend': self.name
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Command timed out',
                'backend': self.name
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'backend': self.name
            }
    
    def analyze_issue(self, issue_content: str) -> Dict[str, Any]:
        """Analyze GitHub issue using Claude Code."""
        command = f"/project:analyze-github-issue {issue_content}"
        return self.execute_command(command)
    
    def implement_solution(self, plan: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Implement solution using Claude Code."""
        command = f"/project:implement-github-issue {plan}"
        return self.execute_command(command, files)
    
    def review_code(self, files: List[str]) -> Dict[str, Any]:
        """Review code using Claude Code."""
        command = "/project:review-pull-request"
        return self.execute_command(command, files)
    
    def generate_documentation(self, files: List[str]) -> Dict[str, Any]:
        """Generate documentation using Claude Code."""
        command = "/project:document-project"
        return self.execute_command(command, files)
    
    def is_available(self) -> bool:
        """Check if Claude Code is available."""
        try:
            result = subprocess.run(['claude-code', '--version'], capture_output=True)
            return result.returncode == 0 and bool(self.api_key)
        except FileNotFoundError:
            return False


class AiderBackend(AIBackend):
    """Aider backend implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get('aider_model', 'gemini-exp')
        self.api_key = self._get_api_key()
        self.auto_commits = config.get('aider_auto_commits', True)
        self.stream = config.get('aider_stream', False)
    
    def _get_api_key(self) -> Optional[str]:
        """Get the appropriate API key based on model."""
        if 'gemini' in self.model.lower():
            return self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        elif 'gpt' in self.model.lower() or 'openai' in self.model.lower():
            return self.config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        else:
            return self.config.get('aider_api_key')
    
    def execute_command(self, command: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute an Aider command."""
        try:
            cmd_args = [
                'aider',
                '--model', self.model,
                '--no-stream' if not self.stream else '--stream',
                '--yes' if self.auto_commits else '--no-auto-commits',
                '--message', command
            ]
            
            if files:
                cmd_args.extend(files)
            
            # Set environment variable for API key
            env = os.environ.copy()
            if self.api_key:
                if 'gemini' in self.model.lower():
                    env['GEMINI_API_KEY'] = self.api_key
                elif 'gpt' in self.model.lower():
                    env['OPENAI_API_KEY'] = self.api_key
            
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for aider
                env=env
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'backend': self.name
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Aider command timed out',
                'backend': self.name
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'backend': self.name
            }
    
    def analyze_issue(self, issue_content: str) -> Dict[str, Any]:
        """Analyze GitHub issue using Aider."""
        command = f"Analyze this GitHub issue and create an implementation plan: {issue_content}"
        return self.execute_command(command)
    
    def implement_solution(self, plan: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Implement solution using Aider."""
        command = f"Implement the following plan: {plan}"
        return self.execute_command(command, files)
    
    def review_code(self, files: List[str]) -> Dict[str, Any]:
        """Review code using Aider."""
        command = "Review the code changes and provide feedback on potential issues"
        return self.execute_command(command, files)
    
    def generate_documentation(self, files: List[str]) -> Dict[str, Any]:
        """Generate documentation using Aider."""
        command = "Generate comprehensive documentation for this project"
        return self.execute_command(command, files)
    
    def is_available(self) -> bool:
        """Check if Aider is available."""
        try:
            result = subprocess.run(['aider', '--version'], capture_output=True)
            return result.returncode == 0 and bool(self.api_key)
        except FileNotFoundError:
            return False


class BackendFactory:
    """Factory class for creating AI backend instances."""
    
    _backends = {
        'claude-code': ClaudeCodeBackend,
        'aider': AiderBackend
    }
    
    @classmethod
    def create_backend(cls, backend_type: str, config: Dict[str, Any]) -> AIBackend:
        """Create an AI backend instance."""
        if backend_type not in cls._backends:
            raise ValueError(f"Unknown backend type: {backend_type}. Available: {list(cls._backends.keys())}")
        
        backend_class = cls._backends[backend_type]
        return backend_class(config)
    
    @classmethod
    def get_available_backends(cls, config: Dict[str, Any]) -> List[str]:
        """Get list of available backends."""
        available = []
        for backend_type, backend_class in cls._backends.items():
            try:
                backend = backend_class(config)
                if backend.is_available():
                    available.append(backend_type)
            except Exception as e:
                logger.warning(f"Backend {backend_type} not available: {e}")
        return available
    
    @classmethod
    def get_preferred_backend(cls, config: Dict[str, Any]) -> Optional[str]:
        """Get the preferred backend based on configuration and availability."""
        preferred = config.get('ai_backend', 'claude-code')
        
        # Check if preferred backend is available
        available = cls.get_available_backends(config)
        if preferred in available:
            return preferred
        
        # Fallback to first available backend
        if available:
            logger.warning(f"Preferred backend '{preferred}' not available, using '{available[0]}'")
            return available[0]
        
        return None