"""Tests for HFM custom exceptions."""

from __future__ import annotations

import pytest

from pyhfm.exceptions import (
    HFMDataExtractionError,
    HFMError,
    HFMFileError,
    HFMMetadataError,
    HFMParsingError,
    HFMUnsupportedFormatError,
    HFMValidationError,
)


class TestHFMError:
    """Test the base HFMError exception."""

    def test_hfm_error_creation(self) -> None:
        """Test basic HFMError creation."""
        error = HFMError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.file_path is None

    def test_hfm_error_with_file_path(self) -> None:
        """Test HFMError with file path."""
        error = HFMError("Test error", "/path/to/file.tst")
        assert str(error) == "Test error (file: /path/to/file.tst)"
        assert error.message == "Test error"
        assert error.file_path == "/path/to/file.tst"

    def test_hfm_error_inheritance(self) -> None:
        """Test that HFMError inherits from Exception."""
        error = HFMError("Test")
        assert isinstance(error, Exception)

    def test_hfm_error_with_cause(self) -> None:
        """Test HFMError with a cause."""
        cause = ValueError("Original error")
        try:
            raise cause
        except ValueError as e:
            error = HFMError("Wrapper error")
            error.__cause__ = e

        assert str(error) == "Wrapper error"
        assert error.__cause__ is cause


class TestHFMFileError:
    """Test HFMFileError exception."""

    def test_hfm_file_error_basic(self) -> None:
        """Test basic HFMFileError creation."""
        error = HFMFileError("File not found", "/path/to/file.tst", "read")

        assert str(error) == "File not found (operation: read, file: /path/to/file.tst)"
        assert error.file_path == "/path/to/file.tst"
        assert error.operation == "read"

    def test_hfm_file_error_no_operation(self) -> None:
        """Test HFMFileError without operation."""
        error = HFMFileError("File error", "/path/to/file.tst", None)

        assert str(error) == "File error (file: /path/to/file.tst)"
        assert error.file_path == "/path/to/file.tst"
        assert error.operation is None

    def test_hfm_file_error_inheritance(self) -> None:
        """Test HFMFileError inheritance."""
        error = HFMFileError("Test", "file.tst", "read")
        assert isinstance(error, HFMError)
        assert isinstance(error, Exception)

    def test_hfm_file_error_different_operations(self) -> None:
        """Test different file operations."""
        read_error = HFMFileError("Read failed", "file.tst", "read")
        write_error = HFMFileError("Write failed", "file.tst", "write")
        detect_error = HFMFileError("Detect failed", "file.tst", "detect_encoding")

        assert "operation: read" in str(read_error)
        assert "operation: write" in str(write_error)
        assert "operation: detect_encoding" in str(detect_error)


class TestHFMParsingError:
    """Test HFMParsingError exception."""

    def test_hfm_parsing_error_basic(self) -> None:
        """Test basic HFMParsingError creation."""
        error = HFMParsingError("Parse failed", "/path/to/file.tst")

        assert str(error) == "Parse failed (file: /path/to/file.tst)"
        assert error.file_path == "/path/to/file.tst"
        assert error.line_number is None

    def test_hfm_parsing_error_with_line_number(self) -> None:
        """Test HFMParsingError with line number."""
        error = HFMParsingError("Parse failed", "/path/to/file.tst", 42)

        assert str(error) == "Parse failed (file: /path/to/file.tst, line: 42)"
        assert error.file_path == "/path/to/file.tst"
        assert error.line_number == 42

    def test_hfm_parsing_error_no_file(self) -> None:
        """Test HFMParsingError without file path."""
        error = HFMParsingError("Parse failed", None)

        assert str(error) == "Parse failed"
        assert error.file_path is None

    def test_hfm_parsing_error_inheritance(self) -> None:
        """Test HFMParsingError inheritance."""
        error = HFMParsingError("Test", "file.tst")
        assert isinstance(error, HFMError)
        assert isinstance(error, Exception)


