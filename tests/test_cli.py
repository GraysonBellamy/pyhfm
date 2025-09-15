"""Tests for CLI functionality and export functions."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pyarrow.parquet as pq

from pyhfm.api.loaders import _handle_output, _print_to_stdout, _write_output_file, main


class TestCLIFunctions:
    """Test CLI helper functions."""

    def create_sample_table(self) -> pa.Table:
        """Create a sample PyArrow table for testing."""
        data = {
            "setpoint": [1, 2, 3],
            "temperature": [25.0, 30.0, 35.0],
            "conductivity": [0.1, 0.15, 0.2],
        }
        return pa.table(data)

    def create_sample_metadata(self) -> dict[str, str]:
        """Create sample metadata for testing."""
        return {
            "sample_id": "TEST001",
            "date_performed": "2024-01-01T10:00:00+00:00",
            "type": "CONDUCTIVITY",
        }

    @patch("builtins.print")
    def test_print_to_stdout_csv(self, mock_print: MagicMock) -> None:
        """Test printing CSV to stdout."""
        args = argparse.Namespace(format="csv")
        table = self.create_sample_table()
        metadata = self.create_sample_metadata()

        _print_to_stdout(args, table, metadata)

        # Should have printed CSV data and metadata
        assert mock_print.call_count >= 2
        # First call should contain CSV header
        csv_output = mock_print.call_args_list[0][0][0]
        assert "setpoint,temperature,conductivity" in csv_output

    @patch("builtins.print")
    def test_print_to_stdout_json(self, mock_print: MagicMock) -> None:
        """Test printing JSON to stdout."""
        args = argparse.Namespace(format="json")
        table = self.create_sample_table()
        metadata = None

        _print_to_stdout(args, table, metadata)

        # Should have printed JSON data
        mock_print.assert_called_once()
        json_output = mock_print.call_args[0][0]
        assert '"setpoint":1' in json_output or '"setpoint": 1' in json_output

    @patch("builtins.print")
    def test_print_to_stdout_default(self, mock_print: MagicMock) -> None:
        """Test printing default format to stdout."""
        args = argparse.Namespace(format="table")
        table = self.create_sample_table()
        metadata = None

        _print_to_stdout(args, table, metadata)

        # Should have printed table representation
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_print_to_stdout_with_metadata(self, mock_print: MagicMock) -> None:
        """Test printing output with metadata."""
        args = argparse.Namespace(format="csv")
        table = self.create_sample_table()
        metadata = self.create_sample_metadata()

        _print_to_stdout(args, table, metadata)

        # Should have multiple print calls for data and metadata
        assert mock_print.call_count >= 2
        # Check that metadata was printed
        printed_args = [call[0][0] for call in mock_print.call_args_list]
        metadata_found = any("METADATA" in str(arg) for arg in printed_args)
        assert metadata_found

    def test_write_output_file_csv(self) -> None:
        """Test writing CSV output to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            args = argparse.Namespace(format="csv", output=str(output_path))
            table = self.create_sample_table()
            metadata = self.create_sample_metadata()

            with patch("builtins.print"):
                _write_output_file(args, table, metadata)

            # Check that CSV file was created
            assert output_path.exists()
            csv_content = output_path.read_text()
            assert "setpoint,temperature,conductivity" in csv_content
            assert "1,25.0,0.1" in csv_content

            # Check that metadata file was created
            metadata_path = output_path.with_suffix(".metadata.json")
            assert metadata_path.exists()
            metadata_content = json.loads(metadata_path.read_text())
            assert metadata_content["sample_id"] == "TEST001"

    def test_write_output_file_parquet(self) -> None:
        """Test writing Parquet output to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.parquet"
            args = argparse.Namespace(format="parquet", output=str(output_path))
            table = self.create_sample_table()
            metadata = None

            with patch("builtins.print"):
                _write_output_file(args, table, metadata)

            # Check that Parquet file was created
            assert output_path.exists()

            # Verify we can read it back
            read_table = pq.read_table(output_path)
            assert read_table.shape == table.shape

    def test_write_output_file_json(self) -> None:
        """Test writing JSON output to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            args = argparse.Namespace(format="json", output=str(output_path))
            table = self.create_sample_table()
            metadata = None

            with patch("builtins.print"):
                _write_output_file(args, table, metadata)

            # Check that JSON file was created
            assert output_path.exists()
            json_content = json.loads(output_path.read_text())
            assert isinstance(json_content, list)
            assert len(json_content) == 3  # 3 rows
            assert json_content[0]["setpoint"] == 1

    @patch("pyhfm.api.loaders._print_to_stdout")
    def test_handle_output_no_file(self, mock_print: MagicMock) -> None:
        """Test handle_output without output file."""
        args = argparse.Namespace(output=None)
        table = self.create_sample_table()
        metadata = None

        _handle_output(args, table, metadata)

        mock_print.assert_called_once_with(args, table, metadata)

    @patch("pyhfm.api.loaders._write_output_file")
    def test_handle_output_with_file(self, mock_write: MagicMock) -> None:
        """Test handle_output with output file."""
        args = argparse.Namespace(output="test.csv")
        table = self.create_sample_table()
        metadata = None

        _handle_output(args, table, metadata)

        mock_write.assert_called_once_with(args, table, metadata)


