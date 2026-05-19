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
from datetime import datetime

# --- NEW IMPORT FOR CALENDAR ---
from tkcalendar import DateEntry 
from PIL import Image, ImageTk 

# Matplotlib for Live Plotting
import matplotlib
matplotlib.use("TkAgg") 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# ==============================================================================
# WORKER FUNCTIONS
# ==============================================================================

def worker_extract(args):
    infile, outfile = args
    possible_encodings = ["utf-8-sig", "utf-16", "latin1"]
    lines = None
    for enc in possible_encodings:
        try:
            with open(infile, "r", encoding=enc) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError: continue  
    if not lines: return 0

    count = 0
    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Tag", "Name", "Value", "Unit", "Type", "Timestamp"])
        for line in lines:
            if "Angolo" in line or "angolo" in line:
                parts = [p.strip() for p in line.strip().split(";")]
                if len(parts) >= 6:
                    name = parts[1].lower()
                    if "angolo target" in name or "angolo attuale" in name:
                        writer.writerow(parts[:6])
                        count += 1
    return count

def worker_read_csv(filepath):
    pattern = re.compile(r"Data_Mod_NCU_(\d+)_TCU_(\d+)\.TC(\d+),([^,]+),([^,]+),([^,]+),([^,]+),(.+)")
    rows = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = pattern.match(line.strip())
                if m:
                    rows.append({
                        "NCU": m.group(1), "TCU": m.group(2), "TC": m.group(3),
                        "Parametro": m.group(4), "Valore": m.group(5),
                        "Timestamp": m.group(8)
                    })
        return pd.DataFrame(rows)
    except: return pd.DataFrame()

def worker_plot_file(args):
    import matplotlib
    matplotlib.use('Agg') 
    import matplotlib.pyplot as plt
    ncu, tcu, data_dict, out_path = args
    try:
        df = pd.DataFrame(data_dict)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df["Valore"] = pd.to_numeric(df["Valore"])
        target = df[df["TC"] == 4].sort_values("Timestamp")
        actual = df[df["TC"] == 5].sort_values("Timestamp")
        if target.empty and actual.empty: return "Empty"

        fig, ax = plt.subplots(figsize=(10, 6))
        if not target.empty: ax.plot(target["Timestamp"], target["Valore"], label="Target", lw=1)
        if not actual.empty: ax.plot(actual["Timestamp"], actual["Valore"], label="Actual", lw=1)
        ax.set_title(f"NCU {ncu} - TCU {tcu}")
        ax.grid(True); ax.legend()
        fig.tight_layout(); fig.savefig(out_path, dpi=80); plt.close(fig)
        return "OK"
    except: plt.close('all'); return "Error"

