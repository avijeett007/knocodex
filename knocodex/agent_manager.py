#!/usr/bin/env python3
"""
Agent manager for Knocodex
"""

import os
import sys
import shutil
import subprocess
import logging
import time
import signal
import json
from pathlib import Path
import pkg_resources
import redis

from .config import Config
from .project_manager import ProjectManager

logger = logging.getLogger("knocodex.agent_manager")

class AgentManager:
    """Agent manager for Knocodex"""

    def __init__(self, project_path):
        """Initialize the agent manager"""
        self.project_path = Path(project_path)
        self.config = Config(project_path)

        # Get project configuration
        try:
            self.project_config = self.config.get_project_config()
            self.agent_type = self.project_config["agent_type"]
        except Exception as e:
            logger.warning(f"Failed to get project configuration: {e}")
            logger.info("Using global configuration")
            self.project_config = None
            global_config = self.config.get_global_config()
            self.agent_type = global_config["agent_type"]

        # Set up paths
        self.knocodex_dir = self.project_path / ".knocodex"
        self.logs_dir = self.knocodex_dir / "logs"
        self.commands_dir = self.knocodex_dir / "commands"
        self.tasks_dir = self.knocodex_dir / "tasks"
        self.venv_dir = self.knocodex_dir / "venv"

        # Get template paths
        self.template_dir = Path(pkg_resources.resource_filename("knocodex", "templates"))
        
        # Initialize workflow components
        self.redis_conn = None
        self.project_manager = None
        self.workflow_engine = None
        self.queue_manager = None
        
        # Try to initialize Redis connection
        try:
            from redis import Redis
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
            self.redis_conn = Redis.from_url(redis_url)
            
            # Initialize workflow components if Redis is available
            from .project_manager import ProjectManager
            from .workflow_engine import SubtaskWorkflowEngine, WorkflowConfig
            from .utils.redis_utils import ProjectQueueManager
            
            # Check if ProjectManager accepts a Config object or a string path
            import inspect
            try:
                project_manager_params = inspect.signature(ProjectManager.__init__).parameters
                if 'config' in project_manager_params and 'redis_client' in project_manager_params:
                    # If it expects a Config object and Redis client
                    self.project_manager = ProjectManager(self.config, self.redis_conn)
                else:
                    # If it expects something else, create it with minimal params
                    self.project_manager = ProjectManager(redis_url)
            except Exception as e:
                logger.warning(f"Failed to create ProjectManager: {e}")
                # Fallback initialization
                self.project_manager = ProjectManager(redis_url)
            
            # Initialize workflow engine with Redis connection and config
            workflow_config = WorkflowConfig()
            self.workflow_engine = SubtaskWorkflowEngine(self.redis_conn, workflow_config)
            
            # Initialize queue manager with Redis URL
            self.queue_manager = ProjectQueueManager(redis_url=redis_url)
        except Exception as e:
            logger.warning(f"Failed to initialize workflow components: {e}")

    def init_project(self, agent_type=None):
        """Initialize a project for Knocodex"""
        # Create directories
        self.knocodex_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.commands_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        # Create project configuration
        if agent_type:
            self.config.update_project_config({"agent_type": agent_type})
            self.agent_type = agent_type
        else:
            self.config.create_project_config()
            self.project_config = self.config.get_project_config()
            self.agent_type = self.project_config["agent_type"]

        # Create virtual environment
        if not self.venv_dir.exists():
            logger.info("Creating virtual environment...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", str(self.venv_dir)],
                    check=True,
                )
                logger.info("Virtual environment created successfully")

                # Install dependencies
                logger.info("Installing dependencies...")
                pip_path = self.venv_dir / "bin" / "pip"
                subprocess.run(
                    [str(pip_path), "install", "redis", "rq", "rq-dashboard"],
                    check=True,
                )
                logger.info("Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create virtual environment: {e}")

        # Create Claude commands if using Claude
        if self.agent_type == "claude":
            self._create_claude_commands()

        # Create CLAUDE.md if using Claude
        if self.agent_type == "claude" and not (self.project_path / "CLAUDE.md").exists():
            self._create_claude_md()

        logger.info("Project initialization complete")

    def _create_claude_commands(self):
        """Create custom Claude commands"""
        logger.info("Creating custom Claude commands...")

        # Create .claude/commands directory
        claude_commands_dir = self.project_path / ".claude" / "commands"
        claude_commands_dir.mkdir(parents=True, exist_ok=True)

        # Copy command templates
        command_templates = [
            "analyze-github-issue.md",
            "implement-github-issue.md",
            "document-project.md",
            "review-pull-request.md",
        ]

        for template in command_templates:
            source = self.template_dir / "commands" / template
            destination = claude_commands_dir / template

            # Skip if the file already exists
            if destination.exists():
                continue

            # Copy the template
            try:
                with open(source, "r") as src_file:
                    content = src_file.read()

                with open(destination, "w") as dest_file:
                    dest_file.write(content)

                logger.info(f"Created command: {template}")
            except Exception as e:
                logger.error(f"Failed to create command {template}: {e}")

    def _create_claude_md(self):
        """Create CLAUDE.md file"""
        logger.info("Creating CLAUDE.md file...")

        try:
            source = self.template_dir / "CLAUDE.md"
            destination = self.project_path / "CLAUDE.md"

            with open(source, "r") as src_file:
                content = src_file.read()

            with open(destination, "w") as dest_file:
                dest_file.write(content)

            logger.info("Created CLAUDE.md file")
        except Exception as e:
            logger.error(f"Failed to create CLAUDE.md file: {e}")

    def import_mcp_servers(self):
        """Import MCP servers from Claude Desktop"""
        if self.agent_type != "claude":
            logger.warning("MCP servers are only supported with Claude agent")
            return

        logger.info("Importing MCP servers from Claude Desktop...")

        try:
            # Check if Claude is installed
            claude_path = shutil.which("claude")
            if not claude_path:
                logger.error("Claude Code is not installed")
                return

            # Run the command to import MCP servers
            subprocess.run(
                [claude_path, "mcp", "add-from-claude-desktop"],
                check=True,
            )

            logger.info("MCP servers imported successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to import MCP servers: {e}")

    def start(self):
        """Start the autonomous agent"""
        logger.info(f"Starting {self.agent_type} agent...")

        # Create directories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.commands_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        if self.agent_type == "claude":
            # Start Claude agent
            self._start_claude_agent()
        elif self.agent_type == "aider":
            logger.error("Aider agent is not yet supported")
            return
        else:
            logger.error(f"Unknown agent type: {self.agent_type}")
            return

        # Start Redis
        self._start_redis()

        # Start worker (legacy single-task processor)
        self._start_worker()
        
        # Start subtask worker (new subtask-based workflow)
        self._start_subtask_worker()

        # Start dashboard
        self._start_dashboard()

        # Start main loop
        self._start_main_loop()

    def _start_claude_agent(self):
        """Start the Claude agent"""
        logger.info("Starting Claude agent...")

        # Start Redis if not running
        self._start_redis()

        # Start worker
        self._start_worker()

        # Start dashboard
        self._start_dashboard()

        # Start main loop
        self._start_main_loop()

    def _start_redis(self):
        """Start Redis server"""
        logger.info("Starting Redis server...")

        try:
            # Check if Redis is running
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and "PONG" in result.stdout:
                logger.info("Redis server is already running")
                return

            # Start Redis
            if os.name == "posix":
                subprocess.run(
                    ["brew", "services", "start", "redis"],
                    check=True,
                )
                logger.info("Redis server started successfully")
            else:
                logger.error("Automatic starting of Redis is only supported on macOS")
                logger.info("Please start Redis manually")
        except Exception as e:
            logger.error(f"Failed to start Redis server: {e}")

    def _start_worker(self):
        """Start the worker process"""
        logger.info("Starting worker process...")

        # Check if worker is already running
        worker_pid_file = self.knocodex_dir / "worker.pid"
        if worker_pid_file.exists():
            with open(worker_pid_file, "r") as f:
                pid = int(f.read().strip())

            try:
                # Check if process is running
                os.kill(pid, 0)
                logger.info(f"Worker is already running with PID {pid}")
                return
            except OSError:
                # Process is not running
                logger.info(f"Removing stale worker PID file")
                worker_pid_file.unlink()

        # Start worker
        try:
            # Create worker script if it doesn't exist
            worker_script = self.knocodex_dir / "worker.py"
            if not worker_script.exists():
                self._create_worker_script()

            # Start worker process
            worker_log = self.logs_dir / "worker.log"
            worker_process = subprocess.Popen(
                [
                    str(self.venv_dir / "bin" / "python"),
                    str(worker_script),
                ],
                stdout=open(worker_log, "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            # Save worker PID
            with open(worker_pid_file, "w") as f:
                f.write(str(worker_process.pid))

            logger.info(f"Worker started with PID {worker_process.pid}")
        except Exception as e:
            logger.error(f"Failed to start worker process: {e}")

    def _create_worker_script(self):
        """Create the worker script"""
        logger.info("Creating worker script...")

        try:
            source = self.template_dir / "worker.py"
            destination = self.knocodex_dir / "worker.py"

            with open(source, "r") as src_file:
                content = src_file.read()

            with open(destination, "w") as dest_file:
                dest_file.write(content)

            # Make the script executable
            os.chmod(destination, 0o755)

            logger.info("Created worker script")
        except Exception as e:
            logger.error(f"Failed to create worker script: {e}")

    def _start_dashboard(self):
        """Start the RQ dashboard"""
        logger.info("Starting RQ dashboard...")

        # Check if dashboard is already running
        dashboard_pid_file = self.knocodex_dir / "dashboard.pid"
        if dashboard_pid_file.exists():
            with open(dashboard_pid_file, "r") as f:
                pid = int(f.read().strip())

            try:
                # Check if process is running
                os.kill(pid, 0)
                logger.info(f"Dashboard is already running with PID {pid}")
                return
            except OSError:
                # Process is not running
                logger.info(f"Removing stale dashboard PID file")
                dashboard_pid_file.unlink()

        # Start dashboard
        try:
            # Start dashboard process
            dashboard_log = self.logs_dir / "dashboard.log"
            dashboard_process = subprocess.Popen(
                [
                    str(self.venv_dir / "bin" / "rq-dashboard"),
                    "-H", "localhost",
                    "-p", "9181",
                ],
                stdout=open(dashboard_log, "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            # Save dashboard PID
            with open(dashboard_pid_file, "w") as f:
                f.write(str(dashboard_process.pid))

            logger.info(f"Dashboard started with PID {dashboard_process.pid}")
        except Exception as e:
            logger.error(f"Failed to start dashboard process: {e}")

    def _start_main_loop(self):
        """Start the main polling loop"""
        logger.info("Starting main polling loop...")

        # Create main loop script if it doesn't exist
        main_loop_script = self.knocodex_dir / "main_loop.py"
        if not main_loop_script.exists():
            self._create_main_loop_script()

        # Start main loop process
        try:
            main_loop_log = self.logs_dir / "main_loop.log"
            main_loop_process = subprocess.Popen(
                [
                    str(self.venv_dir / "bin" / "python"),
                    str(main_loop_script),
                ],
                stdout=open(main_loop_log, "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            # Save main loop PID
            with open(self.knocodex_dir / "main_loop.pid", "w") as f:
                f.write(str(main_loop_process.pid))

            logger.info(f"Main loop started with PID {main_loop_process.pid}")
        except Exception as e:
            logger.error(f"Failed to start main loop process: {e}")

    def _create_main_loop_script(self):
        """Create the main loop script"""
        logger.info("Creating main loop script...")

        try:
            source = self.template_dir / "main_loop.py"
            destination = self.knocodex_dir / "main_loop.py"

            with open(source, "r") as src_file:
                content = src_file.read()

            with open(destination, "w") as dest_file:
                dest_file.write(content)

            # Make the script executable
            os.chmod(destination, 0o755)

            logger.info("Created main loop script")
        except Exception as e:
            logger.error(f"Failed to create main loop script: {e}")

    def stop(self):
        """Stop the autonomous agent"""
        logger.info("Stopping autonomous agent...")

        # Stop main loop
        self._stop_process("main_loop.pid")

        # Stop dashboard
        self._stop_process("dashboard.pid")

        # Stop worker
        self._stop_process("worker.pid")
        
        # Stop subtask worker
        self._stop_process("subtask_worker.pid")

        logger.info("Autonomous agent stopped")

    def _stop_process(self, pid_file):
        """Stop a process using its PID file"""
        pid_file_path = self.knocodex_dir / pid_file
        if not pid_file_path.exists():
            logger.info(f"No PID file found for {pid_file}")
            return

        try:
            with open(pid_file_path, "r") as f:
                pid = int(f.read().strip())

            # Try to terminate the process
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to process {pid}")

                # Wait for the process to terminate
                for _ in range(10):
                    try:
                        os.kill(pid, 0)
                        time.sleep(0.5)
                    except OSError:
                        break

                # If the process is still running, kill it
                try:
                    os.kill(pid, 0)
                    os.kill(pid, signal.SIGKILL)
                    logger.info(f"Sent SIGKILL to process {pid}")
                except OSError:
                    pass
            except OSError:
                logger.info(f"Process {pid} is not running")

            # Remove the PID file
            pid_file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to stop process {pid_file}: {e}")

    def status(self):
        """Get the status of the autonomous agent"""
        status = {
            "agent_type": self.agent_type,
            "worker_running": False,
            "subtask_worker_running": False,
            "redis_running": False,
            "dashboard_running": False,
            "main_loop_running": False,
            "workflow_engine": self.workflow_engine is not None,
            "project_manager": self.project_manager is not None
        }

        # Check worker
        worker_pid_file = self.knocodex_dir / "worker.pid"
        if worker_pid_file.exists():
            with open(worker_pid_file, "r") as f:
                pid = int(f.read().strip())

            try:
                os.kill(pid, 0)
                status["worker_running"] = True
            except OSError:
                pass
                
        # Check subtask worker
        subtask_worker_pid_file = self.knocodex_dir / "subtask_worker.pid"
        if subtask_worker_pid_file.exists():
            with open(subtask_worker_pid_file, "r") as f:
                pid = int(f.read().strip())

            try:
                os.kill(pid, 0)
                status["subtask_worker_running"] = True
            except OSError:
                pass

        # Check Redis
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and "PONG" in result.stdout:
                status["redis_running"] = True
        except Exception:
            pass

        # Check dashboard
        dashboard_pid_file = self.knocodex_dir / "dashboard.pid"
        if dashboard_pid_file.exists():
            with open(dashboard_pid_file, "r") as f:
                pid = int(f.read().strip())

            try:
                os.kill(pid, 0)
                status["dashboard_running"] = True
            except OSError:
                pass

        # Check main loop
        main_loop_pid_file = self.knocodex_dir / "main_loop.pid"
        if main_loop_pid_file.exists():
            with open(main_loop_pid_file, "r") as f:
                pid = int(f.read().strip())

            try:
                os.kill(pid, 0)
                status["main_loop_running"] = True
            except OSError:
                pass
                
        # Add project information if available
        if self.project_manager:
            status["projects"] = self.project_manager.list_projects()
            
            # Add active workflows if workflow engine is available
            if self.workflow_engine:
                status["active_workflows"] = []
                # This would need to be implemented in the workflow engine

        return status

    def generate_docs(self):
        """Generate project documentation"""
        if self.agent_type == "claude":
            self._generate_claude_docs()
        elif self.agent_type == "aider":
            logger.error("Aider agent is not yet supported")
        else:
            logger.error(f"Unknown agent type: {self.agent_type}")

    def start_dashboard(self):
        """Start the RQ dashboard"""
        self._start_dashboard()

    def _generate_claude_docs(self):
        """Generate documentation using Claude"""
        logger.info("Generating documentation using Claude...")

        try:
            # Check if Claude is installed
            claude_path = shutil.which("claude")
            if not claude_path:
                logger.error("Claude Code is not installed")
                return

            # Run the command to generate documentation
            subprocess.run(
                [claude_path, "-p", "/project:document-project"],
                check=True,
            )

            logger.info("Documentation generated successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate documentation: {e}")
            
    def _start_subtask_worker(self):
        """Start the subtask worker process"""
        logger.info("Starting subtask worker process...")

        # Check if subtask worker is already running
        subtask_worker_pid_file = self.knocodex_dir / "subtask_worker.pid"
        if subtask_worker_pid_file.exists():
            with open(subtask_worker_pid_file, "r") as f:
                pid = int(f.read().strip())

            try:
                # Check if process is running
                os.kill(pid, 0)
                logger.info(f"Subtask worker is already running with PID {pid}")
                return
            except OSError:
                # Process is not running
                logger.info(f"Removing stale subtask worker PID file")
                subtask_worker_pid_file.unlink()

        # Start subtask worker
        try:
            # Create subtask worker script if it doesn't exist
            subtask_worker_script = self.knocodex_dir / "subtask_worker.py"
            if not subtask_worker_script.exists():
                self._create_subtask_worker_script()

            # Start subtask worker process
            subtask_worker_log = self.logs_dir / "subtask_worker.log"
            subtask_worker_process = subprocess.Popen(
                [
                    str(self.venv_dir / "bin" / "python"),
                    str(subtask_worker_script),
                ],
                stdout=open(subtask_worker_log, "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            # Save subtask worker PID
            with open(subtask_worker_pid_file, "w") as f:
                f.write(str(subtask_worker_process.pid))

            logger.info(f"Subtask worker started with PID {subtask_worker_process.pid}")
        except Exception as e:
            logger.error(f"Failed to start subtask worker process: {e}")
            
    def _create_subtask_worker_script(self):
        """Create the subtask worker script"""
        logger.info("Creating subtask worker script...")

        try:
            # Use the new subtask_worker.py template
            source_file = pkg_resources.resource_filename("knocodex", "subtask_worker.py")
            destination = self.knocodex_dir / "subtask_worker.py"

            # If the source file doesn't exist in package resources, copy from templates directory
            if not os.path.exists(source_file):
                source_file = str(self.template_dir.parent / "subtask_worker.py")

            with open(source_file, "r") as src_file:
                content = src_file.read()

            with open(destination, "w") as dest_file:
                dest_file.write(content)

            # Make the script executable
            os.chmod(destination, 0o755)

            logger.info("Created subtask worker script")
        except Exception as e:
            logger.error(f"Failed to create subtask worker script: {e}")
            
    def create_project(self, project_name, repository_url, labels=None):
        """Create a new project configuration for subtask workflow"""
        if not self.project_manager:
            logger.error("Project manager is not initialized")
            return None
            
        try:
            labels = labels or ["knocodex"]
            project_id = self.project_manager.create_project(
                name=project_name,
                repository_url=repository_url,
                local_path=str(self.project_path),
                github_token=os.environ.get("GITHUB_TOKEN", ""),
                labels=labels,
                max_concurrent_workflows=3,
                max_concurrent_subtasks=10
            )
            
            logger.info(f"Created project {project_name} with ID {project_id}")
            return project_id
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None
            
    def list_projects(self):
        """List all projects managed by knocodex"""
        if not self.project_manager:
            logger.error("Project manager is not initialized")
            return []
            
        try:
            return self.project_manager.list_projects()
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
            
    def get_project_status(self, project_id):
        """Get status of a specific project and its workflows"""
        if not self.project_manager or not self.workflow_engine:
            logger.error("Project manager or workflow engine is not initialized")
            return None
            
        try:
            project = self.project_manager.get_project(project_id)
            if not project:
                logger.error(f"Project {project_id} not found")
                return None
                
            metrics = self.project_manager.get_project_metrics(project_id)
            queue_status = self.queue_manager.get_queue_status(project_id) if self.queue_manager else {}
            
            # Get all subtask plans for this project
            active_workflows = []
            # This would need to be implemented in the workflow engine to list active workflows by project
            
            return {
                "project": project.__dict__,
                "metrics": metrics.__dict__ if metrics else {},
                "queue": queue_status,
                "active_workflows": active_workflows
            }
        except Exception as e:
            logger.error(f"Failed to get project status: {e}")
            return None
            
    def process_github_issue(self, issue_number, project_id=None):
        """Process a GitHub issue with subtasks"""
        if not self.workflow_engine:
            logger.error("Workflow engine is not initialized")
            return False
            
        try:
            # Default to the first project if none specified
            if not project_id and self.project_manager:
                projects = self.project_manager.list_projects()
                if projects:
                    project_id = projects[0]
                else:
                    project_id = "default"
                    
            # Get issue details
            import subprocess
            result = subprocess.run(
                ["gh", "issue", "view", str(issue_number), "--json", "number,title,body,labels"],
                capture_output=True,
                text=True,
                check=True
            )
            
            issue_data = json.loads(result.stdout)
            
            # Process the issue with subtasks
            plan_id = self.workflow_engine.process_github_issue(project_id, issue_data)
            
            logger.info(f"Started processing GitHub issue {issue_number} with plan ID {plan_id}")
            return plan_id
        except Exception as e:
            logger.error(f"Failed to process GitHub issue {issue_number}: {e}")
            return False
