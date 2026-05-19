import os
import glob
import pandas as pd

# ============ CONFIG ============

# Folder for the month to process
MONTH_FOLDER = r"//S01/get/03 - REPORT/Report/Daily Reports/Humidity Reports/05 2025"

# XM subfolders
XM_FOLDERS = ["XM1", "XM3"]

# Output folder
OUTPUT_FOLDER = os.path.join(MONTH_FOLDER, "Merged_Monthly")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Pattern of daily files
FILE_PATTERN = "*.csv"

# Map XM → TS tag for filename
TS_TAG = {
    "XM1": "TS_01",
    "XM3": "TS_03",
}

# =================================


def read_daily_file(path: str) -> pd.DataFrame:
    """
    Read a daily CSV file using ITALIAN FORMAT:
    - Separator: ;
    - Decimal: ,
    Remove 'Colonna1' row if present.
    """
    df = pd.read_csv(
        path,
        sep=";", 
        header=None,
        dtype=str,
        encoding="latin1",
        decimal=","
    )

    # Remove useless header line
    if str(df.iloc[0, 0]).strip().lower() == "colonna1":
        df = df.iloc[1:].reset_index(drop=True)

    return df


def merge_month_for_xm(xm_name: str):
    xm_folder = os.path.join(MONTH_FOLDER, xm_name)

    print(f"\n=== Processing {xm_name} ===")

    files = sorted(glob.glob(os.path.join(xm_folder, FILE_PATTERN)))
    if not files:
        print("  No CSV files found.")
        return

    frames = []
    for path in files:
        print(f"  Reading: {os.path.basename(path)}")
        df = read_daily_file(path)
        if not df.empty:
            frames.append(df)

    if not frames:
        print("  No data found.")
        return

    # Stack all daily files vertically
    merged = pd.concat(frames, ignore_index=True)

    # Extract month/year from folder name
    folder_name = os.path.basename(MONTH_FOLDER)
    try:
        month_str, year_str = folder_name.split()
    except ValueError:
        month_str = "XX"
        year_str = "YYYY"

    tag = TS_TAG.get(xm_name, "TS_XX")

    # Output example: 2025-03_TS_01_Weather_Hour_Month.csv
    out_name = f"{year_str}-{month_str}_{tag}_Weather_Hour_Month.csv"
    out_path = os.path.join(OUTPUT_FOLDER, out_name)

    # Write in Italian CSV format (; separator, , decimal)
    merged.to_csv(
        out_path,
        sep=";",
        index=False,
        header=False,
        decimal=","
    )

    print(f"  Saved: {out_path}")


def main():
    for xm in XM_FOLDERS:
        merge_month_for_xm(xm)

    print("\nAll done!")


if __name__ == "__main__":
    main()
