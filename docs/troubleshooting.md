# Troubleshooting

Common issues and solutions when working with pyhfm.

## Installation Issues

### Package Not Found

**Problem**: `pip install pyhfm` fails with package not found.

**Solution**:
```bash
# Check if you're using the correct package name
pip search pyhfm

# Try installing from the development repository
pip install git+https://github.com/GraysonBellamy/pyhfm.git
```

### Dependency Conflicts

**Problem**: Installation fails due to conflicting dependencies.

**Solution**:
```bash
# Create a fresh virtual environment
python -m venv pyhfm_env
source pyhfm_env/bin/activate  # On Windows: pyhfm_env\Scripts\activate

# Install pyhfm in clean environment
pip install pyhfm
```

## File Reading Issues

### Encoding Problems

**Problem**: `UnicodeDecodeError` when reading HFM files.

**Symptoms**:
```
UnicodeDecodeError: 'utf-16le' codec can't decode bytes
```

**Solutions**:

1. **Auto-detect encoding**:
```python
import chardet
import pyhfm

# Check file encoding
with open("problem_file.tst", "rb") as f:
    raw_data = f.read(1000)
    result = chardet.detect(raw_data)
    print(f"Detected encoding: {result['encoding']}")

# Use detected encoding
config = {"default_encoding": result['encoding']}
table = pyhfm.read_hfm("problem_file.tst", config=config)
```

2. **Try common encodings**:
```python
encodings = ["utf-16le", "utf-8", "cp1252", "iso-8859-1"]

for encoding in encodings:
    try:
        config = {"default_encoding": encoding}
        table = pyhfm.read_hfm("problem_file.tst", config=config)
        print(f"Success with encoding: {encoding}")
        break
    except UnicodeDecodeError:
        continue
```

### File Format Issues

**Problem**: File appears to be corrupted or in unexpected format.

**Symptoms**:
```
HFMParsingError: Unable to parse file header
```

**Solutions**:

1. **Verify file integrity**:
```bash
# Check file size
ls -la problem_file.tst

# Check file type
file problem_file.tst
```

2. **Examine file contents**:
```python
# Look at raw file contents
with open("problem_file.tst", "rb") as f:
    header = f.read(100)
    print(header)
```

3. **Use custom parser**:
```python
from pyhfm import HFMParser

# Try with relaxed validation
config = {"skip_validation": True}
parser = HFMParser(config=config)
table = parser.parse_file("problem_file.tst")
```

### Permission Issues

**Problem**: Cannot read file due to permissions.

**Solution**:
```bash
# Check file permissions
ls -la problem_file.tst

# Fix permissions (Unix/Linux/macOS)
chmod 644 problem_file.tst
```

## Data Issues

### Missing Expected Columns

**Problem**: Expected columns not present in parsed data.

**Symptoms**:
```python
KeyError: 'upper_thermal_conductivity'
```

**Solutions**:

1. **Check measurement type**:
```python
metadata, table = pyhfm.read_hfm("file.tst", return_metadata=True)
measurement_type = metadata.get('type', 'unknown')
print(f"Measurement type: {measurement_type}")

# Check available columns
import polars as pl
df = pl.from_arrow(table)
print(f"Available columns: {df.columns}")
```

2. **Handle different measurement types**:
```python
import polars as pl
df = pl.from_arrow(table)

if "upper_thermal_conductivity" in df.columns:
    # Thermal conductivity data
    print("Processing thermal conductivity data")
elif "volumetric_heat_capacity" in df.columns:
    # Heat capacity data
    print("Processing heat capacity data")
else:
    print("Unknown measurement type")
```

### Empty or Invalid Data

**Problem**: File loads but contains no useful data.

**Solutions**:

1. **Check data dimensions**:
```python
import polars as pl
df = pl.from_arrow(table)
print(f"Data shape: {df.shape}")
print(f"Data types: {df.dtypes}")
```

2. **Examine metadata**:
```python
metadata, table = pyhfm.read_hfm("file.tst", return_metadata=True)
print("Metadata keys:", metadata.keys())
print("Number of setpoints:", metadata.get('number_of_setpoints', 0))
```

3. **Check for null values**:
```python
null_counts = df.null_count()
print("Null values per column:", null_counts)
```

### Unexpected Data Values

**Problem**: Data contains unrealistic values (negative thermal conductivity, etc.).

**Solutions**:

1. **Data validation**:
```python
def validate_thermal_conductivity(df):
    if "upper_thermal_conductivity" in df.columns:
        tc_col = df["upper_thermal_conductivity"]

        # Check for negative values
        negative_count = (tc_col < 0).sum()
        if negative_count > 0:
            print(f"Warning: {negative_count} negative thermal conductivity values")

        # Check for unrealistic values
        very_high = (tc_col > 1000).sum()  # Adjust threshold as needed
        if very_high > 0:
            print(f"Warning: {very_high} unusually high thermal conductivity values")

validate_thermal_conductivity(df)
```

