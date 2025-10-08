# GitHub Repository Setup Guide

Complete guide to set up branch protection and best practices for CloudMask.

## Quick Setup Checklist

- [ ] Enable branch protection rules
- [ ] Configure required status checks
- [ ] Set up code owners
- [ ] Enable security features
- [ ] Configure secrets
- [ ] Install recommended apps
- [ ] Update repository settings

## 1. Branch Protection Rules

### Via GitHub UI

1. Navigate to **Settings** → **Branches**
2. Click **Add rule** for `main` branch
3. Configure the following:

#### Protect matching branches
- ✅ Require a pull request before merging
  - ✅ Require approvals: **1**
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners
  - ✅ Require approval of the most recent reviewable push

#### Status checks
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - Select: `test (3.10)`, `test (3.11)`, `test (3.12)`

#### Additional settings
- ✅ Require conversation resolution before merging
- ✅ Require linear history
- ❌ Allow force pushes
- ❌ Allow deletions

### Via GitHub CLI

```bash
# Install GitHub CLI if needed
brew install gh

# Authenticate
gh auth login

# Apply branch protection
gh api repos/samfakhreddine/cloudmask/branches/main/protection \
  --method PUT \
  --input .github/branch-protection.json
```

## 2. Repository Settings

### General Settings

Navigate to **Settings** → **General**:

- **Default branch**: `main`
- ✅ Allow squash merging
- ❌ Allow merge commits
- ✅ Allow rebase merging
- ✅ Automatically delete head branches
- ✅ Allow auto-merge

### Security Settings

Navigate to **Settings** → **Security**:

#### Dependabot
- ✅ Enable Dependabot alerts
- ✅ Enable Dependabot security updates
- ✅ Enable Dependabot version updates

Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "python"
```

#### Code scanning
- ✅ Enable CodeQL analysis
- ✅ Enable secret scanning
- ✅ Enable push protection

#### Private vulnerability reporting
- ✅ Enable private vulnerability reporting

## 3. Required Secrets

Navigate to **Settings** → **Secrets and variables** → **Actions**:

### Repository Secrets

```bash
# PyPI token for publishing
gh secret set PYPI_TOKEN

# Test PyPI token
gh secret set TEST_PYPI_TOKEN

# Codecov token (optional but recommended)
gh secret set CODECOV_TOKEN

# GitHub token (automatically provided)
# GITHUB_TOKEN - No setup needed
```

### Environment Secrets

Create environments for different deployment stages:

1. **test** - Test PyPI deployment
2. **production** - PyPI deployment

For each environment:
- Add protection rules
- Add required reviewers
- Add deployment branch rules

## 4. GitHub Apps Installation

### Recommended Apps

1. **Codecov** - Code coverage reporting
   - Visit: https://github.com/apps/codecov
   - Install and authorize for repository

2. **Dependabot** - Dependency updates
   - Built-in, just enable in settings

3. **Probot Settings** (Optional) - Automate settings
   - Visit: https://github.com/apps/settings
   - Reads from `.github/settings.yml`

4. **Pull Request Size** - Label PRs by size
   - Configured in workflows

## 5. Code Owners Setup

The `.github/CODEOWNERS` file is already created. Update with your GitHub username:

```bash
# Replace @samfakhreddine with your username
sed -i '' 's/@samfakhreddine/@YOUR_USERNAME/g' .github/CODEOWNERS
```

## 6. Enable GitHub Features

### Actions
Navigate to **Settings** → **Actions** → **General**:
- ✅ Allow all actions and reusable workflows
- ✅ Allow GitHub Actions to create and approve pull requests

### Pages (Optional)
For documentation hosting:
- Source: Deploy from a branch
- Branch: `gh-pages` / `docs`

### Discussions (Optional)
- ✅ Enable Discussions for community Q&A

## 7. Workflow Permissions

Navigate to **Settings** → **Actions** → **General** → **Workflow permissions**:
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

## 8. Rulesets (Alternative to Branch Protection)

GitHub Rulesets are the modern alternative to branch protection rules.

Navigate to **Settings** → **Rules** → **Rulesets**:

1. Click **New ruleset** → **New branch ruleset**
2. Name: `main-protection`
3. Enforcement status: **Active**
4. Target branches: `main`
5. Configure rules:
   - ✅ Require pull request before merging (1 approval)
   - ✅ Require status checks to pass
   - ✅ Require conversation resolution
   - ✅ Block force pushes

## 9. Verification

### Test Branch Protection

```bash
# Try to push directly to main (should fail)
git checkout main
echo "test" >> README.md
git commit -am "test: direct push"
git push origin main
# Expected: Error - protected branch

# Correct workflow
git checkout -b test/branch-protection
git push origin test/branch-protection
gh pr create --title "test: branch protection" --body "Testing branch protection rules"
```

### Test Status Checks

1. Create a PR with failing tests
2. Verify merge button is disabled
3. Fix tests
4. Verify merge button is enabled

### Test Code Owners

1. Create a PR
2. Verify code owner is automatically requested for review
3. Verify PR cannot merge without code owner approval

## 10. Monitoring and Maintenance

### Weekly Tasks
- Review Dependabot PRs
- Check security alerts
- Monitor CI/CD health

### Monthly Tasks
- Review and update branch protection rules
- Audit repository access
- Update documentation

### Quarterly Tasks
- Review and update workflows
- Audit secrets and tokens
- Review code owner assignments

## 11. Team Setup (For Organizations)

### Create Teams
1. Navigate to **Organization** → **Teams**
2. Create teams:
   - `cloudmask-maintainers` - Full access
   - `cloudmask-contributors` - Write access
   - `cloudmask-reviewers` - Triage access

### Update CODEOWNERS
```
* @cloudmask-maintainers
/src/ @cloudmask-maintainers
/tests/ @cloudmask-contributors
/docs/ @cloudmask-reviewers
```

## 12. Troubleshooting

### Status checks not appearing
- Ensure workflows have run at least once
- Check workflow names match exactly
- Verify workflows are on the default branch

### Cannot merge despite passing checks
- Check all conversations are resolved
- Verify branch is up to date
- Check for required reviews

### Dependabot not creating PRs
- Verify `dependabot.yml` syntax
- Check Dependabot logs in Security tab
- Ensure dependencies are in supported ecosystems

## 13. Additional Resources

- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot)
- [Code Owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

## 14. Quick Commands Reference

```bash
# View branch protection
gh api repos/samfakhreddine/cloudmask/branches/main/protection

# List required status checks
gh api repos/samfakhreddine/cloudmask/branches/main/protection/required_status_checks

# View repository settings
gh repo view samfakhreddine/cloudmask --json name,description,isPrivate,defaultBranchRef

# List secrets
gh secret list

# View workflow runs
gh run list

# View security alerts
gh api repos/samfakhreddine/cloudmask/vulnerability-alerts
```
