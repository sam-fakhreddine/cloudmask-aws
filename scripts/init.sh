#!/bin/bash
# Initialize CloudMask project after creation

echo "🎭 CloudMask Project Initialization"
echo "===================================="

# Make scripts executable
chmod +x run_tests.sh
chmod +x build.sh

echo "✓ Made scripts executable"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate and install
echo ""
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate

pip install --upgrade pip > /dev/null 2>&1
pip install -e ".[dev]" > /dev/null 2>&1

echo "✓ Dependencies installed"

# Run tests to verify
echo ""
echo "Running tests to verify installation..."
pytest tests/ -v --tb=short

echo ""
echo "===================================="
echo "✓ CloudMask is ready!"
echo "===================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Customize your package:"
echo "   - Edit pyproject.toml (name, email, GitHub username)"
echo "   - Edit LICENSE (your name)"
echo "   - Edit README.md (update GitHub URLs)"
echo ""
echo "2. Try it out:"
echo "   cloudmask --help"
echo "   python examples/basic_usage.py"
echo ""
echo "3. Initialize git:"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo ""
echo "4. Read GETTING_STARTED.md for full instructions"
echo ""
