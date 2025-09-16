# Getting Started

This guide will help you install pyhfm and parse your first HFM data file.

## Installation

### Requirements

- Python 3.10 or higher
- Operating System: Windows, macOS, or Linux

### Install from PyPI

```bash
pip install pyhfm
```

### Verify Installation

```bash
python -c "import pyhfm; print('pyhfm installed successfully')"
```

### Development Installation

If you want to contribute or use the latest features:

```bash
git clone https://github.com/GraysonBellamy/pyhfm.git
cd pyhfm
pip install -e ".[dev,test]"
```

## Your First HFM File

### Basic File Loading

```python
import pyhfm
import polars as pl

# Load an HFM file
table = pyhfm.read_hfm("your_file.tst")

# Convert to DataFrame for analysis
df = table.to_polars()

print(f"Loaded {df.height} measurements with {df.width} columns")
print(f"Available columns: {df.columns}")
```

### Accessing Metadata

HFM files contain rich metadata embedded in the file structure:

```python
# Extract metadata from the file
metadata, table = pyhfm.read_hfm("your_file.tst", return_metadata=True)

# Print key information
print(f"Sample ID: {metadata.get('sample_id', 'Unknown')}")
print(f"Measurement type: {metadata.get('type', 'Unknown')}")
print(f"Number of setpoints: {metadata.get('number_of_setpoints', 'Unknown')}")
print(f"Operator: {metadata.get('operator', 'Unknown')}")
```

### Basic Data Exploration

```python
# Check data types and basic statistics
print(df.describe())

# Temperature analysis for thermal conductivity measurements
if "upper_temperature" in df.columns:
    temp_min = df["upper_temperature"].min()
    temp_max = df["upper_temperature"].max()
    print(f"Temperature range: {temp_min:.1f} to {temp_max:.1f} °C")

# Thermal conductivity analysis
if "upper_thermal_conductivity" in df.columns:
    tc_mean = df["upper_thermal_conductivity"].mean()
    tc_std = df["upper_thermal_conductivity"].std()
    print(f"Average thermal conductivity: {tc_mean:.4f} ± {tc_std:.4f} W/m·K")
```

## Command Line Interface

pyhfm includes a powerful CLI for data conversion and analysis.

### Basic Usage

```bash
# Convert single file to Parquet (default)
pyhfm sample.tst

# Convert to CSV
pyhfm sample.tst --format csv --output sample.csv

# Convert with metadata included
pyhfm sample.tst --format parquet --metadata --output sample.parquet

# Print as JSON to stdout
pyhfm sample.tst --format json
```

### Output Formats

```bash
# Parquet format (preserves metadata)
pyhfm sample.tst --format parquet --output data.parquet

# CSV format (data only)
pyhfm sample.tst --format csv --output data.csv

# JSON format (for inspection)
pyhfm sample.tst --format json > data.json
```

### Get Help

```bash
pyhfm --help
```

## Data Types and Structure

### Thermal Conductivity Measurements

For thermal conductivity files, you'll see these columns:

| Column | Type | Description |
|--------|------|-------------|
| `setpoint` | int32 | Setpoint number |
| `upper_temperature` | float64 | Upper plate temperature (°C) |
| `lower_temperature` | float64 | Lower plate temperature (°C) |
| `upper_thermal_conductivity` | float64 | Upper thermal conductivity (W/m·K) |
| `lower_thermal_conductivity` | float64 | Lower thermal conductivity (W/m·K) |

### Volumetric Heat Capacity Measurements

For volumetric heat capacity files:

| Column | Type | Description |
|--------|------|-------------|
| `setpoint` | int32 | Setpoint number |
| `average_temperature` | float64 | Average temperature (°C) |
| `volumetric_heat_capacity` | float64 | Volumetric heat capacity (J/m³·K) |

## Data Export Options

### Parquet (Recommended)

Parquet preserves all data types and metadata efficiently:

```python
import pyarrow.parquet as pq

# Export to Parquet (metadata included in schema)
pq.write_table(table, "output.parquet")

# Load back with metadata intact
loaded_table = pq.read_table("output.parquet")
```

### CSV Export

```python
# Convert to CSV (loses metadata)
df = table.to_polars()
df.write_csv("output.csv")
```

### JSON Export

```python
import json

# Export metadata separately
with open("metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
```

## Quick Visualization

```python
import matplotlib.pyplot as plt

# Thermal conductivity vs temperature
if "upper_temperature" in df.columns and "upper_thermal_conductivity" in df.columns:
    plt.figure(figsize=(10, 6))
    plt.plot(df["upper_temperature"], df["upper_thermal_conductivity"], 'o-')
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Thermal Conductivity (W/m·K)")
    plt.title("Thermal Conductivity vs Temperature")
    plt.grid(True, alpha=0.3)
    plt.show()

# Heat capacity vs temperature
if "average_temperature" in df.columns and "volumetric_heat_capacity" in df.columns:
    plt.figure(figsize=(10, 6))
    plt.plot(df["average_temperature"], df["volumetric_heat_capacity"], 's-')
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Volumetric Heat Capacity (J/m³·K)")
    plt.title("Volumetric Heat Capacity vs Temperature")
    plt.grid(True, alpha=0.3)
    plt.show()
```

## Next Steps

Now that you can load and examine HFM files, explore these advanced features:

- **[User Guide](user-guide.md)** - Learn about data analysis, custom parsing, and advanced features
- **[API Reference](api-reference.md)** - Complete function documentation
- **[Troubleshooting](troubleshooting.md)** - Solutions to common issues

## Common File Types

pyhfm supports these HFM file extensions:

- `.tst` - HFM test files (main data format)

The parser automatically detects whether the file contains thermal conductivity or volumetric heat capacity measurements and applies the appropriate schema.
