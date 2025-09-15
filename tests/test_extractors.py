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
