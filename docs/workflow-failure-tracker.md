# Workflow Failure Tracker

This document describes the [Workflow Failure Tracker](../.github/workflows/workflow-failure-tracker.yml) functionality that automatically monitors GitHub Actions workflow failures and creates/updates issues for them.

## Overview

The Workflow Failure Tracker is a GitHub Actions workflow that:

1. **Monitors workflow failures** - Triggers when CI, CodeQL Analysis, or Pre-commit workflows fail
2. **Creates tracking issues** - Automatically creates issues for new workflow failures
3. **Updates existing issues** - Adds new failure occurrences to existing tracking issues
4. **Provides structured information** - Includes failure details, investigation checklists, and history

## How it Works

### Triggers

The workflow triggers when any of the following workflows complete with a failure status:
- CI
- CodeQL Analysis  
- Pre-commit

### Behavior

1. **First failure**: Creates a new issue with the title "Workflow Failure: [Workflow Name]"
2. **Subsequent failures**: Adds a comment to the existing issue with the new failure details

### Issue Structure

Each tracking issue contains:

- **Current Failure Details**: Information about the most recent failure
- **Investigation Checklist**: Steps to investigate and resolve the issue
- **Proposed Solution**: Space for documenting the fix (to be updated manually)
- **Failure History**: List of all failure occurrences

### Labels

Issues are automatically labeled with:
- `workflow-failure`: Identifies issues created by this tracker
- `automated`: Indicates the issue was created automatically
- `bug`: Categorizes as a bug/problem

## Benefits

1. **No missed failures**: Ensures workflow failures are tracked even when not related to specific PRs
2. **Centralized tracking**: Groups related failures into single issues
3. **Historical context**: Maintains a record of failure patterns
4. **Structured investigation**: Provides checklists to guide troubleshooting

## Configuration

The workflow is configured in `.github/workflows/workflow-failure-tracker.yml` and requires:

- **Permissions**: `contents: read`, `issues: write`, `actions: read`
- **Dependencies**: GitHub CLI (`gh`) for issue management
- **Environment**: Uses `GITHUB_TOKEN` for authentication

## Customization

To monitor additional workflows, update the `workflows` list in the trigger configuration:

```yaml
on:
  workflow_run:
    workflows: ["CI", "CodeQL Analysis", "Pre-commit", "Your Workflow Name"]
    types:
      - completed
```

## Maintenance

- Issues remain open until manually closed after resolution
- The workflow runs automatically and requires no manual intervention
- Failed runs of the tracker itself should be investigated to ensure continued monitoring

## Testing

Tests for the workflow configuration are located in `tests/test_workflow_failure_tracker.py` and validate:

- Workflow structure and syntax
- Trigger configuration
- Required permissions
- Step definitions
- Conditional logic