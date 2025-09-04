# Input Validation and Security

This document describes the comprehensive input validation and sanitization system implemented in the GitHub Actions Optimizer to prevent security vulnerabilities.

## Overview

The validation system provides security-focused input validation across all user-facing interfaces, including:

- CLI argument validation
- File path sanitization  
- GitHub API input validation
- Environment variable validation
- YAML content validation
- URL validation

## Validation Module

The core validation logic is implemented in `gh_actions_optimizer/shared/validation.py` with the `InputValidator` class.

### Key Features

- **Repository Name Validation**: Validates GitHub repository format (`owner/repo`) and prevents injection attacks
- **File Path Sanitization**: Prevents directory traversal attacks and validates file paths
- **YAML Content Validation**: Safely parses YAML with security pattern detection
- **URL Validation**: Validates URLs and enforces allowed schemes (HTTPS by default)
- **Environment Variable Validation**: Validates environment variable names and values
- **Input Length Limits**: Enforces maximum lengths to prevent DoS attacks
- **Shell Safety**: Validates input for safe shell execution

### Security Patterns Detected

The validator detects and blocks dangerous patterns including:

- Directory traversal (`../`, `..\`)
- Variable injection (`${...}`)
- Script injection (`<script>`, `javascript:`)
- Code evaluation (`eval(`, `exec(`, `system(`)
- Dynamic imports (`__import__`, `import os`)

## Integration Points

### CLI Arguments

All command-line arguments are validated in `main.py` using `validate_parsed_args()`:

```python
# Validate all parsed arguments for security
validate_parsed_args(args)
```

### Repository Validation

Repository names are validated using enhanced logic:

```python
# Enhanced validation with security checks
validated_repo = validate_and_log_error(InputValidator.validate_repository_name, repo)
```

### File Operations

File paths and content are validated before processing:

```python
# Validate file paths
validate_and_log_error(InputValidator.validate_file_path, file_path, allow_absolute=True)

# Validate YAML content
parsed_yaml = validate_and_log_error(InputValidator.validate_yaml_content, content)
```

### URL Handling

URLs are validated before opening:

```python
# Validate URLs with allowed schemes
validated_url = validate_and_log_error(InputValidator.validate_url, url, ["https"])
```

## Validation Rules

### Repository Names

- Format: `owner/repo` (exactly one slash)
- Length: Maximum 100 characters
- Characters: Alphanumeric, hyphens, underscores, dots
- No dangerous patterns (injection, traversal)

### File Paths

- No directory traversal (`../`)
- No null bytes or control characters
- Configurable absolute path handling
- Filename validation for reserved names

### YAML Content

- Safe parsing with `yaml.safe_load()`
- Maximum content size (1MB)
- Security pattern detection
- Structured validation (must be dictionary)

### URLs

- Valid URL format
- Allowed schemes (HTTPS by default)
- No dangerous patterns
- No script injection

### Environment Variables

- Valid name format (uppercase alphanumeric + underscore)
- Maximum value length (4KB)
- No dangerous patterns in values

## Error Handling

Validation errors are handled consistently:

1. **ValidationError**: Specific validation failures with descriptive messages
2. **Logging**: Errors are logged with context
3. **Exit**: Invalid input causes immediate termination with exit code 1

```python
try:
    result = InputValidator.validate_repository_name(repo)
except ValidationError as e:
    log_error(f"Validation error: {e}")
    sys.exit(1)
```

## Testing

Comprehensive test coverage is provided in `tests/test_validation.py`:

- **Unit Tests**: Each validation method tested with valid/invalid inputs
- **Integration Tests**: Real-world scenarios and attack patterns
- **Edge Cases**: Boundary conditions and corner cases

### Test Categories

1. **Valid Input Tests**: Ensure legitimate input passes validation
2. **Invalid Input Tests**: Ensure malicious input is blocked
3. **Boundary Tests**: Test size limits and edge cases
4. **Integration Tests**: Test validation in realistic scenarios

## Performance Considerations

- **Regex Compilation**: Patterns are compiled as class attributes for efficiency
- **Early Validation**: Input is validated as early as possible in the pipeline
- **Minimal Overhead**: Validation is fast and doesn't impact normal operation

## Security Benefits

This validation system provides protection against:

- **Directory Traversal**: Prevents access to unauthorized files
- **Code Injection**: Blocks attempts to execute arbitrary code
- **Script Injection**: Prevents XSS and script-based attacks
- **Variable Injection**: Blocks attempts to inject environment variables
- **DoS Attacks**: Input length limits prevent resource exhaustion
- **Path Manipulation**: Prevents unauthorized file system access

## Usage Examples

### Validating Repository Names

```python
from gh_actions_optimizer.shared.validation import InputValidator

# Valid repository
repo = InputValidator.validate_repository_name("owner/repo")

# Invalid repository (raises ValidationError)
try:
    InputValidator.validate_repository_name("../malicious")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Validating File Paths

```python
# Safe file path
path = InputValidator.validate_file_path("config/settings.yml")

# Dangerous path (raises ValidationError)
try:
    InputValidator.validate_file_path("../../etc/passwd")
except ValidationError as e:
    print(f"Path validation failed: {e}")
```

### Validating YAML Content

```python
yaml_content = """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
"""

# Safe YAML parsing
parsed = InputValidator.validate_yaml_content(yaml_content)
```

## Best Practices

1. **Validate Early**: Validate input as soon as it's received
2. **Use Type Annotations**: Ensure proper typing for validation functions
3. **Handle Errors Gracefully**: Provide clear error messages
4. **Test Thoroughly**: Include both positive and negative test cases
5. **Document Patterns**: Document what patterns are considered dangerous
6. **Regular Updates**: Keep validation patterns updated with new threats

## Environment Variables

The following environment variables affect validation behavior:

- **NO_COLOR**: Disables colored output in error messages
- **FORCE_COLOR**: Forces colored output regardless of terminal

## Maintenance

The validation system should be regularly reviewed and updated:

1. **Pattern Updates**: Add new dangerous patterns as they're discovered
2. **Limit Adjustments**: Adjust size limits based on usage patterns
3. **Performance Monitoring**: Monitor validation performance impact
4. **Security Review**: Regular security audits of validation logic

## Contributing

When adding new validation:

1. Add validation method to `InputValidator` class
2. Include comprehensive type annotations
3. Add unit tests for valid and invalid cases
4. Update documentation
5. Follow existing naming conventions

## References

- [OWASP Input Validation](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/)
- [Python Security Best Practices](https://python.org/dev/security/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)