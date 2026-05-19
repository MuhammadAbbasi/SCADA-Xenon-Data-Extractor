import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import csv
import glob
import re
import pandas as pd
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import sys
import time
import random
import gc
from datetime import datetime, timedelta

# --- ASTRONOMY LIBRARY ---
try:
    from astral import LocationInfo
    from astral.sun import sun
    import pytz 
except ImportError:
    print("WARNING: 'astral' or 'pytz' not found. Run: pip install astral pytz")

# --- PLOTTING ---
import matplotlib
matplotlib.use("TkAgg") 
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# ==============================================================================
# SOLAR CALCULATION (Precise)
# ==============================================================================

def get_sun_times(date_obj, lat=37.7717, lon=12.6304):
    """Calculates precise Sunrise/Sunset for Mazara using Astral."""
    try:
        site = LocationInfo("Mazara", "Italy", "Europe/Rome", lat, lon)
        s = sun(site.observer, date=date_obj)
        tz = pytz.timezone("Europe/Rome")
        sr = s['sunrise'].astimezone(tz).replace(tzinfo=None)
        ss = s['sunset'].astimezone(tz).replace(tzinfo=None)
        return sr, ss
    except:
        base = datetime.combine(date_obj.date(), datetime.min.time())
        return base + timedelta(hours=7), base + timedelta(hours=18)

# ==============================================================================
# WORKER FUNCTIONS
# ==============================================================================