# --- NEW WORKER: OVERVIEW & THRESHOLD ANALYSIS ---
def worker_overview_analysis(input_csv, output_dir, date_str, threshold=28.0):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        base_name = f"NCU_TCU_{date_str}"
        
        # Load Data
        df = pd.read_csv(input_csv, dtype=str)
        df["NCU"] = pd.to_numeric(df["NCU"], errors="coerce")
        df["TCU"] = pd.to_numeric(df["TCU"], errors="coerce")
        df["TC"] = pd.to_numeric(df["TC"], errors="coerce")
        df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        
        df = df.dropna(subset=["NCU", "TCU", "TC", "Valore", "Timestamp"])
        df = df[df["TC"].isin([4, 5])]
        
        all_ncus = sorted(df["NCU"].unique())
        
        series_by_ncu = {}
        below_thresh_rows = []
        below_thresh_pairs = set()
        
        # Processing
        for ncu in all_ncus:
            df_ncu = df[df["NCU"] == ncu]
            tcu_map = {}
            tcus = sorted(df_ncu["TCU"].unique())
            
            for tcu in tcus:
                part = df_ncu[df_ncu["TCU"] == tcu]
                target = part[part["TC"] == 4][["Timestamp", "Valore"]].rename(columns={"Valore": "target"})
                actual = part[part["TC"] == 5][["Timestamp", "Valore"]].rename(columns={"Valore": "actual"})
                
                # Merge Asof
                merged = pd.merge_asof(
                    target.sort_values("Timestamp"),
                    actual.sort_values("Timestamp"),
                    on="Timestamp", direction="nearest", tolerance=pd.Timedelta("1s")
                ).dropna()
                
                if merged.empty: continue
                
                tcu_map[tcu] = merged
                
                # Threshold Check
                low = merged[merged["actual"] < threshold]
                if not low.empty:
                    below_thresh_pairs.add((ncu, tcu))
                    for _, row in low.iterrows():
                        below_thresh_rows.append({
                            "NCU": ncu, "TCU": tcu, "Timestamp": row["Timestamp"], "Angle": row["actual"]
                        })
            series_by_ncu[ncu] = tcu_map

        # Plotting Function Internal
        def make_plot_internal(ncus_to_plot, filename, title_suf):
            fig, ax = plt.subplots(figsize=(20, 4))
            # Colors
            color_map = {1: plt.cm.Blues, 2: plt.cm.Greens, 3: plt.cm.Reds}
            
            for ncu in ncus_to_plot:
                tcu_map = series_by_ncu.get(ncu, {})
                if not tcu_map: continue
                
                cmap = color_map.get(ncu, plt.cm.tab10)
                tcus_sorted = sorted(tcu_map.keys())
                N = len(tcus_sorted)
                shades = [cmap(i / max(N - 1, 1)) for i in range(N)]
                
                for i, tcu in enumerate(tcus_sorted):
                    merged = tcu_map[tcu]
                    ax.plot(merged["Timestamp"], merged["actual"], color=shades[i], linewidth=0.8)
            
            ax.set_title(f"Actual Angle - {title_suf}")
            ax.set_ylabel("Angle (°)")
            ax.grid(True)
            
            # Legend & Text box
            legend_lines = []
            legend_lbls = []
            for ncu in ncus_to_plot:
                if ncu in series_by_ncu and series_by_ncu[ncu]:
                    legend_lbls.append(f"NCU {ncu}")
                    cmap = color_map.get(ncu, plt.cm.tab10)
                    legend_lines.append(plt.Line2D([0], [0], color=cmap(0.7), lw=4))
            
            if legend_lines: ax.legend(legend_lines, legend_lbls, loc="upper right")
            
            local_pairs = sorted(p for p in below_thresh_pairs if p[0] in ncus_to_plot)
            if local_pairs:
                txt = "Low Angle:\n" + "\n".join([f"N{n}-T{t}" for n, t in local_pairs])
            else: txt = "No Low Angles"
            
            ax.text(0.01, 0.99, txt, transform=ax.transAxes, va="top", fontsize=8, 
                    bbox=dict(facecolor="white", alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(filename, dpi=300)
            plt.close(fig)

        # Generate Plots
        # 1. ALL
        make_plot_internal(all_ncus, os.path.join(output_dir, f"{base_name}_ALL.png"), "All NCUs")
        
        # 2. Per NCU
        for ncu in all_ncus:
            make_plot_internal([ncu], os.path.join(output_dir, f"{base_name}_NCU{ncu}.png"), f"NCU {ncu}")
            
        # Generate CSV
        if below_thresh_rows:
            csv_out = os.path.join(output_dir, f"{base_name}_below_{int(threshold)}deg.csv")
            df_low = pd.DataFrame(below_thresh_rows)
            df_low["Angle"] = pd.to_numeric(df_low["Angle"]).round(2)
            df_low.sort_values(["NCU", "TCU", "Timestamp"], inplace=True)
            df_low.to_csv(csv_out, index=False, sep=";", decimal=",")
            
        return f"Created plots for {len(all_ncus)} NCUs and 1 CSV."
        
    except Exception as e:
        return f"Error: {str(e)}"

def worker_health_check(csv_path, angle_th, dev_th):
    issues = []
    try:
        df = pd.read_csv(csv_path, dtype=str)
        df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df["NCU"] = pd.to_numeric(df["NCU"], errors="coerce")
        df["TCU"] = pd.to_numeric(df["TCU"], errors="coerce")
        df["TC"] = pd.to_numeric(df["TC"], errors="coerce")
        df = df[df["TC"].isin([4, 5])].dropna(subset=["Valore"])

        for (ncu, tcu), g in df.groupby(["NCU", "TCU"]):
            target = g[g["TC"] == 4]["Valore"]
            actual = g[g["TC"] == 5]["Valore"]
            
            if len(actual) < 10:
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "DATA LOSS", "Msg": f"Only {len(actual)} pts", "Sev": "High"})
                continue
            if target.std() > 5 and actual.std() < 1.0:
                 issues.append({"NCU": ncu, "TCU": tcu, "Type": "STUCK", "Msg": "Target moving, Actual flat", "Sev": "Critical"})

            t_df = g[g["TC"] == 4].set_index("Timestamp")["Valore"]
            a_df = g[g["TC"] == 5].set_index("Timestamp")["Valore"]
            common = t_df.index.intersection(a_df.index)
            if len(common) > 0:
                diff = (t_df[common] - a_df[common]).abs().mean()
                if diff > float(dev_th):
                    issues.append({"NCU": ncu, "TCU": tcu, "Type": "DEVIATION", "Msg": f"Avg Diff {diff:.1f}°", "Sev": "Medium"})
            
            if not actual.empty and actual.min() < float(angle_th):
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "LOW ANGLE", "Msg": f"Min {actual.min():.1f}°", "Sev": "High"})
        return issues
    except Exception as e: return [{"NCU":0, "TCU":0, "Type": "ERROR", "Msg": str(e), "Sev": "Critical"}]

