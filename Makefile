# Self-documenting Makefile
#
# NOTE: This project now uses Poe the Poet (more pythonic!)
# Run 'poe' to see all tasks defined in pyproject.toml
# This Makefile is kept for compatibility.
#
# Add '##' after target name to include it in help output

.DEFAULT_GOAL := help
.PHONY: help install install-dev test test-verbose coverage docs docs-serve clean clean-all build upload

help: ## Show this help message
	@echo "NOTE: This project now uses Poe the Poet!"
	@echo "      Run 'poe' to see all tasks (defined in pyproject.toml)"
	@echo "      This Makefile is kept for compatibility."
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "Prefer using: poe <task>  (see 'poe' for list)"

# Installation targets
install: ## Install package in development mode
	pip install -e .

install-dev: ## Install package with development dependencies
	pip install -e ".[dev]"

install-docs: ## Install documentation dependencies only
	pip install -e ".[docs]"

install-test: ## Install test dependencies only
	pip install -e ".[test]"

# Testing targets
test: ## Run tests with pytest
	pytest

test-verbose: ## Run tests with verbose output
	pytest -vv

coverage: ## Run tests with coverage report
	pytest --cov=eml2pdf --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Documentation targets
docs: ## Build HTML documentation with Sphinx
	@echo "Building documentation..."
	cd docs && sphinx-build -b html . _build/html
	@echo ""
	@echo "Documentation built in docs/_build/html/index.html"

docs-serve: docs ## Build docs and serve locally on http://localhost:8000
	@echo "Serving documentation on http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	cd docs/_build/html && python -m http.server 8000

docs-clean: ## Clean documentation build files
	rm -rf docs/_build

# Build and distribution targets
build: clean ## Build source and wheel distributions
	python -m build
	@echo ""
	@echo "Build complete. Distributions in dist/"

upload-test: build ## Upload to TestPyPI (requires credentials)
	python -m twine upload --repository testpypi dist/*

upload: build ## Upload to PyPI (requires credentials)
	python -m twine upload dist/*

# Cleaning targets
clean: ## Remove build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-all: clean docs-clean ## Remove all build, cache, and documentation files
	@echo "Cleaned all build artifacts"

# Development workflow targets
check: test coverage ## Run all tests with coverage (alias)

dev-setup: install-dev ## Complete development environment setup
	@echo ""
	@echo "Development environment ready!"
	@echo "Try: make test, make docs, make build"
