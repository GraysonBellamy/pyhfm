# User Guide

This guide covers the essential functionality of pyhfm for parsing and analyzing Heat Flow Meter (HFM) data files.

## Core Functions

### Loading HFM Files

The primary function for loading HFM files is `read_hfm()`:

```python
import pyhfm
import polars as pl

# Basic loading
table = pyhfm.read_hfm("sample.tst")
df = table.to_polars()

# Load with metadata separated
metadata, table = pyhfm.read_hfm("sample.tst", return_metadata=True)

# Custom configuration
config = {"default_encoding": "utf-8"}
table = pyhfm.read_hfm("sample.tst", config=config)
```

### Understanding File Types

pyhfm automatically detects the measurement type:

```python
metadata, table = pyhfm.read_hfm("sample.tst", return_metadata=True)

measurement_type = metadata.get('type', 'unknown')
if measurement_type == 'thermal_conductivity':
    print("This file contains thermal conductivity measurements")
elif measurement_type == 'volumetric_heat_capacity':
    print("This file contains volumetric heat capacity measurements")
```

## Data Analysis Patterns

### Thermal Conductivity Analysis

```python
# Load thermal conductivity data
df = table.to_polars()

if "upper_thermal_conductivity" in df.columns:
    # Calculate statistics
    tc_stats = df.select([
        pl.col("upper_thermal_conductivity").mean().alias("tc_mean"),
        pl.col("upper_thermal_conductivity").std().alias("tc_std"),
        pl.col("upper_thermal_conductivity").min().alias("tc_min"),
        pl.col("upper_thermal_conductivity").max().alias("tc_max")
    ])
    print(tc_stats)

    # Temperature dependence
    temp_tc_corr = df.select([
        pl.corr("upper_temperature", "upper_thermal_conductivity").alias("temp_tc_correlation")
    ])
    print(f"Temperature-TC correlation: {temp_tc_corr[0, 0]:.3f}")
```

### Heat Capacity Analysis

```python
if "volumetric_heat_capacity" in df.columns:
    # Basic statistics
    hc_stats = df.select([
        pl.col("volumetric_heat_capacity").mean().alias("hc_mean"),
        pl.col("volumetric_heat_capacity").std().alias("hc_std"),
        pl.col("average_temperature").min().alias("temp_min"),
        pl.col("average_temperature").max().alias("temp_max")
    ])
    print(hc_stats)

    # Temperature range
    temp_range = df["average_temperature"].max() - df["average_temperature"].min()
    print(f"Temperature range: {temp_range:.1f} °C")
```

### Setpoint Analysis

```python
# Analyze measurement by setpoint
setpoint_analysis = df.group_by("setpoint").agg([
    pl.col("upper_temperature").mean().alias("avg_temp"),
    pl.col("upper_thermal_conductivity").mean().alias("avg_tc"),
    pl.col("upper_thermal_conductivity").std().alias("tc_std")
])

print("Per-setpoint analysis:")
print(setpoint_analysis)

# Find most stable measurements (lowest std dev)
most_stable = setpoint_analysis.filter(
    pl.col("tc_std") == pl.col("tc_std").min()
)
print(f"Most stable setpoint: {most_stable['setpoint'][0]}")
```

## Data Export and Integration

### Working with Different Formats

```python
# Export to various formats
import pyarrow.parquet as pq
import json

# Parquet (preserves metadata)
pq.write_table(table, "output.parquet")

# CSV (data only)
df = table.to_polars()
df.write_csv("output.csv")

# JSON with metadata
with open("metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
```

### Integration with Pandas

```python
import pandas as pd

# Convert to Pandas DataFrame
df_pandas = table.to_pandas()

# Perform Pandas operations
correlation_matrix = df_pandas.corr()
print(correlation_matrix)
```

### Integration with NumPy

```python
import numpy as np

# Extract specific columns as NumPy arrays
if "upper_temperature" in df.columns:
    temperatures = table.column('upper_temperature').to_numpy()
    thermal_conductivity = table.column('upper_thermal_conductivity').to_numpy()

    # Polynomial fit
    coeffs = np.polyfit(temperatures, thermal_conductivity, 2)
    print(f"Polynomial coefficients: {coeffs}")
```

## Advanced Analysis

### Quality Control Checks

```python
# Check for missing data
missing_data = df.null_count()
print("Missing values per column:", missing_data)

# Check for outliers (using IQR method)
if "upper_thermal_conductivity" in df.columns:
    q1 = df["upper_thermal_conductivity"].quantile(0.25)
    q3 = df["upper_thermal_conductivity"].quantile(0.75)
    iqr = q3 - q1

    outlier_threshold = 1.5 * iqr
    outliers = df.filter(
        (pl.col("upper_thermal_conductivity") < q1 - outlier_threshold) |
        (pl.col("upper_thermal_conductivity") > q3 + outlier_threshold)
    )

    print(f"Found {outliers.height} outliers")
```

### Temperature Stability Analysis

