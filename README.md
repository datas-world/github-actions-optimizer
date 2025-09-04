# GitHub Actions Optimizer

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/datas-world/github-actions-optimizer/workflows/Main%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/datas-world/github-actions-optimizer/actions/workflows/main.yml)
[![CodeQL](https://github.com/datas-world/github-actions-optimizer/workflows/Main%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/datas-world/github-actions-optimizer/actions/workflows/main.yml)
[![Workflow Tracker](https://github.com/datas-world/github-actions-optimizer/workflows/Workflow%20Failure%20Tracker/badge.svg)](https://github.com/datas-world/github-actions-optimizer/actions/workflows/workflow-failure-tracker.yml)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=datas-world_github-actions-optimizer&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=datas-world_github-actions-optimizer)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=datas-world_github-actions-optimizer&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=datas-world_github-actions-optimizer)
[![GitHub CLI Extension](https://img.shields.io/badge/GitHub%20CLI-Extension-brightgreen)](https://cli.github.com/)

A comprehensive GitHub CLI extension for optimizing GitHub Actions workflows through cost analysis, performance optimization, and security auditing.

## Features

🚀 **Core Capabilities**

- Workflow analysis and optimization recommendations
- Cost calculation and optimization strategies
- Security auditing and compliance checks
- Runner optimization suggestions
- Integration with GitHub API via gh CLI

🔧 **Advanced Features**

- Real-time GitHub API integration with cost analysis
- Multiple output formats (JSON, table)
- Security-focused workflow auditing
- Comprehensive cost optimization recommendations
- GitHub CLI extension architecture

## Quick Start

### Prerequisites

- Python 3.10+
- [GitHub CLI (gh)](https://cli.github.com/) installed and authenticated
- `jq` command-line JSON processor

### Installation

#### Option 1: Install as GitHub CLI Extension (Recommended)

```bash
gh extension install datas-world/github-actions-optimizer
```

#### Option 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/datas-world/github-actions-optimizer.git
cd github-actions-optimizer

# Install dependencies
pip install -e .

# Make executable
chmod +x gh-actions-optimizer
```

### Basic Usage

```bash
# Analyze workflows in a repository
gh actions-optimizer analyze --repo owner/repo

# Check cost optimization opportunities
gh actions-optimizer cost --format json

# Run security audit
gh actions-optimizer security --repo owner/repo

# Get runner optimization recommendations
gh actions-optimizer runners

# Live repository analysis (requires GITHUB_TOKEN)
export GITHUB_TOKEN="your_token_here"
python github-actions-optimizer.py --repo "owner/repository" --format table

# Generate self-hosted runner setup
python github-actions-optimizer.py --sample-data --generate-runner-setup
```

## GitHub CLI Extension

This tool is designed to be compatible with GitHub CLI extensions. See the development documentation for conversion details.

## License Compatibility

✅ **All dependencies verified GPLv3 compatible**

This project uses only dependencies with licenses compatible with GPLv3:

- MIT, BSD, Apache-2.0, LGPL-3.0, MPL-2.0 licensed components
- Full compatibility analysis in `LICENSE_COMPATIBILITY.md`

## Documentation

- [Development Lessons Learned](docs/github-actions-optimizer-lessons-learned.md)
- [License Compatibility Analysis](LICENSE_COMPATIBILITY.md)

## Contributing

This project is released under GPLv3. Contributions are welcome under the same license terms.

## License

Copyright (C) 2025 Torsten Marco Knodt

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See [LICENSE](LICENSE) for the full license text.
