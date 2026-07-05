---
description: pyhfm is a Python package for reading and analyzing Heat Flow Meter (HFM) data files, extracting thermal conductivity and volumetric heat capacity measurements into PyArrow tables.
---

# pyhfm

pyhfm is a Python package for reading and analyzing Heat Flow Meter (HFM) data
files. It provides a clean, modern API for parsing HFM measurement data and
extracting thermal conductivity and volumetric heat capacity measurements,
with comprehensive metadata extraction built on PyArrow.

## Install

```bash
pip install pyhfm
```

## Quick Example

```python
import pyhfm

# Read an HFM file and get a PyArrow table
table = pyhfm.read_hfm("sample.tst")

# Convert to a polars DataFrame for analysis
import polars as pl
df = pl.from_arrow(table)
print(df.head())
```

## What You Can Do

- Parse HFM test files (`.tst`) with a simple `read_hfm()` function
- Extract thermal conductivity and volumetric heat capacity measurements
- Access rich, validated metadata alongside the measurement data
- Handle UTF-16LE (default), UTF-8, and auto-detected encodings
- Convert files to CSV, Parquet, or JSON from the command line

## Start Here

- [Getting Started](getting-started.md)
- [User Guide](user-guide.md)
- [API Reference](api-reference.md)
- [Troubleshooting](troubleshooting.md)
- [Contributing](contributing.md)
