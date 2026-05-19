import os
import glob
import pandas as pd

# ============ CONFIG ============

BASE_FOLDER = r"//S01/get/03 - REPORT/Report/Daily Reports/Humidity Reports/05 2025"

# Map each folder → correct TS tag
TAG_MAP = {
    "XM1": "TS_01_Weather_Hour",
    "XM3": "TS_03_Weather_Hour"
}

FILE_PATTERN = "*Weather_Hour*.csv"

# =================================


def get_date_from_file(path: str):
    """Extract only the DATE (no time) from the first valid data row in the file."""
    try:
        df = pd.read_csv(path, sep=";", header=None, nrows=2, encoding="latin1")
    except Exception as e:
        print(f"  ERROR reading {path}: {e}")
        return None

    if df.empty:
        print(f"  WARNING empty file: {path}")
        return None

    # Handle "Colonna1" header row
    first = str(df.iloc[0, 0]).strip().lower()
    row = df.iloc[1] if first == "colonna1" and len(df) > 1 else df.iloc[0]

    if len(row) < 6:
        print(f"  WARNING missing columns: {path}")
        return None

    date_str = str(row[4]).strip()  # only date
    time_str = str(row[5]).strip()  # still needed to validate

    # Parse full timestamp first (for safety)
    dt = pd.to_datetime(f"{date_str} {time_str}",
                        format="%d/%m/%Y %H:%M:%S.%f",
                        errors="coerce")

    if pd.isna(dt):
        dt = pd.to_datetime(f"{date_str} {time_str}",
                            format="%d/%m/%Y %H:%M:%S",
                            errors="coerce")

    if pd.isna(dt):
        print(f"  WARNING cannot parse date in {path}")
        return None

    return dt.date()  # <-- return only the DATE


def rename_files(folder_name: str):
    folder_path = os.path.join(BASE_FOLDER, folder_name)
    tag = TAG_MAP.get(folder_name, "TS_XX_Weather_Hour")

    print(f"\n=== Processing {folder_name} ({tag}) ===")

    files = sorted(glob.glob(os.path.join(folder_path, FILE_PATTERN)))
    if not files:
        print("  No matching files.")
        return

    for old_path in files:
        old_name = os.path.basename(old_path)
        print(f"  -> {old_name}")

        date_obj = get_date_from_file(old_path)
        if date_obj is None:
            print("     Skipped (no date).")
            continue

        # New filename format: YYYY-MM-DD_TS_XX_Weather_Hour.csv
        new_name = f"{date_obj:%Y-%m-%d}_{tag}.csv"
        new_path = os.path.join(folder_path, new_name)

        # Avoid overwriting if multiple files have same date
        if os.path.exists(new_path):
            base, ext = os.path.splitext(new_name)
            i = 2
            while True:
                alt = f"{base}_v{i}{ext}"
                alt_path = os.path.join(folder_path, alt)
                if not os.path.exists(alt_path):
                    new_path = alt_path
                    new_name = alt
                    break
                i += 1

        try:
            os.rename(old_path, new_path)
            print(f"     Renamed to: {new_name}")
        except Exception as e:
            print(f"     ERROR: {e}")


def main():
    for folder in TAG_MAP:
        rename_files(folder)
    print("\nDone.")


if __name__ == "__main__":
    main()
