.PHONY: help venv install install-dev format lint type-check test test-cov docs docs-clean clean pre-commit-install pre-commit-run quality-check all

help:
	@echo "CloudMask Development Commands"
	@echo "=============================="
	@echo "venv              - Create virtual environment with uv"
	@echo "install           - Install package"
	@echo "install-dev       - Install package with dev dependencies"
	@echo "format            - Format code with black"
	@echo "lint              - Lint code with ruff"
	@echo "type-check        - Type check with mypy"
	@echo "docstring-check   - Check docstrings with pydocstyle"
	@echo "test              - Run tests"
	@echo "test-cov          - Run tests with coverage report"
	@echo "docs              - Build HTML documentation"
	@echo "docs-clean        - Clean documentation build"
	@echo "pre-commit-install - Install pre-commit hooks"
	@echo "pre-commit-run    - Run pre-commit on all files"
	@echo "quality-check     - Run all quality checks (format, lint, type-check, docstring-check)"
	@echo "clean             - Remove build artifacts"
	@echo "all               - Run quality checks and tests"

venv:
	uv venv

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

format:
	black cloudmask/ tests/ examples/

lint:
	ruff check cloudmask/ tests/ examples/

lint-fix:
	ruff check --fix cloudmask/ tests/ examples/

type-check:
	mypy cloudmask/

docstring-check:
	pydocstyle cloudmask/

test:
	pytest

test-cov:
	pytest --cov=cloudmask --cov-report=term-missing --cov-report=html

pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

quality-check: format lint type-check docstring-check
	@echo "✓ All quality checks passed!"

all: quality-check test
	@echo "✓ All checks and tests passed!"

docs:
	cd docs && make html
	@echo "Documentation built in docs/_build/html/"

docs-clean:
	cd docs && make clean

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/ .coverage
	rm -rf docs/_build
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
