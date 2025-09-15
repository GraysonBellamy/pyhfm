"""Basic usage examples for PyHFM package."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

import pyhfm


def basic_reading_example() -> None:
    """Demonstrate basic HFM file reading."""
    print("=== Basic HFM File Reading ===")

    # Example file path (replace with your actual file)
    file_path = "path/to/your/hfm_file.tst"

    try:
        # Basic usage - returns PyArrow table with embedded metadata
        table = pyhfm.read_hfm(file_path)

        print(f"Loaded HFM data with {len(table)} rows")
        print(f"Columns: {table.column_names}")
        print()

        # Convert to polars for easier viewing
        df = table.to_polars()
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

    file_path = "path/to/your/hfm_file.tst"

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
        for setpoint_name, setpoint_data in setpoints.items():
            print(f"  {setpoint_name}:")
            if "temperature" in setpoint_data:
                temp_data = setpoint_data["temperature"]
                if "upper" in temp_data and "lower" in temp_data:
                    upper_temp = temp_data["upper"]
                    lower_temp = temp_data["lower"]
                    print(
                        f"    Temperature range: {lower_temp['value']} - {upper_temp['value']} {upper_temp['unit']}"
                    )
        print()

    except Exception as e:
        print(f"Error: {e}")


def custom_configuration_example() -> None:
    """Demonstrate using custom configuration."""
    print("=== Custom Configuration ===")

    file_path = "path/to/your/hfm_file.tst"

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

    # Create parser instance with custom configuration
    parser = pyhfm.HFMParser(config={"default_encoding": "utf-16le"})

    file_path = "path/to/your/hfm_file.tst"

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

    file_path = "path/to/your/hfm_file.tst"

    try:
        table = pyhfm.read_hfm(file_path)

        # Export to CSV
        df = table.to_polars()
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
        df.to_json(json_path, orient="records", indent=2)
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
        pyhfm.read_hfm("wrong_format.txt")
    except pyhfm.HFMUnsupportedFormatError as e:
        print(f"Caught format error: {e}")

    # Example 3: General HFM error handling
    try:
        pyhfm.read_hfm("potentially_problematic_file.tst")
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
        "Note: Replace 'path/to/your/hfm_file.tst' with actual file paths to run these examples."
    )


if __name__ == "__main__":
    main()
