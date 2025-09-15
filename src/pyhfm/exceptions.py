"""Custom exceptions for HFM data processing."""

from __future__ import annotations


class HFMError(Exception):
    """Base exception for all HFM-related errors."""

    def __init__(self, message: str, file_path: str | None = None) -> None:
        """Initialize HFM error.

        Args:
            message: Error description
            file_path: Optional path to file that caused the error
        """
        self.message = message
        self.file_path = file_path
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with optional file path."""
        if self.file_path:
            return f"{self.message} (file: {self.file_path})"
        return self.message


class HFMParsingError(HFMError):
    """Raised when HFM file parsing fails."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        line_number: int | None = None,
    ) -> None:
        """Initialize parsing error.

        Args:
            message: Error description
            file_path: Optional path to file that caused the error
            line_number: Optional line number where error occurred
        """
        self.line_number = line_number
        super().__init__(message, file_path)

    def _format_message(self) -> str:
        """Format error message with optional file path and line number."""
        parts = [self.message]
        if self.file_path:
            parts.append(f"file: {self.file_path}")
        if self.line_number is not None:
            parts.append(f"line: {self.line_number}")

        if len(parts) > 1:
            return f"{parts[0]} ({', '.join(parts[1:])})"
        return parts[0]


class HFMValidationError(HFMError):
    """Raised when HFM data validation fails."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        field_name: str | None = None,
        invalid_value: str | float | int | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error description
            file_path: Optional path to file that caused the error
            field_name: Optional name of the invalid field
            invalid_value: Optional invalid value that caused the error
        """
        self.field_name = field_name
        self.invalid_value = invalid_value
        super().__init__(message, file_path)

    def _format_message(self) -> str:
        """Format error message with optional details."""
        parts = [self.message]
        if self.field_name:
            parts.append(f"field: {self.field_name}")
        if self.invalid_value is not None:
            parts.append(f"value: {self.invalid_value}")
        if self.file_path:
            parts.append(f"file: {self.file_path}")

        if len(parts) > 1:
            return f"{parts[0]} ({', '.join(parts[1:])})"
        return parts[0]


class HFMMetadataError(HFMError):
    """Raised when metadata extraction fails."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        missing_fields: list[str] | None = None,
    ) -> None:
        """Initialize metadata error.

        Args:
            message: Error description
            file_path: Optional path to file that caused the error
            missing_fields: Optional list of missing required fields
        """
        self.missing_fields = missing_fields or []
        super().__init__(message, file_path)

    def _format_message(self) -> str:
        """Format error message with missing fields."""
        parts = [self.message]
        if self.missing_fields:
            parts.append(f"missing fields: {', '.join(self.missing_fields)}")
        if self.file_path:
            parts.append(f"file: {self.file_path}")

        if len(parts) > 1:
            return f"{parts[0]} ({', '.join(parts[1:])})"
        return parts[0]


class HFMDataExtractionError(HFMError):
    """Raised when data extraction from metadata fails."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        measurement_type: str | None = None,
        setpoint: int | None = None,
    ) -> None:
        """Initialize data extraction error.

        Args:
            message: Error description
            file_path: Optional path to file that caused the error
            measurement_type: Optional measurement type (conductivity, heat_capacity)
            setpoint: Optional setpoint number that caused the error
        """
        self.measurement_type = measurement_type
        self.setpoint = setpoint
        super().__init__(message, file_path)

    def _format_message(self) -> str:
        """Format error message with extraction details."""
        parts = [self.message]
        if self.measurement_type:
            parts.append(f"type: {self.measurement_type}")
        if self.setpoint is not None:
            parts.append(f"setpoint: {self.setpoint}")
        if self.file_path:
            parts.append(f"file: {self.file_path}")

        if len(parts) > 1:
            return f"{parts[0]} ({', '.join(parts[1:])})"
        return parts[0]


class HFMFileError(HFMError):
    """Raised when file operations fail."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
    ) -> None:
        """Initialize file error.

        Args:
            message: Error description
            file_path: Optional path to file that caused the error
            operation: Optional operation that failed (read, write, detect_encoding)
        """
        self.operation = operation
        super().__init__(message, file_path)

    def _format_message(self) -> str:
        """Format error message with operation details."""
        parts = [self.message]
        if self.operation:
            parts.append(f"operation: {self.operation}")
        if self.file_path:
            parts.append(f"file: {self.file_path}")

        if len(parts) > 1:
            return f"{parts[0]} ({', '.join(parts[1:])})"
        return parts[0]


class HFMUnsupportedFormatError(HFMError):
    """Raised when file format is not supported."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        detected_format: str | None = None,
        supported_formats: list[str] | None = None,
    ) -> None:
        """Initialize unsupported format error.

        Args:
            message: Error description
            file_path: Optional path to file that caused the error
            detected_format: Optional detected file format
            supported_formats: Optional list of supported formats
        """
        self.detected_format = detected_format
        self.supported_formats = supported_formats or []
        super().__init__(message, file_path)

    def _format_message(self) -> str:
        """Format error message with format details."""
        parts = [self.message]
        if self.detected_format:
            parts.append(f"detected: {self.detected_format}")
        if self.supported_formats:
            parts.append(f"supported: {', '.join(self.supported_formats)}")
        if self.file_path:
            parts.append(f"file: {self.file_path}")

        if len(parts) > 1:
            return f"{parts[0]} ({', '.join(parts[1:])})"
        return parts[0]
