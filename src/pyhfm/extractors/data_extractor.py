"""Data extraction from HFM metadata."""

from __future__ import annotations

from typing import Any, NoReturn

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

    def _raise_unsupported_type_error(self, measurement_type: str) -> NoReturn:
        """Raise error for unsupported measurement type."""
        error_msg = f"Unsupported measurement type: {measurement_type}"
        raise HFMDataExtractionError(
            error_msg,
            measurement_type=measurement_type,
        )

    def _extract_temperature_data_safely(
        self, value: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Safely extract upper and lower temperature data from a setpoint value.

        Args:
            value: Setpoint dictionary containing temperature data

        Returns:
            Tuple of (upper_temp_data, lower_temp_data) dictionaries
        """
        temp_data_item_raw = value.get("temperature", {})
        temp_data_item: dict[str, Any] = (
            temp_data_item_raw if isinstance(temp_data_item_raw, dict) else {}
        )

        if isinstance(temp_data_item, dict):
            upper_temp_raw: dict[str, Any] | float | str = temp_data_item.get(
                "upper", {}
            )
            lower_temp_raw: dict[str, Any] | float | str = temp_data_item.get(
                "lower", {}
            )
            upper_temp_data = upper_temp_raw if isinstance(upper_temp_raw, dict) else {}
            lower_temp_data = lower_temp_raw if isinstance(lower_temp_raw, dict) else {}
        else:
            upper_temp_data = {}
            lower_temp_data = {}

        return upper_temp_data, lower_temp_data

    def _extract_results_data_safely(
        self, value: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Safely extract upper and lower results data from a setpoint value.

        Args:
            value: Setpoint dictionary containing results data

        Returns:
            Tuple of (upper_results, lower_results) dictionaries
        """
        results_data_item_raw = value.get("results", {})
        results_data_item: dict[str, Any] = (
            results_data_item_raw if isinstance(results_data_item_raw, dict) else {}
        )

        if isinstance(results_data_item, dict):
            upper_results_raw: dict[str, Any] | float | str = results_data_item.get(
                "upper", {}
            )
            lower_results_raw: dict[str, Any] | float | str = results_data_item.get(
                "lower", {}
            )
            upper_results = (
                upper_results_raw if isinstance(upper_results_raw, dict) else {}
            )
            lower_results = (
                lower_results_raw if isinstance(lower_results_raw, dict) else {}
            )
        else:
            upper_results = {}
            lower_results = {}

        return upper_results, lower_results

    def _extract_conductivity_units(
        self,
        upper_temp_data: dict[str, Any],
        lower_temp_data: dict[str, Any],
        upper_results: dict[str, Any],
        lower_results: dict[str, Any],
    ) -> list[str]:
        """Extract units from conductivity data.

        Args:
            upper_temp_data: Upper temperature data dictionary
            lower_temp_data: Lower temperature data dictionary
            upper_results: Upper results data dictionary
            lower_results: Lower results data dictionary

        Returns:
            List of units [upper_temp_unit, lower_temp_unit, upper_result_unit, lower_result_unit]
        """
        upper_temp_unit = (
            upper_temp_data.get("unit") if isinstance(upper_temp_data, dict) else None
        )
        lower_temp_unit = (
            lower_temp_data.get("unit") if isinstance(lower_temp_data, dict) else None
        )
        upper_result_unit = (
            upper_results.get("unit") if isinstance(upper_results, dict) else None
        )
        lower_result_unit = (
            lower_results.get("unit") if isinstance(lower_results, dict) else None
        )

        return [
            upper_temp_unit if isinstance(upper_temp_unit, str) else "°C",
            lower_temp_unit if isinstance(lower_temp_unit, str) else "°C",
            upper_result_unit if isinstance(upper_result_unit, str) else "W/m·K",
            lower_result_unit if isinstance(lower_result_unit, str) else "W/m·K",
        ]

    def _extract_conductivity_data(self, metadata: FileMetadata) -> pa.Table:
        """Extract thermal conductivity data with optimized pre-allocation."""
        if "setpoints" not in metadata:
            error_msg = "No setpoints found in metadata"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.CONDUCTIVITY.value,
            )

        setpoints = metadata["setpoints"]

        # Check if we have any setpoints with actual data (not just empty structures)
        valid_setpoints_with_data: list[tuple[str, dict[str, Any]]] = []
        for key, value in setpoints.items():
            if (
                isinstance(value, dict)
                and "temperature" in value
                and "results" in value
                and isinstance(value["temperature"], dict)
                and isinstance(value["results"], dict)
            ):
                temp_data = value["temperature"]
                results_data = value["results"]
                # Check if we have both upper and lower data with actual values
                upper_temp = temp_data.get("upper")
                lower_temp = temp_data.get("lower")
                upper_result = results_data.get("upper")
                lower_result = results_data.get("lower")

                if (
                    isinstance(upper_temp, dict)
                    and isinstance(lower_temp, dict)
                    and isinstance(upper_result, dict)
                    and isinstance(lower_result, dict)
                    and upper_temp.get("value") is not None
                    and lower_temp.get("value") is not None
                    and upper_result.get("value") is not None
                    and lower_result.get("value") is not None
                ):
                    valid_setpoints_with_data.append((key, value))

        num_rows = len(valid_setpoints_with_data)
        if num_rows == 0:
            error_msg = "No setpoints with valid conductivity data found"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.CONDUCTIVITY.value,
            )

        # Use only valid setpoints for processing
        setpoints = dict(valid_setpoints_with_data)

        # Pre-allocate arrays for known size (much faster than list appends)
        setpoint_ids = np.empty(num_rows, dtype=np.int32)
        upper_temps = np.empty(num_rows, dtype=np.float64)
        lower_temps = np.empty(num_rows, dtype=np.float64)
        upper_conds = np.empty(num_rows, dtype=np.float64)
        lower_conds = np.empty(num_rows, dtype=np.float64)

        units: list[str] = []

        try:
            # Single-pass extraction with pre-allocated arrays
            for i, (key, value) in enumerate(setpoints.items()):
                setpoint_ids[i] = int(key.split("_")[1])

                # Extract temperature and results data using helper methods
                upper_temp_data, lower_temp_data = (
                    self._extract_temperature_data_safely(value)
                )
                upper_results, lower_results = self._extract_results_data_safely(value)

                # Extract temperature values
                upper_temps[i] = (
                    upper_temp_data.get("value", np.nan)
                    if isinstance(upper_temp_data, dict)
                    else np.nan
                )
                lower_temps[i] = (
                    lower_temp_data.get("value", np.nan)
                    if isinstance(lower_temp_data, dict)
                    else np.nan
                )

                # Extract conductivity values
                upper_conds[i] = (
                    upper_results.get("value", np.nan)
                    if isinstance(upper_results, dict)
                    else np.nan
                )
                lower_conds[i] = (
                    lower_results.get("value", np.nan)
                    if isinstance(lower_results, dict)
                    else np.nan
                )

                # Collect units from first valid entry
                if (
                    not units
                    and upper_temp_data
                    and lower_temp_data
                    and upper_results
                    and lower_results
                ):
                    units = self._extract_conductivity_units(
                        upper_temp_data, lower_temp_data, upper_results, lower_results
                    )

            # Direct PyArrow table creation (no transpose needed)
            table = pa.table(
                {
                    "setpoint": pa.array(setpoint_ids),
                    "upper_temperature": pa.array(upper_temps),
                    "lower_temperature": pa.array(lower_temps),
                    "upper_thermal_conductivity": pa.array(upper_conds),
                    "lower_thermal_conductivity": pa.array(lower_conds),
                }
            )

            # Add column metadata if units available
            if units:
                col_units = {
                    "upper_temperature": {"units": units[0]},
                    "lower_temperature": {"units": units[1]},
                    "upper_thermal_conductivity": {"units": units[2]},
                    "lower_thermal_conductivity": {"units": units[3]},
                }
                table = set_metadata(table, col_meta=col_units)

        except Exception as e:
            if isinstance(e, HFMDataExtractionError):
                raise
            error_msg = f"Failed to process conductivity data: {e}"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.CONDUCTIVITY.value,
            ) from e
        else:
            return table

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
        """Extract volumetric heat capacity data with optimized pre-allocation."""
        if "setpoints" not in metadata:
            error_msg = "No setpoints found in metadata"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.VOLUMETRIC_HEAT_CAPACITY.value,
            )

        setpoints = metadata["setpoints"]

        # Filter valid setpoints with actual data first to get accurate count
        valid_setpoints = []
        for key, value in setpoints.items():
            if not isinstance(value, dict):
                continue
            required_keys = ["temperature_average", "volumetric_heat_capacity"]
            if all(k in value for k in required_keys):
                # Check if the data actually has values
                temp_avg_data = value.get("temperature_average", {})
                heat_cap_data = value.get("volumetric_heat_capacity", {})
                if (
                    isinstance(temp_avg_data, dict)
                    and isinstance(heat_cap_data, dict)
                    and temp_avg_data.get("value") is not None
                    and heat_cap_data.get("value") is not None
                ):
                    valid_setpoints.append((key, value))

        num_rows = len(valid_setpoints)
        if num_rows == 0:
            error_msg = "No setpoints with valid heat capacity data found"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.VOLUMETRIC_HEAT_CAPACITY.value,
            )

        # Pre-allocate arrays for known size
        setpoint_ids = np.empty(num_rows, dtype=np.int32)
        avg_temps = np.empty(num_rows, dtype=np.float64)
        heat_caps = np.empty(num_rows, dtype=np.float64)

        units: list[str] = []

        try:
            # Single-pass extraction with pre-allocated arrays
            for i, (key, value) in enumerate(valid_setpoints):
                setpoint_ids[i] = int(key.split("_")[1])

                # Extract temperature average with direct access
                temp_avg_data = value["temperature_average"]
                avg_temps[i] = (
                    temp_avg_data.get("value", np.nan)
                    if isinstance(temp_avg_data, dict)
                    else np.nan
                )

                # Extract heat capacity with direct access
                heat_cap_data = value["volumetric_heat_capacity"]
                heat_caps[i] = (
                    heat_cap_data.get("value", np.nan)
                    if isinstance(heat_cap_data, dict)
                    else np.nan
                )

                # Collect units from first valid entry
                if not units and temp_avg_data and heat_cap_data:
                    temp_unit = (
                        temp_avg_data.get("unit")
                        if isinstance(temp_avg_data, dict)
                        else None
                    )
                    heat_cap_unit = (
                        heat_cap_data.get("unit")
                        if isinstance(heat_cap_data, dict)
                        else None
                    )
                    units = [
                        temp_unit if isinstance(temp_unit, str) else "°C",
                        heat_cap_unit if isinstance(heat_cap_unit, str) else "J/m³·K",
                    ]

            # Direct PyArrow table creation
            table = pa.table(
                {
                    "setpoint": pa.array(setpoint_ids),
                    "average_temperature": pa.array(avg_temps),
                    "volumetric_heat_capacity": pa.array(heat_caps),
                }
            )

            # Add column metadata if units available
            if units:
                col_units = {
                    "average_temperature": {"units": units[0]},
                    "volumetric_heat_capacity": {"units": units[1]},
                }
                table = set_metadata(table, col_meta=col_units)

        except Exception as e:
            if isinstance(e, HFMDataExtractionError):
                raise
            error_msg = f"Failed to process heat capacity data: {e}"
            raise HFMDataExtractionError(
                error_msg,
                measurement_type=HFMType.VOLUMETRIC_HEAT_CAPACITY.value,
            ) from e
        else:
            return table

    def _create_table(
        self,
        data: list[list[Any]],
        schema: pa.Schema,
        col_units: dict[str, dict[str, Any]],
    ) -> pa.Table:
        """Create PyArrow table from data (legacy method - now replaced by direct table creation).

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

        except Exception as e:
            error_msg = f"Failed to create PyArrow table: {e}"
            raise HFMDataExtractionError(error_msg) from e
        else:
            return table
