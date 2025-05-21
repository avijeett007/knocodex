# Contributing to Knocodex

Thank you for your interest in contributing to Knocodex! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. **Fork the Repository**:
   - Fork the repository on GitHub
   - Clone your fork locally

2. **Set Up Development Environment**:
   ```bash
   # Clone your fork
   git clone https://github.com/your-username/knocodex.git
   cd knocodex
   
   # Install in development mode
   pip install -e .
   
   # Install development dependencies
   pip install pytest pytest-cov flake8
   ```

3. **Create a Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused on a single task

### Testing

- Write unit tests for all new functionality
- Run tests before submitting a pull request:
  ```bash
  pytest
  ```

- Aim for high test coverage:
  ```bash
  pytest --cov=knocodex
  ```

### Documentation

- Update documentation for any changes to the API
- Add examples for new features
- Keep the README.md up to date

## Pull Request Process

1. **Update your fork**:
   ```bash
   git remote add upstream https://github.com/original-owner/knocodex.git
   git fetch upstream
   git merge upstream/main
   ```

2. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation

3. **Run tests and linting**:
   ```bash
   pytest
   flake8 knocodex
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature X"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing to Knocodex, you agree that your contributions will be licensed under the project's MIT License.
