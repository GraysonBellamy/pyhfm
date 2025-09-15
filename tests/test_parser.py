"""Tests for HFM parser functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pyhfm.core.parser import HFMParser
from pyhfm.exceptions import HFMFileError, HFMParsingError

if TYPE_CHECKING:
    from pathlib import Path


class TestHFMParser:
    """Test cases for HFMParser class."""

    def test_parser_initialization(self) -> None:
        """Test parser initialization."""
        parser = HFMParser()
        assert parser.config is not None

    def test_parser_custom_config(self) -> None:
        """Test parser with custom configuration."""
        config = {"default_encoding": "utf-8"}
        parser = HFMParser(config)
        assert parser.config.default_encoding == "utf-8"

    def test_parse_file_success(self, temp_hfm_file: Path) -> None:
        """Test successful file parsing."""
        parser = HFMParser()
        table = parser.parse_file(temp_hfm_file)

        assert table is not None
        assert len(table) > 0

    def test_parse_file_not_found(self) -> None:
        """Test parsing non-existent file."""
        parser = HFMParser()

        with pytest.raises(HFMFileError, match="File not found"):
            parser.parse_file("nonexistent.tst")

    def test_parse_date_valid(self) -> None:
        """Test date parsing with valid date."""
        parser = HFMParser()
        date_str = "Sunday, January 01, 2023, Time 10:00"
        result = parser._parse_date(date_str)

        assert result is not None
        assert "2023-01-01T10:00:00" in result

    def test_parse_date_invalid(self) -> None:
        """Test date parsing with invalid date."""
        parser = HFMParser()
        result = parser._parse_date("invalid date")

        assert result is None

    def test_extract_value_and_unit(self) -> None:
        """Test value and unit extraction."""
        parser = HFMParser()
        result = parser._extract_value_and_unit("25.40 mm")

        assert result["value"] == 25.40
        assert result["unit"] == "mm"

    def test_extract_value_and_unit_no_value(self) -> None:
        """Test value and unit extraction with no numeric value."""
        parser = HFMParser()

        with pytest.raises(HFMParsingError, match="No numeric value found"):
            parser._extract_value_and_unit("no numbers here")

    def test_is_comment_line(self) -> None:
        """Test comment line detection."""
        parser = HFMParser()

        assert parser._is_comment_line("[This is a comment]")
        assert not parser._is_comment_line("Not a comment")
        assert not parser._is_comment_line("[Nested [brackets] not allowed]")
