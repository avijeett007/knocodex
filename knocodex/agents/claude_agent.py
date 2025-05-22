"""Claude Code agent implementation."""

import os
import subprocess
import shutil
import logging
from typing import Dict, Any, List
from pathlib import Path

from .base_agent import BaseAgent, TaskResult, IssueAnalysis

logger = logging.getLogger(__name__)


class ClaudeAgent(BaseAgent):
    """Claude Code agent for AI-powered coding assistance."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Claude agent."""
        super().__init__(config)
        self.claude_path = shutil.which("claude")
        
        if not self.claude_path:
            logger.warning("Claude Code is not installed or not in PATH")
    
    def validate_config(self) -> bool:
        """Validate Claude agent configuration."""
        if not self.claude_path:
            logger.error("Claude Code is not installed")
            return False
        
        # Check if project has Claude commands
        project_path = Path(self.config.get("project_path", "."))
        claude_commands_dir = project_path / ".claude" / "commands"
        
        if not claude_commands_dir.exists():
            logger.warning("Claude commands directory not found")
            return False
        
        required_commands = [
            "analyze-github-issue.md",
            "implement-github-issue.md", 
            "document-project.md",
            "review-pull-request.md"
        ]
        
        for command in required_commands:
            if not (claude_commands_dir / command).exists():
                logger.warning(f"Missing Claude command: {command}")
                return False
        
        return True
    
    def analyze_issue(self, issue: Dict[str, Any]) -> TaskResult:
        """Analyze a GitHub issue using Claude Code.
        
        Args:
            issue: GitHub issue data containing title, body, labels, etc.
            
        Returns:
            TaskResult with analysis details and implementation plan.
        """
        try:
            if not self.claude_path:
                return TaskResult(
                    success=False,
                    output="",
                    error="Claude Code is not installed"
                )
            
            # Create issue analysis file
            project_path = Path(self.config.get("project_path", "."))
            issue_file = project_path / f"issue-{issue['number']}.md"
            
            with open(issue_file, "w") as f:
                f.write(f"# Issue #{issue['number']}: {issue['title']}\n\n")
                f.write(f"**URL:** {issue['html_url']}\n\n")
                f.write(f"**Body:**\n{issue['body']}\n\n")
                if issue.get('labels'):
                    labels = ", ".join([label['name'] for label in issue['labels']])
                    f.write(f"**Labels:** {labels}\n\n")
            
            # Run Claude analyze command
            result = subprocess.run(
                [self.claude_path, "-p", "/project:analyze-github-issue", str(issue_file)],
                capture_output=True,
                text=True,
                cwd=project_path
            )
            
            # Clean up temporary file
            if issue_file.exists():
                issue_file.unlink()
            
            if result.returncode == 0:
                return TaskResult(
                    success=True,
                    output=result.stdout,
                    metadata={"issue_number": issue['number']}
                )
            else:
                return TaskResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze issue with Claude: {e}")
            return TaskResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def implement_solution(self, issue: Dict[str, Any], plan: str) -> TaskResult:
        """Implement a solution using Claude Code.
        
        Args:
            issue: GitHub issue data
            plan: Implementation plan from analyze_issue
            
        Returns:
            TaskResult with implementation details and modified files.
        """
        try:
            if not self.claude_path:
                return TaskResult(
                    success=False,
                    output="",
                    error="Claude Code is not installed"
                )
            
            # Create implementation context file
            project_path = Path(self.config.get("project_path", "."))
            context_file = project_path / f"implement-issue-{issue['number']}.md"
            
            with open(context_file, "w") as f:
                f.write(f"# Implement Issue #{issue['number']}: {issue['title']}\n\n")
                f.write(f"**Issue URL:** {issue['html_url']}\n\n")
                f.write(f"**Issue Body:**\n{issue['body']}\n\n")
                f.write(f"**Implementation Plan:**\n{plan}\n\n")
            
            # Run Claude implement command
            result = subprocess.run(
                [self.claude_path, "-p", "/project:implement-github-issue", str(context_file)],
                capture_output=True,
                text=True,
                cwd=project_path
            )
            
            # Clean up temporary file
            if context_file.exists():
                context_file.unlink()
            
            if result.returncode == 0:
                return TaskResult(
                    success=True,
                    output=result.stdout,
                    metadata={"issue_number": issue['number']}
                )
            else:
                return TaskResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr
                )
                
        except Exception as e:
            logger.error(f"Failed to implement solution with Claude: {e}")
            return TaskResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def generate_docs(self, files: List[str], context: str = "") -> TaskResult:
        """Generate documentation using Claude Code.
        
        Args:
            files: List of file paths to document
            context: Additional context or requirements
            
        Returns:
            TaskResult with generated documentation.
        """
        try:
            if not self.claude_path:
                return TaskResult(
                    success=False,
                    output="",
                    error="Claude Code is not installed"
                )
            
            project_path = Path(self.config.get("project_path", "."))
            
            # Create documentation context file if needed
            context_file = None
            if context:
                context_file = project_path / "doc-context.md"
                with open(context_file, "w") as f:
                    f.write(f"# Documentation Context\n\n{context}\n\n")
                    if files:
                        f.write("**Files to document:**\n")
                        for file_path in files:
                            f.write(f"- {file_path}\n")
            
            # Run Claude document command
            cmd = [self.claude_path, "-p", "/project:document-project"]
            if context_file:
                cmd.append(str(context_file))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_path
            )
            
            # Clean up temporary file
            if context_file and context_file.exists():
                context_file.unlink()
            
            if result.returncode == 0:
                return TaskResult(
                    success=True,
                    output=result.stdout,
                    files_modified=files
                )
            else:
                return TaskResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr
                )
                
        except Exception as e:
            logger.error(f"Failed to generate docs with Claude: {e}")
            return TaskResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def review_pr(self, pr_data: Dict[str, Any]) -> TaskResult:
        """Review a pull request using Claude Code.
        
        Args:
            pr_data: Pull request data including diff, description, etc.
            
        Returns:
            TaskResult with review comments and suggestions.
        """
        try:
            if not self.claude_path:
                return TaskResult(
                    success=False,
                    output="",
                    error="Claude Code is not installed"
                )
            
            # Create PR review context file
            project_path = Path(self.config.get("project_path", "."))
            pr_file = project_path / f"pr-{pr_data['number']}.md"
            
            with open(pr_file, "w") as f:
                f.write(f"# Pull Request #{pr_data['number']}: {pr_data['title']}\n\n")
                f.write(f"**URL:** {pr_data['html_url']}\n\n")
                f.write(f"**Description:**\n{pr_data['body'] or 'No description provided'}\n\n")
                if pr_data.get('diff_url'):
                    f.write(f"**Diff URL:** {pr_data['diff_url']}\n\n")
            
            # Run Claude review command
            result = subprocess.run(
                [self.claude_path, "-p", "/project:review-pull-request", str(pr_file)],
                capture_output=True,
                text=True,
                cwd=project_path
            )
            
            # Clean up temporary file
            if pr_file.exists():
                pr_file.unlink()
            
            if result.returncode == 0:
                return TaskResult(
                    success=True,
                    output=result.stdout,
                    metadata={"pr_number": pr_data['number']}
                )
            else:
                return TaskResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr
                )
                
        except Exception as e:
            logger.error(f"Failed to review PR with Claude: {e}")
            return TaskResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def health_check(self) -> bool:
        """Check if Claude agent is healthy and ready to work."""
        if not self.validate_config():
            return False
        
        try:
            # Test Claude Code is responsive
            result = subprocess.run(
                [self.claude_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """Get list of Claude agent capabilities."""
        capabilities = super().get_capabilities()
        capabilities.extend([
            "mcp_servers",
            "custom_commands",
            "interactive_coding"
        ])
        return capabilities