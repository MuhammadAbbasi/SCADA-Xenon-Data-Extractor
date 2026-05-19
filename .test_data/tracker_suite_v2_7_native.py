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

# --- LIBRARIES FOR IMAGE & PLOTTING ---
from PIL import Image, ImageTk 
import matplotlib
matplotlib.use("TkAgg") 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages 

# NOTE: 'tkcalendar' REMOVED to fix button issues and simplify EXE generation.

# ==============================================================================
# WORKER FUNCTIONS
# ==============================================================================

def worker_extract(args):
    infile, outfile = args
    possible_encodings = ["utf-8-sig", "utf-16", "latin1"]
    lines = None
    for enc in possible_encodings:
        try:
            with open(infile, "r", encoding=enc) as f: lines = f.readlines(); break
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
                        writer.writerow(parts[:6]); count += 1
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
    import matplotlib.pyplot as plt
    matplotlib.use('Agg') 
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
        ax.set_title(f"NCU {ncu} - TCU {tcu}"); ax.grid(True); ax.legend()
        fig.tight_layout(); fig.savefig(out_path, dpi=300); plt.close(fig)
        return "OK"
    except: plt.close('all'); return "Error"

def worker_overview_analysis(input_csv, output_dir, date_str, threshold=28.0):
    import matplotlib.pyplot as plt
    matplotlib.use('Agg')
    try:
        os.makedirs(output_dir, exist_ok=True)
        base_name = f"NCU_TCU_{date_str}"
        df = pd.read_csv(input_csv, dtype=str)
        cols = ["NCU", "TCU", "TC", "Valore"]; df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=cols + ["Timestamp"])
        df = df[df["TC"].isin([4, 5])]
        
        all_ncus = sorted(df["NCU"].unique())
        series_by_ncu = {}
        below_thresh_rows = []
        
        for ncu in all_ncus:
            df_ncu = df[df["NCU"] == ncu]
            tcu_map = {}
            for tcu in df_ncu["TCU"].unique():
                part = df_ncu[df_ncu["TCU"] == tcu]
                target = part[part["TC"] == 4][["Timestamp", "Valore"]].rename(columns={"Valore": "target"})
                actual = part[part["TC"] == 5][["Timestamp", "Valore"]].rename(columns={"Valore": "actual"})
                merged = pd.merge_asof(target.sort_values("Timestamp"), actual.sort_values("Timestamp"), on="Timestamp", direction="nearest", tolerance=pd.Timedelta("1s")).dropna()
                if not merged.empty:
                    tcu_map[tcu] = merged
                    low = merged[merged["actual"] < threshold]
                    for _, row in low.iterrows():
                        below_thresh_rows.append({"NCU": ncu, "TCU": tcu, "Timestamp": row["Timestamp"], "Angle": row["actual"]})
            series_by_ncu[ncu] = tcu_map

        def make_plot(ncus, fname, title):
            fig, ax = plt.subplots(figsize=(15, 4))
            colors = {1: plt.cm.Blues, 2: plt.cm.Greens, 3: plt.cm.Reds}
            for ncu in ncus:
                tmap = series_by_ncu.get(ncu, {})
                if not tmap: continue
                cmap = colors.get(ncu, plt.cm.tab10)
                tcus = sorted(tmap.keys()); N = len(tcus)
                for i, tcu in enumerate(tcus):
                    d = tmap[tcu]
                    ax.plot(d["Timestamp"], d["actual"], color=cmap(i/max(N-1,1)), lw=0.8)
            ax.set_title(title); ax.grid(True); ax.set_ylabel("Angle (°)")
            fig.tight_layout(); fig.savefig(fname, dpi=600); plt.close(fig)

        make_plot(all_ncus, os.path.join(output_dir, f"{base_name}_ALL.png"), "All Trackers")
        for ncu in all_ncus:
            make_plot([ncu], os.path.join(output_dir, f"{base_name}_NCU{ncu}.png"), f"NCU {ncu} Overview")
            
        if below_thresh_rows:
            pd.DataFrame(below_thresh_rows).to_csv(os.path.join(output_dir, f"{base_name}_below_{int(threshold)}deg.csv"), index=False, sep=";")
            
        return "Overview Generation Complete"
    except Exception as e: return f"Error: {e}"

