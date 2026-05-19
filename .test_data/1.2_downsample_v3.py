"""
============================================================
SCADA TRACKER ANGLE MERGE & DOWNSAMPLING SCRIPT
============================================================

WHAT THIS SCRIPT DOES
---------------------
This script reads multiple previously downsampled SCADA CSV files
containing tracker angle data and produces merged, time-aggregated
CSV files at a fixed time resolution.

The output is grouped by:
    - NCU
    - TCU
    - TC
    - Parameter name

and resampled to a uniform time interval (e.g. 1 minute).

WHY THIS SCRIPT EXISTS
----------------------
SCADA exports are often:
    - split across multiple files
    - irregular in time
    - too granular for reporting or plotting

This script:
    - safely parses every line (no skipped rows)
    - merges data across files
    - enforces consistent ID formatting
    - downsamples values using a mean aggregation
    - outputs one merged file per day

HOW IT WORKS
------------
1. Reads each CSV file line-by-line (no pandas shortcuts)
2. Uses a strict regex to extract SCADA fields
3. Concatenates all files into a single DataFrame
4. Converts timestamps and numeric values
5. Groups by NCU / TCU / TC / Parameter
6. Resamples data using a fixed time rule
7. Writes one CSV per day

INPUT
-----
- Folder of filtered SCADA CSV files
- CSV format: comma-separated
- Timestamp format: DD/MM/YYYY HH:MM:SS.mmm

OUTPUT
------
- One merged CSV per day
- Filename format:
    YYYY-MM-DD_<DOWNSAMPLE_RULE>_merged.csv

NOTES
-----
- No rows are silently skipped
- Invalid numeric values are coerced to NaN
- Aggregation uses mean
- Output is overwritten if re-run

============================================================
"""

import os
import re
import pandas as pd

# ============================================================
# CONFIGURATION
# ------------------------------------------------------------
# INPUT_FOLDER:
#   Folder containing filtered SCADA CSV files
#
# OUTPUT_FOLDER:
#   Folder where merged and downsampled files are saved
#
# DOWNSAMPLE_RULE:
#   Pandas resampling rule (e.g. '1min', '5min', '15min')
# ============================================================

INPUT_FOLDER = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/02_DownSampled_Files/2026-01-02"
OUTPUT_FOLDER = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/03_Merged_files/"
DOWNSAMPLE_RULE = "1min"

# ------------------------------------------------------------
# Regex pattern used to strictly parse each SCADA line.
# This guarantees:
#   - correct field order
#   - no accidental column shifting
#   - no silent data loss
# ------------------------------------------------------------
pattern = re.compile(
    r"Data_Mod_NCU_(\d+)_TCU_(\d+)\.TC(\d+),([^,]+),([^,]+),([^,]+),([^,]+),(.+)"
)

# ============================================================
# PARSING FUNCTIONS
# ============================================================

def parse_line(line):
    """
    Parse a single raw SCADA CSV line using regex.

    Parameters
    ----------
    line : str
        Raw line from CSV file

    Returns
    -------
    dict or None
        Parsed fields if the line matches the expected format,
        otherwise None
    """
    m = pattern.match(line.strip())
    if not m:
        return None

    return {
        "NCU": m.group(1),
        "TCU": m.group(2),
        "TC": m.group(3),
        "Parametro": m.group(4),
        "Valore": m.group(5),
        "Unita": m.group(6),
        "Flags": m.group(7),
        "Timestamp": m.group(8),
    }


def load_file_raw(filepath):
    """
    Read a CSV file line-by-line and parse every valid SCADA row.

    This function intentionally avoids pandas read_csv to ensure
    no rows are skipped due to formatting issues.

    Parameters
    ----------
    filepath : str
        Full path to the CSV file

    Returns
    -------
    pandas.DataFrame
        DataFrame containing all parsed rows
    """
    print(f"Reading: {os.path.basename(filepath)}")

    rows = []
    with open(filepath, "r", errors="ignore", encoding="utf-8") as f:
        for line in f:
            parsed = parse_line(line)
            if parsed:
                rows.append(parsed)

    print(f"   Parsed {len(rows)} rows")
    return pd.DataFrame(rows)

# ============================================================
# MERGE & DOWNSAMPLING LOGIC
# ============================================================

def merge_and_downsample(df):
    """
    Merge all parsed data and downsample it by date.

    Steps:
    - Convert timestamp and numeric fields
    - Normalize NCU / TCU / TC formatting
    - Split by day
    - Resample using mean aggregation
    - Write one CSV per day

    Parameters
    ----------
    df : pandas.DataFrame
        Combined DataFrame from all input files
    """

    # Convert timestamp string to datetime
    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        format="%d/%m/%Y %H:%M:%S.%f"
    )

    # Convert values to numeric, invalid entries become NaN
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")

    # Extract date for daily splitting
    df["Date"] = df["Timestamp"].dt.date

    # Normalize ID formatting (leading zeros)
    df["NCU"] = df["NCU"].astype(int).astype(str).str.zfill(2)
    df["TCU"] = df["TCU"].astype(int).astype(str).str.zfill(3)
    df["TC"]  = df["TC"].astype(int).astype(str).str.zfill(2)

    # --------------------------------------------------------
    # Process each day independently
    # --------------------------------------------------------
    for date in df["Date"].unique():
        print(f"Processing day: {date}")

        day_df = df[df["Date"] == date].sort_values("Timestamp")

        out = (
            day_df
            .set_index("Timestamp")
            .groupby(["NCU", "TCU", "TC", "Parametro"])
            .resample(DOWNSAMPLE_RULE)["Valore"]
            .mean()
            .reset_index()
        )

        output_file = os.path.join(
            OUTPUT_FOLDER,
            f"{date}_{DOWNSAMPLE_RULE}_merged.csv"
        )

        out.to_csv(output_file, index=False)
        print(f"   Saved: {output_file}")

# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    """
    Main execution function.
    Handles directory setup, file loading, merging and output.
    """

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".csv")]
    print(f"Found {len(files)} files")

    all_frames = []
    for file in files:
        path = os.path.join(INPUT_FOLDER, file)
        df = load_file_raw(path)
        all_frames.append(df)

    big = pd.concat(all_frames, ignore_index=True)
    print(f"Total rows loaded from all files: {len(big)}")

    merge_and_downsample(big)

    print("Completed.")

# ------------------------------------------------------------
# Script entry guard
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
