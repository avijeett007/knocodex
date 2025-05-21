#!/usr/bin/env python3
"""
Script to create a new Knocodex project
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def create_project(project_name, project_path=None):
    """Create a new Knocodex project"""
    # Determine the project path
    if project_path:
        project_dir = Path(project_path) / project_name
    else:
        project_dir = Path.cwd() / project_name
    
    # Create the project directory
    print(f"Creating project directory: {project_dir}")
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a basic README.md
    readme_path = project_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(f"# {project_name}\n\n")
        f.write("This project is managed with Knocodex, an open-source Python library for autonomous coding with AI agents.\n\n")
        f.write("## Getting Started\n\n")
        f.write("```bash\n")
        f.write("# Initialize the project\n")
        f.write("cd " + project_name + "\n")
        f.write("knocodex init\n\n")
        f.write("# Start the autonomous agent\n")
        f.write("knocodex start\n")
        f.write("```\n")
    
    # Create a basic .gitignore
    gitignore_path = project_dir / ".gitignore"
    with open(gitignore_path, "w") as f:
        f.write("# Python\n")
        f.write("__pycache__/\n")
        f.write("*.py[cod]\n")
        f.write("*$py.class\n")
        f.write("*.so\n")
        f.write("*.egg-info/\n")
        f.write("dist/\n")
        f.write("build/\n")
        f.write("*.egg\n\n")
        f.write("# Virtual environments\n")
        f.write("venv/\n")
        f.write("env/\n")
        f.write(".env/\n\n")
        f.write("# Knocodex\n")
        f.write(".knocodex/\n")
    
    # Initialize git repository
    try:
        print(f"Initializing git repository in {project_dir}")
        subprocess.run(["git", "init"], cwd=project_dir, check=True)
        
        # Add files to git
        subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
        
        # Initial commit
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir, check=True)
        
        print("Git repository initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to initialize git repository: {e}")
        print("You can initialize it manually later")
    
    print(f"\nProject {project_name} created successfully!")
    print(f"To get started, run:\n")
    print(f"cd {project_dir}")
    print(f"knocodex init")
    print(f"knocodex start")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Create a new Knocodex project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--path", help="Path where the project should be created")
    
    args = parser.parse_args()
    
    create_project(args.project_name, args.path)

if __name__ == "__main__":
    main()