def worker_extract(args):
    infile, outfile = args
    filename = os.path.basename(infile)
    print(f"[EXTRACT] Processing: {filename}...", flush=True)
    possible_encodings = ["utf-8-sig", "utf-16", "latin1"]
    lines = None
    for enc in possible_encodings:
        try:
            with open(infile, "r", encoding=enc) as f: lines = f.readlines(); break
        except UnicodeDecodeError: continue  
    if not lines: return f"Failed: {filename}"
    try:
        with open(outfile, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Tag", "Name", "Value", "Unit", "Type", "Timestamp"])
            for line in lines:
                if "Angolo" in line or "angolo" in line:
                    parts = [p.strip() for p in line.strip().split(";")]
                    if len(parts) >= 6:
                        writer.writerow(parts[:6])
        return f"Done: {filename}"
    except Exception: return f"Error: {filename}"

def worker_read_csv(filepath):
    filename = os.path.basename(filepath)
    print(f"[MERGE] Reading: {filename}...", flush=True)
    pattern = re.compile(r"Data_Mod_NCU_(\d+)_TCU_(\d+)\.TC(\d+),([^,]+),([^,]+),([^,]+),([^,]+),(.+)")
    rows = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = pattern.match(line.strip())
                if m:
                    rows.append({
                        "NCU": int(m.group(1)), "TCU": int(m.group(2)), "TC": int(m.group(3)),
                        "Parametro": m.group(4), "Valore": float(m.group(5).replace(',', '.')),
                        "Timestamp": m.group(8)
                    })
        return pd.DataFrame(rows)
    except Exception as e: 
        print(f"[MERGE] Error: {e}", flush=True)
        return pd.DataFrame()

def worker_plot_file(args):
    import matplotlib.pyplot as plt
    matplotlib.use('Agg') 
    ncu, tcu, data_dict, out_path = args
    try:
        df = pd.DataFrame(data_dict)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        target = df[df["TC"] == 4].sort_values("Timestamp")
        actual = df[df["TC"] == 5].sort_values("Timestamp")
        if target.empty and actual.empty: return "Empty"
        fig, ax = plt.subplots(figsize=(10, 6))
        if not target.empty: ax.plot(target["Timestamp"], target["Valore"], label="Target", lw=1)
        if not actual.empty: ax.plot(actual["Timestamp"], actual["Valore"], label="Actual", lw=1)
        ax.set_title(f"NCU {ncu} - TCU {tcu}")
        ax.grid(True)
        ax.legend(loc="upper right")
        if not actual.empty:
            stats = f"Min: {actual['Valore'].min():.1f}° | Max: {actual['Valore'].max():.1f}°"
            ax.text(0.02, 0.02, stats, transform=ax.transAxes, fontsize=9, 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        fig.tight_layout()
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return "OK"
    except Exception: 
        plt.close('all'); return "Error"

def worker_overview_analysis(input_csv, output_dir, date_str):
    import matplotlib.pyplot as plt
    matplotlib.use('Agg')
    print(f"[OVERVIEW] Starting Analysis...", flush=True)
    try:
        os.makedirs(output_dir, exist_ok=True)
        df = pd.read_csv(input_csv, dtype={"NCU": int, "TCU": int, "TC": int, "Valore": float})
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df[df["TC"] == 5]
        all_ncus = sorted(df["NCU"].unique())
        fig, ax = plt.subplots(figsize=(15, 5))
        for ncu in all_ncus:
            s = df[df["NCU"] == ncu]
            ax.scatter(s["Timestamp"], s["Valore"], s=1, alpha=0.5, label=f"NCU {ncu}")
        ax.set_title("All Trackers Overview")
        fig.savefig(os.path.join(output_dir, f"NCU_TCU_{date_str}_ALL.png"), dpi=300)
        plt.close(fig)
        for ncu in all_ncus:
            fig, ax = plt.subplots(figsize=(15, 5))
            s = df[df["NCU"] == ncu]
            for tcu in s["TCU"].unique():
                t = s[s["TCU"] == tcu]
                ax.plot(t["Timestamp"], t["Valore"], lw=0.5)
            ax.set_title(f"NCU {ncu} Overview")
            fig.savefig(os.path.join(output_dir, f"NCU_TCU_{date_str}_NCU{ncu}.png"), dpi=300)
            plt.close(fig)
        return "Done"
    except Exception as e: return f"Error: {e}"

def worker_health_check(csv_path, date_str):
    issues = []
    print(f"[HEALTH] Reading CSV: {csv_path}", flush=True)
    try:
        df = pd.read_csv(csv_path, dtype={"NCU": int, "TCU": int, "TC": int, "Valore": float})
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        # Keep both 4 (Target) and 5 (Actual)
        df = df[df["TC"].isin([4, 5])].dropna(subset=["Valore"])
        
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        sr, ss = get_sun_times(dt_obj)
        start_check = sr + timedelta(minutes=30)
        end_check = ss - timedelta(minutes=30)
        
        print("--------------------------------------------------", flush=True)
        print(f"  SUNRISE (Italy): {sr.strftime('%H:%M:%S')}", flush=True)
        print(f"  SUNSET  (Italy): {ss.strftime('%H:%M:%S')}", flush=True)
        print("--------------------------------------------------", flush=True)

        groups = list(df.groupby(["NCU", "TCU"]))
        print(f"[HEALTH] Analyzing {len(groups)} trackers...", flush=True)

        for i, ((ncu, tcu), g) in enumerate(groups):
            # Sort crucial for rolling operations
            actual_df = g[g["TC"] == 5].sort_values("Timestamp")
            target_df = g[g["TC"] == 4].sort_values("Timestamp")
            
            if actual_df.empty:
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "NO DATA", "Msg": "No data", "Sev": "High"})
                continue
            
            # 1. COMM ERROR
            if (actual_df["Valore"] <= 30).any() or (actual_df["Valore"] >= 150).any():
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "COMM ERROR", "Msg": "Value outside 30-150 range", "Sev": "Communication Error"})

            # 2. SUDDEN JUMP
            actual_df['diff'] = actual_df['Valore'].diff().abs()
            actual_df['prev_val'] = actual_df['Valore'].shift(1)
            valid_jumps = actual_df[(actual_df['diff'] > 15) & (actual_df['Valore'] > 30) & (actual_df['prev_val'] > 30)]
            if not valid_jumps.empty:
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "SUDDEN JUMP", "Msg": f"Jump of {valid_jumps['diff'].max():.1f}°", "Sev": "Medium"})

            # 3. STUCK & HIGH WIND (SMART LOGIC)
            # Filter daylight hours
            daylight = actual_df[(actual_df["Timestamp"] >= start_check) & (actual_df["Timestamp"] <= end_check)].copy()
            
            if len(daylight) > 15:
                # FIX: Set index to Timestamp for time-based rolling
                daylight_indexed = daylight.set_index("Timestamp")
                
                # Calculate rolling std deviation over 15 mins
                rolling_std = daylight_indexed['Valore'].rolling('15min').std()
                
                # Check if there are any periods where std == 0 (Stuck)
                stuck_timestamps = rolling_std[rolling_std == 0].index

                if not stuck_timestamps.empty:
                    # Isolate the stuck periods
                    stuck_period_actual = daylight[daylight["Timestamp"].isin(stuck_timestamps)]
                    
                    # Merge with target to check if this stuck behavior is INTENTIONAL
                    merged = pd.merge_asof(stuck_period_actual.sort_values("Timestamp"), 
                                           target_df.sort_values("Timestamp"), 
                                           on="Timestamp", 
                                           direction="nearest", 
                                           tolerance=pd.Timedelta("2min"), 
                                           suffixes=("_act", "_tgt"))
                    
                    # Calculate deviation
                    merged['deviation'] = (merged['Valore_act'] - merged['Valore_tgt']).abs()

                    # Only flag if deviation is > 5 degrees
                    problematic = merged[merged['deviation'] > 5.0]

                    if not problematic.empty:
                        # We have confirmed issues
                        stuck_val = problematic['Valore_act'].mean()
                        
                        # Differentiate High Wind vs Stuck
                        if 85 <= stuck_val <= 98: 
                            issues.append({"NCU": ncu, "TCU": tcu, "Type": "HIGH WIND MODE", "Msg": f"Stowed at {stuck_val:.1f}° (Dev > 5°)", "Sev": "Low"})
                        else:
                            issues.append({"NCU": ncu, "TCU": tcu, "Type": "STUCK", "Msg": f"Stuck at {stuck_val:.1f}° (Dev > 5°)", "Sev": "Medium"})

            # 4. LOW ANGLE
            min_val = actual_df["Valore"].min()
            if 0.1 < min_val < 10:
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "LOW ANGLE", "Msg": f"Min {min_val:.1f}°", "Sev": "Low"})

        del df, groups
        gc.collect()
        return issues
    except Exception as e: 
        print(f"[HEALTH] Error: {e}", flush=True)
        return [{"NCU":0, "TCU":0, "Type": "ERROR", "Msg": str(e), "Sev": "Critical"}]

