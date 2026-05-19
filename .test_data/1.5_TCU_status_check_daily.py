"""
============================================================
SCADA TRACKER ANGLE DEVIATION ANALYSIS (TCU-LEVEL)
============================================================

WHAT THIS SCRIPT DOES
---------------------
This script analyzes merged and downsampled SCADA tracker data and
identifies all timestamps where the difference between:

    - Angolo Target (TC = 4)
    - Angolo Attuale (TC = 5)

exceeds a defined threshold (in degrees).

Each exceedance is recorded in a CSV report at TCU level, including
the associated NCU, timestamp, target angle, actual angle, and
absolute difference.

WHY THIS SCRIPT EXISTS
----------------------
In tracker performance analysis, large deviations between target
and actual angle usually indicate:
    - mechanical issues
    - control problems
    - communication delays
    - trackers stuck or drifting

This script provides:
    - an objective, timestamp-level deviation report
    - a clean CSV suitable for audits and engineering reviews
    - traceability back to NCU and TCU

HOW IT WORKS
------------
1. Loads a merged, downsampled SCADA CSV file
2. Converts all relevant columns to proper numeric/datetime types
3. Groups data by TCU
4. Merges target and actual signals using exact timestamp matching
5. Computes absolute angle difference
6. Keeps only rows exceeding the defined threshold
7. Exports a CSV report with human-readable formatting

INPUT
-----
- One merged CSV file (from the merge & downsampling pipeline)

OUTPUT
------
- CSV file:
    * One row per exceedance event
    * Includes NCU, TCU, timestamp, target, actual, difference

NOTES
-----
- Timestamp matching is STRICT (inner join on Timestamp)
- No resampling or smoothing is applied
- Difference is absolute value in degrees
- CSV is saved with UTF-8 BOM to preserve degree symbol (°)

============================================================
"""

import pandas as pd
import numpy as np
import os

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_CSV = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/03_Merged_files/2026-01-02_1min_merged.csv"
OUTPUT_CSV = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/04_Tracker_plots_angles/2026-01-02/TCU_analysis_report.csv"

difference_selected = 20   # Angle deviation threshold in degrees

# ============================================================
# LOAD AND PREPARE DATA
# ============================================================

# Load CSV as strings to avoid silent type issues
df = pd.read_csv(INPUT_CSV, dtype=str)

# Explicit type conversion
df["TC"] = pd.to_numeric(df["TC"], errors="coerce")
df["TCU"] = pd.to_numeric(df["TCU"], errors="coerce")
df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

# Keep NCU as string for labeling (do NOT drop rows on NCU)
df["NCU"] = df["NCU"].astype(str)

# Remove rows missing essential data
df = df.dropna(subset=["Timestamp", "TCU", "TC", "Valore"])

# Identify all TCUs present in the file
unique_tcus = sorted(df["TCU"].unique())

# ============================================================
# DEVIATION ANALYSIS
# ============================================================

rows = []   # Collected rows for output CSV

for tcu in unique_tcus:

    # Select data for this TCU only
    part = df[df["TCU"] == tcu]

    # --------------------------------------------------------
    # Extract target and actual signals
    # TC = 4 -> target
    # TC = 5 -> actual
    # --------------------------------------------------------
    target = part[part["TC"] == 4][["Timestamp", "Valore", "NCU"]].rename(
        columns={"Valore": "target", "NCU": "NCU_target"}
    )

    actual = part[part["TC"] == 5][["Timestamp", "Valore", "NCU"]].rename(
        columns={"Valore": "actual", "NCU": "NCU_actual"}
    )

    # --------------------------------------------------------
    # Exact timestamp merge (STRICT)
    # Only rows with identical timestamps are kept
    # --------------------------------------------------------
    merged = pd.merge(target, actual, on="Timestamp", how="inner")

    if merged.empty:
        continue

    # --------------------------------------------------------
    # Compute absolute angle difference
    # --------------------------------------------------------
    merged["diff"] = np.abs(merged["actual"] - merged["target"])

    # Keep only rows exceeding the threshold
    exceed = merged[merged["diff"] > difference_selected]

    if exceed.empty:
        continue

    # --------------------------------------------------------
    # Store results for CSV output
    # --------------------------------------------------------
    for _, row in exceed.iterrows():

        # Prefer NCU from target side, fall back to actual if needed
        ncu_val = (
            row["NCU_target"]
            if pd.notna(row["NCU_target"])
            else row["NCU_actual"]
        )

        rows.append({
            "NCU": ncu_val,
            "TCU": tcu,
            "Timestamp": row["Timestamp"],
            "Target (°)": f"{row['target']}°",
            "Actual (°)": f"{row['actual']}°",
            "Difference (°)": f"{row['diff']:.2f}°"
        })

# ============================================================
# EXPORT RESULTS
# ============================================================

report_df = pd.DataFrame(rows)

# Sort for readability if data exists
if not report_df.empty:
    report_df = report_df.sort_values(
        by=["NCU", "TCU", "Timestamp"]
    )

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

# Save CSV with UTF-8 BOM to preserve degree symbol
report_df.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# FINAL SUMMARY
# ============================================================

print("CSV saved:", OUTPUT_CSV)
print("Total exceed records:", len(report_df))

if not report_df.empty:
    print("Unique NCU/TCU combinations exceeding:")
    print(
        report_df[["NCU", "TCU"]]
        .drop_duplicates()
        .to_string(index=False)
    )
