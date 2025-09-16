"""Core HFM file parser functionality.

This module provides backward compatibility for the original HFMParser interface
while delegating to the new modular parsing architecture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyhfm.core.file_parser import FileParser

if TYPE_CHECKING:
    from pathlib import Path

    import pyarrow as pa


class HFMParser:
    """Main parser for HFM data files.

    This class maintains backward compatibility while delegating to the new
    modular FileParser architecture.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize HFM parser.

        Args:
            config: Optional configuration overrides
        """
        self._file_parser = FileParser(config)

    def parse_file(self, file_path: str | Path) -> pa.Table:
        """Parse an HFM file and return PyArrow table.

        Args:
            file_path: Path to HFM file

        Returns:
            PyArrow table with embedded metadata

        Raises:
            HFMFileError: If file cannot be read
            HFMUnsupportedFormatError: If file format not supported
            HFMParsingError: If parsing fails
        """
        return self._file_parser.parse_file(file_path)

    @property
    def config(self) -> Any:
        """Access to parser configuration for backward compatibility."""
        return self._file_parser.config

    # Expose parser methods for backward compatibility with tests
    def _extract_value_and_unit(self, sub_line: str) -> dict[str, float | str]:
        """Extract value and unit from a line using pre-compiled patterns."""
        return self._file_parser._extract_value_and_unit(sub_line)

    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a comment."""
        return self._file_parser._is_comment_line(line)

    def _parse_date(self, line: str) -> str | None:
        """Parse date from a line."""
        return self._file_parser._parse_date(line)