def worker_health_check(csv_path, angle_th, dev_th):
    issues = []
    try:
        df = pd.read_csv(csv_path, dtype=str)
        cols = ["Valore", "NCU", "TCU", "TC"]; df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df = df[df["TC"].isin([4, 5])].dropna(subset=["Valore"])
        for (ncu, tcu), g in df.groupby(["NCU", "TCU"]):
            target = g[g["TC"] == 4]["Valore"]
            actual = g[g["TC"] == 5]["Valore"]
            if len(actual) < 10:
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "DATA LOSS", "Msg": f"{len(actual)} pts", "Sev": "High"}); continue
            if target.std() > 5 and actual.std() < 1.0:
                 issues.append({"NCU": ncu, "TCU": tcu, "Type": "STUCK", "Msg": "Target moving, Actual flat", "Sev": "Critical"})
            t_df = g[g["TC"] == 4].set_index("Timestamp")["Valore"]
            a_df = g[g["TC"] == 5].set_index("Timestamp")["Valore"]
            common = t_df.index.intersection(a_df.index)
            if len(common) > 0:
                diff = (t_df[common] - a_df[common]).abs().mean()
                if diff > float(dev_th): issues.append({"NCU": ncu, "TCU": tcu, "Type": "DEVIATION", "Msg": f"Avg Diff {diff:.1f}°", "Sev": "Medium"})
            if not actual.empty and actual.min() < float(angle_th):
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "LOW ANGLE", "Msg": f"Min {actual.min():.1f}°", "Sev": "High"})
        return issues
    except Exception as e: return [{"NCU":0, "TCU":0, "Type": "ERROR", "Msg": str(e), "Sev": "Critical"}]

def worker_generate_pdf(csv_path, overview_dir, output_pdf, date_str):
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages
    
    matplotlib.use('Agg')
    
    try:
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
        
        with PdfPages(output_pdf) as pdf:
            print("Adding Overview plots to PDF...")
            search_pattern = os.path.join(overview_dir, f"*{date_str}*.png")
            overview_files = sorted(glob.glob(search_pattern))
            overview_files = [f for f in overview_files if "TX_" not in os.path.basename(f) and "each_tracker" not in f]
            
            for img_path in overview_files:
                try:
                    img = mpimg.imread(img_path)
                    fig_img, ax_img = plt.subplots(figsize=(15.5, 11.2))
                    ax_img.imshow(img); ax_img.axis('off')
                    ax_img.set_title(f"Overview: {os.path.basename(img_path)}", fontsize=10)
                    pdf.savefig(fig_img, orientation='landscape', bbox_inches='tight'); plt.close(fig_img)
                except: 
                    print(f"  Warning: Could not add image {img_path} to PDF.")

            print("Generating 370+ individual plots directly to PDF...")
            df = pd.read_csv(csv_path, dtype=str)
            cols = ["Valore", "NCU", "TCU", "TC"]; df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            df = df.dropna(subset=["Valore"])
            
            count = 0
            for (ncu, tcu), group in df.groupby(["NCU", "TCU"]):
                count += 1
                if count % 20 == 0: print(f"  Processed {count} trackers...", end="\r")
                
                target = group[group["TC"] == 4].sort_values("Timestamp")
                actual = group[group["TC"] == 5].sort_values("Timestamp")
                
                fig, ax = plt.subplots(figsize=(10, 6))
                if not target.empty: ax.plot(target["Timestamp"], target["Valore"], label="Target", color="blue", lw=1)
                if not actual.empty: ax.plot(actual["Timestamp"], actual["Valore"], label="Actual", color="red", lw=1)
                
                ax.set_title(f"Tracker Detail: NCU {int(ncu)} - TCU {int(tcu)}")
                ax.set_ylabel("Angle (°)"); ax.set_xlabel("Time"); ax.grid(True, alpha=0.3)
                ax.legend(loc="upper right")
                
                if not actual.empty:
                    stats = f"Min: {actual['Valore'].min():.1f}° | Max: {actual['Valore'].max():.1f}°"
                    ax.text(0.02, 0.02, stats, transform=ax.transAxes, fontsize=8, bbox=dict(facecolor='white', alpha=0.8))

                pdf.savefig(fig); plt.close(fig)
                
        return f"PDF Report Generated successfully!\nSaved to: {output_pdf}"

    except Exception as e: return f"Critical Error generating PDF: {str(e)}"

