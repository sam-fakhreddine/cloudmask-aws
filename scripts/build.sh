#!/bin/bash
# Quick build and publish script for CloudMask

set -e

echo "====================================="
echo "  CloudMask Build Script"
echo "====================================="

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: venv not found. Run: python -m venv venv"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Run tests
echo ""
echo "🧪 Running tests..."
pytest tests/ -v || {
    echo "❌ Tests failed! Fix errors before building."
    exit 1
}

# Format code
echo ""
echo "🎨 Formatting code..."
black cloudmask tests examples

# Lint code
echo ""
echo "🔍 Linting code..."
ruff check cloudmask tests

# Build package
echo ""
echo "📦 Building package..."
python -m build

# Check package
echo ""
echo "✅ Checking package..."
twine check dist/*

echo ""
echo "====================================="
echo "  ✓ Build complete!"
echo "====================================="
echo ""
echo "Package files created in dist/:"
ls -lh dist/
echo ""
echo "Next steps:"
echo ""
echo "To test on TestPyPI:"
echo "  twine upload --repository testpypi dist/*"
echo ""
echo "To publish to PyPI:"
echo "  twine upload dist/*"
echo ""
