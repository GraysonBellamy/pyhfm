"""Basic usage examples for PyHFM package."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

import pyhfm


def basic_reading_example() -> None:
    """Demonstrate basic HFM file reading."""
    print("=== Basic HFM File Reading ===")

    # Find a test file to use as example
    test_files = list(Path("tests/test_files").glob("*.tst"))
    if not test_files:
        print(
            "⚠️  No test files found. Place HFM files in tests/test_files/ to run this example."
        )
        return

    file_path = test_files[0]
    print(f"Using example file: {file_path.name}")

    try:
        # Basic usage - returns PyArrow table with embedded metadata
        table = pyhfm.read_hfm(file_path)

        print(f"Loaded HFM data with {len(table)} rows")
        print(f"Columns: {table.column_names}")
        print()

        # Convert to polars for easier viewing
        df = pl.from_arrow(table)
        print("Data preview:")
        print(df.head())
        print()

    except pyhfm.HFMFileError as e:
        print(f"File error: {e}")
    except pyhfm.HFMParsingError as e:
        print(f"Parsing error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def metadata_access_example() -> None:
    """Demonstrate accessing metadata separately."""
    print("=== Accessing Metadata ===")

    # Find a test file to use as example
    test_files = list(Path("tests/test_files").glob("*.tst"))
    if not test_files:
        print(
            "⚠️  No test files found. Place HFM files in tests/test_files/ to run this example."
        )
        return

    file_path = test_files[0]
    print(f"Using example file: {file_path.name}")

    try:
        # Get both metadata and data
        metadata, _table = pyhfm.read_hfm(file_path, return_metadata=True)

        print("Sample metadata:")
        print(f"  Sample ID: {metadata.get('sample_id', 'N/A')}")
        print(f"  Measurement type: {metadata.get('type', 'N/A')}")
        print(f"  Date performed: {metadata.get('date_performed', 'N/A')}")
        print(f"  Number of setpoints: {metadata.get('number_of_setpoints', 'N/A')}")
        print()

        # Access setpoint information
        setpoints = metadata.get("setpoints", {})
        print(f"Found {len(setpoints)} setpoints:")
        for setpoint_name, setpoint_data in list(setpoints.items())[:3]:  # Show first 3
            print(f"  {setpoint_name}:")
            if isinstance(setpoint_data, dict) and "temperature" in setpoint_data:
                temp_data = setpoint_data["temperature"]
                if (
                    isinstance(temp_data, dict)
                    and "upper" in temp_data
                    and "lower" in temp_data
                ):
                    upper_temp = temp_data["upper"]
                    lower_temp = temp_data["lower"]
                    if isinstance(upper_temp, dict) and isinstance(lower_temp, dict):
                        print(
                            f"    Temperature range: {lower_temp.get('value', 'N/A')} - {upper_temp.get('value', 'N/A')} {upper_temp.get('unit', 'N/A')}"
                        )
        print()

    except Exception as e:
        print(f"Error: {e}")


def custom_configuration_example() -> None:
    """Demonstrate using custom configuration."""
    print("=== Custom Configuration ===")

    # Find a test file to use as example
    test_files = list(Path("tests/test_files").glob("*.tst"))
    if not test_files:
        print(
            "⚠️  No test files found. Place HFM files in tests/test_files/ to run this example."
        )
        return

    file_path = test_files[0]
    print(f"Using example file: {file_path.name}")

    # Custom configuration
    config = {
        "default_encoding": "utf-8",  # Override default encoding
    }

    try:
        table = pyhfm.read_hfm(file_path, config=config)
        print(f"Successfully loaded with custom config: {len(table)} rows")
        print()

    except Exception as e:
        print(f"Error with custom config: {e}")


def advanced_parser_usage() -> None:
    """Demonstrate advanced parser usage."""
    print("=== Advanced Parser Usage ===")

    # Find a test file to use as example
    test_files = list(Path("tests/test_files").glob("*.tst"))
    if not test_files:
        print(
            "⚠️  No test files found. Place HFM files in tests/test_files/ to run this example."
        )
        return

    file_path = test_files[0]
    print(f"Using example file: {file_path.name}")

    # Create parser instance with custom configuration
    parser = pyhfm.HFMParser(config={"default_encoding": "utf-16le"})

    try:
        # Parse file directly
        table = parser.parse_file(file_path)

        print(f"Parsed with custom parser: {len(table)} rows")
        print(f"Schema: {table.schema}")
        print()

    except Exception as e:
        print(f"Parser error: {e}")


def data_export_example() -> None:
    """Demonstrate exporting data to different formats."""
    print("=== Data Export Examples ===")

    # Find a test file to use as example
    test_files = list(Path("tests/test_files").glob("*.tst"))
    if not test_files:
        print(
            "⚠️  No test files found. Place HFM files in tests/test_files/ to run this example."
        )
        return

    file_path = test_files[0]
    print(f"Using example file: {file_path.name}")

    try:
        table = pyhfm.read_hfm(file_path)

        # Export to CSV
        df = pl.from_arrow(table)
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        csv_path = output_dir / "hfm_data.csv"
        df.write_csv(csv_path)
        print(f"Exported to CSV: {csv_path}")

        # Export to Parquet (preserves metadata)
        parquet_path = output_dir / "hfm_data.parquet"
        pq.write_table(table, parquet_path)
        print(f"Exported to Parquet: {parquet_path}")

        # Export to JSON
        json_path = output_dir / "hfm_data.json"
        df.write_json(json_path)
        print(f"Exported to JSON: {json_path}")
        print()

    except Exception as e:
        print(f"Export error: {e}")


def error_handling_example() -> None:
    """Demonstrate comprehensive error handling."""
    print("=== Error Handling Examples ===")

    # Example 1: File not found
    try:
        pyhfm.read_hfm("nonexistent_file.tst")
    except pyhfm.HFMFileError as e:
        print(f"Caught file error: {e}")

    # Example 2: Unsupported format
    try:
        # Create a temporary text file to simulate wrong format
        temp_file = Path("temp_wrong_format.txt")
        temp_file.write_text("This is not an HFM file")
        pyhfm.read_hfm(temp_file)
    except pyhfm.HFMUnsupportedFormatError as e:
        print(f"Caught format error: {e}")
    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()

    # Example 3: General HFM error handling
    try:
        pyhfm.read_hfm("nonexistent_file_2.tst")
    except pyhfm.HFMError as e:
        print(f"Caught HFM error: {e}")
    except Exception as e:
        print(f"Caught unexpected error: {e}")

    print()


def main() -> None:
    """Run all examples."""
    print("PyHFM Usage Examples")
    print("=" * 50)
    print()

    basic_reading_example()
    metadata_access_example()
    custom_configuration_example()
    advanced_parser_usage()
    data_export_example()
    error_handling_example()

    print("Examples complete!")
    print()
    print(
        "Note: This example uses test files from tests/test_files/. "
        "Place your own HFM files there to test with real data."
    )


if __name__ == "__main__":
    main()