class TestHFMUnsupportedFormatError:
    """Test HFMUnsupportedFormatError exception."""

    def test_hfm_unsupported_format_error_basic(self) -> None:
        """Test basic HFMUnsupportedFormatError creation."""
        error = HFMUnsupportedFormatError(
            "Unsupported extension", "/path/to/file.xyz", ".xyz", [".tst", ".dat"]
        )

        expected = (
            "Unsupported extension (detected: .xyz, "
            "supported: .tst, .dat, file: /path/to/file.xyz)"
        )
        assert str(error) == expected
        assert error.file_path == "/path/to/file.xyz"
        assert error.detected_format == ".xyz"
        assert error.supported_formats == [".tst", ".dat"]

    def test_hfm_unsupported_format_error_no_supported(self) -> None:
        """Test HFMUnsupportedFormatError without supported formats."""
        error = HFMUnsupportedFormatError("Bad format", "file.bad", ".bad", None)

        expected = "Bad format (detected: .bad, file: file.bad)"
        assert str(error) == expected
        assert error.supported_formats == []

    def test_hfm_unsupported_format_error_inheritance(self) -> None:
        """Test HFMUnsupportedFormatError inheritance."""
        error = HFMUnsupportedFormatError("Test", "file.bad", ".bad", [])
        assert isinstance(error, HFMError)
        assert isinstance(error, Exception)


class TestHFMDataExtractionError:
    """Test HFMDataExtractionError exception."""

    def test_hfm_data_extraction_error_basic(self) -> None:
        """Test basic HFMDataExtractionError creation."""
        error = HFMDataExtractionError("No data found", measurement_type="conductivity")

        assert str(error) == "No data found (type: conductivity)"
        assert error.measurement_type == "conductivity"
        assert error.setpoint is None

    def test_hfm_data_extraction_error_with_setpoint(self) -> None:
        """Test HFMDataExtractionError with setpoint."""
        error = HFMDataExtractionError(
            "Invalid setpoint", measurement_type="conductivity", setpoint=5
        )

        assert str(error) == "Invalid setpoint (type: conductivity, setpoint: 5)"
        assert error.measurement_type == "conductivity"
        assert error.setpoint == 5

    def test_hfm_data_extraction_error_no_type(self) -> None:
        """Test HFMDataExtractionError without measurement type."""
        error = HFMDataExtractionError("Extraction failed", measurement_type=None)

        assert str(error) == "Extraction failed"
        assert error.measurement_type is None

    def test_hfm_data_extraction_error_inheritance(self) -> None:
        """Test HFMDataExtractionError inheritance."""
        error = HFMDataExtractionError("Test", measurement_type="test")
        assert isinstance(error, HFMError)
        assert isinstance(error, Exception)


class TestHFMValidationError:
    """Test HFMValidationError exception."""

    def test_hfm_validation_error_basic(self) -> None:
        """Test basic HFMValidationError creation."""
        error = HFMValidationError("Invalid value", field_name="temperature")

        assert str(error) == "Invalid value (field: temperature)"
        assert error.field_name == "temperature"
        assert error.invalid_value is None

    def test_hfm_validation_error_with_value(self) -> None:
        """Test HFMValidationError with invalid value."""
        error = HFMValidationError(
            "Value out of range", field_name="temperature", invalid_value=-500.0
        )

        assert str(error) == "Value out of range (field: temperature, value: -500.0)"
        assert error.field_name == "temperature"
        assert error.invalid_value == -500.0

    def test_hfm_validation_error_no_field(self) -> None:
        """Test HFMValidationError without field name."""
        error = HFMValidationError("Validation failed", field_name=None)

        assert str(error) == "Validation failed"
        assert error.field_name is None

    def test_hfm_validation_error_inheritance(self) -> None:
        """Test HFMValidationError inheritance."""
        error = HFMValidationError("Test", field_name="test")
        assert isinstance(error, HFMError)
        assert isinstance(error, Exception)


class TestHFMMetadataError:
    """Test HFMMetadataError exception."""

    def test_hfm_metadata_error_basic(self) -> None:
        """Test basic HFMMetadataError creation."""
        error = HFMMetadataError("Missing metadata")

        assert str(error) == "Missing metadata"
        assert error.missing_fields == []

    def test_hfm_metadata_error_with_missing_fields(self) -> None:
        """Test HFMMetadataError with missing fields."""
        error = HFMMetadataError(
            "Required fields missing", missing_fields=["thickness", "type"]
        )

        expected = "Required fields missing (missing fields: thickness, type)"
        assert str(error) == expected
        assert error.missing_fields == ["thickness", "type"]

    def test_hfm_metadata_error_inheritance(self) -> None:
        """Test HFMMetadataError inheritance."""
        error = HFMMetadataError("Test")
        assert isinstance(error, HFMError)
        assert isinstance(error, Exception)