# ==============================================================================
# GUI CLASS
# ==============================================================================

class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
    def write(self, s):
        try:
            self.widget.config(state="normal")
            self.widget.insert("end", s)
            self.widget.see("end")
            self.widget.config(state="disabled")
            self.widget.update_idletasks()
        except: pass
    def flush(self): pass

class TrackerSuiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GET - SCADA Tracker Suite v2.11")
        self.root.geometry("850x780") 
        self.cpu_cores = min(multiprocessing.cpu_count(), 10)
        
        self.folder_path = tk.StringVar(value=r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report")
        today = datetime.now()
        self.var_year = tk.StringVar(value=str(today.year))
        self.var_month = tk.StringVar(value=str(today.month).zfill(2))
        self.var_day = tk.StringVar(value=str(today.day).zfill(2))
        self.date_val = tk.StringVar()
        self.update_date_str()

        self.setup_layout()
        sys.stdout = TextRedirector(self.log_text)
        
        # FIX: Replaced depreciated trace() with trace_add()
        self.var_year.trace_add("write", self.update_date_str)
        self.var_month.trace_add("write", self.update_date_str)
        self.var_day.trace_add("write", self.update_date_str)

    def update_date_str(self, *args):
        y, m, d = self.var_year.get(), self.var_month.get().zfill(2), self.var_day.get().zfill(2)
        self.date_val.set(f"{y}-{m}-{d}")

    def setup_layout(self):
        cfg = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        cfg.pack(fill="x", padx=10, pady=5)
        
        f_frame = ttk.Frame(cfg)
        f_frame.pack(fill="x", pady=2)
        ttk.Label(f_frame, text="Root Folder:").pack(side="left")
        ttk.Entry(f_frame, textvariable=self.folder_path, width=60).pack(side="left", padx=5)
        ttk.Button(f_frame, text="Browse", command=self.browse).pack(side="left")

        d_frame = ttk.Frame(cfg)
        d_frame.pack(fill="x", pady=5)
        ttk.Label(d_frame, text="Date:").pack(side="left")
        ttk.Spinbox(d_frame, from_=2020, to=2030, textvariable=self.var_year, width=5).pack(side="left", padx=2)
        ttk.Spinbox(d_frame, from_=1, to=12, textvariable=self.var_month, width=3).pack(side="left")
        ttk.Spinbox(d_frame, from_=1, to=31, textvariable=self.var_day, width=3).pack(side="left")

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=5)
        self.tab_pipe = ttk.Frame(self.tabs); self.tabs.add(self.tab_pipe, text="Pipeline")
        self.tab_dash = ttk.Frame(self.tabs); self.tabs.add(self.tab_dash, text="Health Dashboard")

        btn_f = ttk.Frame(self.tab_pipe)
        btn_f.pack(fill="x", pady=10, padx=50)

        tk.Button(btn_f, text="1. EXTRACT", bg="#ddd", command=self.run_step1).pack(fill="x", pady=2)
        tk.Button(btn_f, text="2. MERGE", bg="#ddd", command=self.run_step2).pack(fill="x", pady=2)
        ttk.Separator(btn_f, orient="horizontal").pack(fill="x", pady=5)
        
        tk.Button(btn_f, text="3. GENERATE OVERVIEW (Merged)", bg="#FFD54F", font=("Arial", 9, "bold"), command=self.run_step3_overview).pack(fill="x", pady=2)
        
        ov_row = ttk.Frame(btn_f)
        ov_row.pack(fill="x", pady=2)
        for txt, sfx in [("Show All NCUs", "ALL"), ("Show NCU 1", "NCU1"), ("Show NCU 2", "NCU2"), ("Show NCU 3", "NCU3")]:
            tk.Button(ov_row, text=txt, bg="#e1f5fe", command=lambda s=sfx: self.check_and_show_overview(s)).pack(side="left", fill="x", expand=True, padx=1)

        split = ttk.Frame(btn_f); split.pack(fill="x", pady=5)
        tk.Button(split, text="4. GENERATE INDIVIDUAL PLOTS", bg="#ddd", command=self.run_step4_indiv).pack(side="left", fill="x", expand=True, padx=2)
        tk.Button(split, text="5. RUN HEALTH CHECK", bg="#4CAF50", fg="white", command=self.run_step5_health).pack(side="right", fill="x", expand=True, padx=2)
        
        tk.Button(btn_f, text="6. EXPORT PDF REPORT", bg="#ddd", fg="#D32F2F", command=self.run_pdf_export).pack(fill="x", pady=5)
        self.log_text = tk.Text(self.tab_pipe, height=8, bg="#f0f0f0", state="disabled"); self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # --- DASHBOARD WITH SCROLLBAR ---
        dash_frame = ttk.Frame(self.tab_dash)
        dash_frame.pack(fill="both", expand=True)
        cols = ("NCU", "TCU", "Type", "Severity", "Details")
        self.tree = ttk.Treeview(dash_frame, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        vsb = ttk.Scrollbar(dash_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.on_double_click_plot)
        for tag, color in [("communication error", "#ffcccc"), ("critical", "#ffcccc"), ("high", "#ffe0b2"), ("medium", "#fff9c4"), ("low", "#f1f8e9")]:
            self.tree.tag_configure(tag, background=color)

    def browse(self):
        d = filedialog.askdirectory(); 
        if d: self.folder_path.set(d)

    def run_thread(self, target): threading.Thread(target=target).start()
    def run_step1(self): self.run_thread(self.exec_step1)
    def run_step2(self): self.run_thread(self.exec_step2)
    def run_step3_overview(self): self.run_thread(self.exec_overview)
    def run_step4_indiv(self): self.run_thread(self.exec_indiv)
    def run_step5_health(self): self.run_thread(self.exec_health)
    def run_pdf_export(self): messagebox.showinfo("Info", "PDF Export requires full PDF engine (omitted for brevity).")

    def exec_step1(self):
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        in_d = os.path.join(base, "01_Original_files", y, m, date)
        out_d = os.path.join(base, "02_DownSampled_Files", y, m, date)
        os.makedirs(out_d, exist_ok=True)
        files = glob.glob(os.path.join(in_d, "*.csv")) + glob.glob(os.path.join(in_d, "*.txt"))
        with ProcessPoolExecutor(self.cpu_cores) as e: 
            list(e.map(worker_extract, [(f, os.path.join(out_d, os.path.splitext(os.path.basename(f))[0]+".csv")) for f in files]))
        print("Extract Complete.")

    def exec_step2(self):
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        in_d = os.path.join(base, "02_DownSampled_Files", y, m, date)
        out_d = os.path.join(base, "03_Merged_files", y, m)
        os.makedirs(out_d, exist_ok=True)
        files = glob.glob(os.path.join(in_d, "*.csv"))
        dfs = []
        with ProcessPoolExecutor(self.cpu_cores) as e: dfs = list(e.map(worker_read_csv, files))
        if dfs:
            full = pd.concat(dfs, ignore_index=True)
            full["Timestamp"] = pd.to_datetime(full["Timestamp"], format="%d/%m/%Y %H:%M:%S.%f")
            final = full.groupby(["NCU", "TCU", "TC", "Parametro"]).resample("1min", on="Timestamp")["Valore"].mean().reset_index()
            final.to_csv(os.path.join(out_d, f"{date}_1min_merged.csv"), index=False)
            print("Merge Complete.")

    def exec_overview(self):
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        csv_path = os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv")
        out_dir = os.path.join(base, "04_Tracker_plots_angles", y, m, date)
        if os.path.exists(csv_path): worker_overview_analysis(csv_path, out_dir, date)

    def check_and_show_overview(self, suffix):
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        out_dir = os.path.join(base, "04_Tracker_plots_angles", y, m, date)
        fname = f"NCU_TCU_{date}_{suffix}.png"
        path = os.path.normpath(os.path.join(out_dir, fname))
        if not os.path.exists(path):
            print(f"Generating {suffix}...")
            self.exec_overview()
            if not os.path.exists(path): return
        os.startfile(path.replace("/", "\\"))

    def exec_indiv(self):
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        csv_path = os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv")
        out_dir = os.path.join(base, "04_Tracker_plots_angles", y, m, date, "each_tracker_plots")
        os.makedirs(out_dir, exist_ok=True)
        df = pd.read_csv(csv_path)
        groups = [(n,t,g.to_dict("list"), os.path.join(out_dir, f"TX_{n}_TCU_{int(t)}.png")) for (n,t), g in df.groupby(["NCU", "TCU"])]
        with ProcessPoolExecutor(self.cpu_cores) as e: list(e.map(worker_plot_file, groups))
        print("Individual Plots Complete.")

    def exec_health(self):
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        csv_path = os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv")
        if os.path.exists(csv_path):
            issues = worker_health_check(csv_path, date)
            self.root.after(0, lambda: self.show_results(issues))

    def show_results(self, issues):
        self.tabs.select(self.tab_dash)
        for r in self.tree.get_children(): self.tree.delete(r)
        sev_order = {"Communication Error": 0, "Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        issues.sort(key=lambda x: sev_order.get(x["Sev"], 99))
        for i in issues: 
            self.tree.insert("", "end", values=(i["NCU"], i["TCU"], i["Type"], i["Sev"], i["Msg"]), tags=(i["Sev"].lower(),))

    def on_double_click_plot(self, event):
        item = self.tree.selection()
        if not item: return
        vals = self.tree.item(item[0], "values"); ncu, tcu = vals[0], vals[1]
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        rel_path = os.path.join("04_Tracker_plots_angles", y, m, date, "each_tracker_plots", f"TX_{int(ncu)}_TCU_{int(tcu)}.png")
        full_path = os.path.normpath(os.path.join(base, rel_path)).replace("/", "\\")
        if os.path.exists(full_path):
            try: os.startfile(full_path)
            except OSError:
                import subprocess; subprocess.run(['explorer', full_path], shell=True)
        else:
            messagebox.showwarning("File Missing", f"Plot not found:\n{full_path}\n\nRun 'Generate Individual Plots' first.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = TrackerSuiteApp(root)
    root.mainloop()