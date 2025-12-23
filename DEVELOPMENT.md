# Development Guide

This guide explains how to set up the development environment and use the
project tools.

All tasks are defined in `pyproject.toml` using [Poe the
Poet](https://poethepoet.natn.io/).

## Initial Setup

1. Clone and navigate to the project:

   ```bash
   cd /path/to/eml2pdf
   ```

2. Install in development mode with all dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

   This installs the package in editable mode with pytest, coverage, Sphinx,
   and poe.

   Or use the automated setup:

   ```bash
   poe dev-setup
   ```

## Available Commands

Run `poe` to see all available tasks:

```bash
poe
```

All tasks are defined in the `[tool.poe.tasks]` section of `pyproject.toml`.

## Common Workflows

### Running Tests

```bash
# Run all tests
poe test

# Run tests with verbose output
poe test-verbose

# Run tests with coverage report
poe coverage
```

Coverage reports are generated in:

- Terminal: Shows missing lines
- HTML: `htmlcov/index.html`

### Building Documentation

```bash
# Build HTML documentation
poe docs

# Build and serve documentation locally
poe docs-serve
```

Documentation is generated from:

- Google-style docstrings in source code (`eml2pdf/*.py`)
- RST files in `docs/` directory
- Markdown files (via `myst_parser`)

View the built docs at `docs/_build/html/index.html`

### Building Distribution Packages

```bash
# Build source distribution and wheel
poe build
```

Output goes to `dist/` directory:

- `eml2pdf-X.Y.Z.tar.gz` - Source distribution
- `eml2pdf-X.Y.Z-py3-none-any.whl` - Wheel

### Publishing to PyPI

```bash
# Test on TestPyPI first
poe upload-test

# Upload to real PyPI
poe upload
```

**Note**: Requires PyPI credentials configured in `~/.pypirc` or set via
environment variables.

### Cleaning

```bash
# Remove build artifacts and cache
poe clean

# Remove everything including docs
poe clean-all
```

## Project Configuration

All project configuration is in `pyproject.toml`:

### Dependencies

- Core dependencies: Required for running the package
- [dev]: All development tools (tests + docs)
- [test]: Testing tools only
- [docs]: Documentation tools only

Install specific groups:

```bash
pip install -e ".[test]"   # Just testing tools
pip install -e ".[docs]"   # Just documentation tools
pip install -e ".[dev]"    # Everything
```

### Poe the Poet Tasks

All tasks are defined in `[tool.poe.tasks]` in `pyproject.toml`.

### Pytest Configuration

Test settings are in `[tool.pytest.ini_options]`.

### Sphinx Configuration

Documentation settings are in `docs/conf.py`.

- Extensions: autodoc, napoleon, myst_parser
- Theme: Read the Docs
- Napoleon settings for Google-style docstrings

## Writing Documentation

### Docstrings

Use Google-style docstrings in Python code:

Refer to [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).

### RST Files

Create new `.rst` files in `docs/` and add them to the `toctree` in `index.rst`.

Don't document twice. Github shows markdown files. Reuse those instead of
rewriting in rst.

### Markdown Files

Markdown files are supported via `myst_parser`. Include them in RST files:

```rst
.. include:: ../README.md
   :parser: myst_parser.sphinx_
```

## Version Management

Version is managed by `setuptools_scm` based on git tags:

```bash
# Create a new version
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Build will use this version
poe build
```
