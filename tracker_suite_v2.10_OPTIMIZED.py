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
from datetime import datetime

# --- LIBRARIES FOR IMAGE & PLOTTING ---
from PIL import Image, ImageTk 
import matplotlib
matplotlib.use("TkAgg") 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages 

# ==============================================================================
# WORKER FUNCTIONS
# ==============================================================================

def worker_extract(args):
    infile, outfile = args
    filename = os.path.basename(infile)
    print(f"[EXTRACT] Starting: {filename}...\n per favore non cliccare piu... aspetti", flush=True)

    possible_encodings = ["utf-8-sig", "utf-16", "latin1"]
    lines = None
    for enc in possible_encodings:
        try:
            with open(infile, "r", encoding=enc) as f: lines = f.readlines(); break
        except UnicodeDecodeError: continue  
    if not lines: 
        print(f"[EXTRACT] FAILED (Encoding): {filename}", flush=True)
        return f"Failed: {filename}"

    count = 0
    try:
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
        
        print(f"[EXTRACT] Success: {filename} ({count} rows)", flush=True)
        # Clear memory
        del lines
        return f"Done: {filename}"
    except Exception as e:
        print(f"[EXTRACT] Error writing {filename}: {e}", flush=True)
        return f"Error: {filename}"

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
                        "NCU": int(m.group(1)), # Convert to int immediately to save space
                        "TCU": int(m.group(2)),
                        "TC": int(m.group(3)),
                        "Parametro": m.group(4), 
                        "Valore": float(m.group(5).replace(',', '.')), # Float for value
                        "Timestamp": m.group(8)
                    })
        return pd.DataFrame(rows)
    except Exception as e: 
        print(f"[MERGE] Error reading {filename}: {e}", flush=True)
        return pd.DataFrame()

def worker_plot_file(args):
    import matplotlib.pyplot as plt
    matplotlib.use('Agg') 
    ncu, tcu, data_dict, out_path = args
    
    print(f"[PLOT] Processing NCU {ncu} - TCU {tcu}...", flush=True)
    
    try:
        df = pd.DataFrame(data_dict)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        # Valore is likely float already due to read_csv optimization
        target = df[df["TC"] == 4].sort_values("Timestamp")
        actual = df[df["TC"] == 5].sort_values("Timestamp")
        
        if target.empty and actual.empty: 
            print(f"[PLOT] Skipped (Empty): NCU {ncu} - TCU {tcu}", flush=True)
            return "Empty"

        fig, ax = plt.subplots(figsize=(10, 6))
        if not target.empty: ax.plot(target["Timestamp"], target["Valore"], label="Target", lw=1)
        if not actual.empty: ax.plot(actual["Timestamp"], actual["Valore"], label="Actual", lw=1)
        ax.set_title(f"NCU {ncu} - TCU {tcu}")
        ax.grid(True)
        ax.legend(loc="upper right")
        
        # --- NEW CODE: ADD MIN/MAX LEGEND ---
        if not actual.empty:
            stats = f"Min: {actual['Valore'].min():.1f}° | Max: {actual['Valore'].max():.1f}°"
            ax.text(0.02, 0.02, stats, transform=ax.transAxes, fontsize=9, 
                    verticalalignment='bottom',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='#cccccc'))
        # ------------------------------------

        fig.tight_layout()
        fig.savefig(out_path, dpi=600)
        plt.close(fig)
        plt.clf() # Extra cleanup
        del df, target, actual # Explicit delete
        return "OK"
    except Exception as e: 
        plt.close('all')
        print(f"[PLOT] Error NCU {ncu}: {e}", flush=True)
        return "Error"

