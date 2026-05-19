import pandas as pd

INPUT_CSV = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/03_Merged_files/2025-11-01_1min_merged.csv"

# Try reading normally
try:
    df = pd.read_csv(INPUT_CSV, dtype=str)
    print("Read mode: normal header")
except:
    print("Normal read failed — trying header=None...")
    df = pd.read_csv(INPUT_CSV, dtype=str, header=None)

print("\n===== FIRST 20 ROWS =====")
print(df.head(20))

print("\n===== SHAPE =====")
print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\n===== COLUMN NAMES =====")
print(df.columns.tolist())

# Try detecting column types automatically
print("\n===== SNIFFING COLUMN TYPES =====")
for col in df.columns:
    sample = df[col].dropna().head(5).tolist()
    print(f"{col}: samples -> {sample}")

# Try converting expected columns (if present)
possible_cols = ["NCU", "TCU", "TC", "Timestamp", "Valore"]
print("\n===== CHECKING EXPECTED COLUMNS =====")
for c in possible_cols:
    print(f"{c} present? {'YES' if c in df.columns else 'NO'}")

# If NCU + TCU exists, inspect structure
if "NCU" in df.columns and "TCU" in df.columns:
    # convert numeric fields
    df["NCU"] = pd.to_numeric(df["NCU"], errors="coerce")
    df["TCU"] = pd.to_numeric(df["TCU"], errors="coerce")

    print("\n===== UNIQUE NCU VALUES =====")
    print(sorted(df["NCU"].dropna().unique()))

    print("\n===== NCU VALUE COUNTS =====")
    print(df["NCU"].value_counts().sort_index())

    print("\n===== UNIQUE TCU VALUES (global) =====")
    print(sorted(df["TCU"].dropna().unique())[:50])
    print("...")

    print("\n===== TCU RANGE PER NCU =====")
    for ncu in sorted(df["NCU"].dropna().unique()):
        tcu_values = sorted(df[df["NCU"] == ncu]["TCU"].unique())
        print(f"NCU {ncu}: min TCU={min(tcu_values)}, max TCU={max(tcu_values)}, count={len(tcu_values)}")

    print("\n===== CHECKING FOR DUPLICATES (NCU,TCU,Timestamp) =====")
    if "Timestamp" in df.columns:
        dups = df.duplicated(subset=["NCU", "TCU", "Timestamp"])
        print("Duplicate rows:", dups.sum())
else:
    print("\n===== NCU/TCU COLUMNS NOT FOUND =====")
