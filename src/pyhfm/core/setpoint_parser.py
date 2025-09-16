"""Setpoint parsing functionality for HFM files."""

from __future__ import annotations

import re
from datetime import datetime as dt
from datetime import timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyhfm.constants import HFMParsingConfig


class SetpointParser:
    """Handles setpoint-specific parsing from HFM files."""

    def __init__(self, config: HFMParsingConfig) -> None:
        """Initialize setpoint parser.

        Args:
            config: Parsing configuration
        """
        self.config = config

    def parse_setpoints_header(
        self,
        line: str,
        _lines: list[str],
        _i: int,
        metadata: dict[str, Any],
        _measurement_type: str,
    ) -> None:
        """Parse setpoints header and initialize setpoint structures."""
        metadata["number_of_setpoints"] = int(line.split(":", 1)[1].strip())
        # Initialize empty setpoints dict - setpoints will be added when actual data is found
        if "setpoints" not in metadata:
            metadata["setpoints"] = {}

    def parse_setpoint_data(
        self, line: str, lines: list[str], i: int, metadata: dict[str, Any]
    ) -> None:
        """Parse detailed setpoint data."""
        setpoint = int(line.split(".")[1].strip())
        setpoint_key = f"setpoint_{setpoint}"

        # Ensure setpoint structure exists
        if setpoint_key not in metadata["setpoints"]:
            metadata["setpoints"][setpoint_key] = {}

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

    def parse_block_averages_setpoint(
        self, line: str, lines: list[str], i: int, metadata: dict[str, Any]
    ) -> None:
        """Parse setpoint data from Block Averages format (specific heat files)."""
        # Extract setpoint number using pre-compiled pattern
        setpoint_match = self.config.patterns.setpoint_pattern.search(line)
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
        """Parse setpoint temperature data using pre-compiled patterns."""
        line_data = sub_line.split(":", 1)[1].strip()
        value_match = self.config.patterns.value_pattern.search(line_data)
        unit_match = self.config.patterns.unicode_unit_pattern.search(line_data)

        if not value_match or not unit_match:
            return

        if "setpoint_temperature" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["setpoint_temperature"] = {}

        metadata["setpoints"][setpoint_key]["setpoint_temperature"][position] = {
            "value": float(value_match.group()),
            "unit": unit_match.group(),
        }

    def _parse_temperature(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any], position: str
    ) -> None:
        """Parse temperature data using pre-compiled patterns."""
        line_data = sub_line.split(":", 1)[1].strip()
        value_match = self.config.patterns.value_pattern.search(line_data)
        unit_match = self.config.patterns.unicode_unit_pattern.search(line_data)

        if not value_match or not unit_match:
            return

        if "temperature" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["temperature"] = {}

        metadata["setpoints"][setpoint_key]["temperature"][position] = {
            "value": float(value_match.group()),
            "unit": unit_match.group(),
        }

    def _parse_results(
        self, sub_line: str, setpoint_key: str, metadata: dict[str, Any], position: str
    ) -> None:
        """Parse results data using pre-compiled patterns."""
        line_data = sub_line.split(":", 1)[1].strip()
        value_match = self.config.patterns.value_pattern.search(line_data)
        unit_match = self.config.patterns.unit_ratio_pattern.search(line_data)

        if not value_match or not unit_match:
            return

        if "results" not in metadata["setpoints"][setpoint_key]:
            metadata["setpoints"][setpoint_key]["results"] = {}

        metadata["setpoints"][setpoint_key]["results"][position] = {
            "value": float(value_match.group()),
            "unit": unit_match.group(),
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
        """Parse temperature average data using pre-compiled patterns."""
        line_data = sub_line.split(":", 1)[1].strip()
        value_match = self.config.patterns.value_pattern.search(line_data)
        unit_match = self.config.patterns.unicode_unit_pattern.search(line_data)

        if not value_match or not unit_match:
            return

        metadata["setpoints"][setpoint_key]["temperature_average"] = {
            "value": float(value_match.group()),
            "unit": unit_match.group(),
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
