# GitHub Actions Optimizer

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

A comprehensive platform for optimizing GitHub Actions workflows through cost analysis, performance optimization, and resource management.

## Features

🚀 **Core Capabilities**
- Real-time GitHub API integration with cost analysis
- Statistical analysis with variance and distribution metrics
- Cost optimization for all runner types (standard, larger, ARM64, GPU)
- Self-hosted runner setup and configuration generation
- Workflow patch generation for optimal runner usage

🔧 **Advanced Features**
- Machine specification detection and optimization
- Multiple output formats (JSON, YAML, CSV, table)
- GitHub Copilot prompt generation for improvements
- Comprehensive resource efficiency analysis
- Security-hardened self-hosted runner scripts

## Quick Start

### Prerequisites
- Python 3.13+
- GitHub personal access token
- Internet connection for live analysis

### Installation

```bash
# Clone the repository
git clone https://github.com/datas-world/github-actions-optimizer.git
cd github-actions-optimizer

# Install dependencies
pip install -r requirements.txt

# Run sample analysis
python github-actions-optimizer.py --sample-data --format table
```

### Basic Usage

```bash
# Analyze with sample data
python github-actions-optimizer.py --sample-data --format json --output analysis.json

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
