# Dependency Security Policy

## Overview

This document outlines the dependency security and supply chain protection measures implemented in the GitHub Actions Optimizer project.

## Dependency Management

### Version Pinning

All dependencies are pinned to specific versions to ensure reproducible builds and prevent supply chain attacks:

- **Runtime dependencies**: Pinned in `requirements.txt` with exact versions
- **Development dependencies**: Pinned in `pyproject.toml` with exact versions  
- **Input files**: `requirements.in` and `requirements-dev.in` contain unpinned versions for updates

### Dependency Sources

- All dependencies are sourced from PyPI (Python Package Index)
- Dependencies are verified against known vulnerability databases
- Hash verification is used where possible for critical dependencies

## Vulnerability Scanning

### Automated Scanning Tools

1. **pip-audit**: Primary vulnerability scanner
   - Scans installed packages against OSV and PyPI vulnerability databases
   - Integrated into CI/CD pipeline and pre-commit hooks
   - Runs on every commit and pull request

2. **safety**: Additional vulnerability scanner
   - Cross-references with Safety DB vulnerability database
   - Provides complementary coverage to pip-audit
   - Configured with appropriate ignore lists for false positives

### Scanning Schedule

- **Pre-commit**: Vulnerability scans run before every commit
- **CI/CD Pipeline**: Scans run on all pushes and pull requests
- **Daily**: Automated dependency updates trigger new scans
- **Manual**: Developers can run `pip-audit` or `safety check` anytime

## Supply Chain Security

### Package Integrity

- Dependencies are pinned to specific versions to prevent version confusion attacks
- Hash verification is implemented for critical dependencies
- Package sources are limited to trusted repositories (PyPI)

### Dependency Updates

- **Dependabot**: Configured for daily automated dependency updates
- **Review Process**: All dependency updates require review by @copilot
- **Testing**: All updates are tested through CI/CD pipeline before merge
- **Security Focus**: Security updates are prioritized and fast-tracked

### SBOM Generation

Software Bill of Materials (SBOM) can be generated using:

```bash
# Generate SBOM in CycloneDX format
pip-audit --format=cyclonedx-json --output=sbom.json

# Generate SBOM in CycloneDX XML format  
pip-audit --format=cyclonedx-xml --output=sbom.xml
```

## Security Monitoring

### Vulnerability Response

1. **Detection**: Automated scans detect vulnerabilities
2. **Assessment**: Vulnerability impact is evaluated
3. **Remediation**: Updates or mitigations are applied
4. **Verification**: Fixes are tested and verified
5. **Documentation**: Security incidents are documented

### Alert Channels

- **CI/CD Failures**: Failed vulnerability scans block deployments
- **Dependabot PRs**: Automated security update pull requests
- **GitHub Security Advisories**: Repository security advisories for critical issues

## Configuration Files

### Dependabot Configuration

- **File**: `.github/dependabot.yml`
- **Schedule**: Daily updates
- **Assignee**: @torsknod2
- **Reviewer**: @copilot
- **Scope**: All dependency types (pip, github-actions)

### Pre-commit Configuration

- **File**: `.pre-commit-config.yaml`
- **Tools**: pip-audit, safety, bandit (static analysis)
- **Frequency**: Every commit

### CI/CD Configuration

- **File**: `.github/workflows/main.yml`
- **Integration**: Vulnerability scanning in pre-commit and test jobs
- **Frequency**: Every push and pull request

## Compliance and Reporting

### License Compatibility

- All dependencies are checked for GPLv3 compatibility
- License compatibility matrix maintained in `LICENSE_COMPATIBILITY.md`
- No GPL-incompatible licenses are permitted

### Audit Trail

- All dependency changes are tracked in version control
- Vulnerability scan results are logged in CI/CD
- Security incidents are documented in repository security advisories

## Developer Guidelines

### Adding New Dependencies

1. Check license compatibility with GPLv3
2. Verify dependency reputation and maintenance status
3. Add to appropriate requirements file with version range
4. Pin specific version after testing
5. Update security documentation if needed

### Updating Dependencies

1. Review dependency changelogs for security fixes
2. Test updates in development environment
3. Run full vulnerability scans
4. Update pinned versions in requirements files
5. Document any security-relevant changes

### Security Best Practices

- Never commit secrets or credentials
- Use dependency scanning before adding new packages
- Keep dependencies up to date with security patches
- Monitor security advisories for used packages
- Report security issues through proper channels

## Contact

For security-related dependency issues:

- Create GitHub security advisory for vulnerabilities
- Contact repository maintainers through GitHub
- Follow responsible disclosure practices

---

*This policy is reviewed and updated regularly to maintain current security best practices.*