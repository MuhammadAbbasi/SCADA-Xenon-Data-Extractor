"""
============================================================
SCADA TRACKER ANGLE CSV EXTRACTION SCRIPT
============================================================

WHAT THIS SCRIPT DOES
---------------------
This script scans a folder containing raw SCADA-exported CSV files
and creates a filtered version of each file.

Only rows related to tracker angle measurements are kept:
    - "Angolo Target"   (target tracker angle)
    - "Angolo Attuale"  (actual tracker angle)

All other SCADA signals are discarded.

WHY THIS SCRIPT EXISTS
----------------------
Raw SCADA CSV exports are typically very large and contain hundreds
of signals that are not relevant for tracker analysis.

This script:
    - Reduces file size
    - Keeps only angle-related data
    - Standardizes output structure
    - Makes downstream analysis and plotting faster and cleaner

HOW IT WORKS
------------
1. Scans the input directory for CSV files
2. Tries multiple encodings to safely read SCADA exports
3. Parses each file line-by-line using ';' as separator
4. Filters rows based on signal name
5. Writes a cleaned CSV with a fixed header
6. Saves the output using UTF-8 encoding

INPUT
-----
- Folder containing original SCADA CSV files
- CSV separator: ';'
- Variable file encoding (auto-detected)

OUTPUT
------
- One filtered CSV per input file
- Same filename, saved in the output folder
- Columns:
    Tag, Name, Value, Unit, Type, Timestamp

NOTES
-----
- The script does NOT modify timestamps or values
- No resampling or aggregation is performed
- Only filtering and standardization
- Safe to run multiple times (output is overwritten)

============================================================
"""

import os
import csv
from glob import glob

# ================== CONFIG ===================
INPUT_FOLDER = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/01_Original_files/2026-01-02"
OUTPUT_FOLDER = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/02_DownSampled_files/2026-01-0200"
# =============================================

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

possible_encodings = ["utf-8-sig", "utf-16", "latin1"]

print("Scanning for files...")

for input_file in glob(os.path.join(INPUT_FOLDER, "*.csv")):
    file_name = os.path.basename(input_file)
    output_file = os.path.join(OUTPUT_FOLDER, file_name)

    print(f"\nProcessing: {file_name}")

    lines = None
    for enc in possible_encodings:
        try:
            with open(input_file, "r", encoding=enc) as infile:
                lines = infile.readlines()
            print(f"  ✔ File successfully read with encoding: {enc}")
            break
        except UnicodeDecodeError:
            continue

    if lines is None:
        print(f"  ⚠ Could not decode {file_name}. Skipping.")
        continue

    with open(output_file, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["Tag", "Name", "Value", "Unit", "Type", "Timestamp"])

        match_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(";")]
            if len(parts) < 6:
                continue

            name = parts[1].lower()
            if "angolo target" in name or "angolo attuale" in name:
                writer.writerow(parts[:6])
                match_count += 1

        print(f"  ➜ {match_count} matching rows written to {output_file}")

print("\n✅ Extraction complete. All filtered files are in the output folder.")
