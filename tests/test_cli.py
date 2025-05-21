#!/usr/bin/env python3
"""
Tests for the CLI module
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from knocodex.cli import main

class TestCLI(unittest.TestCase):
    """Tests for the CLI module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test the main help command"""
        result = self.runner.invoke(main, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Knocodex", result.output)
        self.assertIn("--help", result.output)
        self.assertIn("--version", result.output)
    
    @patch("knocodex.cli.check_requirements")
    @patch("knocodex.cli.setup_global_config")
    def test_setup_command(self, mock_setup_global_config, mock_check_requirements):
        """Test the setup command"""
        # Set up mocks
        mock_check_requirements.return_value = True
        mock_setup_global_config.return_value = True
        
        # Run the command
        result = self.runner.invoke(main, ["setup"])
        
        # Check the result
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Setting up Knocodex globally", result.output)
        self.assertIn("Knocodex setup complete", result.output)
        
        # Check that the mocks were called
        mock_check_requirements.assert_called_once()
        mock_setup_global_config.assert_called_once_with("claude")
    
    @patch("knocodex.cli.AgentManager")
    def test_init_command(self, mock_agent_manager):
        """Test the init command"""
        # Set up mocks
        mock_instance = MagicMock()
        mock_instance.agent_type = "claude"
        mock_agent_manager.return_value = mock_instance
        
        # Run the command
        result = self.runner.invoke(main, ["init"])
        
        # Check the result
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Initializing project for Knocodex", result.output)
        self.assertIn("Project initialization complete", result.output)
        
        # Check that the mocks were called
        mock_agent_manager.assert_called_once()
        mock_instance.init_project.assert_called_once_with(None)
        mock_instance.import_mcp_servers.assert_called_once()
    
    @patch("knocodex.cli.AgentManager")
    def test_start_command(self, mock_agent_manager):
        """Test the start command"""
        # Set up mocks
        mock_instance = MagicMock()
        mock_agent_manager.return_value = mock_instance
        
        # Run the command
        result = self.runner.invoke(main, ["start"])
        
        # Check the result
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Starting Knocodex autonomous agent", result.output)
        self.assertIn("Knocodex agent started", result.output)
        
        # Check that the mocks were called
        mock_agent_manager.assert_called_once()
        mock_instance.start.assert_called_once()
    
    @patch("knocodex.cli.AgentManager")
    def test_stop_command(self, mock_agent_manager):
        """Test the stop command"""
        # Set up mocks
        mock_instance = MagicMock()
        mock_agent_manager.return_value = mock_instance
        
        # Run the command
        result = self.runner.invoke(main, ["stop"])
        
        # Check the result
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Stopping Knocodex autonomous agent", result.output)
        self.assertIn("Knocodex agent stopped", result.output)
        
        # Check that the mocks were called
        mock_agent_manager.assert_called_once()
        mock_instance.stop.assert_called_once()
    
    @patch("knocodex.cli.AgentManager")
    def test_status_command(self, mock_agent_manager):
        """Test the status command"""
        # Set up mocks
        mock_instance = MagicMock()
        mock_instance.status.return_value = {
            "agent_type": "claude",
            "worker_running": True,
            "redis_running": True,
            "dashboard_running": True,
        }
        mock_agent_manager.return_value = mock_instance
        
        # Run the command
        result = self.runner.invoke(main, ["status"])
        
        # Check the result
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Checking Knocodex agent status", result.output)
        self.assertIn("Agent type: claude", result.output)
        self.assertIn("Worker running: Yes", result.output)
        self.assertIn("Redis running: Yes", result.output)
        self.assertIn("Dashboard running: Yes", result.output)
        
        # Check that the mocks were called
        mock_agent_manager.assert_called_once()
        mock_instance.status.assert_called_once()

if __name__ == "__main__":
    unittest.main()
