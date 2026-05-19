import pandas as pd
import matplotlib.pyplot as plt
import os

# ========= CONFIG =========
INPUT_CSV = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/03_Merged_files/2025-12-13_1min_merged.csv"
OUTPUT_DIR = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/04_Tracker_plots_angles/2025-12-13/test_without_zero"

BASE_NAME = "NCU_TCU_2025-12-13"
ANGLE_THRESHOLD = 28.0
ZERO_EPS = 0.1    # treat <= this as zero
# ==========================

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- Load & convert types ----
df = pd.read_csv(INPUT_CSV, dtype=str)

df["NCU"] = pd.to_numeric(df["NCU"], errors="coerce")
df["TCU"] = pd.to_numeric(df["TCU"], errors="coerce")
df["TC"] = pd.to_numeric(df["TC"], errors="coerce")
df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

df = df.dropna(subset=["NCU", "TCU", "TC", "Valore", "Timestamp"])

# only target (4) & actual (5)
df = df[df["TC"].isin([4, 5])]

all_ncus = sorted(df["NCU"].unique())
print("NCUs found in file:", all_ncus)

# ---- Precompute merged series for every NCU/TCU ----
series_by_ncu = {}
below_28_rows = []
below_28_pairs = set()
skipped_pairs = []

for ncu in all_ncus:
    df_ncu = df[df["NCU"] == ncu]
    tcu_map = {}

    for tcu in sorted(df_ncu["TCU"].unique()):
        part = df_ncu[df_ncu["TCU"] == tcu]

        target = part[part["TC"] == 4][["Timestamp", "Valore"]].rename(columns={"Valore": "target"})
        actual = part[part["TC"] == 5][["Timestamp", "Valore"]].rename(columns={"Valore": "actual"})

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

        # ---- MASK INVALID VALUES (DO NOT SMOOTH) ----
        invalid_mask = (
            (merged["actual"].abs() <= ZERO_EPS) |
            (merged["actual"] < ANGLE_THRESHOLD) |
            (merged["actual"] > 180)
        )

        merged.loc[invalid_mask, "actual"] = pd.NA

        tcu_map[tcu] = merged

        # ---- collect < 28° info (original values, before masking) ----
        low = actual[actual["actual"] < ANGLE_THRESHOLD]
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

# ---- Color maps per NCU ----
color_map = {
    1: plt.cm.Blues,
    2: plt.cm.Greens,
    3: plt.cm.Reds
}

def make_plot(ncus_to_plot, output_png, title_suffix):
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

    # ---- Legend ----
    legend_labels = []
    legend_lines = []

    for ncu in ncus_to_plot:
        tcu_map = series_by_ncu.get(ncu, {})
        if not tcu_map:
            continue

        legend_labels.append(f"NCU {ncu} ({len(tcu_map)} TCU)")
        cmap = color_map.get(ncu, plt.cm.tab10)
        legend_lines.append(plt.Line2D([0], [0], color=cmap(0.7), linewidth=4))

    if legend_lines:
        ax.legend(legend_lines, legend_labels, loc="upper right", fontsize=10)

    # ---- Text box < 28° ----
    local_pairs = sorted(p for p in below_28_pairs if p[0] in ncus_to_plot)
    if local_pairs:
        text = "NCU/TCU < 28°:\n" + "\n".join(f"NCU {n}-TCU {t}" for n, t in local_pairs)
    else:
        text = "No NCU/TCU < 28°"

    ax.text(
        0.01, 0.99, text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8,
        bbox=dict(facecolor="white", alpha=0.85)
    )

    plt.tight_layout()
    plt.savefig(output_png, dpi=350)
    plt.close()
    print("Saved plot:", output_png)


# ---- Generate plots ----
make_plot(all_ncus, os.path.join(OUTPUT_DIR, BASE_NAME + "_ALL.png"), "Tutti i NCU/TCU")

for ncu in all_ncus:
    make_plot(
        [ncu],
        os.path.join(OUTPUT_DIR, f"{BASE_NAME}_NCU{ncu}.png"),
        f"NCU {ncu}"
    )

# ---- CSVs for < 28° ----
if below_28_rows:
    df_low = pd.DataFrame(below_28_rows).sort_values(["NCU", "TCU", "Timestamp"])
    out_csv = os.path.join(OUTPUT_DIR, BASE_NAME + "_below_28deg_ALL.csv")
    df_low.to_csv(out_csv, index=False)
    print("Saved CSV:", out_csv)
else:
    print("No points below 28°.")