class TestExceptionChaining:
    """Test exception chaining and context."""

    def test_exception_chaining(self) -> None:
        """Test that exceptions can be chained properly."""
        original = ValueError("Original error")

        try:
            raise original
        except ValueError as e:
            parsing_error = HFMParsingError("Parse failed", "file.tst")
            parsing_error.__cause__ = e

        assert parsing_error.__cause__ is original
        assert str(parsing_error) == "Parse failed (file: file.tst)"

    def test_exception_context(self) -> None:
        """Test exception context without explicit chaining."""

        def create_error() -> HFMFileError:
            msg = "Test error"
            return HFMFileError(msg, "file.tst", "read")

        with pytest.raises(HFMFileError):
            raise create_error()

    def test_nested_hfm_errors(self) -> None:
        """Test nesting HFM errors."""
        inner_error = HFMValidationError("Bad field", field_name="test")
        outer_error = HFMParsingError("Parse failed due to validation", "file.tst")
        outer_error.__cause__ = inner_error

        assert outer_error.__cause__ is inner_error
        assert isinstance(outer_error.__cause__, HFMValidationError)


class TestExceptionMessages:
    """Test exception message formatting."""

    def test_long_file_paths(self) -> None:
        """Test exceptions with very long file paths."""
        long_path = "/very/long/path/to/some/deep/directory/structure/file.tst"
        error = HFMFileError("Error", long_path, "read")

        assert long_path in str(error)
        assert "operation: read" in str(error)

    def test_special_characters_in_paths(self) -> None:
        """Test exceptions with special characters in file paths."""
        special_path = "/path/with spaces/üñíçødé/file.tst"
        error = HFMParsingError("Parse error", special_path)

        assert special_path in str(error)

    def test_empty_messages(self) -> None:
        """Test exceptions with empty or minimal messages."""
        error = HFMError("")
        assert str(error) == ""

        file_error = HFMFileError("", "file.tst", "read")
        assert str(file_error) == " (operation: read, file: file.tst)"

    def test_none_values_in_messages(self) -> None:
        """Test exceptions with None values."""
        error = HFMDataExtractionError("Error", measurement_type=None)
        assert str(error) == "Error"

        validation_error = HFMValidationError("Error", field_name=None)
        assert str(validation_error) == "Error"


class TestExceptionAttributes:
    """Test exception attribute access and modification."""

    def test_file_error_attributes(self) -> None:
        """Test HFMFileError attributes."""
        error = HFMFileError("Message", "/path/file.tst", "write")

        # Test initial attributes
        assert error.file_path == "/path/file.tst"
        assert error.operation == "write"

        # Test attribute modification
        error.file_path = "/new/path.tst"
        error.operation = "delete"

        assert error.file_path == "/new/path.tst"
        assert error.operation == "delete"

    def test_parsing_error_attributes(self) -> None:
        """Test HFMParsingError attributes."""
        error = HFMParsingError("Message", "/path/file.tst", 42)

        assert error.file_path == "/path/file.tst"
        assert error.line_number == 42

        error.file_path = None
        error.line_number = None
        assert error.file_path is None
        assert error.line_number is None

    def test_unsupported_format_error_attributes(self) -> None:
        """Test HFMUnsupportedFormatError attributes."""
        error = HFMUnsupportedFormatError("Message", "file.bad", ".bad", [".good"])

        assert error.file_path == "file.bad"
        assert error.detected_format == ".bad"
        assert error.supported_formats == [".good"]

    def test_data_extraction_error_attributes(self) -> None:
        """Test HFMDataExtractionError attributes."""
        error = HFMDataExtractionError(
            "Message", measurement_type="conductivity", setpoint=1
        )

        assert error.measurement_type == "conductivity"
        assert error.setpoint == 1

        error.measurement_type = "heat_capacity"
        error.setpoint = 2
        assert error.measurement_type == "heat_capacity"
        assert error.setpoint == 2

    def test_validation_error_attributes(self) -> None:
        """Test HFMValidationError attributes."""
        error = HFMValidationError(
            "Message", field_name="temperature", invalid_value=100.0
        )

        assert error.field_name == "temperature"
        assert error.invalid_value == 100.0

        error.field_name = "thickness"
        error.invalid_value = "bad_value"
        assert error.field_name == "thickness"
        assert error.invalid_value == "bad_value"

    def test_metadata_error_attributes(self) -> None:
        """Test HFMMetadataError attributes."""
        error = HFMMetadataError("Message", missing_fields=["field1", "field2"])

        assert error.missing_fields == ["field1", "field2"]

        error.missing_fields = ["field3"]
        assert error.missing_fields == ["field3"]
