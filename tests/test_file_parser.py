"""Tests for FileParser functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pyhfm.core.file_parser import FileParser
from pyhfm.exceptions import HFMParsingError


class TestFileParser:
    """Test cases for FileParser class."""

    def test_file_parser_initialization(self) -> None:
        """Test FileParser initialization."""
        parser = FileParser()
        assert parser.config is not None
        assert parser.metadata_parser is not None
        assert parser.setpoint_parser is not None

    def test_parse_file_success(self, temp_hfm_file: Path) -> None:
        """Test successful file parsing."""
        parser = FileParser()
        table = parser.parse_file(temp_hfm_file)

        assert table is not None
        assert len(table) > 0

    def test_parse_file_with_binary_encoding_detection(
        self, temp_hfm_file: Path
    ) -> None:
        """Test file parsing when encoding detection returns 'binary'."""
        with patch("pyhfm.core.file_parser.detect_encoding") as mock_detect:
            mock_detect.return_value = "binary"

            parser = FileParser()
            table = parser.parse_file(temp_hfm_file)

            assert table is not None

    def test_parse_file_with_unknown_encoding_detection(
        self, temp_hfm_file: Path
    ) -> None:
        """Test file parsing when encoding detection returns 'unknown'."""
        with patch("pyhfm.core.file_parser.detect_encoding") as mock_detect:
            mock_detect.return_value = "unknown"

            parser = FileParser()
            table = parser.parse_file(temp_hfm_file)

            assert table is not None

    def test_parse_file_encoding_detection_failure(self, temp_hfm_file: Path) -> None:
        """Test file parsing when encoding detection raises an exception."""
        with patch("pyhfm.core.file_parser.detect_encoding") as mock_detect:
            mock_detect.side_effect = Exception("Encoding detection failed")

            parser = FileParser()
            table = parser.parse_file(temp_hfm_file)

            assert table is not None

    def test_extract_metadata_hash_calculation_failure(
        self, temp_hfm_file: Path
    ) -> None:
        """Test metadata extraction when hash calculation fails."""
        # Mock the file operations and hash calculation
        with (
            patch.object(Path, "open") as mock_open,
            patch("pyhfm.core.file_parser.get_hash") as mock_hash,
        ):
            # Setup file mock
            mock_file = MagicMock()
            mock_file.readlines.return_value = ["Sample data"]
            mock_open.return_value.__enter__.return_value = mock_file

            # Make hash calculation fail
            mock_hash.side_effect = Exception("Hash calculation failed")

            parser = FileParser()
            with pytest.raises(HFMParsingError, match="Failed to calculate file hash"):
                parser._extract_metadata(temp_hfm_file, "utf-8")

    def test_parse_setpoint_specific_patterns(self, temp_hfm_file: Path) -> None:
        """Test parsing of setpoint-specific patterns."""
        # Create a mock file with setpoint patterns
        test_lines = [
            "Block Averages for setpoint 1",
            "Number of Setpoints: 5",
            "Setpoint No. 1",
        ]

        with (
            patch.object(Path, "open") as mock_open,
            patch("pyhfm.core.file_parser.get_hash") as mock_hash,
        ):
            mock_file = MagicMock()
            mock_file.readlines.return_value = test_lines
            mock_open.return_value.__enter__.return_value = mock_file
            mock_hash.return_value = "test_hash"

            parser = FileParser()
            # This should exercise the setpoint-specific parsing logic
            metadata = parser._extract_metadata(temp_hfm_file, "utf-8")

            assert isinstance(metadata, dict)
