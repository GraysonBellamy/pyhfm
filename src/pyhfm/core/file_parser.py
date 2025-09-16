"""File parsing orchestrator for HFM files."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pyhfm.constants import DEFAULT_PARSING_CONFIG, FileMetadata
from pyhfm.core.metadata_parser import MetadataParser
from pyhfm.core.setpoint_parser import SetpointParser
from pyhfm.exceptions import (
    HFMFileError,
    HFMParsingError,
    HFMUnsupportedFormatError,
)
from pyhfm.extractors.data_extractor import DataExtractor
from pyhfm.utils import detect_encoding, get_hash, set_metadata

if TYPE_CHECKING:
    import pyarrow as pa


class FileParser:
    """Orchestrates HFM file parsing using specialized parsers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize file parser.

        Args:
            config: Optional configuration overrides
        """
        if config:
            # Create new config with overrides
            config_dict = {
                key: value
                for key, value in config.items()
                if hasattr(DEFAULT_PARSING_CONFIG, key)
            }
            self.config = replace(DEFAULT_PARSING_CONFIG, **config_dict)
        else:
            self.config = DEFAULT_PARSING_CONFIG

        # Initialize specialized parsers
        self.metadata_parser = MetadataParser(self.config)
        self.setpoint_parser = SetpointParser(self.config)

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
        path = Path(file_path)

        # Validate file exists and extension
        if not path.exists():
            error_msg = f"File not found: {path}"
            raise HFMFileError(error_msg, str(path), "read")

        if path.suffix not in self.config.supported_extensions:
            error_msg = f"Unsupported file extension: {path.suffix}"
            raise HFMUnsupportedFormatError(
                error_msg,
                str(path),
                path.suffix,
                list(self.config.supported_extensions),
            )

        try:
            # Detect encoding, with fallback to default
            encoding = detect_encoding(str(path))
            # Handle case where detect_encoding returns 'binary' or other invalid encoding
            if encoding in ("binary", "unknown"):
                encoding = self.config.default_encoding
        except Exception:
            # Fall back to default encoding if detection fails
            encoding = self.config.default_encoding

        try:
            # Extract metadata
            metadata = self._extract_metadata(path, encoding)

            # Extract data from metadata
            data_table = self._extract_data(metadata)

            # Embed metadata in table
            return set_metadata(
                data_table, tbl_meta={"file_metadata": metadata, "type": "HFM"}
            )

        except Exception as e:
            if isinstance(e, (HFMParsingError, HFMFileError)):
                raise
            error_msg = f"Failed to parse HFM file: {e}"
            raise HFMParsingError(
                error_msg,
                str(path),
            ) from e

    def _extract_metadata(self, path: Path, encoding: str) -> FileMetadata:
        """Extract metadata from HFM file.

        Args:
            path: Path to HFM file
            encoding: File encoding

        Returns:
            Extracted metadata dictionary

        Raises:
            HFMFileError: If file cannot be read
            HFMParsingError: If metadata extraction fails
        """
        try:
            with path.open(encoding=encoding) as f:
                lines = f.readlines()
        except Exception as e:
            error_msg = f"Failed to read file: {e}"
            raise HFMFileError(
                error_msg,
                str(path),
                "read",
            ) from e

        # Initialize metadata
        metadata: dict[str, Any] = {}

        # Get file hash
        try:
            file_hash = get_hash(str(path))
        except Exception as e:
            msg = f"Failed to calculate file hash: {e}"
            raise HFMParsingError(
                msg,
                str(path),
            ) from e

        try:
            # Use metadata parser for basic metadata extraction
            measurement_type = self.metadata_parser.extract_basic_metadata(
                lines, metadata
            )

            # Parse setpoint-specific data
            self._parse_setpoint_lines(lines, metadata)

        except Exception as e:
            if isinstance(e, HFMParsingError):
                raise
            msg = f"Failed to parse metadata: {e}"
            raise HFMParsingError(
                msg,
                str(path),
                getattr(e, "line_number", None),
            ) from e

        # Add final metadata
        metadata["type"] = measurement_type
        metadata["file_hash"] = {
            "file": path.name,
            "method": "BLAKE2b",
            "hash": file_hash,
        }

        return metadata  # type: ignore[return-value]

    def _parse_setpoint_lines(self, lines: list[str], metadata: dict[str, Any]) -> None:
        """Parse lines for setpoint-specific data."""
        for i, raw_line in enumerate(lines):
            line = raw_line.strip()

            # Handle setpoint-specific patterns
            if "Block Averages for setpoint" in line:
                self.setpoint_parser.parse_block_averages_setpoint(
                    line, lines, i, metadata
                )
            elif line.startswith("Number of Setpoints"):
                self.setpoint_parser.parse_setpoints_header(
                    line, lines, i, metadata, ""
                )
            elif line.startswith("Setpoint No."):
                self.setpoint_parser.parse_setpoint_data(line, lines, i, metadata)

    def _extract_data(self, metadata: FileMetadata) -> pa.Table:
        """Extract data from metadata and create PyArrow table.

        Args:
            metadata: Extracted metadata dictionary

        Returns:
            PyArrow table with measurement data
        """
        extractor = DataExtractor()
        return extractor.extract_data(metadata)

    # Expose parser methods for backward compatibility with tests
    def _extract_value_and_unit(self, sub_line: str) -> dict[str, float | str]:
        """Extract value and unit from a line using pre-compiled patterns."""
        return self.metadata_parser._extract_value_and_unit(sub_line)

    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a comment."""
        return self.metadata_parser._is_comment_line(line)

    def _parse_date(self, line: str) -> str | None:
        """Parse date from a line."""
        return self.metadata_parser._parse_date(line)
