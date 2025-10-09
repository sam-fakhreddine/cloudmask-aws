#!/bin/bash
set -e

REPO="sam-fakhreddine/cloudmask"

echo "🤖 Setting up Dependabot automerge for $REPO"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "Install with: brew install gh"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "🔐 Authenticating with GitHub..."
    gh auth login
fi

# Enable Dependabot
echo "📦 Enabling Dependabot..."
gh api repos/$REPO/vulnerability-alerts --method PUT || echo "Already enabled"
gh api repos/$REPO/automated-security-fixes --method PUT || echo "Already enabled"

# Create workflow for auto-approving and merging Dependabot PRs
echo ""
echo "📝 Creating automerge workflow..."

mkdir -p .github/workflows

cat > .github/workflows/dependabot-automerge.yml << 'EOF'
name: Dependabot Auto-merge

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: write
  pull-requests: write

jobs:
  automerge:
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]'
    steps:
      - name: Dependabot metadata
        id: metadata
        uses: dependabot/fetch-metadata@v1
        with:
          github-token: "${{ secrets.GITHUB_TOKEN }}"

      - name: Approve PR
        run: gh pr review --approve "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Enable auto-merge
        if: steps.metadata.outputs.update-type == 'version-update:semver-patch' || steps.metadata.outputs.update-type == 'version-update:semver-minor'
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
EOF

echo "✅ Workflow created at .github/workflows/dependabot-automerge.yml"

# Create dependabot.yml if it doesn't exist
if [ ! -f .github/dependabot.yml ]; then
    echo ""
    echo "📝 Creating dependabot.yml..."

    cat > .github/dependabot.yml << 'EOF'
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "sam-fakhreddine"
    labels:
      - "dependencies"
      - "python"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    reviewers:
      - "sam-fakhreddine"
    labels:
      - "dependencies"
      - "github-actions"
EOF

    echo "✅ Created .github/dependabot.yml"
fi

echo ""
echo "🎉 Automerge setup complete!"
echo ""
echo "How it works:"
echo "  1. Dependabot creates a PR"
echo "  2. Tests run automatically"
echo "  3. Workflow auto-approves (as GitHub Actions bot)"
echo "  4. Workflow enables auto-merge for patch/minor updates"
echo "  5. PR merges automatically when tests pass"
echo ""
echo "Next steps:"
echo "  1. Commit and push the new workflow files"
echo "  2. Ensure branch protection allows auto-merge"
echo "  3. Wait for Dependabot PRs to test it"
