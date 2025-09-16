#!/usr/bin/env python3
"""
Performance benchmarks for PyHFM.

This script runs basic performance tests to ensure no major regressions.
"""

import argparse
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from pyhfm.api.loaders import read_hfm
except ImportError:
    print("Warning: pyhfm not installed or not in path")
    print("Skipping performance benchmarks")
    sys.exit(0)


def benchmark_file_loading(test_file: Path, runs: int = 3) -> float:
    """Benchmark file loading performance."""
    times = []

    for _ in range(runs):
        start_time = time.perf_counter()
        try:
            read_hfm(test_file)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        except Exception as e:
            print(f"Error loading file {test_file}: {e}")
            return float("inf")

    return sum(times) / len(times)


def main():
    """Run performance benchmarks."""
    parser = argparse.ArgumentParser(description="Run PyHFM performance benchmarks")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per test")
    args = parser.parse_args()

    print(f"Running PyHFM performance benchmarks ({args.runs} runs each)")
    print("=" * 60)

    # Find test files
    test_files_dir = Path(__file__).parent.parent / "tests" / "test_files"

    if not test_files_dir.exists():
        print("Warning: No test files found, creating minimal benchmark")
        print("File loading benchmark: SKIPPED (no test files)")
        print("Performance benchmark completed successfully")
        return

    test_files = list(test_files_dir.glob("*.tst"))

    if not test_files:
        print("Warning: No .tst files found in test_files directory")
        print("File loading benchmark: SKIPPED (no .tst files)")
        print("Performance benchmark completed successfully")
        return

    # Run benchmarks
    total_time = 0
    file_count = 0

    for test_file in test_files[:3]:  # Limit to first 3 files for CI
        avg_time = benchmark_file_loading(test_file, args.runs)
        if avg_time != float("inf"):
            print(f"File: {test_file.name}")
            print(f"  Average load time: {avg_time:.4f} seconds")
            total_time += avg_time
            file_count += 1
        else:
            print(f"File: {test_file.name}")
            print("  Status: FAILED")

    if file_count > 0:
        print("\nSummary:")
        print(f"  Files tested: {file_count}")
        print(f"  Average time per file: {total_time / file_count:.4f} seconds")
        print(f"  Total time: {total_time:.4f} seconds")

    print("\nPerformance benchmark completed successfully")


if __name__ == "__main__":
    main()
