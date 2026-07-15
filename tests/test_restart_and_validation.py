"""Tests for restarted-run handling, setpoint-count validation, and signed values.

Covers two bugs found while auditing conductivity processing:

1. When an interrupted test is restarted, WinTherm appends the remaining
   setpoints to the same .tst file with numbering that starts over from 1.
   Setpoints must be keyed by order of appearance so second-pass blocks do
   not overwrite same-numbered first-pass blocks.
2. Negative values (e.g. ``Temperature Upper: -0.02 °C`` at a 0 °C setpoint)
   must keep their sign when parsed.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import pytest

from pyhfm import HFMValidationWarning, read_hfm
from pyhfm.constants import HFMParsingConfig
from pyhfm.core.setpoint_parser import SetpointParser

TEST_FILES = Path(__file__).parent / "test_files"
RESTART_FILE = TEST_FILES / "RO_HFM_Oven_Resurfaced_Conductivity_240910_S12.tst"


def _write_conductivity_file(
    path: Path,
    declared_setpoints: int,
    blocks: list[tuple[int, str, str, str, str]],
) -> Path:
    """Write a minimal UTF-16LE conductivity file with given summary blocks.

    Each block is (setpoint_number, upper_temp, lower_temp, upper_k, lower_k).
    """
    lines = [
        "\tSunday, January 01, 2023, Time 10:00",
        "",
        "\tSample Name: TEST_SAMPLE",
        "\tThickness: 25.40 mm",
        "",
        "\tRun Mode: Thermal Conductivity",
        "",
        f"\tNumber of Setpoints: {declared_setpoints}",
        "",
    ]
    for number, upper_temp, lower_temp, upper_k, lower_k in blocks:
        lines += [
            f"\tSetpoint No.\t{number}",
            f"\t    Temperature Upper:\t{upper_temp}\t°C",
            f"\t    Results Upper:\t\t{upper_k}\tW/mK",
            f"\t    Temperature Lower:\t{lower_temp}\t°C",
            f"\t    Results Lower:\t\t{lower_k}\tW/mK",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-16le")
    return path


class TestRestartedRuns:
    """Setpoints from restarted (resumed) runs must all survive parsing."""

    def test_restart_file_recovers_all_setpoints(self) -> None:
        """The S12 restart file yields all 7 setpoints, not 4."""
        with pytest.warns(HFMValidationWarning, match="numbering restarted"):
            metadata, table = read_hfm(RESTART_FILE, return_metadata=True)

        assert metadata["number_of_setpoints"] == 7
        assert table.num_rows == 7
        assert table["setpoint"].to_pylist() == [1, 2, 3, 4, 5, 6, 7]

        # First pass (blocks numbered 1-4) then second pass (blocks 1-3)
        assert table["upper_temperature"].to_pylist() == [
            0.01,
            10.00,
            20.01,
            30.01,
            40.01,
            50.01,
            55.01,
        ]
        # Temperature/conductivity pairing must stay intact across the restart
        assert table["upper_thermal_conductivity"].to_pylist() == [
            0.1254,
            0.1282,
            0.1325,
            0.1378,
            0.1420,
            0.1446,
            0.1436,
        ]
        assert table["lower_temperature"].to_pylist() == [
            20.00,
            30.01,
            40.02,
            50.01,
            60.01,
            70.01,
            75.01,
        ]

        # The instrument's own numbering (1,2,3,4,1,2,3) is preserved
        instrument_numbers = [
            metadata["setpoints"][f"setpoint_{n}"]["instrument_setpoint_number"]
            for n in range(1, 8)
        ]
        assert instrument_numbers == [1, 2, 3, 4, 1, 2, 3]

    def test_synthesized_two_pass_file(self, tmp_path: Path) -> None:
        """A two-pass file with numbering 1,2,1,2 yields four distinct rows."""
        test_file = _write_conductivity_file(
            tmp_path / "restart.tst",
            declared_setpoints=4,
            blocks=[
                (1, "0.01", "20.00", "0.1254", "0.1443"),
                (2, "10.00", "30.01", "0.1282", "0.1447"),
                (1, "20.01", "40.02", "0.1325", "0.1444"),
                (2, "30.01", "50.01", "0.1378", "0.1436"),
            ],
        )

        with pytest.warns(HFMValidationWarning, match="numbering restarted"):
            table = read_hfm(test_file)

        assert table.num_rows == 4
        assert table["setpoint"].to_pylist() == [1, 2, 3, 4]
        assert table["upper_temperature"].to_pylist() == [0.01, 10.00, 20.01, 30.01]

    def test_normal_file_parses_without_warning(self, tmp_path: Path) -> None:
        """A complete single-pass file emits no validation warning."""
        test_file = _write_conductivity_file(
            tmp_path / "normal.tst",
            declared_setpoints=2,
            blocks=[
                (1, "25.00", "15.00", "0.15", "0.14"),
                (2, "35.00", "25.00", "0.16", "0.15"),
            ],
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error", HFMValidationWarning)
            table = read_hfm(test_file)

        assert table.num_rows == 2
        assert table["setpoint"].to_pylist() == [1, 2]


class TestSetpointCountValidation:
    """Declared vs. parsed setpoint counts are validated."""

    def test_declared_count_mismatch_warns(self, tmp_path: Path) -> None:
        """A file declaring 3 setpoints but containing 2 blocks warns."""
        test_file = _write_conductivity_file(
            tmp_path / "truncated.tst",
            declared_setpoints=3,
            blocks=[
                (1, "25.00", "15.00", "0.15", "0.14"),
                (2, "35.00", "25.00", "0.16", "0.15"),
            ],
        )

        with pytest.warns(
            HFMValidationWarning, match="declares 3 setpoints but 2 were parsed"
        ):
            table = read_hfm(test_file)

        assert table.num_rows == 2


class TestSignedValueParsing:
    """Negative values must keep their sign."""

    def test_negative_temperature_survives_end_to_end(self, tmp_path: Path) -> None:
        """A summary block at a 0 °C setpoint reading -0.02 °C keeps its sign."""
        test_file = _write_conductivity_file(
            tmp_path / "negative.tst",
            declared_setpoints=1,
            blocks=[(1, "-0.02", "19.98", "0.1254", "0.1443")],
        )

        table = read_hfm(test_file)

        assert table.num_rows == 1
        assert table["upper_temperature"].to_pylist() == [-0.02]
        assert table["lower_temperature"].to_pylist() == [19.98]

    def test_value_pattern_matches_negative_numbers(self) -> None:
        """The shared value pattern preserves a leading minus sign."""
        pattern = HFMParsingConfig().patterns.value_pattern
        match = pattern.search("-0.02\t°C")
        assert match is not None
        assert match.group() == "-0.02"
        # Positive values still parse as before
        positive = pattern.search("20.01\t°C")
        assert positive is not None
        assert positive.group() == "20.01"

    def test_parse_temperature_negative_value(self) -> None:
        """_parse_temperature keeps the sign of sub-zero readings."""
        parser = SetpointParser(HFMParsingConfig())
        metadata: dict[str, Any] = {"setpoints": {"setpoint_1": {}}}

        parser._parse_temperature(
            "Temperature Upper:\t-0.02\t°C", "setpoint_1", metadata, "upper"
        )

        temperature = metadata["setpoints"]["setpoint_1"]["temperature"]["upper"]
        assert temperature["value"] == -0.02
        assert temperature["unit"] == "°C"

    def test_parse_specific_heat_keeps_full_value_and_sign(self) -> None:
        """_parse_specific_heat handles integers, decimals, and signs."""
        parser = SetpointParser(HFMParsingConfig())
        metadata: dict[str, Any] = {"setpoints": {"setpoint_1": {}}}

        # Integer value as written by the instrument
        parser._parse_specific_heat(
            "Specific Heat      :\t598541\tJ/(m³K)", "setpoint_1", metadata
        )
        heat_capacity = metadata["setpoints"]["setpoint_1"]["volumetric_heat_capacity"]
        assert heat_capacity["value"] == 598541.0
        assert heat_capacity["unit"] == "J/(m³K)"

        # Negative decimal value must not be truncated to its integer part
        parser._parse_specific_heat(
            "Specific Heat      :\t-1234.56\tJ/(m³K)", "setpoint_1", metadata
        )
        heat_capacity = metadata["setpoints"]["setpoint_1"]["volumetric_heat_capacity"]
        assert heat_capacity["value"] == -1234.56
        assert heat_capacity["unit"] == "J/(m³K)"