# ==============================================================================
# GUI CLASS
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
        self.root.title("GET - SCADA Tracker Suite")
        self.root.geometry("850x650")
        
        self.logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(self.logo_path):
            try: self.root.iconphoto(False, tk.PhotoImage(file=self.logo_path))
            except: pass

        self.cpu_cores = min(multiprocessing.cpu_count(), 6)
        
        # State Variables
        self.folder_path = tk.StringVar()
        self.date_val = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

        # Date Components
        today = datetime.now()
        self.var_year = tk.StringVar(value=str(today.year))
        self.var_month = tk.StringVar(value=str(today.month).zfill(2))
        self.var_day = tk.StringVar(value=str(today.day).zfill(2))

        self.setup_layout()
        sys.stdout = TextRedirector(self.log_text)
        
        # Update triggers
        self.folder_path.trace("w", self.trigger_check)
        self.var_year.trace("w", self.update_date_str)
        self.var_month.trace("w", self.update_date_str)
        self.var_day.trace("w", self.update_date_str)

    def update_date_str(self, *args):
        # Combine spinboxes into the master date string
        y = self.var_year.get()
        m = self.var_month.get().zfill(2)
        d = self.var_day.get().zfill(2)
        self.date_val.set(f"{y}-{m}-{d}")
        self.trigger_check()

    def setup_layout(self):
        # BANNER
        logo_frame = tk.Frame(self.root, bg="white", height=80)
        logo_frame.pack(fill="x", side="top")
        if os.path.exists(self.logo_path):
            try:
                load = Image.open(self.logo_path); aspect = load.width / load.height
                render = ImageTk.PhotoImage(load.resize((int(60*aspect), 60), Image.LANCZOS))
                self.logo_image = render 
                tk.Label(logo_frame, image=render, bg="white", bd=0).pack(pady=10)
            except: tk.Label(logo_frame, text="SCADA SUITE", bg="white", font=("Arial", 16)).pack(pady=20)
        else: tk.Label(logo_frame, text="SCADA SUITE", bg="white", font=("Arial", 16)).pack(pady=20)

        # CONFIG
        cfg = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        cfg.pack(fill="x", padx=10, pady=5)
        
        # Row 1: Folder
        f_frame = ttk.Frame(cfg)
        f_frame.pack(fill="x", pady=2)
        ttk.Label(f_frame, text="Root Folder:").pack(side="left")
        ttk.Entry(f_frame, textvariable=self.folder_path, width=60).pack(side="left", padx=5)
        ttk.Button(f_frame, text="Browse", command=self.browse).pack(side="left")

        # Row 2: Native Date Selector
        d_frame = ttk.Frame(cfg)
        d_frame.pack(fill="x", pady=5)
        ttk.Label(d_frame, text="Date Selection:").pack(side="left")
        
        # Year
        ttk.Spinbox(d_frame, from_=2020, to=2030, textvariable=self.var_year, width=5).pack(side="left", padx=(5,0))
        ttk.Label(d_frame, text="-").pack(side="left")
        # Month
        ttk.Spinbox(d_frame, from_=1, to=12, textvariable=self.var_month, width=3, format="%02.0f").pack(side="left")
        ttk.Label(d_frame, text="-").pack(side="left")
        # Day
        ttk.Spinbox(d_frame, from_=1, to=31, textvariable=self.var_day, width=3, format="%02.0f").pack(side="left")
        
        # Refresh Button
        ttk.Button(d_frame, text="Refresh Status", command=self.check_status).pack(side="left", padx=20)

        # TABS
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=5)
        self.tab_pipe = ttk.Frame(self.tabs); self.tabs.add(self.tab_pipe, text="Pipeline")
        self.tab_dash = ttk.Frame(self.tabs); self.tabs.add(self.tab_dash, text="Health Dashboard")

        # CONTROLS
        btn_f = ttk.Frame(self.tab_pipe)
        btn_f.pack(fill="x", pady=10, padx=50)

        self.btn_step1 = tk.Button(btn_f, text="1. EXTRACT", bg="#ddd", command=self.run_step1)
        self.btn_step1.pack(fill="x", pady=2)
        self.btn_step2 = tk.Button(btn_f, text="2. MERGE", bg="#ddd", state="disabled", command=self.run_step2)
        self.btn_step2.pack(fill="x", pady=2)
        
        ttk.Separator(btn_f, orient="horizontal").pack(fill="x", pady=8)
        
        self.btn_step3 = tk.Button(btn_f, text="3. GENERATE OVERVIEW (Merged)", bg="#ddd", state="disabled", font=("Arial", 9, "bold"), command=self.run_step3_overview)
        self.btn_step3.pack(fill="x", pady=5)
        
        split = ttk.Frame(btn_f); split.pack(fill="x")
        self.btn_step4 = tk.Button(split, text="4. GENERATE INDIVIDUAL PLOTS\n(Images in Folder)", bg="#ddd", state="disabled", command=self.run_step4_indiv)
        self.btn_step4.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.btn_step5 = tk.Button(split, text="5. RUN HEALTH CHECK\n(Fast Analysis)", bg="#ddd", state="disabled", command=self.run_step5_health)
        self.btn_step5.pack(side="right", fill="x", expand=True, padx=(5,0))
        
        ttk.Separator(btn_f, orient="horizontal").pack(fill="x", pady=8)
        
        self.btn_pdf = tk.Button(btn_f, text="6. EXPORT FULL PDF REPORT\n(Overview + All 370 Trackers -> '05_Tracker_report_pdf')", bg="#ddd", state="disabled", font=("Arial", 10, "bold"), fg="#D32F2F", command=self.run_pdf_export)
        self.btn_pdf.pack(fill="x", pady=5)

        self.log_text = tk.Text(self.tab_pipe, height=8, bg="#f0f0f0", state="disabled"); self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # DASHBOARD
        cols = ("NCU", "TCU", "Type", "Severity", "Details")
        self.tree = ttk.Treeview(self.tab_dash, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(side="left", fill="both", expand=True)
        scrl = ttk.Scrollbar(self.tab_dash, orient="vertical", command=self.tree.yview)
        scrl.pack(side="right", fill="y"); self.tree.configure(yscroll=scrl.set)
        self.tree.bind("<Double-1>", self.on_double_click_plot)

    def browse(self):
        d = filedialog.askdirectory(); 
        if d: self.folder_path.set(d)
    def trigger_check(self, *args): self.root.after(500, self.check_status)

    def check_status(self):
        base, date = self.folder_path.get(), self.date_val.get()
        if not base or not date: return
        p_raw = os.path.join(base, "01_Original_files", date)
        p_down = os.path.join(base, "02_DownSampled_files", date)
        p_merged = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        
        if os.path.exists(p_raw): self.btn_step1.config(state="normal", bg="#e1f5fe")
        else: self.btn_step1.config(state="disabled", bg="#ddd")
        if os.path.exists(p_down) and glob.glob(os.path.join(p_down, "*.csv")):
            self.btn_step2.config(state="normal", bg="#e1f5fe"); self.btn_step1.config(bg="#c8e6c9", text="1. EXTRACT (Done)")
        else: self.btn_step2.config(state="disabled", bg="#ddd")
        
        if os.path.exists(p_merged):
            self.btn_step2.config(bg="#c8e6c9", text="2. MERGE (Done)")
            self.btn_step3.config(state="normal", bg="#FFD54F")
            self.btn_step4.config(state="normal", bg="#e1f5fe")
            self.btn_step5.config(state="normal", bg="#4CAF50", fg="white")
            self.btn_pdf.config(state="normal", bg="#FFAB91")
        else:
            self.btn_step3.config(state="disabled", bg="#ddd")
            self.btn_step4.config(state="disabled", bg="#ddd")
            self.btn_step5.config(state="disabled", bg="#ddd")
            self.btn_pdf.config(state="disabled", bg="#ddd")

    def run_thread(self, target): threading.Thread(target=target).start()
    def run_step1(self): self.run_thread(self.exec_step1)
    def run_step2(self): self.run_thread(self.exec_step2)
    def run_step3_overview(self): self.run_thread(self.exec_overview)
    def run_step4_indiv(self): self.run_thread(self.exec_indiv)
    def run_step5_health(self): self.run_thread(self.exec_health)
    def run_pdf_export(self): self.run_thread(self.exec_pdf)

    def exec_step1(self):
        print("Extracting..."); base, date = self.folder_path.get(), self.date_val.get()
        in_d = os.path.join(base, "01_Original_files", date); out_d = os.path.join(base, "02_DownSampled_files", date)
        os.makedirs(out_d, exist_ok=True); files = glob.glob(os.path.join(in_d, "*.csv"))
        with ProcessPoolExecutor(self.cpu_cores) as e: list(e.map(worker_extract, [(f, os.path.join(out_d, os.path.basename(f))) for f in files]))
        print("Extracted."); self.root.after(0, self.check_status)

    def exec_step2(self):
        print("Merging..."); base, date = self.folder_path.get(), self.date_val.get()
        in_d = os.path.join(base, "02_DownSampled_files", date); out_d = os.path.join(base, "03_Merged_files")
        os.makedirs(out_d, exist_ok=True); files = glob.glob(os.path.join(in_d, "*.csv"))
        with ProcessPoolExecutor(self.cpu_cores) as e: dfs = list(e.map(worker_read_csv, files))
        full = pd.concat(dfs, ignore_index=True)
        full["Timestamp"] = pd.to_datetime(full["Timestamp"], format="%d/%m/%Y %H:%M:%S.%f")
        full["Valore"] = pd.to_numeric(full["Valore"], errors="coerce")
        full["NCU"] = pd.to_numeric(full["NCU"]).astype(str).str.zfill(2); full["TCU"] = pd.to_numeric(full["TCU"]).astype(str).str.zfill(3); full["TC"] = pd.to_numeric(full["TC"]).astype(str).str.zfill(2)
        res = full.set_index("Timestamp").groupby(["NCU", "TCU", "TC", "Parametro"]).resample("1min")["Valore"].mean().reset_index()
        res.to_csv(os.path.join(out_d, f"{date}_1min_merged.csv"), index=False)
        print("Merged."); self.root.after(0, self.check_status)

    def exec_overview(self):
        print("Generating Overview..."); base, date = self.folder_path.get(), self.date_val.get()
        msg = worker_overview_analysis(os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv"), os.path.join(base, "04_Tracker_plots_angles", date), date)
        print(msg); self.root.after(0, self.check_status)

    def exec_indiv(self):
        print("Batch Plotting to Folder..."); base, date = self.folder_path.get(), self.date_val.get()
        df = pd.read_csv(os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv"))
        out = os.path.join(base, "04_Tracker_plots_angles", date, "each_tracker_plots"); os.makedirs(out, exist_ok=True)
        with ProcessPoolExecutor(4) as e: list(e.map(worker_plot_file, [(n,t,g.to_dict("list"), os.path.join(out, f"TX_{n}_TCU_{int(t)}.png")) for (n,t), g in df.groupby(["NCU", "TCU"])]))
        print("Batch Plots Saved."); self.root.after(0, self.check_status)

    def exec_health(self):
        print("Health Check..."); base, date = self.folder_path.get(), self.date_val.get()
        issues = worker_health_check(os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv"), 28, 20)
        self.root.after(0, lambda: self.show_results(issues))

    def exec_pdf(self):
        base, date = self.folder_path.get(), self.date_val.get()
        print("\n--- STARTING PDF EXPORT ---")
        
        pdf_folder = os.path.join(base, "05_Tracker_report_pdf")
        os.makedirs(pdf_folder, exist_ok=True)
        out_pdf = os.path.join(pdf_folder, f"Tracker_Report_{date}.pdf")

        csv_path = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        overview_dir = os.path.join(base, "04_Tracker_plots_angles", date)
        
        msg = worker_generate_pdf(csv_path, overview_dir, out_pdf, date)
        print(msg)
        messagebox.showinfo("PDF Export", msg)

    def show_results(self, issues):
        self.tabs.select(self.tab_dash)
        for r in self.tree.get_children(): self.tree.delete(r)
        for i in issues: 
            tag = "crit" if i["Sev"]=="Critical" else "high"
            self.tree.insert("", "end", values=(i["NCU"], i["TCU"], i["Type"], i["Sev"], i["Msg"]), tags=(tag,))
        self.tree.tag_configure("crit", background="#ffcccc"); self.tree.tag_configure("high", background="#fff3e0")

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