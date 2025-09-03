# GitHub CLI Extension Best Practices for Actions Optimizer

## Repository Context
✅ **Auto-detect current repository**: Use `gh repo view` or git remote
✅ **Explicit repository**: Accept `--repo owner/repo` (standard GH CLI pattern)
✅ **No --github-repository**: Use standard `--repo` or `-R` flags

## Authentication
✅ **Use GitHub CLI's auth**: `gh auth token` provides authenticated token
✅ **No --github-token needed**: Extensions inherit authentication automatically
✅ **API calls**: Use `gh api` wrapper or get token programmatically

## Argument Naming Conventions
✅ **Repository**: `--repo` or `-R` (standard GitHub CLI)
✅ **Output**: `--output` or `-o` (not --output-dir for files)
✅ **Format**: `--format` (json|yaml|table) - consistent with GH CLI
✅ **Verbose**: `--verbose` or `-v`
✅ **Quiet**: `--quiet` or `-q`
✅ **Web**: `--web` or `-w` (open in browser when applicable)

## Subcommand Structure
✅ **Flat is better**: Avoid deep nesting (max 2 levels)
✅ **Consistent verbs**: analyze, generate, validate, etc.
✅ **Resource nouns**: runner-setup, machine-config, etc.

## Updated Structure Following GH CLI Patterns:

gh actions-optimizer analyze [flags]
gh actions-optimizer generate runner-setup [flags]
gh actions-optimizer generate machine-config [flags]
gh actions-optimizer generate workflow-patch [flags]
gh actions-optimizer generate copilot-prompt [flags]
gh actions-optimizer validate runners [flags]
gh actions-optimizer benchmark [flags]

STANDARD FLAGS (following gh patterns):
- --repo, -R string     Target repository (owner/repo)
- --format string       Output format: json|yaml|table|csv
- --output, -o string   Output to file
- --web, -w            Open results in browser
- --verbose, -v        Verbose output
- --quiet, -q          Minimal output
- --help, -h           Show help

NO LONGER NEEDED:
- --github-repository  (use --repo instead)
- --github-token       (use gh auth automatically)
- --output-dir         (use --output for files, default to stdout)
