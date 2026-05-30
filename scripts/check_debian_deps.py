#!/usr/bin/env python3
"""Check if dependencies are at versions supported by Debian stable."""

import argparse
import subprocess
import re
import sys
from pathlib import Path


def check_rmadison():
    """Check if rmadison is available, install hint if on Debian."""
    try:
        subprocess.run(['rmadison', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check if we're on a Debian-based system
    try:
        with open('/etc/os-release') as f:
            content = f.read()
            if 'debian' in content.lower() or 'ubuntu' in content.lower():
                print("Error: 'rmadison' not found.", file=sys.stderr)
                print("Install it on Debian/Ubuntu with:", file=sys.stderr)
                print("  sudo apt install devscripts", file=sys.stderr)
                sys.exit(1)
    except FileNotFoundError:
        pass
    
    print("Error: 'rmadison' not found and could not detect Debian system.", file=sys.stderr)
    print("Install devscripts package or ensure rmadison is in PATH.", file=sys.stderr)
    sys.exit(1)


check_rmadison()

parser = argparse.ArgumentParser(
    description='Check if project dependencies match Debian stable versions'
)
parser.add_argument(
    '--suite',
    default='stable',
    help='Debian suite to check against (default: stable)'
)
args = parser.parse_args()

# Mapping from PyPI package names to Debian package names
PYPI_TO_DEBIAN = {
    'weasyprint': 'weasyprint',
    'markdown': 'python3-markdown',
    'beautifulsoup4': 'python3-bs4',
    'hurry.filesize': 'python3-hurry.filesize',
}

# Development dependencies
DEV_DEPS = {
    'pytest': 'python3-pytest',
    'pytest-cov': 'python3-pytest-cov',
    'sphinx': 'python3-sphinx',
    'sphinx-rtd-theme': 'python3-sphinx-rtd-theme',
    'myst-parser': 'python3-myst-parser',
    'ruff': 'ruff',
    'pymarkdownlnt': 'pymarkdownlnt',
}


def get_debian_version(package, suite):
    """Get the version of a package in Debian suite."""
    try:
        result = subprocess.run(
            ['rmadison', '-s', suite, package],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse the first line: package | version | suite
        lines = result.stdout.strip().split('\n')
        if lines:
            # Format: package_name | version | suite | ...
            match = re.match(r'\S+\s*\|\s*(\S+)\s*\|', lines[0])
            if match:
                return match.group(1)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def read_pinned_version(package):
    """Read the pinned version from pyproject.toml."""
    pyproject = Path(__file__).parent.parent / 'pyproject.toml'
    content = pyproject.read_text()

    # Look for the package in dependencies
    pattern = rf'{re.escape(package)}\s*[>=~!]=\s*["\']?([^"\'\s,]+)'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None


def check_dependencies(deps_map, label, suite):
    """Check and display dependency versions."""
    print(f"\n{label}:")
    print("-" * 60)

    for pypi_name, debian_name in deps_map.items():
        pinned = read_pinned_version(pypi_name)
        debian_ver = get_debian_version(debian_name, suite)

        status = "✓" if pinned and debian_ver and pinned.startswith(debian_ver.rsplit('.')[0]) else "✗"

        print(f"  {status} {pypi_name:20} ({debian_name:25}) pinned: {pinned or 'N/A':<12} debian: {debian_ver or 'N/A'}")


def main():
    print(f"Checking {args.suite} versions for dependencies")
    print("=" * 60)

    check_dependencies(PYPI_TO_DEBIAN, "Main dependencies", args.suite)
    check_dependencies(DEV_DEPS, "Development dependencies", args.suite)

    print(f"\nNote: ✓ = pinned version matches Debian {args.suite} major version")
    print("      ✗ = mismatch or package not found")


if __name__ == '__main__':
    main()
