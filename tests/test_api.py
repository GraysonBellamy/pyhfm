"""Tests for the main API functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyarrow as pa
import pytest

from pyhfm.api.loaders import read_hfm
from pyhfm.exceptions import HFMFileError, HFMUnsupportedFormatError

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
