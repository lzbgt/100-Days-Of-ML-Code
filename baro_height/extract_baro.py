#!/usr/bin/env python3
"""Extract barometer samples (pressure, temperature) from raw gateway logs.

The logs under `data/` contain many packet types; only `IFB_IN` blocks with
`ATMOPRESS` and `TEMPERATURE` are barometer readings. This script walks every
`*.txt` file in the data directory, pulls those fields out, and writes a
single CSV with one row per reading.

Usage (from repo root or `baro_height/`):
  python extract_baro.py                 # writes data/baro_readings.csv
  python extract_baro.py -d custom_dir   # read another directory
  python extract_baro.py -o out.csv      # choose output path
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List

# Grab the leading wall-clock timestamp (keeps original milliseconds).
TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")

# Regex for the new log format
# [17-11-00-24.873]status:0, altitude:92.041279 m,100924.359375 Pa,temp: 67.330704
NEW_LOG_RE = re.compile(r"^\[(\d{2}-\d{2}-\d{2}-\d{2}\.\d{3})\].*?([\d.]+) Pa,temp:\s*([\d.]+)")

# Each IFB_IN block lives on one line; stop at the next ", IFB_IN:" or EOL.
IFB_RE = re.compile(r"IFB_IN:\{.*?(?=, IFB_IN:\{|$)")

ADDR_RE = re.compile(r"addr:\s*([A-F0-9]+)")
PRESS_RE = re.compile(r"ATMOPRESS:\s*([-+]?\d+(?:\.\d+)?)")
TEMP_RE = re.compile(r"TEMPERATURE:\s*([-+]?\d+(?:\.\d+)?)")


def parse_line(line: str) -> List[Dict[str, str]]:
    """Return zero or more barometer samples extracted from a log line."""

    # Try new log format first
    new_log_match = NEW_LOG_RE.match(line)
    if new_log_match:
        timestamp_raw = new_log_match.group(1)
        pressure = new_log_match.group(2)
        temp = new_log_match.group(3)
        # Assuming single tag in this format or tag ID is implicit/unknown
        # Using a dummy address "TAG01" for this format if not specified
        return [{
            "timestamp": timestamp_raw,
            "addr": "TAG01",
            "pressure_pa": pressure,
            "temperature_c": temp
        }]

    ts_match = TS_RE.match(line)
    if not ts_match:
        return []

    timestamp = ts_match.group(1)
    records: List[Dict[str, str]] = []
    for block in IFB_RE.finditer(line):
        text = block.group(0)
        if "ATMOPRESS" not in text or "TEMPERATURE" not in text:
            continue

        addr_match = ADDR_RE.search(text)
        press_match = PRESS_RE.search(text)
        temp_match = TEMP_RE.search(text)
        if not (addr_match and press_match and temp_match):
            continue  # Skip malformed blocks gracefully.

        records.append(
            {
                "timestamp": timestamp,
                "addr": addr_match.group(1),
                "pressure_pa": press_match.group(1),
                "temperature_c": temp_match.group(1),
            }
        )

    return records


def parse_file(path: Path) -> Iterable[Dict[str, str]]:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        for record in parse_line(line):
            record["source_file"] = path.name
            yield record


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract barometer readings to CSV")
    parser.add_argument(
        "-d",
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data",
        help="Directory containing *.txt logs (default: ./data)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "data" / "baro_readings.csv",
        help="Output CSV path (default: data/baro_readings.csv)",
    )

    args = parser.parse_args()
    data_dir: Path = args.data_dir
    out_path: Path = args.output

    if not data_dir.exists() or not data_dir.is_dir():
        raise SystemExit(f"Data dir not found: {data_dir}")

    rows: List[Dict[str, str]] = []
    for file_path in sorted(data_dir.glob("*.txt")):
        rows.extend(parse_file(file_path))

    if not rows:
        raise SystemExit("No barometer samples (ATMOPRESS) found.")

    # Ensure deterministic ordering across files: primary sort by timestamp,
    # secondary by source file for tie-breaking.
    rows.sort(key=lambda r: (r["timestamp"], r["source_file"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["timestamp", "addr", "pressure_pa", "temperature_c", "source_file"]
    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} samples to {out_path}")


if __name__ == "__main__":
    main()
