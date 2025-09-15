"""Main API for loading HFM data files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast, overload

import pyarrow as pa

if TYPE_CHECKING:
    from pyhfm.constants import FileMetadata

from pyhfm.core.parser import HFMParser
from pyhfm.exceptions import HFMError


@overload
def read_hfm(
    file_path: str | Path,
    *,
    return_metadata: Literal[False] = False,
    config: dict[str, Any] | None = None,
) -> pa.Table: ...


@overload
def read_hfm(
    file_path: str | Path,
    *,
    return_metadata: Literal[True],
    config: dict[str, Any] | None = None,
) -> tuple[FileMetadata, pa.Table]: ...


def read_hfm(
    file_path: str | Path,
    *,
    return_metadata: bool = False,
    config: dict[str, Any] | None = None,
) -> pa.Table | tuple[FileMetadata, pa.Table]:
    """Read and parse an HFM data file.

    This is the main entry point for reading Heat Flow Meter (HFM) data files.
    The function returns a PyArrow table with embedded metadata by default, or
    optionally returns a tuple of (metadata, table) for more detailed access.

    Args:
        file_path: Path to the HFM file (.tst format)
        return_metadata: If True, return (metadata, table) tuple instead of just table
        config: Optional configuration overrides for parsing

    Returns:
        PyArrow table with embedded metadata, or tuple of (metadata, table)
        if return_metadata=True

    Raises:
        HFMFileError: If file cannot be read or doesn't exist
        HFMParsingError: If file parsing fails
        HFMUnsupportedFormatError: If file format is not supported
        HFMValidationError: If data validation fails

    Examples:
        Basic usage:
        >>> table = read_hfm("sample.tst")
        >>> print(table.schema)
        >>> print(table.to_pandas())

        Access metadata separately:
        >>> metadata, table = read_hfm("sample.tst", return_metadata=True)
        >>> print(metadata["sample_id"])
        >>> print(metadata["type"])

        Custom configuration:
        >>> config = {"default_encoding": "utf-8"}
        >>> table = read_hfm("sample.tst", config=config)
    """
    try:
        # Initialize parser with optional config
        parser = HFMParser(config)

        # Parse the file
        table = parser.parse_file(file_path)

        if return_metadata:
            # Extract metadata from table
            table_metadata = table.schema.metadata
            if table_metadata and b"file_metadata" in table_metadata:
                # Deserialize the metadata from JSON bytes
                file_metadata_bytes = table_metadata[b"file_metadata"]
                file_metadata = json.loads(file_metadata_bytes.decode("utf-8"))
                return file_metadata, table
            # Fallback - re-parse to get metadata
            metadata_parser = HFMParser(config)
            metadata_table = metadata_parser.parse_file(file_path)
            metadata_dict = metadata_table.schema.metadata
            if metadata_dict and b"file_metadata" in metadata_dict:
                file_metadata_bytes = metadata_dict[b"file_metadata"]
                file_metadata = json.loads(file_metadata_bytes.decode("utf-8"))
                return file_metadata, table
            return {}, table

        return table

    except HFMError:
        # Re-raise HFM-specific errors as-is
        raise
    except Exception as e:
        # Wrap unexpected errors
        error_msg = f"Unexpected error reading HFM file: {e}"
        raise HFMError(error_msg, str(file_path)) from e


def main() -> None:
    """Command-line interface for reading HFM files.

    Usage:
        pyhfm <file_path> [options]
    """
    parser = argparse.ArgumentParser(description="Read and parse HFM data files")
    parser.add_argument("file_path", help="Path to HFM file")
    parser.add_argument(
        "--output", "-o", help="Output file path (default: print to stdout)"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "parquet", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--metadata", "-m", action="store_true", help="Also output metadata information"
    )
    parser.add_argument(
        "--encoding", help="File encoding override (default: auto-detect)"
    )

    args = parser.parse_args()

    try:
        # Prepare config
        config = {}
        if args.encoding:
            config["default_encoding"] = args.encoding

        # Read the file
        metadata: dict[str, Any] | None = None
        if args.metadata:
            file_metadata, table = read_hfm(
                args.file_path, return_metadata=True, config=config if config else None
            )
            metadata = cast("dict[str, Any]", file_metadata)
        else:
            table = read_hfm(args.file_path, config=config if config else None)

        # Handle output
        _handle_output(args, table, metadata)

    except HFMError as e:
        error_msg = f"Error: {e}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)


def _handle_output(
    args: argparse.Namespace, table: Any, metadata: dict[str, Any] | None
) -> None:
    """Handle output writing for the CLI."""
    if args.output:
        _write_output_file(args, table, metadata)
    else:
        _print_to_stdout(args, table, metadata)


def _write_output_file(
    args: argparse.Namespace, table: Any, metadata: dict[str, Any] | None
) -> None:
    """Write output to file."""
    output_path = Path(args.output)

    if args.format == "parquet":
        import pyarrow.parquet as pq  # noqa: PLC0415

        pq.write_table(table, output_path)
    elif args.format == "csv":
        table.to_pandas().to_csv(output_path, index=False)
    elif args.format == "json":
        table.to_pandas().to_json(output_path, orient="records", indent=2)

    print(f"Data written to {output_path}")

    if metadata is not None:
        metadata_path = output_path.with_suffix(".metadata.json")
        with metadata_path.open("w") as f:
            json.dump(metadata, f, indent=2, default=str)
        print(f"Metadata written to {metadata_path}")


def _print_to_stdout(
    args: argparse.Namespace, table: Any, metadata: dict[str, Any] | None
) -> None:
    """Print output to stdout."""
    if args.format == "csv":
        print(table.to_pandas().to_csv(index=False))
    elif args.format == "json":
        print(table.to_pandas().to_json(orient="records", indent=2))
    else:
        print(table.to_pandas())

    if metadata is not None:
        print("\n--- METADATA ---")
        print(json.dumps(metadata, indent=2, default=str))


if __name__ == "__main__":
    main()
