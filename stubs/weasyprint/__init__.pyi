"""Type stubs for WeasyPrint - minimal subset used by eml2pdf.

This stub file provides type information for the WeasyPrint classes
and methods actually used in the eml2pdf package to enable type checking.
"""

from collections.abc import Sequence
from io import IOBase
from typing import Any

class HTML:
    """WeasyPrint HTML document class."""

    def __init__(self, string: str) -> None:
        """Initialize HTML from a string.

        Args:
            string: HTML content as a string.
        """
        ...

    def write_pdf(
        self,
        target: IOBase | str | None | None = ...,
        presentational_hints: bool = ...,
        stylesheets: Sequence[Any] | None = ...,
    ) -> bytes | None:
        """Render the HTML to PDF.

        Args:
            target: Output destination. Can be a file-like object, file path,
                or None.
            presentational_hints: Whether to use presentational hints.
            stylesheets: List of CSS stylesheets to apply.

        Returns:
            PDF content as bytes if target is None, otherwise None.
        """
        ...

class CSS:
    """WeasyPrint CSS stylesheet class."""

    def __init__(self, string: str) -> None:
        """Initialize CSS from a string.

        Args:
            string: CSS content as a string.
        """
        ...
