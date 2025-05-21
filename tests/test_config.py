#!/usr/bin/env python3
"""
Tests for the Config class
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

from knocodex.config import Config

class TestConfig(unittest.TestCase):
    """Tests for the Config class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_create_global_config(self):
        """Test creating a global configuration"""
        # Create a config instance with a custom home directory
        config = Config()
        config.home_dir = self.project_path
        config.global_config_dir = self.project_path / ".knocodex"
        config.global_config_file = config.global_config_dir / "config.json"
        
        # Create the global config
        config_file = config.create_global_config()
        
        # Check that the config file was created
        self.assertTrue(config_file.exists())
        
        # Check that the config file contains the default configuration
        with open(config_file, "r") as f:
            config_data = json.load(f)
        
        self.assertEqual(config_data["agent_type"], "claude")
        self.assertEqual(config_data["redis_url"], "redis://localhost:6379")
        self.assertEqual(config_data["redis_queue"], "knocodex")
    
    def test_create_project_config(self):
        """Test creating a project configuration"""
        # Create a config instance with a custom project path
        config = Config(self.project_path)
        
        # Set up a custom global config for testing
        config.home_dir = self.project_path
        config.global_config_dir = self.project_path / ".knocodex"
        config.global_config_dir.mkdir(parents=True, exist_ok=True)
        config.global_config_file = config.global_config_dir / "config.json"
        
        # Create a global config with a custom agent type
        with open(config.global_config_file, "w") as f:
            json.dump({"agent_type": "test_agent"}, f)
        
        # Create the project config
        config_file = config.create_project_config()
        
        # Check that the config file was created
        self.assertTrue(config_file.exists())
        
        # Check that the config file contains the inherited agent type
        with open(config_file, "r") as f:
            config_data = json.load(f)
        
        self.assertEqual(config_data["agent_type"], "test_agent")
    
    def test_update_project_config(self):
        """Test updating a project configuration"""
        # Create a config instance with a custom project path
        config = Config(self.project_path)
        
        # Set up a custom global config for testing
        config.home_dir = self.project_path
        config.global_config_dir = self.project_path / ".knocodex"
        config.global_config_dir.mkdir(parents=True, exist_ok=True)
        config.global_config_file = config.global_config_dir / "config.json"
        
        # Create a global config with a custom agent type
        with open(config.global_config_file, "w") as f:
            json.dump({"agent_type": "test_agent"}, f)
        
        # Create the project config
        config.create_project_config()
        
        # Update the project config
        config.update_project_config({"github_repo": "test/repo"})
        
        # Check that the config file was updated
        with open(config.project_config_file, "r") as f:
            config_data = json.load(f)
        
        self.assertEqual(config_data["github_repo"], "test/repo")

if __name__ == "__main__":
    unittest.main()
