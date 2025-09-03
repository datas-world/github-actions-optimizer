# GitHub Copilot Instructions for GitHub Actions Optimizer

## Project Overview
This is a GitHub CLI extension for optimizing GitHub Actions workflows through cost analysis, performance optimization, and security auditing. The project follows strict quality standards and modern Python development practices.

## Code Quality Standards (STRICT - NO EXCEPTIONS)

### Python Requirements
- **Minimum Python Version**: 3.10+ (use modern features like pattern matching)
- **Type Checking**: Strict mypy configuration, all functions must have type annotations
- **Code Style**: Black formatter with 88-character line length
- **Import Sorting**: isort with black profile
- **Linting**: flake8 with strict settings
- **Security**: bandit security scanning
- **Documentation**: pydocstyle for docstring compliance

### Pre-commit Configuration
- ALL changes must pass pre-commit hooks before committing
- Use `pre-commit run --all-files` to check all files
- Never commit code that fails quality checks
- Pre-commit includes: black, isort, flake8, mypy, bandit, pydocstyle, yaml validation

### Code Architecture Rules
- **No monolithic files**: Keep functions and classes focused and small
- **Modular structure**: Use the established package hierarchy
- **Shared utilities**: Place common code in `gh_actions_optimizer/shared/`
- **Type annotations**: Every function parameter and return type must be annotated
- **Error handling**: Proper exception handling with informative messages
- **No lazy imports**: All imports at the top of files (except dynamic command imports)

## Package Structure
```
gh_actions_optimizer/
├── __init__.py          # Package exports and metadata
├── main.py              # Entry point with pattern matching command routing
├── shared/              # Common utilities
│   ├── __init__.py
│   ├── cli.py           # CLI utilities and argument handling
│   ├── data.py          # Sample data generators
│   ├── github.py        # GitHub API integration
│   └── output.py        # Output formatting
├── analyze/             # Workflow analysis
├── cost/                # Cost calculation
├── security/            # Security auditing
├── runners/             # Runner optimization
├── generate/            # Code/config generation
│   ├── runner_setup/
│   └── workflow_patch/
├── validate/            # Validation commands
│   └── runners/
└── benchmark/           # Performance benchmarking
```

## User Requirements and Preferences

### Dependency Management
- **Dependabot Configuration**:
  - Daily updates for all package ecosystems
  - No time/timezone restrictions
  - No pull request limits
  - No grouping (individual decisions)
  - Assignee: @torsknod2
  - Reviewer: @copilot (automatic)
  - Allow all dependency types
  - Apply to all branches
  - Block PRs with old dependencies

### GitHub Actions Best Practices
- Use well-known, proven GitHub Actions over custom implementations
- Maximize caching for dependency management
- Pin actions to specific commit SHAs for security
- Use explicit permissions for all workflows
- Implement concurrency controls to prevent redundant runs

### Testing Requirements
- Use `act` package for local workflow testing
- All tests must pass before committing
- Comprehensive test coverage for all commands
- Test both functionality and error cases

### Code Quality Enforcement
- Maximum strictness in all quality checks
- Fix all linting/type checking issues immediately
- No workarounds unless explicitly authorized
- Static imports only (no dynamic/lazy imports)
- Use proper type stubs (e.g., types-PyYAML)

### GitHub CLI Extension Standards
- Follow GitHub CLI extension conventions
- Proper `extension.yml` configuration
- Command structure: `gh actions-optimizer <command>`
- Support for `--help`, `--version`, `--format`, `--output` flags
- JSON and table output formats
- Quiet mode support

## Development Workflow

### Quality Assurance Process
1. **Before any code changes**: Run `pre-commit run --all-files`
2. **During development**: Use VS Code with all configured linters
3. **Before committing**: Ensure all quality checks pass
4. **Testing**: Run full test suite with `pytest`
5. **Local workflow testing**: Use `act` to test GitHub Actions

### Commit and PR Standards
- **Commit messages**: Let GitHub Copilot suggest (enabled in VS Code)
- **PR titles/descriptions**: Use Copilot suggestions
- **Conventional commits**: Use conventional commit format
- **Reviewer assignment**: Always assign @copilot as reviewer
- **Squash commits**: Prefer squash merges for cleaner history

### Error Resolution Philosophy
- **No workarounds**: Fix root causes, not symptoms
- **Ask for guidance**: When in doubt, ask user for authorization
- **Quality first**: Never compromise on code quality standards
- **Comprehensive fixes**: Address all related issues at once

## Technical Implementation Guidelines