def worker_overview_analysis(input_csv, output_dir, date_str, threshold=28.0):
    import matplotlib.pyplot as plt
    matplotlib.use('Agg')
    print(f"[OVERVIEW] Starting Analysis on {input_csv}...", flush=True)
    try:
        os.makedirs(output_dir, exist_ok=True)
        base_name = f"NCU_TCU_{date_str}"
        
        print("[OVERVIEW] Loading CSV into DataFrame...", flush=True)
        # Optimization: Specify types to reduce memory
        df = pd.read_csv(input_csv, dtype={"NCU": int, "TCU": int, "TC": int, "Valore": float})
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=["NCU", "TCU", "TC", "Valore", "Timestamp"])
        df = df[df["TC"].isin([4, 5])]
        
        all_ncus = sorted(df["NCU"].unique())
        print(f"[OVERVIEW] Found {len(all_ncus)} NCUs. Organizing data...", flush=True)
        
        series_by_ncu = {}
        below_thresh_rows = []
        
        for ncu in all_ncus:
            df_ncu = df[df["NCU"] == ncu]
            tcu_map = {}
            for tcu in df_ncu["TCU"].unique():
                part = df_ncu[df_ncu["TCU"] == tcu]
                target = part[part["TC"] == 4][["Timestamp", "Valore"]].rename(columns={"Valore": "target"})
                actual = part[part["TC"] == 5][["Timestamp", "Valore"]].rename(columns={"Valore": "actual"})
                
                # Merge logic
                merged = pd.merge_asof(target.sort_values("Timestamp"), actual.sort_values("Timestamp"), on="Timestamp", direction="nearest", tolerance=pd.Timedelta("1s")).dropna()
                
                if not merged.empty:
                    tcu_map[tcu] = merged
                    low = merged[merged["actual"] < threshold]
                    for _, row in low.iterrows():
                        below_thresh_rows.append({"NCU": ncu, "TCU": tcu, "Timestamp": row["Timestamp"], "Angle": row["actual"]})
            series_by_ncu[ncu] = tcu_map

        def make_plot(ncus, fname, title):
            print(f"[OVERVIEW] Generating plot: {os.path.basename(fname)}", flush=True)
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
            
            fig.tight_layout()
            fig.savefig(fname, dpi=1800)
            plt.close(fig)
            plt.clf()

        make_plot(all_ncus, os.path.join(output_dir, f"{base_name}_ALL.png"), "All Trackers")
        for ncu in all_ncus:
            make_plot([ncu], os.path.join(output_dir, f"{base_name}_NCU{ncu}.png"), f"NCU {ncu} Overview")
            
        if below_thresh_rows:
            csv_out = os.path.join(output_dir, f"{base_name}_below_{int(threshold)}deg.csv")
            print(f"[OVERVIEW] Saving threshold report to {csv_out}", flush=True)
            pd.DataFrame(below_thresh_rows).to_csv(csv_out, index=False, sep=";")
        
        # Cleanup
        del df, series_by_ncu, below_thresh_rows
        gc.collect()
        
        return "Overview Generation Complete"
    except Exception as e: 
        print(f"[OVERVIEW] Critical Error: {e}", flush=True)
        return f"Error: {e}"

