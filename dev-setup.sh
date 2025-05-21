#!/usr/bin/env bash
# Development setup script for Knocodex

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Log function
log() {
  local level=$1
  local message=$2
  
  case $level in
    "INFO")
      echo -e "${BLUE}[INFO]${NC} $message"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[SUCCESS]${NC} $message"
      ;;
    "WARNING")
      echo -e "${YELLOW}[WARNING]${NC} $message"
      ;;
    "ERROR")
      echo -e "${RED}[ERROR]${NC} $message"
      ;;
    *)
      echo -e "$message"
      ;;
  esac
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
  log "ERROR" "Python 3 is not installed. Please install Python 3 and try again."
  exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
  log "ERROR" "pip3 is not installed. Please install pip3 and try again."
  exit 1
fi

# Create a virtual environment
log "INFO" "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install the package in development mode
log "INFO" "Installing Knocodex in development mode..."
pip install -e .

# Install development dependencies
log "INFO" "Installing development dependencies..."
pip install pytest pytest-cov flake8 black

# Run tests
log "INFO" "Running tests..."
pytest

# Success message
log "SUCCESS" "Development setup complete!"
log "INFO" "To activate the virtual environment, run:"
echo "source venv/bin/activate"

log "INFO" "To run tests, use:"
echo "pytest"

log "INFO" "To check code style, use:"
echo "flake8 knocodex"

log "INFO" "To format code, use:"
echo "black knocodex"

log "INFO" "To build the package, use:"
echo "python setup.py sdist bdist_wheel"
