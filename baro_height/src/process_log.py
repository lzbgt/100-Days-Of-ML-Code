#!/usr/bin/env python3
import argparse
import sys
import os

# Add parent directory to path to import local modules if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from baro_height.src.height_calculator import BaroHeightCalculator
from baro_height.extract_baro import parse_file
from pathlib import Path
import statistics

def process_log_file(filepath: Path, baseline_samples: int = 10, scale: float = 1.0, output_csv: Path = None):
    """
    Process a log file and calculate heights.
    """
    calculator = BaroHeightCalculator(scale=scale)

    readings = list(parse_file(filepath))

    if not readings:
        print(f"No readings found in {filepath}")
        return

    # Sort by timestamp
    readings.sort(key=lambda x: x["timestamp"])

    # We might have multiple tags in the log file.
    # For simplicity, let's process each tag separately.
    readings_by_tag = {}
    for r in readings:
        readings_by_tag.setdefault(r["addr"], []).append(r)

    for tag, tag_readings in readings_by_tag.items():
        print(f"Processing tag: {tag}")

        # Take first N samples to baseline
        baseline_readings = tag_readings[:baseline_samples]
        if not baseline_readings:
            continue

        avg_p = statistics.mean([float(r["pressure_pa"]) for r in baseline_readings])
        avg_t = statistics.mean([float(r["temperature_c"]) for r in baseline_readings])

        calculator.reset_zero(avg_p, avg_t)

        print(f"  Baseline set using first {len(baseline_readings)} samples.")
        print(f"  Ref Pressure: {avg_p:.2f} Pa, Ref Temp: {avg_t:.2f} C")

        results = []
        for r in tag_readings:
            p = float(r["pressure_pa"])
            t = float(r["temperature_c"])
            h = calculator.calculate_height(p, t)
            results.append({
                "timestamp": r["timestamp"],
                "addr": tag,
                "pressure_pa": p,
                "temperature_c": t,
                "height_m": h
            })

        # If output CSV is specified, write to it
        if output_csv:
            import csv
            # If multiple tags, we might want to append or write separate files.
            # For now, let's just append or write to one file.
            mode = 'a' if output_csv.exists() else 'w'
            with open(output_csv, mode, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "addr", "pressure_pa", "temperature_c", "height_m"])
                if mode == 'w':
                    writer.writeheader()
                writer.writerows(results)
            print(f"  Wrote results to {output_csv}")
        else:
            # Print last few results
            print("  Last 5 readings:")
            for res in results[-5:]:
                print(f"    {res['timestamp']}: {res['height_m']:.3f} m")

def main():
    parser = argparse.ArgumentParser(description="Calculate height from log files.")
    parser.add_argument("logfile", type=Path, help="Path to the log file.")
    parser.add_argument("--scale", type=float, default=1.0, help="Calibration scale factor.")
    parser.add_argument("--baseline-samples", type=int, default=10, help="Number of samples to use for baseline.")
    parser.add_argument("--output", type=Path, default=None, help="Output CSV file.")

    args = parser.parse_args()

    if args.output and args.output.exists():
        # Clear output file if it exists to avoid appending to old runs
        # unless we were processing multiple files in a loop (which we are not here)
        os.remove(args.output)

    process_log_file(args.logfile, args.baseline_samples, args.scale, args.output)

if __name__ == "__main__":
    main()
