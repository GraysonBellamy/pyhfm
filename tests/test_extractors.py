"""Tests for data extraction functionality."""

from __future__ import annotations

from typing import Any

import pyarrow as pa
import pytest

from pyhfm.exceptions import HFMDataExtractionError
from pyhfm.extractors.data_extractor import DataExtractor


class TestDataExtractor:
    """Test cases for DataExtractor class."""

    def test_extractor_initialization(self) -> None:
        """Test extractor initialization."""
        extractor = DataExtractor()
        assert extractor.config is not None

    def test_extract_conductivity_data(
        self, sample_conductivity_metadata: dict[str, Any]
    ) -> None:
        """Test conductivity data extraction."""
        extractor = DataExtractor()
        table = extractor.extract_data(sample_conductivity_metadata)

        assert isinstance(table, pa.Table)
        assert len(table) == 2  # Two setpoints

        # Check column names
        expected_columns = [
            "setpoint",
            "upper_temperature",
            "lower_temperature",
            "upper_thermal_conductivity",
            "lower_thermal_conductivity",
        ]
        assert table.column_names == expected_columns

        # Check data types
        assert table.schema.field("setpoint").type == pa.int32()
        assert table.schema.field("upper_temperature").type == pa.float64()
        assert table.schema.field("lower_temperature").type == pa.float64()
        assert table.schema.field("upper_thermal_conductivity").type == pa.float64()
        assert table.schema.field("lower_thermal_conductivity").type == pa.float64()

    def test_extract_heat_capacity_data(
        self, sample_heat_capacity_metadata: dict[str, Any]
    ) -> None:
        """Test heat capacity data extraction."""
        extractor = DataExtractor()
        table = extractor.extract_data(sample_heat_capacity_metadata)

        assert isinstance(table, pa.Table)
        assert len(table) == 2  # Two setpoints

        # Check column names
        expected_columns = [
            "setpoint",
            "average_temperature",
            "volumetric_heat_capacity",
        ]
        assert table.column_names == expected_columns

        # Check data types
        assert table.schema.field("setpoint").type == pa.int32()
        assert table.schema.field("average_temperature").type == pa.float64()
        assert table.schema.field("volumetric_heat_capacity").type == pa.float64()

    def test_extract_data_missing_type(self) -> None:
        """Test extraction with missing measurement type."""
        extractor = DataExtractor()
        metadata = {"sample_id": "test"}  # Missing 'type' field

        with pytest.raises(HFMDataExtractionError, match="Missing measurement type"):
            extractor.extract_data(metadata)  # type: ignore[arg-type]

    def test_extract_data_unsupported_type(self) -> None:
        """Test extraction with unsupported measurement type."""
        extractor = DataExtractor()
        metadata = {"type": "unsupported_type"}

        with pytest.raises(
            HFMDataExtractionError, match="Unsupported measurement type"
        ):
            extractor.extract_data(metadata)  # type: ignore[arg-type]

    def test_extract_data_missing_setpoints(self) -> None:
        """Test extraction with missing setpoints."""
        extractor = DataExtractor()
        metadata = {"type": "conductivity"}  # Missing 'setpoints' field

        with pytest.raises(HFMDataExtractionError, match="No setpoints found"):
            extractor.extract_data(metadata)  # type: ignore[arg-type]

    def test_create_table_empty_data(self) -> None:
        """Test table creation with empty data."""
        extractor = DataExtractor()
        schema = pa.schema([pa.field("test", pa.int32())])

        with pytest.raises(HFMDataExtractionError, match="No data to create table"):
            extractor._create_table([], schema, {})

    def test_extractor_initialization_with_config(self) -> None:
        """Test DataExtractor initialization with custom config."""
        custom_config = {"temperature_units": "celsius"}
        extractor = DataExtractor(config=custom_config)
        assert extractor.config is not None

    def test_helper_methods_with_mock_data(self) -> None:
        """Test the helper methods with mock setpoint data."""
        extractor = DataExtractor()

        # Test _extract_temperature_data_safely with dict data
        setpoint_value = {
            "temperature": {"upper": {"value": 25.0}, "lower": {"value": 15.0}}
        }
        upper, lower = extractor._extract_temperature_data_safely(setpoint_value)
        assert upper == {"value": 25.0}
        assert lower == {"value": 15.0}

        # Test _extract_results_data_safely with dict data
        setpoint_value_with_results = {
            "results": {"upper": {"value": 1.5}, "lower": {"value": 1.2}}
        }
        upper, lower = extractor._extract_results_data_safely(
            setpoint_value_with_results
        )
        assert upper == {"value": 1.5}
        assert lower == {"value": 1.2}

        # Test _extract_conductivity_units
        temp_upper = {"unit": "°C"}
        temp_lower = {"unit": "°C"}
        results_upper = {"unit": "W/m·K"}
        results_lower = {"unit": "W/m·K"}
        units = extractor._extract_conductivity_units(
            temp_upper, temp_lower, results_upper, results_lower
        )
        assert len(units) == 4  # Returns temperature units + results units
