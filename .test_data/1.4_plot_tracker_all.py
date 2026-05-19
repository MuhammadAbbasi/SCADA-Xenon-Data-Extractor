"""
============================================================
SCADA TRACKER ANGLE OVERVIEW & THRESHOLD ANALYSIS SCRIPT
============================================================

WHAT THIS SCRIPT DOES
---------------------
This script analyzes merged and downsampled SCADA tracker data and
produces overview plots of the *actual tracker angle* for all TCUs,
grouped by NCU.

It also detects and reports all tracker angles that fall below a
defined threshold (default: 28°).

The script generates:
    - One plot containing ALL NCUs and TCUs
    - One plot per individual NCU
    - A CSV file listing all timestamps where actual angle < threshold

WHY THIS SCRIPT EXISTS
----------------------
When analyzing tracker behavior at plant scale, engineers need:
    - a compact visual overview
    - quick identification of trackers stuck near horizontal
    - evidence (CSV) of abnormal low-angle behavior

This script:
    - merges target and actual signals safely
    - plots only the actual angle (for clarity at scale)
    - highlights problematic NCU/TCU pairs
    - produces both visual and tabular outputs

HOW IT WORKS
------------
1. Loads a merged, downsampled CSV
2. Keeps only target (TC=4) and actual (TC=5) rows
3. Aligns target and actual timestamps (±1s tolerance)
4. Builds per-NCU/per-TCU time series
5. Detects actual angles below threshold
6. Generates overview plots with:
   - color separation by NCU
   - legend summary
   - text box listing problematic trackers
7. Writes CSV files for all low-angle events

INPUT
-----
- One merged CSV file (from previous pipeline step)

OUTPUT
------
- PNG plots:
    * All NCUs combined
    * One plot per NCU
- CSV file:
    * All (NCU, TCU, Timestamp) where angle < threshold

NOTES
-----
- Only actual angle is plotted (no target)
- No smoothing or filtering is applied
- Timestamp matching tolerance: ±1 second
- Safe to re-run (files overwritten)

============================================================
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_CSV = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/03_Merged_files/2026-01-02_1min_merged.csv"
OUTPUT_DIR = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/04_Tracker_plots_angles/2026-01-02"

BASE_NAME = "NCU_TCU_2026-01-01"   # Base name for output files
ANGLE_THRESHOLD = 28.0             # Degrees threshold for low-angle detection

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# LOAD AND PREPARE DATA
# ============================================================

df = pd.read_csv(INPUT_CSV, dtype=str)

# Explicit type conversion to avoid silent errors
df["NCU"] = pd.to_numeric(df["NCU"], errors="coerce")
df["TCU"] = pd.to_numeric(df["TCU"], errors="coerce")
df["TC"] = pd.to_numeric(df["TC"], errors="coerce")
df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

# Drop rows with invalid essential data
df = df.dropna(subset=["NCU", "TCU", "TC", "Valore", "Timestamp"])

# Keep only target (TC=4) and actual (TC=5)
df = df[df["TC"].isin([4, 5])]

# Identify all NCUs present
all_ncus = sorted(df["NCU"].unique())
print("NCUs found in file:", all_ncus)

# ============================================================
# PRECOMPUTE MERGED SERIES AND LOW-ANGLE EVENTS
# ============================================================

series_by_ncu = {}          # {NCU: {TCU: merged_dataframe}}
below_28_rows = []          # rows for CSV export
below_28_pairs = set()      # (NCU, TCU) that ever fall below threshold
skipped_pairs = []          # (NCU, TCU) with no matched timestamps

for ncu in all_ncus:
    df_ncu = df[df["NCU"] == ncu]
    tcu_map = {}
    tcus = sorted(df_ncu["TCU"].unique())
    print(f"Processing NCU {ncu}, {len(tcus)} TCU(s)")

    for tcu in tcus:
        part = df_ncu[df_ncu["TCU"] == tcu]

        # Split target and actual
        target = part[part["TC"] == 4][["Timestamp", "Valore"]].rename(
            columns={"Valore": "target"}
        )
        actual = part[part["TC"] == 5][["Timestamp", "Valore"]].rename(
            columns={"Valore": "actual"}
        )

        # Align timestamps with tolerance
        merged = pd.merge_asof(
            target.sort_values("Timestamp"),
            actual.sort_values("Timestamp"),
            on="Timestamp",
            direction="nearest",
            tolerance=pd.Timedelta("1s")
        ).dropna()

        if merged.empty:
            skipped_pairs.append((ncu, tcu))
            continue

        tcu_map[tcu] = merged

        # Detect angles below threshold
        low = merged[merged["actual"] < ANGLE_THRESHOLD]
        if not low.empty:
            below_28_pairs.add((ncu, tcu))
            for _, row in low.iterrows():
                below_28_rows.append({
                    "NCU": ncu,
                    "TCU": tcu,
                    "Timestamp": row["Timestamp"],
                    "Angle": row["actual"]
                })

    series_by_ncu[ncu] = tcu_map

print("Precomputation done.")

if skipped_pairs:
    print("WARNING: some NCU/TCU pairs had no merged timestamps and were skipped:")
    print(", ".join(f"(NCU {n}-TCU {t})" for n, t in skipped_pairs))

# ============================================================
# PLOTTING UTILITIES
# ============================================================

# Color maps per NCU (for visual separation)
color_map = {
    1: plt.cm.Blues,
    2: plt.cm.Greens,
    3: plt.cm.Reds
}

def make_plot(ncus_to_plot, output_png, title_suffix):
    """
    Create a tracker angle overview plot for selected NCUs.

    Parameters
    ----------
    ncus_to_plot : list
        List of NCU IDs to include in the plot
    output_png : str
        Output file path
    title_suffix : str
        Title suffix for the plot
    """

    fig, ax = plt.subplots(figsize=(20, 4))

    for ncu in ncus_to_plot:
        tcu_map = series_by_ncu.get(ncu, {})
        if not tcu_map:
            continue

        cmap = color_map.get(ncu, plt.cm.tab10)
        tcus_sorted = sorted(tcu_map.keys())
        N = len(tcus_sorted)
        shades = [cmap(i / max(N - 1, 1)) for i in range(N)]

        for i, tcu in enumerate(tcus_sorted):
            merged = tcu_map[tcu]
            ax.plot(
                merged["Timestamp"],
                merged["actual"],
                color=shades[i],
                linewidth=0.8
            )

    ax.set_title(f"Angolo Attuale - {title_suffix}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Angle")
    ax.grid(True)

    # ---- Legend: one entry per NCU ----
    legend_labels = []
    legend_lines = []

    for ncu in ncus_to_plot:
        tcu_map = series_by_ncu.get(ncu, {})
        if not tcu_map:
            continue

        legend_labels.append(f"NCU {ncu} ({len(tcu_map)} TCU)")
        cmap = color_map.get(ncu, plt.cm.tab10)
        legend_lines.append(
            plt.Line2D([0], [0], color=cmap(0.7), linewidth=4)
        )

    if legend_lines:
        ax.legend(
            legend_lines,
            legend_labels,
            loc="upper right",
            fontsize=10,
            frameon=True
        )

    # ---- Text box listing low-angle trackers ----
    local_pairs = sorted(p for p in below_28_pairs if p[0] in ncus_to_plot)
    if local_pairs:
        lines = ["NCU/TCU < 28°:"]
        for ncu, tcu in local_pairs:
            lines.append(f"NCU {ncu}-TCU {tcu}")
        text_str = "\n".join(lines)
    else:
        text_str = "No NCU/TCU < 28°"

    ax.text(
        0.01, 0.99,
        text_str,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="black")
    )

    plt.tight_layout()
    plt.savefig(output_png, dpi=350)
    plt.close()
    print("Saved plot:", output_png)

# ============================================================
# GENERATE PLOTS
# ============================================================

# All NCUs together
all_plot_path = os.path.join(OUTPUT_DIR, BASE_NAME + "_ALL.png")
make_plot(all_ncus, all_plot_path, "Tutti i NCU/TCU")

# One plot per NCU
for ncu in all_ncus:
    single_plot_path = os.path.join(
        OUTPUT_DIR, f"{BASE_NAME}_NCU{ncu}.png"
    )
    make_plot([ncu], single_plot_path, f"NCU {ncu}")

# ============================================================
# EXPORT CSVs FOR LOW ANGLES
# ============================================================
if below_28_rows:
    all_csv = os.path.join(
        OUTPUT_DIR, BASE_NAME + "_below_28deg_ALL.csv"
    )

    df_low = pd.DataFrame(below_28_rows)

    # Ensure angle is numeric and rounded to 2 decimals
    df_low["Angle"] = (
        pd.to_numeric(df_low["Angle"], errors="coerce")
        .round(2)
    )

    # Sort for readability
    df_low.sort_values(
        ["NCU", "TCU", "Timestamp"],
        inplace=True
    )

    # Export in Italian CSV format
    df_low.to_csv(
        all_csv,
        index=False,
        sep=";",          # Italian field separator
        decimal=",",      # Italian decimal separator
        encoding="utf-8-sig"  # Excel-safe (keeps commas & degree symbol)
    )

    print("Saved CSV (Italian format, all NCUs) with angle < 28°:", all_csv)
else:
    print("No points below 28°. No CSVs created.")