```python
# Analyze temperature stability across setpoints
if "upper_temperature" in df.columns and "lower_temperature" in df.columns:
    temp_diff = df.with_columns([
        (pl.col("upper_temperature") - pl.col("lower_temperature")).alias("temp_diff")
    ])

    stability_stats = temp_diff.select([
        pl.col("temp_diff").mean().alias("avg_temp_diff"),
        pl.col("temp_diff").std().alias("temp_diff_std")
    ])

    print("Temperature stability:")
    print(stability_stats)
```

### Measurement Precision

```python
# Calculate measurement precision for repeated setpoints
if "setpoint" in df.columns:
    precision_analysis = df.group_by("setpoint").agg([
        pl.count().alias("num_measurements"),
        pl.col("upper_thermal_conductivity").std().alias("precision")
    ]).filter(pl.col("num_measurements") > 1)

    if precision_analysis.height > 0:
        avg_precision = precision_analysis["precision"].mean()
        print(f"Average measurement precision: {avg_precision:.6f} W/m·K")
```

## Custom Parser Usage

### Advanced Parser Configuration

```python
from pyhfm import HFMParser

# Create parser with custom settings
config = {
    "default_encoding": "utf-16le",
    "skip_validation": False,
    "custom_threshold": 1e-6
}

parser = HFMParser(config=config)
table = parser.parse_file("sample.tst")
```

### Direct Data Extraction

```python
from pyhfm import DataExtractor

# Use the data extractor directly
extractor = DataExtractor()

# Extract from already parsed metadata
table = extractor.extract_data(metadata)
```

## Error Handling and Debugging

### Common Exception Types

```python
import pyhfm

try:
    table = pyhfm.read_hfm("sample.tst")
except pyhfm.HFMFileError as e:
    print(f"File access error: {e}")
except pyhfm.HFMParsingError as e:
    print(f"Parsing error: {e}")
except pyhfm.HFMValidationError as e:
    print(f"Data validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Debugging File Issues

```python
# Check file encoding
import chardet

with open("sample.tst", "rb") as f:
    raw_data = f.read(1000)  # Read first 1000 bytes
    encoding_result = chardet.detect(raw_data)
    print(f"Detected encoding: {encoding_result}")

# Try different encodings
encodings_to_try = ["utf-16le", "utf-8", "cp1252"]
for encoding in encodings_to_try:
    try:
        config = {"default_encoding": encoding}
        table = pyhfm.read_hfm("sample.tst", config=config)
        print(f"Success with encoding: {encoding}")
        break
    except Exception as e:
        print(f"Failed with {encoding}: {e}")
```

## Command Line Advanced Usage

### Batch Processing

```bash
# Process multiple files
for file in *.tst; do
    pyhfm "$file" --format parquet --output "${file%.tst}.parquet"
done

# With metadata extraction
pyhfm *.tst --format csv --metadata --output-dir ./processed/
```

### Custom Output Formats

```bash
# Specific output file
pyhfm sample.tst --format csv --output custom_name.csv

# With metadata included in separate file
pyhfm sample.tst --format parquet --metadata --output data.parquet
```

## Performance Optimization

### Memory Management

```python
# For very large files, consider processing in chunks
import pyarrow as pa

def process_large_hfm_file(filename):
    table = pyhfm.read_hfm(filename)

    # Process in batches if memory is limited
    batch_size = 1000
    for i in range(0, table.num_rows, batch_size):
        batch = table.slice(i, batch_size)
        # Process batch...
        del batch  # Explicit cleanup
```

### Efficient Data Access

```python
# Access columns directly from PyArrow table
temperature_col = table.column('upper_temperature')
tc_col = table.column('upper_thermal_conductivity')

# Convert to NumPy only when needed for calculations
temp_array = temperature_col.to_numpy()
tc_array = tc_col.to_numpy()
```

## Best Practices

### Data Validation

```python
def validate_hfm_data(table, metadata):
    """Validate HFM data for common issues."""
    df = table.to_polars()

    issues = []

    # Check for reasonable temperature ranges
    if "upper_temperature" in df.columns:
        temp_range = df["upper_temperature"].max() - df["upper_temperature"].min()
        if temp_range < 5:
            issues.append("Very small temperature range")

    # Check for reasonable thermal conductivity values
    if "upper_thermal_conductivity" in df.columns:
        tc_values = df["upper_thermal_conductivity"]
        if tc_values.min() < 0:
            issues.append("Negative thermal conductivity values")
        if tc_values.max() > 10:  # Adjust based on expected material range
            issues.append("Unusually high thermal conductivity values")

    return issues
```

### Reproducible Analysis

```python
# Save analysis parameters with results
analysis_config = {
    "file_processed": "sample.tst",
    "processing_date": "2024-01-01",
    "pyhfm_version": pyhfm.__version__,
    "outlier_threshold": 1.5,
    "temperature_range": [temp_min, temp_max]
}

# Include in output
results = {
    "data": df.to_dict(),
    "metadata": metadata,
    "analysis_config": analysis_config
}
```

## Next Steps

- **[API Reference](api-reference.md)** - Complete function documentation
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Contributing](contributing.md)** - Development guidelines

This guide covers the essential workflows for most HFM data analysis applications. For advanced customization and additional features, refer to the complete API documentation.
