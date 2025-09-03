# Contributing to GitHub Actions Optimizer

Thank you for your interest in contributing to the GitHub Actions Optimizer! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Submitting Changes](#submitting-changes)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Security](#security)
- [Getting Help](#getting-help)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.8+ installed
- Git installed and configured
- GitHub CLI (`gh`) installed
- Familiarity with GitHub Actions workflows

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/github-actions-optimizer.git
   cd github-actions-optimizer
   ```

3. **Set up the development environment**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Verify installation**:
   ```bash
   gh actions-optimizer --help
   ```

## Development Process

### Branching Strategy

- `main` branch contains stable, production-ready code
- Create feature branches from `main` for new development
- Use descriptive branch names: `feature/add-workflow-validation`, `fix/memory-leak`, `docs/update-readme`

### Workflow

1. **Create an issue** for bugs or feature requests (if one doesn't exist)
2. **Create a branch** from `main`
3. **Make your changes** following our coding standards
4. **Write or update tests** for your changes
5. **Run the test suite** to ensure nothing is broken
6. **Commit your changes** with clear, descriptive messages
7. **Push to your fork** and create a pull request

## Submitting Changes

### Pull Request Process

1. **Ensure your PR**:
   - Has a clear title and description
   - References related issues (e.g., "Fixes #123")
   - Includes tests for new functionality
   - Updates documentation if needed
   - Passes all automated checks

2. **PR Requirements**:
   - All tests must pass
   - Code coverage must not decrease
   - Pre-commit checks must pass
   - At least one review from a maintainer
   - No merge conflicts with `main`

3. **Review Process**:
   - Maintainers will review your PR
   - Address any feedback promptly
   - Copilot may provide automated reviews
   - Force-push is discouraged after review starts

### Commit Guidelines

Follow conventional commit format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

Example:
```
feat(optimizer): add support for reusable workflows

Add functionality to analyze and optimize reusable workflows
across repositories for better maintainability.

Closes #45
```

## Code Standards

### Python Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters (Black formatter)
- Use descriptive variable and function names
- Add docstrings for all public functions and classes

### Code Quality Tools

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Static type checking
- **bandit**: Security analysis
- **pre-commit**: Automated quality checks

All tools are configured in `pyproject.toml` and `.pre-commit-config.yaml`.

### Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions and classes
- Update command help text for CLI changes
- Include examples in documentation

## Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Maintain or improve code coverage
- Tests should be deterministic and fast

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=gh_actions_optimizer

# Run specific test file
python -m pytest tests/test_optimizer.py

# Run with verbose output
python -m pytest -v
```

### Test Categories

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows
- **Performance tests**: Verify optimization effectiveness

## Security

### Security Considerations

- Never commit secrets or sensitive information
- Validate all inputs, especially from external sources
- Follow the principle of least privilege
- Be cautious with file system operations
- Review security implications of new dependencies

### Reporting Security Issues

Please see our [Security Policy](SECURITY.md) for information on reporting security vulnerabilities.

## Getting Help

### Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Project Issues](https://github.com/datas-world/github-actions-optimizer/issues)

### Communication

- **Issues**: For bug reports and feature requests
- **Discussions**: For general questions and ideas
- **Pull Requests**: For code contributions

### Maintainer Response Times

- Issues will be triaged within 48 hours
- Pull requests will receive initial review within 5 business days
- Security issues will be addressed immediately

## Recognition

Contributors will be:
- Listed in the project's contributor list
- Credited in release notes for significant contributions
- Invited to collaborate on future enhancements

Thank you for contributing to making GitHub Actions optimization better for everyone!

---

*This contributing guide is regularly updated to reflect current best practices and project needs.*