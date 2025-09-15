"""Tests for utility functions."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pyarrow as pa
import pytest

from pyhfm.utils import detect_encoding, get_hash, set_metadata


class TestDetectEncoding:
    """Test the detect_encoding function."""

    def test_detect_encoding_utf8(self) -> None:
        """Test encoding detection for UTF-8 files."""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("Hello, world! This is a UTF-8 file.")
            temp_path = f.name

        try:
            encoding = detect_encoding(temp_path)
            assert encoding in ("utf-8", "ascii")  # ASCII is a subset of UTF-8
        finally:
            Path(temp_path).unlink()

    def test_detect_encoding_ascii(self) -> None:
        """Test encoding detection for ASCII files."""
        with tempfile.NamedTemporaryFile(mode="w", encoding="ascii", delete=False) as f:
            f.write("Hello, world!")
            temp_path = f.name

        try:
            encoding = detect_encoding(temp_path)
            assert encoding in ("utf-8", "ascii")
        finally:
            Path(temp_path).unlink()

    def test_detect_encoding_empty_file(self) -> None:
        """Test encoding detection for empty files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_path = f.name

        try:
            encoding = detect_encoding(temp_path)
            assert encoding == "utf-8"  # Default for empty files
        finally:
            Path(temp_path).unlink()

    def test_detect_encoding_nonexistent_file(self) -> None:
        """Test encoding detection for non-existent files."""
        encoding = detect_encoding("/path/that/does/not/exist.txt")
        assert encoding == "utf-8"  # Fallback

    def test_detect_encoding_binary_file(self) -> None:
        """Test encoding detection for binary files."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\xff\xfe\xfd")
            temp_path = f.name

        try:
            encoding = detect_encoding(temp_path)
            # chardet might detect iso-8859-1 or other encoding for binary data
            # Any valid encoding string is acceptable for this test
            assert isinstance(encoding, str)
            assert len(encoding) > 0
        finally:
            Path(temp_path).unlink()

    def test_detect_encoding_low_confidence(self) -> None:
        """Test encoding detection with low confidence data."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            # Write some ambiguous data that might give low confidence
            f.write(b"a" * 10)  # Very simple, low-confidence data
            temp_path = f.name

        try:
            encoding = detect_encoding(temp_path)
            # Should return detected encoding or fallback to utf-8
            assert isinstance(encoding, str)
            assert len(encoding) > 0
        finally:
            Path(temp_path).unlink()


class TestGetHash:
    """Test the get_hash function."""

    def test_get_hash_basic(self) -> None:
        """Test basic hash calculation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Hello, world!")
            temp_path = f.name

        try:
            hash_value = get_hash(temp_path)
            # SHA-256 of "Hello, world!" should be consistent
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64  # SHA-256 produces 64-character hex string
            assert all(c in "0123456789abcdef" for c in hash_value)
        finally:
            Path(temp_path).unlink()

    def test_get_hash_empty_file(self) -> None:
        """Test hash calculation for empty files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_path = f.name

        try:
            hash_value = get_hash(temp_path)
            # SHA-256 of empty string
            expected = (
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            )
            assert hash_value == expected
        finally:
            Path(temp_path).unlink()

    def test_get_hash_large_file(self) -> None:
        """Test hash calculation for large files (tests chunked reading)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            # Write more than 4KB to test chunked reading
            large_content = "A" * 10000
            f.write(large_content)
            temp_path = f.name

        try:
            hash_value = get_hash(temp_path)
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64

            # Verify consistency - should get same hash for same content
            hash_value2 = get_hash(temp_path)
            assert hash_value == hash_value2
        finally:
            Path(temp_path).unlink()

    def test_get_hash_nonexistent_file(self) -> None:
        """Test hash calculation for non-existent files."""
        with pytest.raises(OSError, match="No such file or directory"):
            get_hash("/path/that/does/not/exist.txt")

    def test_get_hash_binary_file(self) -> None:
        """Test hash calculation for binary files."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\xff\xfe\xfd")
            temp_path = f.name

        try:
            hash_value = get_hash(temp_path)
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64
        finally:
            Path(temp_path).unlink()


