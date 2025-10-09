#!/bin/bash
# Development environment setup script for CloudMask

set -e

echo "🎭 CloudMask Development Setup"
echo "=============================="
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "✓ uv detected"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ Error: Python 3.10+ required (found: $python_version)"
    exit 1
fi
echo "✓ Python $python_version detected"
echo ""

# Create or use virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment found"
fi
echo ""

# Install package with dev dependencies
echo "Installing CloudMask with development dependencies..."
uv pip install -e ".[dev]"
echo "✓ Package installed"
echo ""

# Install pre-commit hooks (only if in a git repo)
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Setting up pre-commit hooks..."
    source .venv/bin/activate
    pre-commit install
    echo "✓ Pre-commit hooks installed"
    echo ""
else
    echo "⚠ Not a git repository - skipping pre-commit hooks setup"
    echo "  Run 'git init' and then 'pre-commit install' manually"
    echo ""
fi

# Run initial quality checks
echo "Running initial quality checks..."
echo ""

echo "1. Formatting with Black..."
.venv/bin/black --check cloudmask/ tests/ examples/ || {
    echo "   Formatting issues found. Run 'make format' to fix."
}

echo ""
echo "2. Linting with Ruff..."
.venv/bin/ruff check cloudmask/ tests/ examples/ || {
    echo "   Linting issues found. Run 'make lint-fix' to auto-fix."
}

echo ""
echo "3. Type checking with Mypy..."
.venv/bin/mypy cloudmask/ || {
    echo "   Type checking issues found. Review and fix manually."
}

echo ""
echo "4. Docstring checking with Pydocstyle..."
.venv/bin/pydocstyle cloudmask/ || {
    echo "   Docstring issues found. Review and fix manually."
}

echo ""
echo "=============================="
echo "✓ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  - Activate the virtual environment: source .venv/bin/activate"
echo "  - Run 'make help' to see available commands"
echo "  - Run 'make quality-check' to run all quality checks"
echo "  - Run 'make test' to run tests"
echo "  - Run 'make all' to run everything"
echo ""
echo "See CODE_QUALITY.md for detailed documentation"
