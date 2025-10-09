# Branch Protection Rules

This document describes the branch protection rules configured for the CloudMask repository.

## Main Branch Protection

The `main` branch has the following protections enabled:

### Required Reviews
- **Minimum approvals**: 1 required approving review
- **Dismiss stale reviews**: Enabled - new commits dismiss previous approvals
- **Require code owner review**: Enabled - at least one code owner must approve
- **Require approval of most recent push**: Enabled - ensures latest changes are reviewed

### Status Checks
All status checks must pass before merging:
- `test (3.10)` - Tests on Python 3.10
- `test (3.11)` - Tests on Python 3.11
- `test (3.12)` - Tests on Python 3.12

Status checks include:
- Code formatting (Black)
- Linting (Ruff)
- Type checking (Mypy)
- Docstring validation (Pydocstyle)
- Test coverage (pytest)

### Additional Protections
- **Require linear history**: Enabled - prevents merge commits
- **Require conversation resolution**: Enabled - all PR comments must be resolved
- **Prevent force pushes**: Enabled
- **Prevent deletion**: Enabled
- **Allow fork syncing**: Enabled

### Admin Enforcement
- Admins can bypass protections for emergency fixes
- Use sparingly and document in commit messages

## Setting Up Branch Protection

### Via GitHub UI
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Configure settings as documented above

### Via GitHub CLI
```bash
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test (3.10)","test (3.11)","test (3.12)"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"require_last_push_approval":true}' \
  --field restrictions=null \
  --field required_linear_history=true \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field required_conversation_resolution=true
```

### Using Probot Settings App
Install the [Probot Settings](https://github.com/apps/settings) app and it will automatically apply the configuration from `.github/settings.yml`.

## Workflow Requirements

### Pull Request Workflow
1. Create feature branch from `main`
2. Make changes and commit
3. Push branch and open PR
4. Wait for CI checks to pass
5. Request review from code owner
6. Address review comments
7. Get approval
8. Squash and merge

### Commit Message Format
Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Test changes
- `build:` - Build system changes
- `ci:` - CI configuration changes
- `chore:` - Other changes

### Security Checks
All PRs are automatically scanned for:
- Vulnerable dependencies (Dependency Review)
- Security issues (CodeQL)
- License compliance
- Secrets exposure

## Emergency Procedures

### Hotfix Process
For critical production issues:
1. Create hotfix branch from `main`
2. Make minimal fix
3. Open PR with `[HOTFIX]` prefix
4. Get expedited review
5. Admin can merge with bypass if necessary
6. Document bypass reason in PR

### Rollback Process
If a merged PR causes issues:
1. Create revert PR
2. Reference original PR
3. Follow normal review process
4. Or admin bypass for critical issues

## Best Practices

### For Contributors
- Keep PRs small and focused
- Write clear commit messages
- Add tests for new features
- Update documentation
- Respond to review comments promptly

### For Reviewers
- Review within 24 hours
- Check code quality and tests
- Verify documentation updates
- Test locally if needed
- Be constructive in feedback

### For Maintainers
- Monitor CI/CD health
- Keep dependencies updated
- Review security alerts promptly
- Update branch protection as needed
- Document any bypasses

## Monitoring

### GitHub Insights
Monitor repository health:
- Pulse: Recent activity
- Contributors: Contribution stats
- Traffic: Views and clones
- Commits: Commit frequency

### Security Alerts
Enable and monitor:
- Dependabot alerts
- Code scanning alerts
- Secret scanning alerts

## References

- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
