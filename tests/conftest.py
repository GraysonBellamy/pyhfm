"""Pytest configuration and fixtures for HFM tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_hfm_file(test_data_dir: Path) -> Path:
    """Path to sample HFM file for testing."""
    # This would point to an actual test file
    # For now, return a placeholder path
    return test_data_dir / "sample.tst"


@pytest.fixture
def sample_conductivity_metadata() -> dict[str, Any]:
    """Sample conductivity measurement metadata for testing."""
    return {
        "sample_id": "TEST_SAMPLE",
        "type": "conductivity",
        "date_performed": "2023-01-01T10:00:00",
        "thickness": {"value": 25.4, "unit": "mm"},
        "number_of_transducers": 2,
        "number_of_setpoints": 2,
        "setpoints": {
            "setpoint_1": {
                "temperature": {
                    "upper": {"value": 25.0, "unit": "°C"},
                    "lower": {"value": 15.0, "unit": "°C"},
                },
                "results": {
                    "upper": {"value": 0.15, "unit": "W/m·K"},
                    "lower": {"value": 0.14, "unit": "W/m·K"},
                },
            },
            "setpoint_2": {
                "temperature": {
                    "upper": {"value": 35.0, "unit": "°C"},
                    "lower": {"value": 25.0, "unit": "°C"},
                },
                "results": {
                    "upper": {"value": 0.16, "unit": "W/m·K"},
                    "lower": {"value": 0.15, "unit": "W/m·K"},
                },
            },
        },
        "file_hash": {
            "file": "test.tst",
            "method": "BLAKE2b",
            "hash": "test_hash",
        },
    }


@pytest.fixture
def sample_heat_capacity_metadata() -> dict[str, Any]:
    """Sample heat capacity measurement metadata for testing."""
    return {
        "sample_id": "TEST_SAMPLE_HC",
        "type": "volumetric_heat_capacity",
        "date_performed": "2023-01-01T10:00:00",
        "thickness": {"value": 25.4, "unit": "mm"},
        "number_of_transducers": 2,
        "number_of_setpoints": 2,
        "setpoints": {
            "setpoint_1": {
                "temperature_average": {"value": 20.0, "unit": "°C"},
                "volumetric_heat_capacity": {"value": 1500000, "unit": "J/m³·K"},
            },
            "setpoint_2": {
                "temperature_average": {"value": 30.0, "unit": "°C"},
                "volumetric_heat_capacity": {"value": 1520000, "unit": "J/m³·K"},
            },
        },
        "file_hash": {
            "file": "test_hc.tst",
            "method": "BLAKE2b",
            "hash": "test_hash_hc",
        },
    }


@pytest.fixture
def temp_hfm_file(tmp_path: Path) -> Path:
    """Create a temporary HFM file for testing."""
    content = """Sunday, January 01, 2023, Time 10:00

Sample Name: TEST_SAMPLE

Run Mode: Thermal Conductivity

Thickness: 25.40 mm

Number of Setpoints: 2

Setpoint No. 1
Temperature Upper: 25.00 °C
Temperature Lower: 15.00 °C
Results Upper: 0.15 W/m·K
Results Lower: 0.14 W/m·K

Setpoint No. 2
Temperature Upper: 35.00 °C
Temperature Lower: 25.00 °C
Results Upper: 0.16 W/m·K
Results Lower: 0.15 W/m·K
"""

    test_file = tmp_path / "test.tst"
    test_file.write_text(content, encoding="utf-16le")
    return test_file
