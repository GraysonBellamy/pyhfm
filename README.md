# PyHFM - Heat Flow Meter Data Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PyHFM is a Python package for reading and analyzing Heat Flow Meter (HFM) data files. It provides a clean, modern API for parsing HFM measurement data and extracting thermal conductivity and volumetric heat capacity measurements.

## Features

- **Simple API**: Clean `read_hfm()` function for easy data loading
- **Multiple Formats**: Support for thermal conductivity and volumetric heat capacity measurements
- **Rich Metadata**: Comprehensive metadata extraction and validation
- **Modern Data Stack**: Built on PyArrow for efficient data handling
- **Type Safety**: Full type annotations for better development experience
- **Comprehensive Testing**: Extensive test suite for reliability
- **CLI Support**: Command-line interface for quick data conversion

## Installation

```bash
pip install pyhfm
```

For development installation:

```bash
git clone https://github.com/GraysonBellamy/pyhfm.git
cd pyhfm
pip install -e ".[dev,test]"
```

## Quick Start

### Basic Usage

```python
import pyhfm

# Read HFM file and get PyArrow table
table = pyhfm.read_hfm("sample.tst")

# Convert to polars DataFrame for analysis
df = table.to_polars()
print(df.head())
```

### Access Metadata

```python
# Get both metadata and data
metadata, table = pyhfm.read_hfm("sample.tst", return_metadata=True)

print(f"Sample: {metadata['sample_id']}")
print(f"Type: {metadata['type']}")
print(f"Setpoints: {metadata['number_of_setpoints']}")
```

### Custom Configuration

```python
# Override default settings
config = {"default_encoding": "utf-8"}
table = pyhfm.read_hfm("sample.tst", config=config)
```

## Data Structure

PyHFM returns data in PyArrow tables with the following schemas:

### Thermal Conductivity Measurements

| Column | Type | Description |
|--------|------|-------------|
| `setpoint` | int32 | Setpoint number |
| `upper_temperature` | float64 | Upper plate temperature |
| `lower_temperature` | float64 | Lower plate temperature |
| `upper_thermal_conductivity` | float64 | Upper thermal conductivity result |
| `lower_thermal_conductivity` | float64 | Lower thermal conductivity result |

### Volumetric Heat Capacity Measurements

| Column | Type | Description |
|--------|------|-------------|
| `setpoint` | int32 | Setpoint number |
| `average_temperature` | float64 | Average temperature |
| `volumetric_heat_capacity` | float64 | Volumetric heat capacity result |

## Command Line Interface

PyHFM includes a CLI for quick data conversion:

```bash
# Convert to CSV
pyhfm sample.tst --output sample.csv --format csv

# Convert to Parquet with metadata
pyhfm sample.tst --output sample.parquet --format parquet --metadata

# Print to stdout as JSON
pyhfm sample.tst --format json
```

## Advanced Usage

### Custom Parser

```python
from pyhfm import HFMParser

# Create parser with custom configuration
parser = HFMParser(config={"default_encoding": "utf-16le"})
table = parser.parse_file("sample.tst")
```

### Data Extraction

```python
from pyhfm import DataExtractor

# Extract data from metadata
extractor = DataExtractor()
table = extractor.extract_data(metadata)
```

### Error Handling

```python
import pyhfm

try:
    table = pyhfm.read_hfm("sample.tst")
except pyhfm.HFMFileError as e:
    print(f"File error: {e}")
except pyhfm.HFMParsingError as e:
    print(f"Parsing error: {e}")
except pyhfm.HFMValidationError as e:
    print(f"Validation error: {e}")
```

## Supported File Formats

- **HFM Test Files** (`.tst`): Standard HFM output format
- **Encodings**: UTF-16LE (default), UTF-8, and auto-detection
- **Measurements**: Thermal conductivity and volumetric heat capacity

## Architecture

PyHFM follows a modular architecture inspired by the [pynetzsch](https://github.com/GraysonBellamy/pynetzsch) package:

```
pyhfm/
   api/           # High-level user API
   core/          # Core parsing logic
   extractors/    # Data extraction components
   constants.py   # Configuration and data types
   exceptions.py  # Custom exception hierarchy
   __init__.py    # Public API exports
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/GraysonBellamy/pyhfm.git
cd pyhfm
pip install -e ".[dev,test]"
pre-commit install
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
ruff check .          # Linting
ruff format .         # Formatting
mypy src/pyhfm        # Type checking
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v0.1.0 (2024-01-01)

- Initial release
- Support for thermal conductivity and volumetric heat capacity measurements
- PyArrow-based data handling
- Comprehensive metadata extraction
- CLI interface
- Full type annotations

## Related Projects

- [pynetzsch](https://github.com/GraysonBellamy/pynetzsch) - Python package for NETZSCH thermal analysis data

## Support

If you encounter any issues or have questions, please:

1. Check the [documentation](https://pyhfm.readthedocs.io/)
2. Search [existing issues](https://github.com/GraysonBellamy/pyhfm/issues)
3. Create a [new issue](https://github.com/GraysonBellamy/pyhfm/issues/new) if needed
