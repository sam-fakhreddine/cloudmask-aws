#!/bin/bash
set -e

REPO="sam-fakhreddine/cloudmask"

echo "🔑 Adding GitHub Secrets for $REPO"
echo ""
echo "Press Enter to skip any secret you don't want to add now."
echo ""

# PYPI_TOKEN
echo "📦 PYPI_TOKEN (for publishing to PyPI):"
echo "Get from: https://pypi.org/manage/account/token/"
read -sp "Enter token (or press Enter to skip): " PYPI_TOKEN
echo ""
if [ -n "$PYPI_TOKEN" ]; then
    echo "$PYPI_TOKEN" | gh secret set PYPI_TOKEN --repo $REPO
    echo "✅ PYPI_TOKEN added"
else
    echo "⏭️  Skipped PYPI_TOKEN"
fi

echo ""

# TEST_PYPI_TOKEN
echo "🧪 TEST_PYPI_TOKEN (for publishing to Test PyPI):"
echo "Get from: https://test.pypi.org/manage/account/token/"
read -sp "Enter token (or press Enter to skip): " TEST_PYPI_TOKEN
echo ""
if [ -n "$TEST_PYPI_TOKEN" ]; then
    echo "$TEST_PYPI_TOKEN" | gh secret set TEST_PYPI_TOKEN --repo $REPO
    echo "✅ TEST_PYPI_TOKEN added"
else
    echo "⏭️  Skipped TEST_PYPI_TOKEN"
fi

echo ""

# CODECOV_TOKEN
echo "📊 CODECOV_TOKEN (for code coverage reporting):"
echo "Get from: https://codecov.io/gh/$REPO/settings"
read -sp "Enter token (or press Enter to skip): " CODECOV_TOKEN
echo ""
if [ -n "$CODECOV_TOKEN" ]; then
    echo "$CODECOV_TOKEN" | gh secret set CODECOV_TOKEN --repo $REPO
    echo "✅ CODECOV_TOKEN added"
else
    echo "⏭️  Skipped CODECOV_TOKEN"
fi

echo ""
echo "🎉 Done! View secrets at:"
echo "https://github.com/$REPO/settings/secrets/actions"