def worker_health_check(csv_path, angle_th, dev_th):
    issues = []
    print(f"[HEALTH] Reading CSV for Health Check: {csv_path}", flush=True)
    try:
        # Optimized Read
        df = pd.read_csv(csv_path, dtype={"NCU": int, "TCU": int, "TC": int, "Valore": float})
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df = df[df["TC"].isin([4, 5])].dropna(subset=["Valore"])
        
        groups = list(df.groupby(["NCU", "TCU"]))
        total = len(groups)
        print(f"[HEALTH] Analyzing {total} trackers...", flush=True)

        for i, ((ncu, tcu), g) in enumerate(groups):
            if i % 50 == 0: print(f"[HEALTH] Analyzed {i}/{total} trackers...", flush=True)
            
            target = g[g["TC"] == 4]["Valore"]
            actual = g[g["TC"] == 5]["Valore"]
            if len(actual) < 10:
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "DATA LOSS", "Msg": f"{len(actual)} pts", "Sev": "High"}); continue
            if target.std() > 5 and actual.std() < 1.0:
                 issues.append({"NCU": ncu, "TCU": tcu, "Type": "STUCK", "Msg": "Target moving, Actual flat", "Sev": "Critical"})
            
            # Use Index intersection for faster diff
            t_df = g[g["TC"] == 4].set_index("Timestamp")["Valore"]
            a_df = g[g["TC"] == 5].set_index("Timestamp")["Valore"]
            common = t_df.index.intersection(a_df.index)
            
            if len(common) > 0:
                diff = (t_df[common] - a_df[common]).abs().mean()
                if diff > float(dev_th): issues.append({"NCU": ncu, "TCU": tcu, "Type": "DEVIATION", "Msg": f"Avg Diff {diff:.1f}°", "Sev": "Medium"})
            
            if not actual.empty and actual.min() < float(angle_th):
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "LOW ANGLE", "Msg": f"Min {actual.min():.1f}°", "Sev": "High"})
        
        del df, groups
        gc.collect()
        return issues
    except Exception as e: 
        print(f"[HEALTH] Error: {e}", flush=True)
        return [{"NCU":0, "TCU":0, "Type": "ERROR", "Msg": str(e), "Sev": "Critical"}]

def worker_generate_pdf(csv_path, overview_dir, output_pdf, date_str):
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages
    
    matplotlib.use('Agg')
    print(f"[PDF] Initializing PDF creation: {output_pdf}", flush=True)
    
    try:
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
        
        with PdfPages(output_pdf) as pdf:
            print("[PDF] Adding Overview Images...", flush=True)
            search_pattern = os.path.join(overview_dir, f"*{date_str}*.png")
            overview_files = sorted(glob.glob(search_pattern))
            overview_files = [f for f in overview_files if "TX_" not in os.path.basename(f) and "each_tracker" not in f]
            
            for img_path in overview_files:
                try:
                    print(f"  -> Adding {os.path.basename(img_path)}", flush=True)
                    img = mpimg.imread(img_path)
                    fig_img, ax_img = plt.subplots(figsize=(15.5, 11.2))
                    ax_img.imshow(img); ax_img.axis('off')
                    pdf.savefig(fig_img, orientation='landscape', bbox_inches='tight', dpi=1800)
                    plt.close(fig_img)
                    plt.clf()
                    del img # Release memory
                except Exception as e: 
                    print(f"  [PDF WARNING] Could not add image {img_path}: {e}", flush=True)

            print("[PDF] Loading data for individual plots...", flush=True)
            # Optimized Read
            df = pd.read_csv(csv_path, dtype={"NCU": int, "TCU": int, "TC": int, "Valore": float})
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            df = df.dropna(subset=["Valore"])
            
            groups = list(df.groupby(["NCU", "TCU"]))
            total_groups = len(groups)
            count = 0
            
            print(f"[PDF] Generating {total_groups} individual tracker pages...", flush=True)
            
            for (ncu, tcu), group in groups:
                count += 1
                if count % 10 == 0: 
                    print(f"[PDF] Processed {count}/{total_groups} pages...", flush=True)
                    if count % 50 == 0: gc.collect() # Periodically clean
                
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
            
            del df, groups
            gc.collect()
                
        return f"PDF Report Generated successfully!\nSaved to: {output_pdf}"

    except Exception as e: return f"Critical Error generating PDF: {str(e)}"

