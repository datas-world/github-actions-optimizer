# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

We take the security of our GitHub Actions Optimizer seriously. If you discover a security vulnerability, please report it responsibly:

### Reporting Process

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Send an email to the repository maintainers with details of the vulnerability
3. Include as much information as possible:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Suggested fix (if available)

### Response Timeline

- **Initial Response**: Within 48 hours of receipt
- **Status Updates**: Every 5 business days until resolution
- **Resolution**: Security fixes will be prioritized and released as soon as possible

### Responsible Disclosure

We appreciate responsible disclosure of security vulnerabilities. We will:

- Acknowledge your report within 48 hours
- Keep you informed of our progress
- Credit you in our security advisory (unless you prefer to remain anonymous)
- Work with you to ensure the vulnerability is properly addressed

## Security Best Practices

When using this GitHub Actions Optimizer:

1. **Input Validation**: Always validate and sanitize inputs before processing
2. **Secrets Management**: Never log or expose secrets in GitHub Actions workflows
3. **Permissions**: Use the principle of least privilege for GitHub tokens
4. **Dependencies**: Keep dependencies updated and review security advisories
5. **Code Review**: All changes must be reviewed before merging

## Security Features

This repository implements several security measures:

- **Dependency Scanning**: Automated vulnerability scanning for dependencies
- **Secret Scanning**: Automatic detection of leaked secrets
- **Code Scanning**: Static analysis for security vulnerabilities
- **Branch Protection**: Protected main branch with required reviews
- **Advanced Security**: GitHub Advanced Security features enabled

## Incident Response

In case of a security incident:

1. The issue will be triaged immediately
2. A security advisory will be created for confirmed vulnerabilities
3. Patches will be developed and tested
4. Coordinated disclosure will be conducted
5. Post-incident review will be performed

## Contact

For security-related inquiries, please contact the repository maintainers through GitHub's private vulnerability reporting feature or create a security advisory.

---

*This security policy is regularly reviewed and updated to ensure it meets current best practices.*
