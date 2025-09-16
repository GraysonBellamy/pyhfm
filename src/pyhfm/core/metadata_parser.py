"""Metadata extraction functionality for HFM files."""

from __future__ import annotations

from datetime import datetime as dt
from datetime import timezone
from typing import TYPE_CHECKING, Any

from pyhfm.constants import HFMType
from pyhfm.exceptions import HFMParsingError

if TYPE_CHECKING:
    from pyhfm.constants import HFMParsingConfig


class MetadataParser:
    """Handles metadata extraction from HFM files."""

    def __init__(self, config: HFMParsingConfig) -> None:
        """Initialize metadata parser.

        Args:
            config: Parsing configuration
        """
        self.config = config
        # Pre-build expensive lookup structures for fast parsing
        self._line_handlers = self._build_line_handlers()

    def _build_line_handlers(self) -> dict[str, str]:
        """Pre-build handler mapping for fast line processing."""
        return {
            "Sample Name: ": "sample_name",
            "Thickness: ": "thickness",
            "Rear Left :": "rear_thickness",
            "Front Left:": "front_thickness",
            "Thickness obtained": "thickness_source",
            "Calibration used": "calibration_type",
            "Calibration File Id": "calibration_file",
            "Number of transducer per plate": "transducers",
            "Transducer Heat Capacity Coefficients": "calibration_coefficients",
        }

    def extract_basic_metadata(self, lines: list[str], metadata: dict[str, Any]) -> str:
        """Extract basic metadata from file lines.

        Args:
            lines: File lines to process
            metadata: Dictionary to populate with metadata

        Returns:
            Measurement type string
        """
        measurement_type = HFMType.CONDUCTIVITY.value  # Default assumption

        # Parse each line for metadata
        for i, raw_line in enumerate(lines):
            line = raw_line.strip()
            measurement_type = self._process_metadata_line(
                line, lines, i, metadata, measurement_type
            )

        return measurement_type

    def _process_metadata_line(
        self,
        line: str,
        _lines: list[str],
        _i: int,
        metadata: dict[str, Any],
        measurement_type: str,
    ) -> str:
        """Process a single metadata line and return updated measurement type."""
        # Handle date parsing (special case - no prefix matching)
        if "date_performed" not in metadata:
            date_performed = self._parse_date(line)
            if date_performed:
                metadata["date_performed"] = date_performed

        # Handle special patterns that need extra parameters
        if line.startswith("Run Mode"):
            return self._parse_run_mode(line)

        # Handle simple prefix-based parsing
        self._process_simple_metadata_line(line, metadata)
        return measurement_type

    def _process_simple_metadata_line(
        self, line: str, metadata: dict[str, Any]
    ) -> None:
        """Process simple metadata lines with optimized prefix matching."""
        # Check comment line first (most common case)
        if self._is_comment_line(line):
            self._parse_comment(line, metadata)
            return

        # Fast prefix categorization using pre-built handlers
        for prefix, handler_type in self._line_handlers.items():
            if line.startswith(prefix):
                self._dispatch_handler(handler_type, line, metadata)
                return

    def _dispatch_handler(
        self, handler_type: str, line: str, metadata: dict[str, Any]
    ) -> None:
        """Dispatch to appropriate handler based on type."""
        if handler_type == "sample_name":
            metadata["sample_id"] = line.split(":", 1)[1].strip()
        elif handler_type == "calibration_coefficients":
            self._parse_calibration_coefficients(line, metadata)
        elif handler_type == "thickness":
            self._parse_thickness(line, metadata)
        elif handler_type == "rear_thickness":
            self._parse_rear_thickness(line, metadata)
        elif handler_type == "front_thickness":
            self._parse_front_thickness(line, metadata)
        elif handler_type == "thickness_source":
            self._parse_thickness_source(line, metadata)
        elif handler_type == "calibration_type":
            self._parse_calibration_type(line, metadata)
        elif handler_type == "calibration_file":
            self._parse_calibration_file(line, metadata)
        elif handler_type == "transducers":
            metadata["number_of_transducers"] = int(line.split(":", 1)[1].strip())

    def _parse_run_mode(self, line: str) -> str:
        """Parse run mode and return measurement type."""
        raw_type = line.split(":", 1)[1].strip().lower().replace(" ", "_")
        if raw_type == "specific_heat":
            return HFMType.VOLUMETRIC_HEAT_CAPACITY.value
        if raw_type == "thermal_conductivity":
            return HFMType.CONDUCTIVITY.value
        return raw_type

    def _parse_date(self, line: str) -> str | None:
        """Parse date from a line."""
        try:
            # Parse datetime and immediately make it timezone-aware
            datetime = dt.strptime(line.strip(), self.config.date_format).replace(
                tzinfo=timezone.utc
            )
            return datetime.isoformat()
        except ValueError:
            return None

    def _extract_value_and_unit(self, sub_line: str) -> dict[str, float | str]:
        """Extract value and unit from a line using pre-compiled patterns."""
        value_match = self.config.patterns.value_pattern.search(sub_line)
        if not value_match:
            msg = f"No numeric value found in: {sub_line}"
            raise HFMParsingError(msg)

        unit_match = self.config.patterns.unit_pattern.search(sub_line)
        if not unit_match:
            msg = f"No unit found in: {sub_line}"
            raise HFMParsingError(msg)

        return {"value": float(value_match.group()), "unit": unit_match.group()}

    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a comment."""
        return (
            line.startswith("[")
            and line.endswith("]")
            and not any(c in line[1:-1] for c in ["[", "]"])
        )

    def _parse_calibration_coefficients(
        self, line: str, metadata: dict[str, Any]
    ) -> None:
        """Parse calibration coefficients from line."""
        if "calibration" not in metadata:
            metadata["calibration"] = {}

        coefficients = self.config.patterns.value_pattern.findall(
            line.split(":", 1)[1].strip()
        )
        if len(coefficients) >= 2:
            metadata["calibration"]["heat_capacity_coefficients"] = {
                "A": float(coefficients[0]),
                "B": float(coefficients[1]),
            }

    def _parse_thickness(self, line: str, metadata: dict[str, Any]) -> None:
        """Parse thickness from line."""
        metadata["thickness"] = self._extract_value_and_unit(
            line.split(":", 1)[1].strip()
        )

    def _parse_rear_thickness(self, line: str, metadata: dict[str, Any]) -> None:
        """Parse rear thickness measurements."""
        if "thickness" not in metadata:
            metadata["thickness"] = {}

        parts = line.split(":")
        if len(parts) >= 3:
            metadata["thickness"]["rear_left"] = self._extract_value_and_unit(
                parts[1].strip()
            )
            metadata["thickness"]["rear_right"] = self._extract_value_and_unit(
                parts[2].strip()
            )

    def _parse_front_thickness(self, line: str, metadata: dict[str, Any]) -> None:
        """Parse front thickness measurements."""
        if "thickness" not in metadata:
            metadata["thickness"] = {}

        parts = line.split(":")
        if len(parts) >= 3:
            metadata["thickness"]["front_left"] = self._extract_value_and_unit(
                parts[1].strip()
            )
            metadata["thickness"]["front_right"] = self._extract_value_and_unit(
                parts[2].strip()
            )

    def _parse_comment(self, line: str, metadata: dict[str, Any]) -> None:
        """Parse comment from line."""
        comment = line.strip("[]").strip()
        if "comment" not in metadata:
            metadata["comment"] = comment
        elif isinstance(metadata["comment"], str):
            metadata["comment"] = [metadata["comment"], comment]
        else:
            metadata["comment"].append(comment)

    def _parse_thickness_source(self, line: str, metadata: dict[str, Any]) -> None:
        """Parse thickness source information."""
        if "thickness" not in metadata:
            metadata["thickness"] = {}
        metadata["thickness"]["obtained"] = line.split(":", 1)[1].strip("from ")

    def _parse_calibration_type(self, line: str, metadata: dict[str, Any]) -> None:
        """Parse calibration type."""
        if "calibration" not in metadata:
            metadata["calibration"] = {}
        metadata["calibration"]["type"] = line.split(":", 1)[1].strip()

    def _parse_calibration_file(self, line: str, metadata: dict[str, Any]) -> None:
        """Parse calibration file."""
        if "calibration" not in metadata:
            metadata["calibration"] = {}
        metadata["calibration"]["file"] = line.split(":", 1)[1].strip()
