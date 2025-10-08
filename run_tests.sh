#!/bin/bash
# Quick test runner for CloudMask

echo "🧪 Running CloudMask Tests..."
echo "=============================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests with coverage
pytest tests/ -v --cov=cloudmask --cov-report=term-missing --cov-report=html

echo ""
echo "=============================="
echo "✓ Tests complete!"
echo ""
echo "View HTML coverage report: open htmlcov/index.html"