class TestMainFunction:
    """Test the main CLI function."""

    def create_sample_table(self) -> pa.Table:
        """Create a sample PyArrow table for testing."""
        data = {
            "setpoint": [1, 2, 3],
            "temperature": [25.0, 30.0, 35.0],
            "conductivity": [0.123, 0.145, 0.167],
        }
        return pa.table(data)

    def create_test_file(self, tmpdir: str) -> Path:
        """Create a test HFM file for CLI testing."""
        test_file = Path(tmpdir) / "test.tst"
        # Create a minimal valid HFM file content
        content = """Date/Time: 01/01/2024 10:00:00
Sample ID: TEST_SAMPLE
Type: Conductivity
Thickness: 25.4 mm

Setpoint,Upper Temperature [°C],Lower Temperature [°C],Upper Thermal Conductivity [W/(mK)],Lower Thermal Conductivity [W/(mK)]
1,25.0,25.2,0.1,0.1
2,30.0,30.1,0.12,0.11
"""
        test_file.write_text(content, encoding="utf-8")
        return test_file

    @patch("builtins.print")
    def test_main_basic_usage(self, mock_print: MagicMock) -> None:
        """Test basic CLI usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = self.create_test_file(tmpdir)

            with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
                mock_args = argparse.Namespace(
                    file_path=str(test_file),
                    output=None,
                    format="csv",
                    metadata=False,
                    encoding=None,
                )
                mock_parse_args.return_value = mock_args

                # Mock the read_hfm function to return a simple table
                with patch("pyhfm.api.loaders.read_hfm") as mock_read_hfm:
                    mock_read_hfm.return_value = self.create_sample_table()

                    # This should not raise an exception
                    main()

                    # Should have called read_hfm and printed something
                    mock_read_hfm.assert_called_once()
                    mock_print.assert_called()

                # Should have printed something
                mock_print.assert_called()

    @patch("sys.argv")
    @patch("sys.exit")
    def test_main_file_not_found(
        self, mock_exit: MagicMock, mock_argv: MagicMock
    ) -> None:
        """Test CLI with non-existent file."""
        mock_argv.__getitem__.side_effect = lambda i: ["pyhfm", "nonexistent.tst"][i]
        mock_argv.__len__.return_value = 2

        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_args = argparse.Namespace(
                file_path="nonexistent.tst",
                output=None,
                format="csv",
                metadata=False,
                encoding=None,
            )
            mock_parse_args.return_value = mock_args

            with patch("builtins.print"):
                main()

            # Should have called sys.exit(1) due to error
            mock_exit.assert_called_with(1)

    @patch("builtins.print")
    def test_main_with_metadata(self, mock_print: MagicMock) -> None:
        """Test CLI with metadata flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = self.create_test_file(tmpdir)

            with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
                mock_args = argparse.Namespace(
                    file_path=str(test_file),
                    output=None,
                    format="csv",
                    metadata=True,
                    encoding=None,
                )
                mock_parse_args.return_value = mock_args

                # Mock the read_hfm function to return table and metadata
                with patch("pyhfm.api.loaders.read_hfm") as mock_read_hfm:
                    mock_read_hfm.return_value = (
                        {"test": "metadata"},
                        self.create_sample_table(),
                    )

                    main()

                    # Should have called read_hfm with return_metadata=True
                    mock_read_hfm.assert_called_once_with(
                        str(test_file), return_metadata=True, config=None
                    )
                    mock_print.assert_called()

                # Should have printed data and metadata
                mock_print.assert_called()

    def test_main_with_output_file(self) -> None:
        """Test CLI with output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = self.create_test_file(tmpdir)
            output_file = Path(tmpdir) / "output.csv"

            with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
                mock_args = argparse.Namespace(
                    file_path=str(test_file),
                    output=str(output_file),
                    format="csv",
                    metadata=False,
                    encoding=None,
                )
                mock_parse_args.return_value = mock_args

                # Mock the read_hfm function
                with patch("pyhfm.api.loaders.read_hfm") as mock_read_hfm:
                    mock_read_hfm.return_value = self.create_sample_table()

                    main()

                    # Should have called read_hfm and created output file
                    mock_read_hfm.assert_called_once()
                    # File should exist
                    assert output_file.exists()

    @patch("builtins.print")
    def test_main_with_custom_encoding(self, mock_print: MagicMock) -> None:
        """Test CLI with custom encoding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = self.create_test_file(tmpdir)

            with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
                mock_args = argparse.Namespace(
                    file_path=str(test_file),
                    output=None,
                    format="csv",
                    metadata=False,
                    encoding="utf-8",
                )
                mock_parse_args.return_value = mock_args

                # Mock the read_hfm function
                with patch("pyhfm.api.loaders.read_hfm") as mock_read_hfm:
                    mock_read_hfm.return_value = self.create_sample_table()

                    # Should not raise an exception
                    main()

                    # Should have called read_hfm with encoding config
                    mock_read_hfm.assert_called_once_with(
                        str(test_file), config={"default_encoding": "utf-8"}
                    )
                    mock_print.assert_called()

    @patch("builtins.print")
    @patch("sys.exit")
    def test_main_unexpected_error(
        self, mock_exit: MagicMock, mock_print: MagicMock
    ) -> None:
        """Test CLI handling of unexpected errors."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            # Simulate an unexpected error during argument parsing
            mock_parse_args.side_effect = RuntimeError("Unexpected error")

            main()

            # Should have called sys.exit(1) and printed error
            mock_exit.assert_called_with(1)
            mock_print.assert_called()