class TestSetMetadata:
    """Test the set_metadata function."""

    def create_sample_table(self) -> pa.Table:
        """Create a sample PyArrow table for testing."""
        data = {
            "column1": [1, 2, 3],
            "column2": [4.5, 5.6, 6.7],
            "column3": ["a", "b", "c"],
        }
        return pa.table(data)

    def test_set_metadata_table_only(self) -> None:
        """Test setting table-level metadata only."""
        table = self.create_sample_table()
        tbl_meta = {"key1": "value1", "key2": 42, "key3": True}

        result = set_metadata(table, tbl_meta=tbl_meta)

        assert result.schema.metadata is not None
        assert b"key1" in result.schema.metadata
        assert b"key2" in result.schema.metadata
        assert b"key3" in result.schema.metadata

        # Verify JSON serialization
        assert json.loads(result.schema.metadata[b"key1"].decode()) == "value1"
        assert json.loads(result.schema.metadata[b"key2"].decode()) == 42
        assert json.loads(result.schema.metadata[b"key3"].decode()) is True

    def test_set_metadata_column_only(self) -> None:
        """Test setting column-level metadata only."""
        table = self.create_sample_table()
        col_meta = {
            "column1": {"unit": "meters", "type": "integer"},
            "column2": {"unit": "seconds", "precision": 2},
        }

        result = set_metadata(table, col_meta=col_meta)

        # Check column1 metadata
        col1_field = result.schema.field("column1")
        assert col1_field.metadata is not None
        assert b"unit" in col1_field.metadata
        assert b"type" in col1_field.metadata
        assert json.loads(col1_field.metadata[b"unit"].decode()) == "meters"
        assert json.loads(col1_field.metadata[b"type"].decode()) == "integer"

        # Check column2 metadata
        col2_field = result.schema.field("column2")
        assert col2_field.metadata is not None
        assert b"unit" in col2_field.metadata
        assert b"precision" in col2_field.metadata
        assert json.loads(col2_field.metadata[b"unit"].decode()) == "seconds"
        assert json.loads(col2_field.metadata[b"precision"].decode()) == 2

        # Check column3 has no metadata
        col3_field = result.schema.field("column3")
        assert col3_field.metadata is None or len(col3_field.metadata) == 0

    def test_set_metadata_both_table_and_column(self) -> None:
        """Test setting both table and column metadata."""
        table = self.create_sample_table()
        tbl_meta = {"source": "test", "version": 1.0}
        col_meta = {"column1": {"unit": "kg"}}

        result = set_metadata(table, tbl_meta=tbl_meta, col_meta=col_meta)

        # Check table metadata
        assert result.schema.metadata is not None
        assert b"source" in result.schema.metadata
        assert b"version" in result.schema.metadata

        # Check column metadata
        col1_field = result.schema.field("column1")
        assert col1_field.metadata is not None
        assert b"unit" in col1_field.metadata
        assert json.loads(col1_field.metadata[b"unit"].decode()) == "kg"

    def test_set_metadata_none_arguments(self) -> None:
        """Test setting metadata with None arguments."""
        table = self.create_sample_table()

        result = set_metadata(table, tbl_meta=None, col_meta=None)

        # Should return equivalent table
        assert result.schema.equals(table.schema)
        assert result.equals(table)

    def test_set_metadata_empty_dicts(self) -> None:
        """Test setting metadata with empty dictionaries."""
        table = self.create_sample_table()

        result = set_metadata(table, tbl_meta={}, col_meta={})

        # Should return equivalent table (empty metadata is not added)
        assert result.schema.equals(table.schema)
        assert result.equals(table)

    def test_set_metadata_complex_data_types(self) -> None:
        """Test setting metadata with complex data types."""
        table = self.create_sample_table()

        complex_meta = {
            "list_value": [1, 2, 3],
            "dict_value": {"nested": "data"},
            "null_value": None,
            "unicode_value": "café",
        }

        result = set_metadata(table, tbl_meta=complex_meta)

        # Verify complex types are properly JSON serialized
        assert result.schema.metadata is not None

        list_val = json.loads(result.schema.metadata[b"list_value"].decode())
        assert list_val == [1, 2, 3]

        dict_val = json.loads(result.schema.metadata[b"dict_value"].decode())
        assert dict_val == {"nested": "data"}

        null_val = json.loads(result.schema.metadata[b"null_value"].decode())
        assert null_val is None

        unicode_val = json.loads(result.schema.metadata[b"unicode_value"].decode())
        assert unicode_val == "café"

    def test_set_metadata_preserves_data(self) -> None:
        """Test that setting metadata doesn't change the actual data."""
        table = self.create_sample_table()
        original_columns = table.column_names
        original_shape = table.shape

        result = set_metadata(table, tbl_meta={"test": "metadata"})

        # Data structure should be identical
        assert result.column_names == original_columns
        assert result.shape == original_shape

        # Column data should be identical
        for col_name in original_columns:
            original_col = table.column(col_name)
            result_col = result.column(col_name)
            assert original_col.equals(result_col)

        # But schema should have metadata
        assert result.schema.metadata is not None
        assert b"test" in result.schema.metadata
