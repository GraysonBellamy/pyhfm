"""Data extraction from HFM metadata."""

from __future__ import annotations

from typing import Any

import numpy as np
import pyarrow as pa

from pyhfm.constants import DEFAULT_COLUMN_CONFIG, FileMetadata, HFMType
from pyhfm.exceptions import HFMDataExtractionError
from pyhfm.utils import set_metadata


class DataExtractor:
    """Extracts tabular data from HFM metadata."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize data extractor.

        Args:
            config: Optional configuration overrides
        """
        self.config = DEFAULT_COLUMN_CONFIG
        if config:
            # Apply configuration overrides
            for key, value in config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

    def extract_data(self, metadata: FileMetadata) -> pa.Table:
        """Extract data from metadata and return PyArrow table.

        Args:
            metadata: HFM metadata dictionary

        Returns:
            PyArrow table with measurement data

        Raises:
            HFMDataExtractionError: If data extraction fails
        """
        measurement_type = metadata.get("type")
        if not measurement_type:
            error_msg = "Missing measurement type in metadata"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=measurement_type,
            )

        try:
            if measurement_type == HFMType.CONDUCTIVITY.value:
                return self._extract_conductivity_data(metadata)
            if measurement_type == HFMType.VOLUMETRIC_HEAT_CAPACITY.value:
                return self._extract_heat_capacity_data(metadata)

            # Handle unsupported measurement type
            self._raise_unsupported_type_error(measurement_type)
        except Exception as e:
            if isinstance(e, HFMDataExtractionError):
                raise
            error_msg = f"Failed to extract data: {e}"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=measurement_type,
            ) from e

    def _raise_unsupported_type_error(self, measurement_type: str) -> None:
        """Raise error for unsupported measurement type."""
        error_msg = f"Unsupported measurement type: {measurement_type}"
        raise HFMDataExtractionError(
            error_msg,
            measurement_type=measurement_type,
        )

    def _extract_conductivity_data(self, metadata: FileMetadata) -> pa.Table:
        """Extract thermal conductivity data."""
        if "setpoints" not in metadata:
            error_msg = "No setpoints found in metadata"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.CONDUCTIVITY.value,
            )

        data = []
        units = []
        col_units = {}

        try:
            # Create schema
            schema = pa.schema(
                [
                    pa.field("setpoint", pa.int32()),
                    pa.field("upper_temperature", pa.float64()),
                    pa.field("lower_temperature", pa.float64()),
                    pa.field("upper_thermal_conductivity", pa.float64()),
                    pa.field("lower_thermal_conductivity", pa.float64()),
                ]
            )

            # Extract data from setpoints
            for key, value in metadata["setpoints"].items():
                try:
                    setpoint = int(key.split("_")[1])

                    # Extract and validate conductivity data
                    conductivity_data = self._extract_conductivity_setpoint(value)
                    if conductivity_data is None:
                        continue

                    data.append([setpoint, *conductivity_data["values"]])
                    units = conductivity_data["units"]

                except (KeyError, ValueError, TypeError) as e:
                    error_msg = f"Missing or invalid data in setpoint {key}: {e}"
                    raise HFMDataExtractionError(
                        error_msg,
                        measurement_type=HFMType.CONDUCTIVITY.value,
                        setpoint=setpoint if "setpoint" in locals() else None,
                    ) from e

            # Set column units
            if units:
                col_units = {
                    "upper_temperature": {"units": units[0]},
                    "lower_temperature": {"units": units[1]},
                    "upper_thermal_conductivity": {"units": units[2]},
                    "lower_thermal_conductivity": {"units": units[3]},
                }

        except Exception as e:
            if isinstance(e, HFMDataExtractionError):
                raise
            error_msg = f"Failed to process conductivity data: {e}"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.CONDUCTIVITY.value,
            ) from e

        return self._create_table(data, schema, col_units)

    def _extract_conductivity_setpoint(self, value: Any) -> dict[str, Any] | None:
        """Extract conductivity data from a single setpoint."""
        # Validate input and extract base structures
        temp_data, results_data = self._validate_and_extract_base_data(value)
        if temp_data is None or results_data is None:
            return None

        # Extract temperature data
        temp_values = self._extract_temperature_data(temp_data)
        if temp_values is None:
            return None

        # Extract conductivity data
        cond_values = self._extract_conductivity_results(results_data)
        if cond_values is None:
            return None

        # Combine and validate all values
        all_values = [*temp_values["values"], *cond_values["values"]]
        all_units = [*temp_values["units"], *cond_values["units"]]

        # Final validation
        if any(x is None for x in all_values) or not all(
            isinstance(x, (int, float)) for x in all_values
        ):
            return None

        return {"values": all_values, "units": all_units}

    def _validate_and_extract_base_data(
        self, value: Any
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Validate input and extract base temperature and results data."""
        if not isinstance(value, dict) or "temperature" not in value:
            return None, None

        temp_data = value["temperature"]
        if not isinstance(temp_data, dict):
            return None, None

        results_data = value.get("results", {})
        if not isinstance(results_data, dict):
            return None, None

        return temp_data, results_data

    def _extract_temperature_data(
        self, temp_data: dict[str, Any]
    ) -> dict[str, list[Any]] | None:
        """Extract temperature values and units."""
        upper_temp_data: Any = temp_data.get("upper", {})
        lower_temp_data: Any = temp_data.get("lower", {})

        if not isinstance(upper_temp_data, dict) or not isinstance(
            lower_temp_data, dict
        ):
            return None

        upper_temp = upper_temp_data.get("value")
        upper_temp_unit = upper_temp_data.get("unit")
        lower_temp = lower_temp_data.get("value")
        lower_temp_unit = lower_temp_data.get("unit")

        return {
            "values": [upper_temp, lower_temp],
            "units": [upper_temp_unit, lower_temp_unit],
        }

    def _extract_conductivity_results(
        self, results_data: dict[str, Any]
    ) -> dict[str, list[Any]] | None:
        """Extract conductivity values and units."""
        upper_results: Any = results_data.get("upper", {})
        lower_results: Any = results_data.get("lower", {})

        if not isinstance(upper_results, dict) or not isinstance(lower_results, dict):
            return None

        upper_cond = upper_results.get("value")
        upper_cond_unit = upper_results.get("unit")
        lower_cond = lower_results.get("value")
        lower_cond_unit = lower_results.get("unit")

        return {
            "values": [upper_cond, lower_cond],
            "units": [upper_cond_unit, lower_cond_unit],
        }

    def _extract_heat_capacity_data(self, metadata: FileMetadata) -> pa.Table:
        """Extract volumetric heat capacity data."""
        if "setpoints" not in metadata:
            error_msg = "No setpoints found in metadata"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.VOLUMETRIC_HEAT_CAPACITY.value,
            )

        data = []
        units = []
        col_units = {}

        try:
            # Create schema
            schema = pa.schema(
                [
                    pa.field("setpoint", pa.int32()),
                    pa.field("average_temperature", pa.float64()),
                    pa.field("volumetric_heat_capacity", pa.float64()),
                ]
            )

            # Extract data from setpoints
            for key, value in metadata["setpoints"].items():
                try:
                    setpoint = int(key.split("_")[1])
                except (ValueError, IndexError):
                    continue

                # Extract average temperature - validate dict and required keys
                if not isinstance(value, dict):
                    continue

                # Check for required keys
                required_keys = ["temperature_average", "volumetric_heat_capacity"]
                if not all(key in value for key in required_keys):
                    continue

                temp_avg_data = value.get("temperature_average", {})
                heat_cap_data = value.get("volumetric_heat_capacity", {})

                if not isinstance(temp_avg_data, dict) or not isinstance(
                    heat_cap_data, dict
                ):
                    continue

                average_temp = temp_avg_data.get("value")
                average_temp_unit = temp_avg_data.get("unit")

                # Extract heat capacity
                specific_heat = heat_cap_data.get("value")
                specific_heat_unit = heat_cap_data.get("unit")

                # Validate values are present and numeric
                if average_temp is None or specific_heat is None:
                    continue
                if not isinstance(average_temp, (int, float)) or not isinstance(
                    specific_heat, (int, float)
                ):
                    continue

                data.append([setpoint, average_temp, specific_heat])
                units = [average_temp_unit, specific_heat_unit]

            # Set column units
            if units:
                col_units = {
                    "average_temperature": {"units": units[0]},
                    "volumetric_heat_capacity": {"units": units[1]},
                }

        except Exception as e:
            if isinstance(e, HFMDataExtractionError):
                raise
            error_msg = f"Failed to process heat capacity data: {e}"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.VOLUMETRIC_HEAT_CAPACITY.value,
            ) from e

        return self._create_table(data, schema, col_units)

    def _create_table(
        self,
        data: list[list[Any]],
        schema: pa.Schema,
        col_units: dict[str, dict[str, Any]],
    ) -> pa.Table:
        """Create PyArrow table from data.

        Args:
            data: List of data rows
            schema: PyArrow schema
            col_units: Column unit metadata

        Returns:
            PyArrow table with metadata
        """
        if not data:
            error_msg = "No data to create table"
            raise HFMDataExtractionError(error_msg)

        try:
            # Transpose data to match schema
            trans_data = np.transpose(data)
            arrays = [pa.array(trans_data[i]) for i in range(len(trans_data))]

            # Create PyArrow table from arrays and schema
            table = pa.Table.from_arrays(arrays, schema=schema)

            # Add column metadata
            if col_units:
                table = set_metadata(table, col_meta=col_units)
            else:
                pass  # No column metadata to add

        except Exception as e:
            error_msg = f"Failed to create PyArrow table: {e}"
            raise HFMDataExtractionError(error_msg) from e
        else:
            return table
