"""Tests for the main API functions."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

from pyhfm.api.loaders import read_hfm
from pyhfm.exceptions import HFMError, HFMFileError, HFMUnsupportedFormatError

if TYPE_CHECKING:
    from pathlib import Path


class TestReadHFM:
    """Test cases for read_hfm function."""

    def test_read_hfm_basic(self, temp_hfm_file: Path) -> None:
        """Test basic read_hfm functionality."""
        table = read_hfm(temp_hfm_file)

        assert isinstance(table, pa.Table)
        assert len(table) > 0
        assert "setpoint" in table.column_names

    def test_read_hfm_with_metadata(self, temp_hfm_file: Path) -> None:
        """Test read_hfm with return_metadata=True."""
        metadata, table = read_hfm(temp_hfm_file, return_metadata=True)

        assert isinstance(table, pa.Table)
        assert isinstance(metadata, dict)
        assert len(table) > 0

    def test_read_hfm_file_not_found(self) -> None:
        """Test read_hfm with non-existent file."""
        with pytest.raises(HFMFileError, match="File not found"):
            read_hfm("nonexistent.tst")

    def test_read_hfm_unsupported_extension(self, tmp_path: Path) -> None:
        """Test read_hfm with unsupported file extension."""
        bad_file = tmp_path / "test.txt"
        bad_file.touch()

        with pytest.raises(
            HFMUnsupportedFormatError, match="Unsupported file extension"
        ):
            read_hfm(bad_file)

    def test_read_hfm_custom_config(self, temp_hfm_file: Path) -> None:
        """Test read_hfm with custom configuration."""
        config = {"default_encoding": "utf-16le"}
        table = read_hfm(temp_hfm_file, config=config)

        assert isinstance(table, pa.Table)
        assert len(table) > 0

    def test_read_hfm_fallback_metadata_parsing(self, temp_hfm_file: Path) -> None:
        """Test read_hfm fallback metadata parsing when table metadata is missing."""
        # Mock the table to not have the file_metadata in schema.metadata
        with patch("pyhfm.api.loaders.HFMParser") as mock_parser:
            # Create a mock table without file_metadata
            mock_table = pa.table({"test": [1, 2, 3]})
            mock_parser.return_value.parse_file.return_value = mock_table

            # This should trigger the fallback metadata parsing path
            metadata, table = read_hfm(temp_hfm_file, return_metadata=True)

            assert isinstance(metadata, dict)
            assert isinstance(table, pa.Table)

    def test_read_hfm_metadata_without_file_metadata_key(
        self, temp_hfm_file: Path
    ) -> None:
        """Test read_hfm when metadata exists but doesn't contain file_metadata key."""
        with patch("pyhfm.api.loaders.HFMParser") as mock_parser:
            # Create a mock table with metadata but no file_metadata key
            mock_table = MagicMock()
            mock_table.schema.metadata = {b"other_key": b"other_value"}
            mock_parser.return_value.parse_file.return_value = mock_table

            # This should return empty dict for metadata
            metadata, table = read_hfm(temp_hfm_file, return_metadata=True)

            assert metadata == {}
            assert table == mock_table

    def test_read_hfm_unexpected_exception(self, temp_hfm_file: Path) -> None:
        """Test read_hfm handling of unexpected exceptions."""
        with patch("pyhfm.api.loaders.HFMParser") as mock_parser:
            # Make the parser raise an unexpected exception
            mock_parser.side_effect = ValueError("Unexpected error")

            with pytest.raises(HFMError, match="Unexpected error reading HFM file"):
                read_hfm(temp_hfm_file)
