"""
============================================================
SCADA TRACKER ANGLE PLOTTING SCRIPT (PER TRACKER)
============================================================

WHAT THIS SCRIPT DOES
---------------------
This script reads a merged and downsampled SCADA CSV file and
generates one plot per tracker (identified by NCU + TCU).

Each plot shows:
    - Angolo Target (target angle)
    - Angolo Attuale (actual angle)

for the full day, aligned in time.

WHY THIS SCRIPT EXISTS
----------------------
After merging and downsampling tracker data, engineers need a
clear visual comparison between target and actual tracker angles
for diagnostics, reporting, and anomaly detection.

This script:
    - Automatically detects all existing (NCU, TCU) pairs
    - Handles missing or inconsistent data gracefully
    - Produces one PNG per tracker
    - Clearly flags data quality issues directly on the plots

HOW IT WORKS
------------
1. Loads the merged CSV file
2. Converts columns to proper numeric and datetime types
3. Identifies unique (NCU, TCU) tracker pairs
4. For each tracker:
   - Extracts target and actual signals
   - Aligns timestamps within a tolerance
   - Handles missing-data cases explicitly
   - Generates and saves a plot
5. Prints a summary of detected issues at the end

INPUT
-----
- One merged CSV file (from the merge & downsampling step)

OUTPUT
------
- One PNG image per tracker
- Filename format:
    TX_<NCU>_TCU_<TCU>.png

NOTES
-----
- Target is identified by TC == 4
- Actual is identified by TC == 5
- Timestamp alignment tolerance: ±1 second
- No smoothing or filtering is applied
- Script is safe to re-run (files are overwritten)

============================================================
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_CSV = (
    "//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/"
    "04 Tracker report/03_Merged_files/2026-01-02_1min_merged.csv"
)

OUTPUT_FOLDER = (
    "//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/"
    "04 Tracker report/04_Tracker_plots_angles/2026-01-02/each_tracker_plots"
)

# Ensure output directory exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ============================================================
# LOAD AND PREPARE DATA
# ============================================================

# Load CSV as strings to avoid silent type coercion
df = pd.read_csv(INPUT_CSV, dtype=str)

# --- Explicit type conversions ---
df["TC"] = pd.to_numeric(df["TC"], errors="coerce")
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
df["TCU"] = pd.to_numeric(df["TCU"], errors="coerce")
df["NCU"] = df["NCU"].astype(str)

# Remove rows with invalid essential fields
df = df.dropna(subset=["TC", "Timestamp", "Valore", "TCU", "NCU"])

# ============================================================
# IDENTIFY REAL TRACKERS PRESENT IN THE FILE
# ============================================================

# Extract unique (TCU, NCU) pairs exactly as present in the data
pairs = (
    df[["TCU", "NCU"]]
    .dropna()
    .drop_duplicates()
    .sort_values(["TCU", "NCU"])
)

# Collect warnings and data issues for final reporting
issues = []

# ============================================================
# MAIN LOOP: ONE PLOT PER TRACKER
# ============================================================

for _, row in pairs.iterrows():
    tcu = row["TCU"]
    tx  = row["NCU"]

    # Select only data for this specific tracker
    part = df[(df["TCU"] == tcu) & (df["NCU"] == tx)]

    # --------------------------------------------------------
    # Extract target and actual angle signals
    # TC == 4 -> target
    # TC == 5 -> actual
    # --------------------------------------------------------
    target = (
        part[part["TC"] == 4][["Timestamp", "Valore"]]
        .sort_values("Timestamp")
        .rename(columns={"Valore": "target"})
    )

    actual = (
        part[part["TC"] == 5][["Timestamp", "Valore"]]
        .sort_values("Timestamp")
        .rename(columns={"Valore": "actual"})
    )

    # Common title and output path
    title_base = f"TX {tx} - TCU {int(tcu)}"
    save_path = os.path.join(
        OUTPUT_FOLDER,
        f"TX_{tx}_TCU_{int(tcu)}.png"
    )

    # ========================================================
    # HANDLE DATA AVAILABILITY CASES
    # ========================================================

    # ---- No data at all ----
    if target.empty and actual.empty:
        msg = f"{title_base}: no target and no actual data."
        issues.append(msg)

        plt.figure(figsize=(16, 9))
        plt.title(title_base)
        plt.xlabel("Time /(Date - Time)")
        plt.ylabel("Angle / °")
        plt.grid(True)

        ax = plt.gca()
        ax.text(
            0.5, 0.5, msg,
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=12, color="red"
        )

        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"Saved WARNING plot (no data): {save_path}")
        continue

    # ---- Only actual present ----
    if target.empty and not actual.empty:
        msg = f"{title_base}: no target data (only actual present)."
        issues.append(msg)

        plt.figure(figsize=(16, 9))
        plt.title(title_base)
        plt.xlabel("Time /(Date - Time)")
        plt.ylabel("Angle / °")
        plt.grid(True)

        ax = plt.gca()
        ax.text(
            0.5, 0.5, msg,
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=12, color="red"
        )

        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"Saved WARNING plot (no target): {save_path}")
        continue

    # ---- Only target present ----
    if actual.empty:
        plt.figure(figsize=(16, 9))
        plt.plot(
            target["Timestamp"],
            target["target"],
            label="Angolo Target",
            linewidth=1
        )

        plt.title(f"{title_base} - Angolo Target")
        plt.xlabel("Time /(Date - Time)")
        plt.ylabel("Angle / °")
        plt.grid(True)
        plt.legend()

        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"Saved {save_path}")
        continue

    # ========================================================
    # ALIGN TARGET AND ACTUAL IN TIME
    # ========================================================

    merged = pd.merge_asof(
        target,
        actual,
        on="Timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("1s")
    ).dropna()

    # ---- Timestamp mismatch ----
    if merged.empty:
        msg = f"{title_base}: timestamps do not match within tolerance."
        issues.append(msg)

        plt.figure(figsize=(16, 9))
        plt.title(title_base)
        plt.xlabel("Time /(Date - Time)")
        plt.ylabel("Angle / °")
        plt.grid(True)

        ax = plt.gca()
        ax.text(
            0.5, 0.5, msg,
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=12, color="red"
        )

        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"Saved WARNING plot (timestamp mismatch): {save_path}")
        continue

    # ========================================================
    # NORMAL CASE: TARGET VS ACTUAL PLOT
    # ========================================================

    plt.figure(figsize=(16, 9))
    plt.plot(
        merged["Timestamp"],
        merged["target"],
        label="Angolo Target",
        linewidth=1
    )
    plt.plot(
        merged["Timestamp"],
        merged["actual"],
        label="Angolo Attuale",
        linewidth=1
    )

    plt.title(f"{title_base} - Angolo Target vs Attuale")
    plt.xlabel("Time /(Date - Time)")
    plt.ylabel("Angle / °")
    plt.grid(True)
    plt.legend()

    plt.savefig(save_path, dpi=400)
    plt.close()
    print(f"Saved {save_path}")

# ============================================================
# FINAL REPORT
# ============================================================

print("Done.")

if issues:
    print("\nWARNING SUMMARY:")
    for msg in issues:
        print(" - " + msg)
else:
    print("\nNo issues detected.")
