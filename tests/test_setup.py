#!/usr/bin/env python3
"""
Tests for the setup utilities
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from knocodex.setup_utils import check_requirements, install_dependencies, setup_github_auth, setup_global_config

class TestSetupUtils(unittest.TestCase):
    """Tests for the setup utilities"""
    
    @patch("knocodex.setup_utils.shutil.which")
    @patch("knocodex.setup_utils.subprocess.run")
    @patch("knocodex.setup_utils.platform.system")
    def test_check_requirements(self, mock_platform_system, mock_subprocess_run, mock_shutil_which):
        """Test checking requirements"""
        # Set up mocks
        mock_platform_system.return_value = "Darwin"
        mock_shutil_which.side_effect = lambda cmd: {
            "brew": "/usr/local/bin/brew",
            "python3": "/usr/local/bin/python3",
            "gh": "/usr/local/bin/gh",
            "claude": "/usr/local/bin/claude",
            "redis-cli": "/usr/local/bin/redis-cli",
        }.get(cmd)
        
        # Mock subprocess.run for gh auth status
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process
        
        # Run the function
        result = check_requirements()
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the mocks were called
        mock_platform_system.assert_called()
        self.assertEqual(mock_shutil_which.call_count, 5)
        mock_subprocess_run.assert_called()
    
    @patch("knocodex.setup_utils.shutil.which")
    @patch("knocodex.setup_utils.subprocess.run")
    @patch("knocodex.setup_utils.platform.system")
    def test_install_dependencies(self, mock_platform_system, mock_subprocess_run, mock_shutil_which):
        """Test installing dependencies"""
        # Set up mocks
        mock_platform_system.return_value = "Darwin"
        mock_shutil_which.side_effect = lambda cmd: {
            "gh": None,
            "redis-cli": None,
            "claude": None,
        }.get(cmd)
        
        # Mock subprocess.run
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        
        # Run the function
        install_dependencies()
        
        # Check that the mocks were called
        mock_platform_system.assert_called()
        self.assertEqual(mock_shutil_which.call_count, 3)
        self.assertEqual(mock_subprocess_run.call_count, 4)  # brew install gh, brew install redis, brew services start redis, npm install -g @anthropic-ai/claude-code
    
    @patch("knocodex.setup_utils.subprocess.run")
    def test_setup_github_auth_already_authenticated(self, mock_subprocess_run):
        """Test setting up GitHub authentication when already authenticated"""
        # Set up mocks
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process
        
        # Run the function
        result = setup_github_auth()
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the mocks were called
        mock_subprocess_run.assert_called_once()
    
    @patch("knocodex.setup_utils.subprocess.run")
    def test_setup_github_auth_not_authenticated(self, mock_subprocess_run):
        """Test setting up GitHub authentication when not authenticated"""
        # Set up mocks
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=1),  # gh auth status fails
            MagicMock(returncode=0),  # gh auth login succeeds
        ]
        
        # Run the function
        result = setup_github_auth()
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the mocks were called
        self.assertEqual(mock_subprocess_run.call_count, 2)
    
    @patch("knocodex.setup_utils.install_dependencies")
    @patch("knocodex.setup_utils.setup_github_auth")
    @patch("knocodex.setup_utils.Config")
    @patch("knocodex.setup_utils.shutil.which")
    @patch("knocodex.setup_utils.setup_claude_mcp_servers")
    def test_setup_global_config(self, mock_setup_claude_mcp_servers, mock_shutil_which, mock_config, mock_setup_github_auth, mock_install_dependencies):
        """Test setting up global configuration"""
        # Set up mocks
        mock_install_dependencies.return_value = True
        mock_setup_github_auth.return_value = True
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_shutil_which.side_effect = lambda cmd: f"/usr/local/bin/{cmd}"
        mock_setup_claude_mcp_servers.return_value = True
        
        # Run the function
        setup_global_config("claude")
        
        # Check that the mocks were called
        mock_install_dependencies.assert_called_once()
        mock_setup_github_auth.assert_called_once()
        mock_config.assert_called_once()
        mock_config_instance.create_global_config.assert_called_once()
        mock_config_instance.update_global_config.assert_called_once()
        mock_setup_claude_mcp_servers.assert_called_once()

if __name__ == "__main__":
    unittest.main()
