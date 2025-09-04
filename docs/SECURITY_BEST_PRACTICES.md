# Security Best Practices for GitHub Actions Optimizer

## Overview

This document outlines the security measures implemented in the GitHub Actions Optimizer to protect sensitive data, tokens, and credentials.

## Security Features Implemented

### 1. Secure Secrets and Token Handling

#### GitHub Token Security
- **No Token Logging**: GitHub tokens are never logged or displayed in output
- **Token Validation**: Validates token format without exposing the token value
- **Environment Variable Security**: Securely retrieves tokens from environment variables
- **Scope Verification**: Checks token permissions without exposing sensitive data

```python
# Example: Secure token handling
from gh_actions_optimizer.shared import get_github_token, validate_github_auth

# Get token securely without logging
token = get_github_token()

# Validate authentication without exposing credentials
if validate_github_auth():
    print("Authentication successful")
```

#### Token Storage Recommendations
- Use environment variables for token storage
- Never hardcode tokens in source code
- Use GitHub CLI's built-in authentication when possible
- Rotate tokens regularly

### 2. Secure Logging Patterns

#### Automatic Log Sanitization
All logging functions automatically sanitize sensitive data:

```python
from gh_actions_optimizer.shared import log_info, log_error

# These will automatically sanitize any tokens or sensitive data
log_info("Processing with token: ghp_xxxxxxxxxxxx")  # → "Processing with token: [REDACTED]"
log_error("Auth failed: Bearer xyz123...")  # → "Auth failed: Bearer [REDACTED]"
```

#### Supported Sanitization Patterns
- GitHub tokens (ghp_, ghs_, ghu_ prefixes)
- Bearer tokens
- Authorization headers
- URLs with embedded credentials
- SSH private keys
- AWS credentials
- Common secret patterns (password=, token=, etc.)

### 3. Error Message Security

#### Safe Error Reporting
Error messages are automatically sanitized to prevent credential exposure:

```python
from gh_actions_optimizer.shared.security import sanitize_error_message

try:
    # Some operation that might fail with sensitive data in error
    pass
except Exception as e:
    safe_error = sanitize_error_message(str(e))
    log_error(f"Operation failed: {safe_error}")
```

#### Repository URL Masking
Repository URLs with embedded credentials are automatically masked:

```python
from gh_actions_optimizer.shared.security import mask_repository_url

url = "https://user:token@github.com/owner/repo"
safe_url = mask_repository_url(url)  # → "https://[REDACTED]@github.com/owner/repo"
```

### 4. Configuration Security

#### Secure Configuration Management
```python
from gh_actions_optimizer.shared import secure_config

# Get configuration safely
config_value = secure_config.get_config_value("SOME_SETTING", default="default_value")

# Validate required configuration without exposing secrets
if secure_config.validate_required_config():
    print("Configuration is valid")

# Get safe summary for debugging (no sensitive values)
summary = secure_config.get_safe_config_summary()
```

#### Environment Variable Best Practices
- Use uppercase names for environment variables
- Prefix sensitive variables with descriptive names
- Never log environment variable values
- Use secure defaults when possible

## Implementation Guidelines

### For Developers

1. **Always Use Secure Logging Functions**
   ```python
   # GOOD
   from gh_actions_optimizer.shared import log_info
   log_info("User authenticated")
   
   # BAD - Direct print/logging can expose secrets
   print(f"Token: {token}")
   ```

2. **Sanitize User Inputs**
   ```python
   from gh_actions_optimizer.shared.security import sanitize_for_logging
   
   user_input = get_user_input()
   safe_input = sanitize_for_logging(user_input)
   log_info(f"Processing: {safe_input}")
   ```

3. **Use Security Utilities for Subprocess Operations**
   ```python
   from gh_actions_optimizer.shared.security import sanitize_subprocess_output
   
   result = subprocess.run(command, capture_output=True, text=True)
   safe_output = sanitize_subprocess_output(result.stdout, command)
   log_info(f"Command output: {safe_output}")
   ```

4. **Validate Tokens Safely**
   ```python
   from gh_actions_optimizer.shared.security import validate_github_token_format
   
   if validate_github_token_format(token):
       log_info("Token format is valid")
   else:
       log_error("Invalid token format")
   ```

### For Configuration

1. **Environment Variables**
   ```bash
   # Required for GitHub access
   export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   
   # Optional: Override repository detection
   export GITHUB_REPOSITORY="owner/repo"
   ```

2. **GitHub CLI Authentication**
   ```bash
   # Preferred method - uses GitHub CLI's secure storage
   gh auth login
   ```

### For CI/CD Pipelines

1. **Use GitHub Secrets**
   ```yaml
   env:
     GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   ```

2. **Limit Token Permissions**
   - Use fine-grained personal access tokens
   - Grant only necessary permissions
   - Set appropriate expiration dates

3. **Monitor for Secret Exposure**
   - Enable secret scanning on repositories
   - Use dependabot for security updates
   - Regular security audits

## Security Audit Features

The security command provides comprehensive security auditing:

```bash
# Run security audit
gh actions-optimizer security

# Audit specific repository
gh actions-optimizer security --repo owner/repo

# Get JSON output for further processing
gh actions-optimizer security --format json
```

### Security Checks Performed

1. **Direct Secrets Usage Detection**
   - Identifies workflows using `${{ secrets.* }}` inappropriately
   - Excludes safe usage like `${{ secrets.GITHUB_TOKEN }}`

2. **Pull Request Target Safety**
   - Detects unsafe `pull_request_target` usage
   - Ensures proper security guards are in place

3. **Script Injection Prevention**
   - Identifies potential script injection vulnerabilities
   - Checks for unsafe user input handling

4. **Permission Verification**
   - Ensures workflows have explicit permissions
   - Identifies missing security constraints

5. **Action Version Pinning**
   - Detects unpinned third-party actions
   - Recommends specific commit SHA pinning

## Incident Response

If you suspect a security issue:

1. **Immediate Actions**
   - Rotate any potentially exposed tokens
   - Review recent logs for sensitive data exposure
   - Check workflow runs for security violations

2. **Investigation**
   - Use the security audit command to identify issues
   - Review configuration and environment variables
   - Check for recent changes to security-sensitive code

3. **Remediation**
   - Apply security patches immediately
   - Update workflows to use secure patterns
   - Implement additional monitoring if needed

4. **Prevention**
   - Regular security audits
   - Automated security testing in CI/CD
   - Team training on security best practices

## Compliance and Standards

This implementation follows security best practices from:

- GitHub Security Best Practices
- OWASP Secure Coding Guidelines
- NIST Cybersecurity Framework
- OpenSSF Security Scorecard recommendations

## Monitoring and Maintenance

### Regular Security Tasks

1. **Token Rotation**
   - Rotate GitHub tokens every 90 days
   - Monitor token usage and permissions
   - Remove unused tokens immediately

2. **Dependency Updates**
   - Keep all dependencies updated
   - Monitor security advisories
   - Use automated dependency scanning

3. **Audit Logging**
   - Review logs for security events
   - Monitor for credential exposure
   - Track authentication failures

### Security Metrics

Track these security metrics:

- Number of security issues detected
- Token rotation frequency  
- Dependency vulnerability count
- Security audit completion rate

## Contact and Support

For security-related questions or to report security issues:

1. **Security Issues**: Use GitHub's private vulnerability reporting
2. **Questions**: Create a GitHub issue with the `security` label
3. **Documentation**: Refer to this guide and inline code documentation

Remember: **When in doubt about security, err on the side of caution and ask for review.**