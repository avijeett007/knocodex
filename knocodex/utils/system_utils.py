#!/usr/bin/env python3
"""
System utilities for Knocodex
"""

import os
import sys
import shutil
import subprocess
import logging
import platform
from pathlib import Path

logger = logging.getLogger("knocodex.utils.system_utils")

def check_command_exists(command):
    """Check if a command exists in the system PATH"""
    return shutil.which(command) is not None

def get_command_path(command):
    """Get the full path of a command"""
    return shutil.which(command)

def run_command(command, check=True, capture_output=True):
    """Run a shell command"""
    try:
        if isinstance(command, str):
            command = command.split()
        
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            check=check,
        )
        
        return {
            "success": True,
            "returncode": result.returncode,
            "stdout": result.stdout if capture_output else "",
            "stderr": result.stderr if capture_output else "",
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "returncode": e.returncode,
            "stdout": e.stdout if capture_output else "",
            "stderr": e.stderr if capture_output else "",
            "error": str(e),
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "",
            "error": str(e),
        }

def create_directory(path, parents=True, exist_ok=True):
    """Create a directory"""
    try:
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def write_file(path, content):
    """Write content to a file"""
    try:
        with open(path, "w") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write to file {path}: {e}")
        return False

def read_file(path):
    """Read content from a file"""
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        return None

def file_exists(path):
    """Check if a file exists"""
    return Path(path).is_file()

def directory_exists(path):
    """Check if a directory exists"""
    return Path(path).is_dir()

def get_os_info():
    """Get information about the operating system"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }

def is_macos():
    """Check if the operating system is macOS"""
    return platform.system() == "Darwin"

def is_linux():
    """Check if the operating system is Linux"""
    return platform.system() == "Linux"

def is_windows():
    """Check if the operating system is Windows"""
    return platform.system() == "Windows"

def get_python_info():
    """Get information about the Python interpreter"""
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "compiler": platform.python_compiler(),
        "build": platform.python_build(),
        "executable": sys.executable,
    }
