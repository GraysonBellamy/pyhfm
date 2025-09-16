"""Utility functions to replace labetl dependencies."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import chardet
import pyarrow as pa


def detect_encoding(file_path: str) -> str:
    """Detect the encoding of a text file.

    Args:
        file_path: Path to the file to analyze

    Returns:
        Detected encoding name (e.g., "utf-8", "ascii", "iso-8859-1")
        Returns "utf-8" as fallback if detection fails
    """
    try:
        with Path(file_path).open("rb") as f:
            # Read a sample of the file for encoding detection
            raw_data = f.read(8192)  # Read first 8KB

        if not raw_data:
            # Empty file, default to utf-8
            return "utf-8"

        result = chardet.detect(raw_data)

        if result and result["encoding"]:
            confidence = result.get("confidence", 0)
            # Only trust high-confidence detections
            if confidence > 0.7:
                encoding = result["encoding"]
                if isinstance(encoding, str):
                    return encoding.lower()

    except Exception:
        # If anything goes wrong, fall back to utf-8
        # We intentionally ignore exceptions here as encoding detection
        # should be best-effort with graceful fallback
        return "utf-8"

    # Fallback to utf-8 if confidence is low or detection failed
    return "utf-8"


def get_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal SHA-256 hash string

    Raises:
        OSError: If file cannot be read
    """
    sha256_hash = hashlib.sha256()

    with Path(file_path).open("rb") as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def set_metadata(
    table: pa.Table,
    tbl_meta: dict[str, Any] | None = None,
    col_meta: dict[str, Any] | None = None,
) -> pa.Table:
    """Set metadata on a PyArrow table.

    Args:
        table: PyArrow table to add metadata to
        tbl_meta: Table-level metadata to add
        col_meta: Column-level metadata to add (column name -> metadata dict)

    Returns:
        New PyArrow table with metadata attached
    """
    # Start with existing metadata
    new_schema = table.schema

    # Add table-level metadata
    if tbl_meta:
        # Convert to JSON bytes as required by PyArrow
        metadata = {k: json.dumps(v).encode() for k, v in tbl_meta.items()}
        new_schema = new_schema.with_metadata(metadata)

    # Add column-level metadata
    if col_meta:
        fields = []
        for field in new_schema:
            field_name = field.name
            if field_name in col_meta:
                # Convert column metadata to JSON bytes
                col_metadata: dict[str | bytes, str | bytes] = {
                    str(k): json.dumps(v).encode()
                    for k, v in col_meta[field_name].items()
                }
                new_field = field.with_metadata(col_metadata)
            else:
                new_field = field
            fields.append(new_field)
        new_schema = pa.schema(
            fields,
            metadata=cast("dict[bytes | str, bytes | str] | None", new_schema.metadata),
        )

    # Return new table with updated schema
    return table.cast(new_schema)