2. **Filter invalid data**:
```python
import polars as pl

# Remove invalid thermal conductivity values
if "upper_thermal_conductivity" in df.columns:
    clean_df = df.filter(
        (pl.col("upper_thermal_conductivity") > 0) &
        (pl.col("upper_thermal_conductivity") < 100)  # Adjust upper limit
    )
    print(f"Removed {df.height - clean_df.height} invalid rows")
```

## Performance Issues

### Slow File Loading

**Problem**: Large files take very long to load.

**Solutions**:

1. **Check file size**:
```bash
ls -lh large_file.tst
```

2. **Monitor memory usage**:
```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory before: {process.memory_info().rss / 1024 / 1024:.1f} MB")

table = pyhfm.read_hfm("large_file.tst")

print(f"Memory after: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

3. **Use streaming for very large files**:
```python
# For extremely large files, consider processing in chunks
# (This would require custom implementation based on file structure)
```

### Memory Issues

**Problem**: Out of memory errors with large files.

**Solutions**:

1. **Increase available memory**:
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS
```

2. **Process smaller chunks**:
```python
# If file structure allows, process subsets
# This depends on the specific file format and requirements
```

## CLI Issues

### Command Not Found

**Problem**: `pyhfm` command not found after installation.

**Solutions**:

1. **Check installation**:
```bash
pip show pyhfm
```

2. **Use module syntax**:
```bash
python -m pyhfm.api.loaders file.tst
```

3. **Check PATH**:
```bash
echo $PATH
```

### CLI Argument Issues

**Problem**: CLI arguments not working as expected.

**Solutions**:

1. **Check help**:
```bash
pyhfm --help
```

2. **Use full argument names**:
```bash
# Instead of short forms, use full names
pyhfm file.tst --format csv --output result.csv
```

## Integration Issues

### Polars Compatibility

**Problem**: Issues with Polars DataFrame operations.

**Solutions**:

1. **Check Polars version**:
```python
import polars as pl
print(f"Polars version: {pl.__version__}")
```

2. **Convert explicitly**:
```python
# Ensure proper conversion
import polars as pl
df = pl.from_arrow(table)
print(f"DataFrame type: {type(df)}")
```

### PyArrow Compatibility

**Problem**: PyArrow table operations failing.

**Solutions**:

1. **Check PyArrow version**:
```python
import pyarrow as pa
print(f"PyArrow version: {pa.__version__}")
```

2. **Verify table structure**:
```python
print(f"Table schema: {table.schema}")
print(f"Table shape: {table.shape}")
```

## Getting Help

### Enable Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Now run your pyhfm operations
table = pyhfm.read_hfm("problem_file.tst")
```

### Collect System Information

```python
import sys
import platform
import pyhfm

print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"pyhfm version: {pyhfm.__version__}")

# Check dependencies
import polars as pl
import pyarrow as pa
print(f"Polars version: {pl.__version__}")
print(f"PyArrow version: {pa.__version__}")
```

### Create Minimal Example

When reporting issues, create a minimal example:

```python
import pyhfm

# Minimal code that reproduces the issue
try:
    table = pyhfm.read_hfm("problem_file.tst")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
```

## Common Workarounds

### Fallback for Encoding Issues

```python
def robust_read_hfm(filename):
    """Robust HFM file reading with multiple fallbacks."""
    encodings = ["utf-16le", "utf-8", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            config = {"default_encoding": encoding}
            table = pyhfm.read_hfm(filename, config=config)
            print(f"Successfully read with encoding: {encoding}")
            return table
        except Exception as e:
            print(f"Failed with {encoding}: {e}")
            continue

    raise ValueError(f"Could not read {filename} with any encoding")
```

### Custom Error Handling

```python
import pyhfm

def safe_read_hfm(filename):
    """Safe HFM reading with comprehensive error handling."""
    try:
        return pyhfm.read_hfm(filename)
    except pyhfm.HFMFileError:
        print(f"File access issue: {filename}")
        return None
    except pyhfm.HFMParsingError:
        print(f"Parsing issue: {filename}")
        return None
    except pyhfm.HFMValidationError:
        print(f"Validation issue: {filename}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

## Still Having Issues?

If you're still experiencing problems:

1. **Check the [GitHub Issues](https://github.com/GraysonBellamy/pyhfm/issues)** for similar problems
2. **Create a new issue** with:
   - Your system information
   - The exact error message
   - A minimal code example
   - Sample file (if possible to share)
3. **Contact the maintainers** through the GitHub repository

Remember to include relevant system information and error messages when seeking help!
