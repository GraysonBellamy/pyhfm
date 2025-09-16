"""PyHFM - Python package for reading and analyzing Heat Flow Meter (HFM) data files.

This package provides tools for parsing HFM data files and extracting measurement
data for thermal conductivity and volumetric heat capacity measurements.

Main functionality:
    - read_hfm(): Primary function for reading HFM files
    - HFMParser: Core parser class for advanced usage
    - DataExtractor: Data extraction utilities
    - Custom exceptions for comprehensive error handling

Example:
    >>> import pyhfm
    >>> import polars as pl
    >>> table = pyhfm.read_hfm("sample.tst")
    >>> print(pl.from_arrow(table))

    >>> # Access metadata
    >>> metadata, table = pyhfm.read_hfm("sample.tst", return_metadata=True)
    >>> print(f"Sample: {metadata['sample_id']}, Type: {metadata['type']}")
"""

from __future__ import annotations

# Public API exports
from .api.loaders import read_hfm
from .constants import (
    DEFAULT_COLUMN_CONFIG,
    DEFAULT_PARSING_CONFIG,
    DEFAULT_VALIDATION_CONFIG,
    FileMetadata,
    HFMType,
)
from .core.file_parser import FileParser as HFMParser
from .exceptions import (
    HFMDataExtractionError,
    HFMError,
    HFMFileError,
    HFMMetadataError,
    HFMParsingError,
    HFMUnsupportedFormatError,
    HFMValidationError,
)
from .extractors.data_extractor import DataExtractor

# Version information
__version__ = "0.1.0"
__author__ = "Grayson Bellamy"
__email__ = "gbellamy@umd.edu"

# Define public API
__all__ = [
    "DEFAULT_COLUMN_CONFIG",
    "DEFAULT_PARSING_CONFIG",
    "DEFAULT_VALIDATION_CONFIG",
    "DataExtractor",
    "FileMetadata",
    "HFMDataExtractionError",
    "HFMError",
    "HFMFileError",
    "HFMMetadataError",
    "HFMParser",
    "HFMParsingError",
    "HFMType",
    "HFMUnsupportedFormatError",
    "HFMValidationError",
    "__author__",
    "__email__",
    "__version__",
    "read_hfm",
]
