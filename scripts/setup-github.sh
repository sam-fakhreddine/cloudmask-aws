#!/bin/bash
set -e

echo "🔧 Setting up GitHub repository protection and secrets..."
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

REPO="sam-fakhreddine/cloudmask"

echo "📋 Repository: $REPO"
echo ""

# Detect default branch
DEFAULT_BRANCH=$(gh api repos/$REPO --jq '.default_branch')
echo "Default branch: $DEFAULT_BRANCH"
echo ""

# Enable branch protection
echo "🛡️  Enabling branch protection for $DEFAULT_BRANCH branch..."
gh api repos/$REPO/branches/$DEFAULT_BRANCH/protection \
  --method PUT \
  --input .github/branch-protection.json \
  && echo "✅ Branch protection enabled" \
  || echo "⚠️  Branch protection failed (may need to run tests first)"

echo ""

# Add secrets
echo "🔑 Adding repository secrets..."
echo ""

echo "Enter PYPI_TOKEN (or press Enter to skip):"
read -s PYPI_TOKEN
if [ -n "$PYPI_TOKEN" ]; then
    echo "$PYPI_TOKEN" | gh secret set PYPI_TOKEN --repo $REPO
    echo "✅ PYPI_TOKEN added"
fi

echo ""
echo "Enter TEST_PYPI_TOKEN (or press Enter to skip):"
read -s TEST_PYPI_TOKEN
if [ -n "$TEST_PYPI_TOKEN" ]; then
    echo "$TEST_PYPI_TOKEN" | gh secret set TEST_PYPI_TOKEN --repo $REPO
    echo "✅ TEST_PYPI_TOKEN added"
fi

echo ""
echo "Enter CODECOV_TOKEN (or press Enter to skip):"
read -s CODECOV_TOKEN
if [ -n "$CODECOV_TOKEN" ]; then
    echo "$CODECOV_TOKEN" | gh secret set CODECOV_TOKEN --repo $REPO
    echo "✅ CODECOV_TOKEN added"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Enable Dependabot: Settings → Security → Dependabot alerts"
echo "2. Enable CodeQL: Settings → Security → Code scanning"
echo "3. Enable Secret scanning: Settings → Security → Secret scanning"
echo "4. Push changes to trigger workflows"