# ==============================================================================
# GUI APPLICATION
# ==============================================================================

class TextRedirector:
    def __init__(self, widget): self.widget = widget
    def write(self, s):
        self.widget.config(state="normal"); self.widget.insert("end", s); self.widget.see("end")
        self.widget.config(state="disabled"); self.widget.update_idletasks()
    def flush(self): pass

class TrackerSuiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SCADA Tracker Suite v2.4 (Overview Added)")
        self.root.geometry("1100x900")
        
        # --- LOGO & ICON ---
        self.logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(self.logo_path):
            try:
                img = tk.PhotoImage(file=self.logo_path)
                self.root.iconphoto(False, img)
            except: pass

        self.cpu_cores = min(multiprocessing.cpu_count(), 6)
        
        # Variables
        self.folder_path = tk.StringVar()
        self.date_val = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

        self.setup_layout()
        sys.stdout = TextRedirector(self.log_text)
        
        # Bind Triggers
        self.folder_path.trace("w", self.trigger_check)
        self.date_val.trace("w", self.trigger_check)

    def setup_layout(self):
        # --- BANNER LOGO ---
        logo_frame = tk.Frame(self.root, bg="white", height=80)
        logo_frame.pack(fill="x", side="top")
        if os.path.exists(self.logo_path):
            try:
                load = Image.open(self.logo_path)
                aspect = load.width / load.height
                new_h = 60; new_w = int(new_h * aspect)
                render = ImageTk.PhotoImage(load.resize((new_w, new_h), Image.LANCZOS))
                self.logo_image = render 
                tk.Label(logo_frame, image=render, bg="white", bd=0).pack(pady=10)
            except: 
                tk.Label(logo_frame, text="SCADA TRACKER SUITE", bg="white", font=("Arial", 16, "bold")).pack(pady=20)
        else:
            tk.Label(logo_frame, text="SCADA TRACKER SUITE", bg="white", font=("Arial", 16, "bold")).pack(pady=20)

        # --- CONFIGURATION ---
        cfg = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        cfg.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(cfg, text="Root Folder:").pack(side="left")
        ttk.Entry(cfg, textvariable=self.folder_path, width=50).pack(side="left", padx=5)
        ttk.Button(cfg, text="Browse", command=self.browse).pack(side="left")
        
        # --- CALENDAR WIDGET ---
        ttk.Label(cfg, text="Date:").pack(side="left", padx=(20, 5))
        self.cal = DateEntry(cfg, width=12, background='darkblue',
                             foreground='white', borderwidth=2,
                             date_pattern='yyyy-mm-dd',
                             textvariable=self.date_val)
        self.cal.pack(side="left", padx=5)
        self.cal.bind("<<DateEntrySelected>>", self.trigger_check)

        ttk.Button(cfg, text="Refresh Status", command=self.check_status).pack(side="right")

        # --- TABS ---
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab_pipe = ttk.Frame(self.tabs); self.tabs.add(self.tab_pipe, text="Pipeline")
        self.tab_dash = ttk.Frame(self.tabs); self.tabs.add(self.tab_dash, text="Health Dashboard")

        # --- PIPELINE CONTROLS ---
        btn_f = ttk.Frame(self.tab_pipe)
        btn_f.pack(fill="x", pady=10, padx=50)

        # Step 1 & 2
        self.btn_step1 = tk.Button(btn_f, text="1. EXTRACT", bg="#ddd", command=self.run_step1)
        self.btn_step1.pack(fill="x", pady=2)
        
        self.btn_step2 = tk.Button(btn_f, text="2. MERGE", bg="#ddd", state="disabled", command=self.run_step2)
        self.btn_step2.pack(fill="x", pady=2)
        
        ttk.Separator(btn_f, orient="horizontal").pack(fill="x", pady=10)
        
        # Step 3: OVERVIEW (New)
        self.btn_step3_overview = tk.Button(btn_f, text="3. GENERATE OVERVIEW (Merged Analysis)", bg="#ddd", state="disabled", font=("Arial", 9, "bold"), command=self.run_step_overview)
        self.btn_step3_overview.pack(fill="x", pady=5)

        ttk.Separator(btn_f, orient="horizontal").pack(fill="x", pady=10)
        
        # Split Frame for Detailed & Health
        split = ttk.Frame(btn_f); split.pack(fill="x")
        
        self.btn_step3_indiv = tk.Button(split, text="4. GENERATE INDIVIDUAL PLOTS\n(Optional Batch - Slow)", bg="#ddd", state="disabled", command=self.run_step3_indiv)
        self.btn_step3_indiv.pack(side="left", fill="x", expand=True, padx=(0,5))
        
        self.btn_step4 = tk.Button(split, text="5. RUN HEALTH CHECK\n(Fast Analysis)", bg="#ddd", state="disabled", command=self.run_step4)
        self.btn_step4.pack(side="right", fill="x", expand=True, padx=(5,0))

        self.log_text = tk.Text(self.tab_pipe, height=10, bg="#f0f0f0", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # --- DASHBOARD ---
        tk.Label(self.tab_dash, text="Double-click a row to see LIVE PLOT.", fg="blue").pack(pady=5)
        cols = ("NCU", "TCU", "Type", "Severity", "Details")
        self.tree = ttk.Treeview(self.tab_dash, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(side="left", fill="both", expand=True)
        scrl = ttk.Scrollbar(self.tab_dash, orient="vertical", command=self.tree.yview)
        scrl.pack(side="right", fill="y"); self.tree.configure(yscroll=scrl.set)
        self.tree.bind("<Double-1>", self.on_double_click_plot)

    def browse(self):
        d = filedialog.askdirectory()
        if d: self.folder_path.set(d)

    def trigger_check(self, *args): self.root.after(500, self.check_status)

    def check_status(self):
        base, date = self.folder_path.get(), self.date_val.get()
        if not base or not date: return
        p_raw = os.path.join(base, "01_Original_files", date)
        p_down = os.path.join(base, "02_DownSampled_files", date)
        p_merged = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        
        # Step 1
        if os.path.exists(p_raw): self.btn_step1.config(state="normal", bg="#e1f5fe")
        else: self.btn_step1.config(state="disabled", bg="#ddd")
        
        # Step 2
        if os.path.exists(p_down) and glob.glob(os.path.join(p_down, "*.csv")):
            self.btn_step2.config(state="normal", bg="#e1f5fe"); self.btn_step1.config(bg="#c8e6c9", text="1. EXTRACT (Done)")
        else: self.btn_step2.config(state="disabled", bg="#ddd")
        
        # Step 3, 4, 5 depend on Merged File
        if os.path.exists(p_merged):
            self.btn_step2.config(bg="#c8e6c9", text="2. MERGE (Done)")
            
            # 3. Overview
            self.btn_step3_overview.config(state="normal", bg="#FFD54F") # Gold Color
            
            # 4. Individual Plots
            self.btn_step3_indiv.config(state="normal", bg="#e1f5fe")
            
            # 5. Health Check
            self.btn_step4.config(state="normal", bg="#4CAF50", fg="white")
        else:
            self.btn_step3_overview.config(state="disabled", bg="#ddd")
            self.btn_step3_indiv.config(state="disabled", bg="#ddd")
            self.btn_step4.config(state="disabled", bg="#ddd")

    def run_threading(self, target): threading.Thread(target=target).start()
    def run_step1(self): self.run_threading(self.execute_step1)
    def run_step2(self): self.run_threading(self.execute_step2)
    def run_step_overview(self): self.run_threading(self.execute_step_overview)
    def run_step3_indiv(self): self.run_threading(self.execute_step3_indiv)
    def run_step4(self): self.run_threading(self.execute_step4)

    def execute_step1(self):
        print("Starting Step 1..."); base, date = self.folder_path.get(), self.date_val.get()
        in_d = os.path.join(base, "01_Original_files", date); out_d = os.path.join(base, "02_DownSampled_files", date)
        os.makedirs(out_d, exist_ok=True); files = glob.glob(os.path.join(in_d, "*.csv"))
        tasks = [(f, os.path.join(out_d, os.path.basename(f))) for f in files]
        with ProcessPoolExecutor(max_workers=self.cpu_cores) as exc: list(exc.map(worker_extract, tasks))
        print("Step 1 Done."); self.root.after(0, self.check_status)

    def execute_step2(self):
        print("Starting Step 2..."); base, date = self.folder_path.get(), self.date_val.get()
        in_d = os.path.join(base, "02_DownSampled_files", date); out_d = os.path.join(base, "03_Merged_files")
        os.makedirs(out_d, exist_ok=True); files = glob.glob(os.path.join(in_d, "*.csv"))
        with ProcessPoolExecutor(max_workers=self.cpu_cores) as exc: dfs = list(exc.map(worker_read_csv, files))
        full = pd.concat(dfs, ignore_index=True)
        print("Resampling..."); full["Timestamp"] = pd.to_datetime(full["Timestamp"], format="%d/%m/%Y %H:%M:%S.%f")
        full["Valore"] = pd.to_numeric(full["Valore"], errors="coerce")
        full["NCU"] = pd.to_numeric(full["NCU"]).astype(str).str.zfill(2); full["TCU"] = pd.to_numeric(full["TCU"]).astype(str).str.zfill(3); full["TC"] = pd.to_numeric(full["TC"]).astype(str).str.zfill(2)
        res = full.set_index("Timestamp").groupby(["NCU", "TCU", "TC", "Parametro"]).resample("1min")["Valore"].mean().reset_index()
        res.to_csv(os.path.join(out_d, f"{date}_1min_merged.csv"), index=False)
        print("Step 2 Done."); self.root.after(0, self.check_status)

    def execute_step_overview(self):
        print("Starting Step 3: Overview Analysis..."); base, date = self.folder_path.get(), self.date_val.get()
        csv_p = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        out_d = os.path.join(base, "04_Tracker_plots_angles", date)
        
        # Run logic directly in thread (since it uses Agg plotting inside)
        # or use Pool if heavy. Thread is fine for single large task.
        msg = worker_overview_analysis(csv_p, out_d, date, 28.0)
        print(msg)
        print("Overview Done."); self.root.after(0, self.check_status)

    def execute_step3_indiv(self):
        print("Starting Individual Plots..."); base, date = self.folder_path.get(), self.date_val.get()
        csv_p = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        out_d = os.path.join(base, "04_Tracker_plots_angles", date, "each_tracker_plots")
        os.makedirs(out_d, exist_ok=True); df = pd.read_csv(csv_p)
        tasks = [(n, t, g.to_dict("list"), os.path.join(out_d, f"TX_{n}_TCU_{int(t)}.png")) for (n,t), g in df.groupby(["NCU", "TCU"])]
        with ProcessPoolExecutor(max_workers=4) as exc: list(exc.map(worker_plot_file, tasks))
        print("Individual Plots Done."); self.root.after(0, self.check_status)

    def execute_step4(self):
        print("Starting Health Check..."); base, date = self.folder_path.get(), self.date_val.get()
        csv_p = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        issues = worker_health_check(csv_p, 28, 20)
        self.root.after(0, lambda: self.show_results(issues))

    def show_results(self, issues):
        self.tabs.select(self.tab_dash)
        for row in self.tree.get_children(): self.tree.delete(row)
        for i in issues:
            tag = "crit" if i["Sev"] == "Critical" else "high"
            self.tree.insert("", "end", values=(i["NCU"], i["TCU"], i["Type"], i["Sev"], i["Msg"]), tags=(tag,))
        self.tree.tag_configure("crit", background="#ffcccc"); self.tree.tag_configure("high", background="#fff3e0")
        messagebox.showinfo("Done", f"Found {len(issues)} issues.")

    def on_double_click_plot(self, event):
        item = self.tree.selection()
        if not item: return
        vals = self.tree.item(item[0], "values"); ncu, tcu = vals[0], vals[1]
        
        rel_path = os.path.join("04_Tracker_plots_angles", self.date_val.get(), "each_tracker_plots", f"TX_{ncu}_TCU_{int(tcu)}.png")
        full_path = os.path.normpath(os.path.join(self.folder_path.get(), rel_path))

        if os.path.exists(full_path):
            try: os.startfile(full_path)
            except OSError:
                import subprocess; subprocess.run(['explorer', full_path], shell=True)
        else:
            print(f"File missing ({full_path}). Generating Live Plot...")
            self.plot_live_popup(ncu, tcu)

    def plot_live_popup(self, ncu, tcu):
        try:
            csv_path = os.path.join(self.folder_path.get(), "03_Merged_files", f"{self.date_val.get()}_1min_merged.csv")
            df = pd.read_csv(csv_path, dtype=str)
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
            mask = (df["NCU"].astype(int) == int(ncu)) & (df["TCU"].astype(int) == int(tcu))
            subset = df[mask]
            target = subset[subset["TC"] == "04"].sort_values("Timestamp")
            actual = subset[subset["TC"] == "05"].sort_values("Timestamp")

            top = tk.Toplevel(self.root); top.title(f"LIVE VIEW: NCU {ncu} - TCU {tcu}"); top.geometry("900x500")
            fig = Figure(figsize=(8, 4), dpi=100); ax = fig.add_subplot(111)
            if not target.empty: ax.plot(target["Timestamp"], target["Valore"], label="Target", color="blue")
            if not actual.empty: ax.plot(actual["Timestamp"], actual["Valore"], label="Actual", color="red", linestyle="--")
            ax.set_title(f"NCU {ncu} - TCU {tcu} (Live Generated)"); ax.set_ylabel("Angle (°)"); ax.legend(); ax.grid(True)
            canvas = FigureCanvasTkAgg(fig, master=top); canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e: messagebox.showerror("Plot Error", f"Could not generate live plot:\n{e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = TrackerSuiteApp(root)
    root.mainloop()