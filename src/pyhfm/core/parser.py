"""Core HFM file parser functionality."""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime as dt
from datetime import timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pyhfm.constants import (
    DEFAULT_PARSING_CONFIG,
    FileMetadata,
    HFMType,
)
from pyhfm.exceptions import (
    HFMFileError,
    HFMParsingError,
    HFMUnsupportedFormatError,
)
from pyhfm.extractors.data_extractor import DataExtractor
from pyhfm.utils import detect_encoding, get_hash, set_metadata

if TYPE_CHECKING:
    import pyarrow as pa


class HFMParser:
    """Main parser for HFM data files."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize HFM parser.

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
        measurement_type = HFMType.CONDUCTIVITY.value  # Default assumption
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
            # Parse each line for metadata
            for i, raw_line in enumerate(lines):
                line = raw_line.strip()
                measurement_type = self._process_metadata_line(
                    line, lines, i, metadata, measurement_type
                )

        except Exception as e:
            if isinstance(e, HFMParsingError):
                raise
            msg = f"Failed to parse metadata: {e}"
            raise HFMParsingError(
                msg,
                str(path),
                i + 1 if "i" in locals() else None,
            ) from e

        # Add final metadata
        metadata["type"] = measurement_type
        metadata["file_hash"] = {
            "file": path.name,
            "method": "BLAKE2b",
            "hash": file_hash,
        }

        return metadata  # type: ignore[return-value]

    def _process_metadata_line(
        self,
        line: str,
        lines: list[str],
        i: int,
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
        if "Block Averages for setpoint" in line:
            self._parse_block_averages_setpoint(line, lines, i, metadata)
            return measurement_type
        if line.startswith("Number of Setpoints"):
            self._parse_setpoints_header(line, lines, i, metadata, measurement_type)
            return measurement_type
        if line.startswith("Setpoint No."):
            self._parse_setpoint_data(line, lines, i, metadata)
            return measurement_type

        # Handle simple prefix-based parsing
        self._process_simple_metadata_line(line, metadata)
        return measurement_type

    def _process_simple_metadata_line(
        self, line: str, metadata: dict[str, Any]
    ) -> None:
        """Process simple metadata lines with prefix matching."""
        simple_parsers = {
            "Sample Name: ": lambda: metadata.update(
                {"sample_id": line.split(":", 1)[1].strip()}
            ),
            "Transducer Heat Capacity Coefficients": lambda: self._parse_calibration_coefficients(
                line, metadata
            ),
            "Thickness: ": lambda: self._parse_thickness(line, metadata),
            "Rear Left :": lambda: self._parse_rear_thickness(line, metadata),
            "Front Left:": lambda: self._parse_front_thickness(line, metadata),
            "Thickness obtained": lambda: self._parse_thickness_source(line, metadata),
            "Calibration used": lambda: self._parse_calibration_type(line, metadata),
            "Calibration File Id": lambda: self._parse_calibration_file(line, metadata),
            "Number of transducer per plate": lambda: metadata.update(
                {"number_of_transducers": int(line.split(":", 1)[1].strip())}
            ),
        }

        # Check comment line (special pattern check)
        if self._is_comment_line(line):
            self._parse_comment(line, metadata)
            return

        # Check simple prefix matches
        for prefix, parser_func in simple_parsers.items():
            if line.startswith(prefix):
                parser_func()
                break

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
        """Extract value and unit from a line."""
        value_match = re.findall(self.config.value_pattern, sub_line)
        if not value_match:
            msg = f"No numeric value found in: {sub_line}"
            raise HFMParsingError(msg)

        unit_match = re.findall(self.config.unit_pattern, sub_line)
        if not unit_match:
            msg = f"No unit found in: {sub_line}"
            raise HFMParsingError(msg)

        return {"value": float(value_match[0]), "unit": unit_match[0]}

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

        coefficients = re.findall(
            self.config.value_pattern, line.split(":", 1)[1].strip()
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

    def _parse_setpoints_header(
        self,
        line: str,
        _lines: list[str],
        _i: int,
        metadata: dict[str, Any],
        _measurement_type: str,
    ) -> None:
        """Parse setpoints header and initialize setpoint structures."""
        metadata["number_of_setpoints"] = int(line.split(":", 1)[1].strip())
        metadata["setpoints"] = {}

        # Initialize setpoint structures based on the number of setpoints
        for setpoint_num in range(1, metadata["number_of_setpoints"] + 1):
            metadata["setpoints"][f"setpoint_{setpoint_num}"] = {}

    def _parse_setpoint_data(
        self, line: str, lines: list[str], i: int, metadata: dict[str, Any]
    ) -> None:
        """Parse detailed setpoint data."""
        setpoint = int(line.split(".")[1].strip())
        setpoint_key = f"setpoint_{setpoint}"

        # Parse date for this setpoint
        if i >= 2:
            date_performed = self._parse_date(lines[i - 2])
            if date_performed:
                metadata["setpoints"][setpoint_key]["date_performed"] = date_performed

        # Parse the following lines for setpoint details
        for j in range(1, min(19, len(lines) - i)):
            if i + j >= len(lines):
                break

            sub_line = lines[i + j].strip()
            self._parse_setpoint_detail(sub_line, lines, i + j, setpoint_key, metadata)

    def _parse_setpoint_detail(
        self,
        sub_line: str,
        _lines: list[str],
        _line_idx: int,
        setpoint_key: str,
        metadata: dict[str, Any],
    ) -> None:
        """Parse individual setpoint detail lines."""
        # Define parsing dispatch table
        parsing_dispatch = {
            "Setpoint Upper:": lambda: self._parse_setpoint_temperature(
                sub_line, setpoint_key, metadata, "upper"
            ),
            "Setpoint Lower:": lambda: self._parse_setpoint_temperature(
                sub_line, setpoint_key, metadata, "lower"
            ),
            "Temperature Upper": lambda: self._parse_temperature(
                sub_line, setpoint_key, metadata, "upper"
            ),
            "Temperature Lower": lambda: self._parse_temperature(
                sub_line, setpoint_key, metadata, "lower"
            ),
            "CalibFactor  Upper": lambda: self._parse_calibration_factor(
                sub_line, setpoint_key, metadata, "upper"
            ),
            "CalibFactor  Lower": lambda: self._parse_calibration_factor(
                sub_line, setpoint_key, metadata, "lower"
            ),
            "Results Upper": lambda: self._parse_results(
                sub_line, setpoint_key, metadata, "upper"
            ),
            "Results Lower": lambda: self._parse_results(
                sub_line, setpoint_key, metadata, "lower"
            ),
            "Temperature Equilibrium": lambda: self._parse_temperature_equilibrium(
                sub_line, setpoint_key, metadata
            ),
            "Between Block HFM Equal.": lambda: self._parse_between_block_equilibrium(
                sub_line, setpoint_key, metadata
            ),
            "HFM Percent Change": lambda: self._parse_percent_change(
                sub_line, setpoint_key, metadata
            ),
            "Min Number of Blocks": lambda: self._parse_min_blocks(
                sub_line, setpoint_key, metadata
            ),
            "Calculation Blocks": lambda: self._parse_calculation_blocks(
                sub_line, setpoint_key, metadata
            ),
            "Temperature Average": lambda: self._parse_temperature_average(
                sub_line, setpoint_key, metadata
            ),
            "Specific Heat": lambda: self._parse_specific_heat(
                sub_line, setpoint_key, metadata
            ),
        }

        # Find matching parser
        for prefix, parser_func in parsing_dispatch.items():
            if sub_line.startswith(prefix):
                parser_func()
                break

    def _parse_setpoint_temperature(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any], position: str
    ) -> None:
        """Parse setpoint temperature data."""
        value_match = re.findall(
            self.config.value_pattern, sub_line.split(":", 1)[1].strip()
        )
        unit_match = re.findall(
            self.config.unicode_unit_pattern, sub_line.split(":", 1)[1].strip()
        )

        if not value_match or not unit_match:
            return

        if "setpoint_temperature" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["setpoint_temperature"] = {}

        metadata["setpoints"][setpoint_key]["setpoint_temperature"][position] = {
            "value": float(value_match[0]),
            "unit": unit_match[0],
        }

    def _parse_temperature(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any], position: str
    ) -> None:
        """Parse temperature data."""
        value_match = re.findall(
            self.config.value_pattern, sub_line.split(":", 1)[1].strip()
        )
        unit_match = re.findall(
            self.config.unicode_unit_pattern, sub_line.split(":", 1)[1].strip()
        )

        if not value_match or not unit_match:
            return

        if "temperature" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["temperature"] = {}

        metadata["setpoints"][setpoint_key]["temperature"][position] = {
            "value": float(value_match[0]),
            "unit": unit_match[0],
        }

    def _parse_results(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any], position: str
    ) -> None:
        """Parse results data."""
        value_match = re.findall(
            self.config.value_pattern, sub_line.split(":", 1)[1].strip()
        )
        unit_match = re.findall(
            self.config.unit_ratio_pattern, sub_line.split(":", 1)[1].strip()
        )

        if not value_match or not unit_match:
            return

        if "results" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["results"] = {}

        metadata["setpoints"][setpoint_key]["results"][position] = {
            "value": float(value_match[0]),
            "unit": unit_match[0],
        }

    def _parse_calibration_factor(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any], position: str
    ) -> None:
        """Parse calibration factor data."""
        if "calibration" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["calibration"] = {}

        unit = self.config.default_calibration_unit
        value = float(sub_line.split(":", 1)[1].strip())
        metadata["setpoints"][setpoint_key]["calibration"][position] = {
            "value": value,
            "unit": unit,
        }

    def _parse_temperature_equilibrium(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any]
    ) -> None:
        """Parse temperature equilibrium data."""
        if "thermal_equilibrium" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["thermal_equilibrium"] = {}

        metadata["setpoints"][setpoint_key]["thermal_equilibrium"]["temperature"] = (
            float(sub_line.split(":", 1)[1].strip())
        )

    def _parse_between_block_equilibrium(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any]
    ) -> None:
        """Parse between block equilibrium data."""
        if "thermal_equilibrium" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["thermal_equilibrium"] = {}

        metadata["setpoints"][setpoint_key]["thermal_equilibrium"]["between_block"] = (
            float(sub_line.split(":", 1)[1].strip())
        )

    def _parse_percent_change(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any]
    ) -> None:
        """Parse HFM percent change data."""
        if "thermal_equilibrium" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["thermal_equilibrium"] = {}

        metadata["setpoints"][setpoint_key]["thermal_equilibrium"]["percent_change"] = (
            float(sub_line.split(":", 1)[1].strip())
        )

    def _parse_min_blocks(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any]
    ) -> None:
        """Parse minimum number of blocks data."""
        if "thermal_equilibrium" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["thermal_equilibrium"] = {}

        metadata["setpoints"][setpoint_key]["thermal_equilibrium"][
            "min_number_of_blocks"
        ] = float(sub_line.split(":", 1)[1].strip())

    def _parse_calculation_blocks(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any]
    ) -> None:
        """Parse calculation blocks data."""
        if "thermal_equilibrium" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["thermal_equilibrium"] = {}

        metadata["setpoints"][setpoint_key]["thermal_equilibrium"][
            "calculation_blocks"
        ] = float(sub_line.split(":", 1)[1].strip())

    def _parse_temperature_average(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any]
    ) -> None:
        """Parse temperature average data."""
        value_match = re.findall(
            self.config.value_pattern, sub_line.split(":", 1)[1].strip()
        )
        unit_match = re.findall(
            self.config.unicode_unit_pattern, sub_line.split(":", 1)[1].strip()
        )

        if not value_match or not unit_match:
            return

        metadata["setpoints"][setpoint_key]["temperature_average"] = {
            "value": float(value_match[0]),
            "unit": unit_match[0],
        }

    def _parse_specific_heat(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any]
    ) -> None:
        """Parse specific heat (volumetric heat capacity) data."""
        sub_line_data = sub_line.split(":", 1)[1].strip()
        value_match = re.findall(r"\d+", sub_line_data)

        if not value_match:
            return

        value = value_match[0]
        unit = sub_line_data.replace(value, "").strip()

        metadata["setpoints"][setpoint_key]["volumetric_heat_capacity"] = {
            "value": float(value),
            "unit": unit,
        }

    def _parse_block_averages_setpoint(
        self, line: str, lines: list[str], i: int, metadata: dict[str, Any]
    ) -> None:
        """Parse setpoint data from Block Averages format (specific heat files)."""
        # Extract setpoint number from "Block Averages for setpoint X in SI units"
        setpoint_match = re.search(r"setpoint\s+(\d+)", line)
        if not setpoint_match:
            return

        setpoint_num = int(setpoint_match.group(1))
        setpoint_key = f"setpoint_{setpoint_num}"

        # Ensure setpoint exists in metadata
        if "setpoints" not in metadata:
            metadata["setpoints"] = {}
        if setpoint_key not in metadata["setpoints"]:
            metadata["setpoints"][setpoint_key] = {}

        # Look forward to find Temperature Average and Specific Heat
        for j in range(i + 1, min(i + 50, len(lines))):
            if j >= len(lines):
                break

            line_content = lines[j].strip()

            if line_content.startswith("Temperature Average:"):
                parts = line_content.split()
                if len(parts) >= 3:
                    try:
                        temp_value = float(parts[2])
                        temp_unit = parts[3] if len(parts) > 3 else "°C"
                        metadata["setpoints"][setpoint_key]["temperature_average"] = {
                            "value": temp_value,
                            "unit": temp_unit,
                        }
                    except (ValueError, IndexError):
                        pass

            elif line_content.startswith("Specific Heat"):
                parts = line_content.split()
                if len(parts) >= 3:
                    try:
                        heat_value = float(parts[3])
                        heat_unit = parts[4] if len(parts) > 4 else "J/(m³K)"
                        metadata["setpoints"][setpoint_key][
                            "volumetric_heat_capacity"
                        ] = {"value": heat_value, "unit": heat_unit}
                    except (ValueError, IndexError):
                        pass

            # Stop if we hit another setpoint section
            elif "Block Averages for setpoint" in line_content:
                break

    def _extract_data(self, metadata: FileMetadata) -> pa.Table:
        """Extract data from metadata and create PyArrow table.

        Args:
            metadata: Extracted metadata dictionary

        Returns:
            PyArrow table with measurement data
        """
        extractor = DataExtractor()
        return extractor.extract_data(metadata)
