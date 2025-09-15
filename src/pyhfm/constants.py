"""Constants and configuration for HFM data processing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


class HFMType(Enum):
    """HFM measurement types."""

    CONDUCTIVITY = "conductivity"
    VOLUMETRIC_HEAT_CAPACITY = "volumetric_heat_capacity"


class FileMetadata(TypedDict, total=False):
    """Structured metadata for HFM files."""

    # Core identification
    sample_id: str
    type: str
    date_performed: str

    # Physical properties
    thickness: dict[str, float | str] | float | str
    number_of_transducers: int
    number_of_setpoints: int

    # Calibration information
    calibration: dict[str, str | dict[str, float]]

    # Comments and notes
    comment: str | list[str]

    # Setpoint data
    setpoints: dict[str, dict[str, float | str | dict[str, float | str]]]

    # File information
    file_hash: dict[str, str]


class TemperatureData(TypedDict):
    """Temperature measurement data structure."""

    value: float
    unit: str


class CalibrationData(TypedDict):
    """Calibration data structure."""

    value: float
    unit: str


class ResultsData(TypedDict):
    """Results data structure."""

    value: float
    unit: str


class ThermalEquilibriumData(TypedDict, total=False):
    """Thermal equilibrium criteria data."""

    temperature: float
    between_block: float
    percent_change: float
    min_number_of_blocks: float
    calculation_blocks: float


class SetpointData(TypedDict, total=False):
    """Complete setpoint data structure."""

    date_performed: str
    setpoint_temperature: dict[str, TemperatureData]
    temperature: dict[str, TemperatureData]
    calibration: dict[str, CalibrationData]
    results: dict[str, ResultsData]
    thermal_equilibrium: ThermalEquilibriumData
    temperature_average: TemperatureData
    volumetric_heat_capacity: dict[str, float | str]


@dataclass(frozen=True)
class HFMParsingConfig:
    """Configuration for HFM file parsing."""

    # Default encoding for HFM files
    default_encoding: str = "utf-16le"

    # Supported file extensions
    supported_extensions: tuple[str, ...] = (".tst",)

    # Date format patterns
    date_format: str = "%A, %B %d, %Y, Time %H:%M"

    # Regex patterns for value extraction
    value_pattern: str = r"\d+\.\d+"
    unit_pattern: str = r"[a-zA-Z]+"
    unicode_unit_pattern: str = r"[^\x00-\x7f]+[a-zA-Z]+"
    unit_ratio_pattern: str = r"[a-zA-Z]/[a-zA-Z]+"

    # Default units for specific measurements
    default_calibration_unit: str = "µV/W"


@dataclass
class ColumnConfig:
    """Configuration for data table columns."""

    # Conductivity measurement columns
    conductivity_schema: dict[str, str] | None = None

    # Heat capacity measurement columns
    heat_capacity_schema: dict[str, str] | None = None

    def __post_init__(self) -> None:
        """Initialize default column schemas."""
        if self.conductivity_schema is None:
            self.conductivity_schema = {
                "setpoint": "int32",
                "upper_temperature": "float64",
                "lower_temperature": "float64",
                "upper_thermal_conductivity": "float64",
                "lower_thermal_conductivity": "float64",
            }

        if self.heat_capacity_schema is None:
            self.heat_capacity_schema = {
                "setpoint": "int32",
                "average_temperature": "float64",
                "volumetric_heat_capacity": "float64",
            }


@dataclass(frozen=True)
class ValidationConfig:
    """Configuration for data validation."""

    # Temperature validation (in Kelvin)
    min_temperature: float = 0.0
    max_temperature: float = 2000.0

    # Conductivity validation (W/m·K)
    min_conductivity: float = 0.0
    max_conductivity: float = 1000.0

    # Heat capacity validation (J/m³·K)
    min_heat_capacity: float = 0.0
    max_heat_capacity: float = 1e7

    # Required metadata fields
    required_metadata: tuple[str, ...] = (
        "sample_id",
        "type",
        "file_hash",
    )

    # Optional but recommended metadata fields
    recommended_metadata: tuple[str, ...] = (
        "date_performed",
        "thickness",
        "calibration",
        "setpoints",
    )


# Default configurations
DEFAULT_PARSING_CONFIG = HFMParsingConfig()
DEFAULT_COLUMN_CONFIG = ColumnConfig()
DEFAULT_VALIDATION_CONFIG = ValidationConfig()

# Common unit conversions
TEMPERATURE_UNITS = {
    "°C": "celsius",
    "C": "celsius",
    "K": "kelvin",
    "°F": "fahrenheit",
    "F": "fahrenheit",
}

CONDUCTIVITY_UNITS = {
    "W/m·K": "watts_per_meter_kelvin",
    "W/mK": "watts_per_meter_kelvin",
    "W/(m·K)": "watts_per_meter_kelvin",
    "W/m-K": "watts_per_meter_kelvin",
}

HEAT_CAPACITY_UNITS = {
    "J/m³·K": "joules_per_cubic_meter_kelvin",
    "J/m3K": "joules_per_cubic_meter_kelvin",
    "J/(m³·K)": "joules_per_cubic_meter_kelvin",
    "J/m³K": "joules_per_cubic_meter_kelvin",
}

# File patterns and markers for different HFM instruments
HFM_MARKERS = {
    "fox": {
        "sample_name": "Sample Name: ",
        "run_mode": "Run Mode",
        "thickness": "Thickness: ",
        "setpoint": "Setpoint No.",
        "comment_start": "[",
        "comment_end": "]",
    }
}