def worker_generate_random_pdf(csv_path, img_folder, output_pdf, date_str):
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages
    
    matplotlib.use('Agg')
    print(f"[RANDOM PDF] Initializing Random Sample PDF: {output_pdf}", flush=True)
    
    try:
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
        
        # 1. Load Data (Optimized)
        print("[RANDOM PDF] Loading CSV Data...", flush=True)
        df = pd.read_csv(csv_path, dtype={"NCU": int, "TCU": int, "TC": int, "Valore": float})
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df = df.dropna(subset=["Valore"])
        
        # 2. Group by NCU
        ncu_groups = df.groupby("NCU")
        
        with PdfPages(output_pdf) as pdf:
            
            # --- OVERVIEW PLOTS ---
            overview_dir = os.path.dirname(img_folder)
            search_pattern = os.path.join(overview_dir, f"*{date_str}*.png")
            all_imgs = sorted(glob.glob(search_pattern))
            overview_files = [f for f in all_imgs if os.path.basename(f).startswith(f"NCU_TCU_{date_str}")]
            
            if overview_files:
                for img_path in overview_files:
                    try:
                        print(f"  -> Adding Overview: {os.path.basename(img_path)}", flush=True)
                        img = mpimg.imread(img_path)
                        fig_img, ax_img = plt.subplots(figsize=(15.5, 11.2))
                        ax_img.imshow(img); ax_img.axis('off')
                        pdf.savefig(fig_img, orientation='landscape', bbox_inches='tight')
                        plt.close(fig_img)
                        plt.clf()
                        del img
                    except Exception as e:
                        print(f"    [WARNING] Could not add overview {img_path}: {e}", flush=True)

            # --- INDIVIDUAL PLOTS ---
            for ncu, ncu_data in ncu_groups:
                tcus = ncu_data["TCU"].unique()
                selected_tcus = sorted(random.sample(list(tcus), k=min(len(tcus), 5)))
                print(f"  -> NCU {int(ncu)}: Selected {selected_tcus}", flush=True)
                
                for tcu in selected_tcus:
                    img_name = f"TX_{int(ncu)}_TCU_{int(tcu)}.png"
                    img_path = os.path.join(img_folder, img_name)
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    if os.path.exists(img_path):
                        try:
                            img = mpimg.imread(img_path)
                            ax.imshow(img)
                            ax.axis('off') 
                        except Exception as e:
                             print(f"    Error loading image {img_name}: {e}", flush=True)
                    else:
                        print(f"    Generating plot for TCU {tcu} (File not found)", flush=True)
                        group = ncu_data[ncu_data["TCU"] == tcu]
                        target = group[group["TC"] == 4].sort_values("Timestamp")
                        actual = group[group["TC"] == 5].sort_values("Timestamp")
                        
                        if not target.empty: ax.plot(target["Timestamp"], target["Valore"], label="Target", color="blue", lw=1)
                        if not actual.empty: ax.plot(actual["Timestamp"], actual["Valore"], label="Actual", color="red", lw=1)
                        
                        ax.set_title(f"NCU {int(ncu)} - TCU {int(tcu)}")
                        ax.set_ylabel("Angle (°)"); ax.set_xlabel("Time"); ax.grid(True, alpha=0.3)
                        ax.legend(loc="upper right")
                        
                        if not actual.empty:
                            stats = f"Min: {actual['Valore'].min():.1f}° | Max: {actual['Valore'].max():.1f}°"
                            ax.text(0.02, 0.02, stats, transform=ax.transAxes, fontsize=8, bbox=dict(facecolor='white', alpha=0.8))

                    pdf.savefig(fig, dpi=600)
                    plt.close(fig)
                    plt.clf()
                
                # Cleanup specific NCU data from memory
                del ncu_data
                gc.collect()

        del df, ncu_groups
        gc.collect()
        return f"Random PDF Generated!\nSaved to: {output_pdf}"
        
    except Exception as e:
        print(f"[RANDOM PDF] Error: {e}", flush=True)
        return f"Error: {e}"

# ==============================================================================
# GUI CLASS
# ==============================================================================

class TextRedirector:
    """Redirects writes to both the GUI widget and the standard Terminal."""
    def __init__(self, widget):
        self.widget = widget
        self.terminal = sys.__stdout__ 

    def write(self, s):
        try:
            self.widget.config(state="normal")
            self.widget.insert("end", s)
            self.widget.see("end")
            self.widget.config(state="disabled")
            self.widget.update_idletasks()
        except:
            pass
        if self.terminal:
            self.terminal.write(s)
            self.terminal.flush() 

    def flush(self):
        if self.terminal:
            self.terminal.flush()

class TrackerSuiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GET - SCADA Tracker Suite")
        self.root.geometry("850x700") 
        
        if hasattr(sys, '_MEIPASS'):
            self.logo_path = os.path.join(sys._MEIPASS, "logo.png")
        else:
            self.logo_path = os.path.join(os.path.dirname(__file__), "logo.png")

        if os.path.exists(self.logo_path):
            try: self.root.iconphoto(False, tk.PhotoImage(file=self.logo_path))
            except: pass

        self.cpu_cores = min(multiprocessing.cpu_count(), 6)
        
        # Default root folder path
        DEFAULT_ROOT_FOLDER = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report"
        self.folder_path = tk.StringVar(value=DEFAULT_ROOT_FOLDER)
        self.date_val = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

        today = datetime.now()
        self.var_year = tk.StringVar(value=str(today.year))
        self.var_month = tk.StringVar(value=str(today.month).zfill(2))
        self.var_day = tk.StringVar(value=str(today.day).zfill(2))

        self.setup_layout()
        sys.stdout = TextRedirector(self.log_text)
        print("--- APP STARTED: Console Output Enabled ---")
        
        self.folder_path.trace("w", self.trigger_check)
        self.var_year.trace("w", self.update_date_str)
        self.var_month.trace("w", self.update_date_str)
        self.var_day.trace("w", self.update_date_str)

    def update_date_str(self, *args):
        y = self.var_year.get()
        m = self.var_month.get().zfill(2)
        d = self.var_day.get().zfill(2)
        self.date_val.set(f"{y}-{m}-{d}")
        self.trigger_check()

    def setup_layout(self):
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

        cfg = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        cfg.pack(fill="x", padx=10, pady=5)
        
        f_frame = ttk.Frame(cfg)
        f_frame.pack(fill="x", pady=2)
        ttk.Label(f_frame, text="Root Folder:").pack(side="left")
        ttk.Entry(f_frame, textvariable=self.folder_path, width=60).pack(side="left", padx=5)
        ttk.Button(f_frame, text="Browse", command=self.browse).pack(side="left")

        d_frame = ttk.Frame(cfg)
        d_frame.pack(fill="x", pady=5)
        ttk.Label(d_frame, text="Date Selection:").pack(side="left")
        
        ttk.Spinbox(d_frame, from_=2020, to=2030, textvariable=self.var_year, width=5).pack(side="left", padx=(5,0))
        ttk.Label(d_frame, text="-").pack(side="left")
        ttk.Spinbox(d_frame, from_=1, to=12, textvariable=self.var_month, width=3, format="%02.0f").pack(side="left")
        ttk.Label(d_frame, text="-").pack(side="left")
        ttk.Spinbox(d_frame, from_=1, to=31, textvariable=self.var_day, width=3, format="%02.0f").pack(side="left")
        
        ttk.Button(d_frame, text="Refresh Status", command=self.check_status).pack(side="left", padx=20)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=5)
        self.tab_pipe = ttk.Frame(self.tabs); self.tabs.add(self.tab_pipe, text="Pipeline")
        self.tab_dash = ttk.Frame(self.tabs); self.tabs.add(self.tab_dash, text="Health Dashboard")

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
        
        self.btn_pdf = tk.Button(btn_f, text="6. EXPORT FULL PDF REPORT\n(Overview + All 370 Trackers)", bg="#ddd", state="disabled", font=("Arial", 10, "bold"), fg="#D32F2F", command=self.run_pdf_export)
        self.btn_pdf.pack(fill="x", pady=2)

        self.btn_pdf_rand = tk.Button(btn_f, text="7. EXPORT RANDOM PDF (5 Random TCUs per NCU)", bg="#ddd", state="disabled", font=("Arial", 9, "bold"), fg="#1976D2", command=self.run_pdf_random)
        self.btn_pdf_rand.pack(fill="x", pady=2)

        self.log_text = tk.Text(self.tab_pipe, height=8, bg="#f0f0f0", state="disabled"); self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

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
        y, m = date[:4], date[5:7]
        p_raw = os.path.join(base, "01_Original_files", y, m, date)
        p_down = os.path.join(base, "02_DownSampled_Files", y, m, date)
        p_merged = os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv")
        
        if os.path.exists(p_raw): self.btn_step1.config(state="normal", bg="#e1f5fe")
        else: self.btn_step1.config(state="disabled", bg="#ddd")
        if os.path.exists(p_down) and glob.glob(os.path.join(p_down, "*.csv")):
            self.btn_step2.config(state="normal", bg="#e1f5fe"); self.btn_step1.config(bg="#c8e6c9", text="1. EXTRACT")
        else: self.btn_step2.config(state="disabled", bg="#ddd")
        
        if os.path.exists(p_merged):
            self.btn_step2.config(bg="#c8e6c9", text="2. MERGE")
            self.btn_step3.config(state="normal", bg="#FFD54F")
            self.btn_step4.config(state="normal", bg="#e1f5fe")
            self.btn_step5.config(state="normal", bg="#4CAF50", fg="white")
            self.btn_pdf.config(state="normal", bg="#FFAB91")
            self.btn_pdf_rand.config(state="normal", bg="#BBDEFB")
        else:
            self.btn_step3.config(state="disabled", bg="#ddd")
            self.btn_step4.config(state="disabled", bg="#ddd")
            self.btn_step5.config(state="disabled", bg="#ddd")
            self.btn_step5.config(state="disabled", bg="#ddd")
            self.btn_pdf.config(state="disabled", bg="#ddd")
            self.btn_pdf_rand.config(state="disabled", bg="#ddd")

    def run_thread(self, target): threading.Thread(target=target).start()
    def run_step1(self): self.run_thread(self.exec_step1)
    def run_step2(self): self.run_thread(self.exec_step2)
    def run_step3_overview(self): self.run_thread(self.exec_overview)
    def run_step4_indiv(self): self.run_thread(self.exec_indiv)
    def run_step5_health(self): self.run_thread(self.exec_health)
    def run_pdf_export(self): self.run_thread(self.exec_pdf)
    def run_pdf_random(self): self.run_thread(self.exec_pdf_random)

    def exec_step1(self):
        print(f"\n[{datetime.now().time()}] --- STEP 1: EXTRACTING  | NON CLICCA PIU |  ---")
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        in_d = os.path.join(base, "01_Original_files", y, m, date)
        out_d = os.path.join(base, "02_DownSampled_Files", y, m, date)
        os.makedirs(out_d, exist_ok=True)

        # Check for .txt files and rename them
        txt_files = glob.glob(os.path.join(in_d, "*.txt"))
        if txt_files:
            print(f"Found {len(txt_files)} .txt files. Renaming to .csv...", flush=True)
            for txt_file in txt_files:
                try:
                    base_name = os.path.splitext(txt_file)[0]
                    new_name = base_name + ".csv"
                    os.rename(txt_file, new_name)
                    print(f"  Renamed: {os.path.basename(txt_file)} -> {os.path.basename(new_name)}", flush=True)
                except Exception as e:
                    print(f"  Error renaming {os.path.basename(txt_file)}: {e}", flush=True)

        files = glob.glob(os.path.join(in_d, "*.csv"))
        
        print(f"Found {len(files)} files to extract.")
        with ProcessPoolExecutor(self.cpu_cores) as e: 
            results = e.map(worker_extract, [(f, os.path.join(out_d, os.path.basename(f))) for f in files])
            for res in results:
                pass 
                
        print("Extracted."); self.root.after(0, self.check_status)

    def exec_step2(self):
        print(f"\n[{datetime.now().time()}] --- STEP 2: MERGING (MEMORY OPTIMIZED) ---")
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        in_d = os.path.join(base, "02_DownSampled_Files", y, m, date)
        out_d = os.path.join(base, "03_Merged_files", y, m)
        os.makedirs(out_d, exist_ok=True)
        
        files = glob.glob(os.path.join(in_d, "*.csv"))
        print(f"Found {len(files)} files. Starting batch processing...")

        BATCH_SIZE = 6 
        resampled_chunks = []
        file_batches = [files[i:i + BATCH_SIZE] for i in range(0, len(files), BATCH_SIZE)]
        total_batches = len(file_batches)
        
        for i, batch_files in enumerate(file_batches):
            print(f"Processing Batch {i+1}/{total_batches} ({len(batch_files)} files)...")
            with ProcessPoolExecutor(self.cpu_cores) as e:
                dfs = list(e.map(worker_read_csv, batch_files))
            
            if not dfs: continue
            
            # Optimization: Use copy=False to avoid duplication
            batch_df = pd.concat(dfs, ignore_index=True, copy=False)
            batch_df["Timestamp"] = pd.to_datetime(batch_df["Timestamp"], format="%d/%m/%Y %H:%M:%S.%f")
            
            mini_resampled = batch_df.set_index("Timestamp").groupby(["NCU", "TCU", "TC", "Parametro"]).resample("1min")["Valore"].mean().reset_index()
            resampled_chunks.append(mini_resampled)
            
            del batch_df, dfs
            gc.collect() # Force clear
            print(f"  > Batch {i+1} reduced to {len(mini_resampled)} rows.")

        print("Concatenating all resampled batches...")
        full_resampled = pd.concat(resampled_chunks, ignore_index=True, copy=False)
        final_df = full_resampled.groupby(["NCU", "TCU", "TC", "Parametro", "Timestamp"])["Valore"].mean().reset_index()

        print("Formatting columns...")
        # Formatting takes memory, doing it at the very end
        final_df["NCU"] = final_df["NCU"].astype(str).str.zfill(2)
        final_df["TCU"] = final_df["TCU"].astype(str).str.zfill(3)
        final_df["TC"] = final_df["TC"].astype(str).str.zfill(2)

        out_file = os.path.join(out_d, f"{date}_1min_merged.csv")
        final_df.to_csv(out_file, index=False)
        
        print(f"Merged CSV saved to: {out_file}")
        del final_df, resampled_chunks, full_resampled
        gc.collect()
        
        self.root.after(0, self.check_status)

    def exec_overview(self):
        print(f"\n[{datetime.now().time()}] --- STEP 3: OVERVIEW ---")
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        msg = worker_overview_analysis(os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv"), os.path.join(base, "04_Tracker_plots_angles", y, m, date), date)
        print(msg); self.root.after(0, self.check_status)

    def exec_indiv(self):
        print(f"\n[{datetime.now().time()}] --- STEP 4: BATCH PLOTTING ---")
        base, date = self.folder_path.get(), self.date_val.get()
        # Read optimized types
        y, m = date[:4], date[5:7]
        df = pd.read_csv(os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv"), dtype={"NCU": int, "TCU": int, "TC": int, "Valore": float})
        out = os.path.join(base, "04_Tracker_plots_angles", y, m, date, "each_tracker_plots"); os.makedirs(out, exist_ok=True)
        
        groups = [(n,t,g.to_dict("list"), os.path.join(out, f"TX_{n}_TCU_{int(t)}.png")) for (n,t), g in df.groupby(["NCU", "TCU"])]
        print(f"Queuing {len(groups)} plots...")
        
        del df # Free main DF before processing
        gc.collect()

        with ProcessPoolExecutor(4) as e: 
            for res in e.map(worker_plot_file, groups):
                pass
                
        print("Batch Plots Saved."); self.root.after(0, self.check_status)

    def exec_health(self):
        print(f"\n[{datetime.now().time()}] --- STEP 5: HEALTH CHECK ---")
        base, date = self.folder_path.get(), self.date_val.get()
        y, m = date[:4], date[5:7]
        issues = worker_health_check(os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv"), 28, 20)
        print(f"Health Check Found {len(issues)} issues.")
        self.root.after(0, lambda: self.show_results(issues))

    def exec_pdf(self):
        base, date = self.folder_path.get(), self.date_val.get()
        print(f"\n[{datetime.now().time()}] --- STEP 6: PDF EXPORT ---")
        
        y, m = date[:4], date[5:7]
        pdf_folder = os.path.join(base, "05_Tracker_Report_PDF", y, m)
        os.makedirs(pdf_folder, exist_ok=True)
        out_pdf = os.path.join(pdf_folder, f"Tracker_Report_{date}.pdf")

        csv_path = os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv")
        overview_dir = os.path.join(base, "04_Tracker_plots_angles", y, m, date)
        
        msg = worker_generate_pdf(csv_path, overview_dir, out_pdf, date)
        print(msg)
        messagebox.showinfo("PDF Export", msg)

    def exec_pdf_random(self):
        base, date = self.folder_path.get(), self.date_val.get()
        print(f"\n[{datetime.now().time()}] --- STEP 7: RANDOM PDF EXPORT ---")
        
        y, m = date[:4], date[5:7]
        pdf_folder = os.path.join(base, "05_Tracker_Report_PDF", y, m)
        os.makedirs(pdf_folder, exist_ok=True)
        out_pdf = os.path.join(pdf_folder, f"Tracker_Random_Sample_{date}.pdf")

        csv_path = os.path.join(base, "03_Merged_files", y, m, f"{date}_1min_merged.csv")
        # Path where images MIGHT exist (for individual plots)
        img_folder = os.path.join(base, "04_Tracker_plots_angles", y, m, date, "each_tracker_plots")
        
        msg = worker_generate_random_pdf(csv_path, img_folder, out_pdf, date)
        print(msg)
        messagebox.showinfo("Random PDF Export", msg)

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
        
        rel_path = os.path.join("04_Tracker_plots_angles", self.date_val.get()[:4], self.date_val.get()[5:7], self.date_val.get(), "each_tracker_plots", f"TX_{ncu}_TCU_{int(tcu)}.png")
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
            date = self.date_val.get()
            y, m = date[:4], date[5:7]
            csv_path = os.path.join(self.folder_path.get(), "03_Merged_files", y, m, f"{date}_1min_merged.csv")
            
            if not os.path.exists(csv_path):
                messagebox.showerror("Error", f"Merged CSV not found:\n{csv_path}")
                return

            df = pd.read_csv(csv_path, dtype={"NCU": int, "TCU": int, "TC": int, "Valore": float})
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            
            mask = (df["NCU"] == int(ncu)) & (df["TCU"] == int(tcu))
            subset = df[mask]
            
            target = subset[subset["TC"] == 4].sort_values("Timestamp")
            actual = subset[subset["TC"] == 5].sort_values("Timestamp")

            top = tk.Toplevel(self.root)
            top.title(f"LIVE VIEW: NCU {ncu} - TCU {tcu}")
            top.geometry("900x500")
            
            fig = Figure(figsize=(8, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            if not target.empty: 
                ax.plot(target["Timestamp"], target["Valore"], label="Target", color="blue")
            if not actual.empty: 
                ax.plot(actual["Timestamp"], actual["Valore"], label="Actual", color="red", linestyle="--")
            
            ax.set_title(f"NCU {ncu} - TCU {tcu} (Live Generated)")
            ax.set_ylabel("Angle (°)")
            ax.legend()
            ax.grid(True)

            if not actual.empty:
                stats = f"Min: {actual['Valore'].min():.1f}° | Max: {actual['Valore'].max():.1f}°"
                ax.text(0.02, 0.02, stats, transform=ax.transAxes, fontsize=9, 
                        verticalalignment='bottom',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='#cccccc'))

            canvas = FigureCanvasTkAgg(fig, master=top)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Cleanup
            del df, subset, target, actual
            gc.collect()
            
        except Exception as e: 
            messagebox.showerror("Plot Error", f"Could not generate live plot:\n{e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = TrackerSuiteApp(root)
    root.mainloop()