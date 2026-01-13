# Git Flow Workflow Guide

## What is Git Flow?

Git Flow is a branching model that provides a robust framework for managing features, releases, and hotfixes. It uses multiple branches with specific purposes:

- **main/master**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: New features
- **release/**: Preparing releases
- **hotfix/**: Urgent production fixes

## Installation

### macOS
```bash
brew install git-flow-avh
```

### Linux
```bash
# Ubuntu/Debian
sudo apt-get install git-flow

# Or use the AVH version (recommended)
wget --no-check-certificate -q https://raw.githubusercontent.com/petervanderdoes/gitflow-avh/develop/contrib/gitflow-installer.sh && sudo bash gitflow-installer.sh install stable; rm gitflow-installer.sh
```

### Verify Installation
```bash
git flow version
```

## Initialization

### Step 1: Initialize Git Flow

```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend

# Initialize git flow (will ask for branch name conventions)
git flow init

# Or use defaults (recommended for first time)
git flow init -d
```

**Default settings:**
- Production branch: `main`
- Development branch: `develop`
- Feature prefix: `feature/`
- Release prefix: `release/`
- Hotfix prefix: `hotfix/`
- Support prefix: `support/`
- Version tag prefix: (empty)

### Step 2: Push Develop Branch

```bash
# Push develop branch to remote
git push -u origin develop
```

## Git Flow Commands

### Feature Branches

**Start a new feature:**
```bash
git flow feature start <feature-name>
# Example: git flow feature start llm-integration
```

**Finish a feature (merges to develop):**
```bash
git flow feature finish <feature-name>
# This merges the feature into develop and deletes the feature branch
```

**Publish a feature (push to remote):**
```bash
git flow feature publish <feature-name>
```

**Pull a published feature:**
```bash
git flow feature pull <feature-name>
```

### Release Branches

**Start a release:**
```bash
git flow release start <version>
# Example: git flow release start 1.0.0
```

**Finish a release (merges to main and develop, creates tag):**
```bash
git flow release finish <version>
# This will:
# 1. Merge to main
# 2. Tag the release
# 3. Merge back to develop
# 4. Delete the release branch
```

**Publish a release:**
```bash
git flow release publish <version>
```

### Hotfix Branches

**Start a hotfix (from main):**
```bash
git flow hotfix start <version>
# Example: git flow hotfix start 1.0.1
```

**Finish a hotfix (merges to main and develop):**
```bash
git flow hotfix finish <version>
# This will:
# 1. Merge to main
# 2. Tag the hotfix
# 3. Merge back to develop
# 4. Delete the hotfix branch
```

## Typical Workflow

### 1. Starting a New Feature

```bash
# Start feature branch
git flow feature start add-tool-wrappers

# Make changes, commit
git add .
git commit -m "Add vector search tool wrapper"

# Push feature branch (optional, for collaboration)
git flow feature publish add-tool-wrappers

# Continue working...
git add .
git commit -m "Add definition lookup tool"

# Finish feature (merges to develop)
git flow feature finish add-tool-wrappers
```

### 2. Preparing a Release

```bash
# Start release branch
git flow release start 1.0.0

# Update version numbers, changelog, etc.
# Make final bug fixes (no new features!)

# Finish release
git flow release finish 1.0.0
# Enter release message when prompted

# Push everything
git push origin main
git push origin develop
git push --tags
```

### 3. Urgent Hotfix

```bash
# Start hotfix from main
git flow hotfix start 1.0.1

# Fix the bug
git add .
git commit -m "Fix API key security issue"

# Finish hotfix
git flow hotfix finish 1.0.1

# Push
git push origin main
git push origin develop
git push --tags
```

## Branch Structure

```
main (production)
  │
  ├── hotfix/1.0.1 (urgent fixes)
  │
develop (integration)
  │
  ├── feature/llm-integration
  ├── feature/tool-wrappers
  │
  └── release/1.0.0 (preparing release)
```

## Best Practices

### 1. Feature Branches
- ✅ Keep features small and focused
- ✅ One feature per branch
- ✅ Regular commits with clear messages
- ✅ Finish features when complete (don't leave them open)

### 2. Release Branches
- ✅ Only bug fixes, no new features
- ✅ Update version numbers
- ✅ Update CHANGELOG.md
- ✅ Test thoroughly before finishing

### 3. Hotfix Branches
- ✅ Only for critical production issues
- ✅ Keep changes minimal
- ✅ Test before finishing

### 4. Commit Messages
Follow conventional commits:
```
feat: add vector search tool wrapper
fix: remove hardcoded API key
docs: update README with setup instructions
refactor: reorganize tool directory structure
test: add unit tests for definition lookup
chore: update dependencies
```

### 5. Branch Naming
- Features: `feature/llm-integration`, `feature/tool-wrappers`
- Releases: `release/1.0.0`, `release/2.1.0`
- Hotfixes: `hotfix/1.0.1`, `hotfix/security-patch`

## Common Scenarios

### Scenario 1: Working on Multiple Features

```bash
# Start feature A
git flow feature start feature-a
# ... work on feature A ...

# Switch to feature B (without finishing A)
git flow feature start feature-b
# ... work on feature B ...

# Switch back to feature A
git checkout feature/feature-a
# ... continue working ...

# Finish feature A
git flow feature finish feature-a

# Continue with feature B
git checkout feature/feature-b
git flow feature finish feature-b
```

### Scenario 2: Collaborating on a Feature

```bash
# Person A starts feature
git flow feature start shared-feature
git flow feature publish shared-feature

# Person B pulls the feature
git flow feature pull shared-feature

# Both work on it, push/pull as needed
git flow feature publish shared-feature  # Person A
git flow feature pull shared-feature      # Person B

# Person A finishes
git flow feature finish shared-feature
```

### Scenario 3: Abandoning a Feature

```bash
# If you need to abandon a feature
git flow feature delete <feature-name>

# Or manually
git checkout develop
git branch -D feature/<feature-name>
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: CI

on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          # Your test commands
```

## Alternative: Git Flow Extensions

For more advanced features, consider:
- **git-flow-avh**: Extended version with more commands
- **GitHub Flow**: Simpler model (main + feature branches)
- **GitLab Flow**: Environment-based branches

## Quick Reference

```bash
# Initialize
git flow init -d

# Features
git flow feature start <name>
git flow feature finish <name>
git flow feature publish <name>

# Releases
git flow release start <version>
git flow release finish <version>

# Hotfixes
git flow hotfix start <version>
git flow hotfix finish <version>

# Push after finishing
git push origin main
git push origin develop
git push --tags
```

## Current Repository Setup

For your `ai-chat-with-kb-backend` repository:

1. **Current state**: You have a `main` branch
2. **Next steps**:
   - Initialize git flow
   - Create `develop` branch
   - Start using feature branches for new work

## Recommended First Steps

```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend

# 1. Initialize git flow
git flow init -d

# 2. Push develop branch
git push -u origin develop

# 3. Start your next feature
git flow feature start <your-feature-name>
```

## Troubleshooting

### "git flow: command not found"
- Install git-flow (see Installation section)

### "fatal: Not a git-flow-enabled repo"
- Run `git flow init` first

### Merge conflicts
- Resolve conflicts normally
- `git add .` after resolving
- Continue with `git flow feature finish`

### Want to keep feature branch after finishing
```bash
# Finish without deleting
git flow feature finish <name> --keep
```