### Modern Python Features (3.10+)
- **Pattern matching**: Use `match/case` for command routing
- **Type hints**: Use `list[str]` instead of `List[str]`
- **Walrus operator**: Use `:=` where appropriate
- **F-strings**: Prefer f-strings for string formatting
- **Dataclasses**: Use dataclasses for structured data

### GitHub API Integration
- Use `gh` CLI for GitHub API access (no direct API calls)
- Implement proper error handling for API failures
- Support both real data and sample data modes
- Cache API responses where appropriate

### Output Formatting
- **Colors**: Use shared Colors class for consistent styling
- **Tables**: Format data in readable table format
- **JSON**: Support JSON output for scripting
- **Quiet mode**: Suppress informational output when requested

### Security Considerations
- **Input validation**: Validate all user inputs
- **Secret handling**: Never log or expose secrets
- **Safe execution**: Use subprocess safely
- **Dependency scanning**: Regular security scans with bandit

## VS Code Configuration

### Required Extensions
- Python (ms-python.python)
- Black Formatter (ms-python.black-formatter)
- Flake8 (ms-python.flake8)
- MyPy (ms-python.mypy-type-checker)
- isort (ms-python.isort)
- GitHub Copilot (github.copilot)
- GitHub Copilot Chat (github.copilot-chat)
- YAML (redhat.vscode-yaml)
- Pre-commit Helper (ms-vscode.vscode-pre-commit-helper)

### Critical Settings
- **Format on save**: Enabled
- **Code actions on save**: Organize imports, fix all
- **GitHub Copilot**: All features enabled including commit messages
- **Type checking**: Strict mode
- **Line length**: 88 characters
- **Python version**: 3.10+

## CI/CD Pipeline

### GitHub Actions Workflows
- **CI Pipeline**: Python 3.10-3.13 matrix testing
- **CodeQL**: Security analysis
- **Pre-commit**: Automated quality checks with auto-updates
- **Dependency Review**: Security scanning for dependencies

### Monitoring and Maintenance
- **Monitor workflows**: Check for issues automatically
- **Resolve issues**: Fix CI/CD problems immediately
- **Update dependencies**: Regular dependency updates via Dependabot
- **Security alerts**: Address security vulnerabilities promptly

## Common Pitfalls to Avoid

### Code Quality Issues
- ❌ Dynamic imports (except for command routing)
- ❌ Missing type annotations
- ❌ Line length violations (>88 characters)
- ❌ Unused imports
- ❌ Inconsistent formatting

### Architecture Mistakes
- ❌ Monolithic functions/files
- ❌ Tight coupling between modules
- ❌ Mixing concerns in single files
- ❌ Missing error handling

### GitHub Actions Anti-patterns
- ❌ Using `@main` or `@master` for actions
- ❌ Missing explicit permissions
- ❌ No concurrency controls
- ❌ Expensive runners (macOS) for simple tasks

## Success Metrics

### Code Quality
- ✅ All pre-commit hooks pass
- ✅ 100% type checking coverage
- ✅ No security vulnerabilities
- ✅ Comprehensive test coverage

### Functionality
- ✅ All commands work with sample and real data
- ✅ Proper error handling and user feedback
- ✅ Consistent output formatting
- ✅ GitHub CLI extension compliance

### Maintainability
- ✅ Clear module separation
- ✅ Comprehensive documentation
- ✅ Easy to extend with new commands
- ✅ Automated quality assurance

## Lessons Learned from This Session

1. **Quality First**: Always implement maximum strictness in quality checks
2. **Architecture Matters**: Refactoring from monolithic to modular improved maintainability significantly
3. **Tool Integration**: Proper integration of pre-commit, VS Code, and GitHub Actions creates a robust development environment
4. **User Preferences**: Respect user's specific requirements (e.g., no time restrictions in dependabot)
5. **Modern Python**: Leveraging Python 3.10+ features improves code readability and maintainability
6. **Testing Strategy**: Local testing with `act` prevents CI/CD failures
7. **Documentation**: Comprehensive instructions prevent repeated mistakes

## Emergency Procedures

### Quality Check Failures
1. **Stop immediately**: Never proceed with failing quality checks
2. **Identify root cause**: Use detailed error messages
3. **Fix comprehensively**: Address all related issues
4. **Re-test thoroughly**: Ensure fix doesn't break other things

### CI/CD Issues
1. **Monitor actively**: Check workflow status after pushes
2. **Fix quickly**: Address failures immediately
3. **No workarounds**: Fix underlying issues
4. **Ask for help**: When uncertain about solutions

Remember: Quality and user requirements are non-negotiable. When in doubt, ask for clarification.
