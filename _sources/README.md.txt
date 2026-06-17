# Documentation Setup

This directory contains Sphinx documentation for eml2pdf.

## Quick Start

1. Install dependencies:

   ```bash
   pip install -e ".[dev]"
   # or just docs dependencies:
   pip install -e ".[docs]"
   ```

2. Build documentation:

   ```bash
   poe docs
   ```

3. View documentation:
   - Open `docs/_build/html/index.html` in your browser
   - Or run `poe docs-serve` to view at <http://localhost:8000>

## Structure

- `conf.py` - Sphinx configuration
- `index.rst` - Main documentation page
- `api.rst` - Auto-generated API documentation from docstrings
- `*.rst` - Other doc pages, only included if added to the toctree in
  index.rst.
- `_build/` - Generated documentation (gitignored)
- `_static/` - Static files for documentation

## Configuration Highlights

- Theme: Read the Docs theme (`sphinx_rtd_theme`)
- Extensions:
  - `autodoc` - Auto-generate docs from docstrings
  - `napoleon` - Google/NumPy docstring support
  - `viewcode` - Link to source code
  - `myst_parser` - Markdown file support

## Rebuilding

After updating docstrings or documentation files:

```bash
poe docs
```

To clean and rebuild:

```bash
poe docs-clean
poe docs
```
