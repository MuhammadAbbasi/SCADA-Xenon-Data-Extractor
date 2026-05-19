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
from PIL import Image, ImageTk

# Matplotlib for Live Plotting
import matplotlib
matplotlib.use("TkAgg") # Required for the popup window
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# ==============================================================================
# WORKER FUNCTIONS (Background Tasks)
# ==============================================================================

def worker_extract(args):
    """Step 1: Extract angle data from raw CSV."""
    infile, outfile = args
    possible_encodings = ["utf-8-sig", "utf-16", "latin1"]
    lines = None
    
    for enc in possible_encodings:
        try:
            with open(infile, "r", encoding=enc) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue
            
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
    """Step 2 Helper: Read single downsampled CSV."""
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
    except:
        return pd.DataFrame()

def worker_plot_file(args):
    """Step 3: Save PNG file to disk (Batch Mode)."""
    # Use Agg backend inside worker process to avoid GUI conflicts
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
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_path, dpi=80)
        plt.close(fig)
        return "OK"
    except:
        plt.close('all')
        return "Error"

def worker_health_check(csv_path, angle_th, dev_th):
    """Step 4: Analyze Data."""
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

            # Sync timestamps for deviation check
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
    except Exception as e:
        return [{"NCU":0, "TCU":0, "Type": "ERROR", "Msg": str(e), "Sev": "Critical"}]

# ==============================================================================
# GUI APPLICATION
# ==============================================================================

class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
    def write(self, s):
        self.widget.config(state="normal")
        self.widget.insert("end", s)
        self.widget.see("end")
        self.widget.config(state="disabled")
        self.widget.update_idletasks()
    def flush(self): pass

class TrackerSuiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SCADA Tracker Suite v2.2")
        self.root.geometry("1100x850") 
        
        # --- LOGO & ICON CONFIGURATION ---
        # 1. Define the file path (Make sure this file actually exists!)
        # Tip: Put 'logo.png' in the same folder as this script.
        self.logo_path = os.path.join(os.path.dirname(__file__), "logo.png")

        # 2. Set the Window Icon (Top-Left & Taskbar)
        if os.path.exists(self.logo_path):
            try:
                # Use standard Tkinter method (Supports PNG)
                img = tk.PhotoImage(file=self.logo_path)
                self.root.iconphoto(False, img)
                print(f"Icon loaded successfully from: {self.logo_path}")
            except Exception as e:
                print(f"Failed to set window icon: {e}")
        else:
            print(f"⚠ Warning: Logo file not found at: {self.logo_path}")

        self.cpu_cores = min(multiprocessing.cpu_count(), 6)
        self.folder_path = tk.StringVar()
        self.date_val = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        
        self.setup_layout()
        sys.stdout = TextRedirector(self.log_text)
        
        self.folder_path.trace("w", self.trigger_check)
        self.date_val.trace("w", self.trigger_check)

    def setup_layout(self):
        # --- BANNER LOGO SECTION ---
        # We create a frame at the top just for the logo
        logo_frame = tk.Frame(self.root, bg="white", height=80)
        logo_frame.pack(fill="x", side="top")
        
        if os.path.exists(self.logo_path):
            try:
                # Load and Resize Logo
                load = Image.open(self.logo_path)
                
                # Resize to height of 60px, keep aspect ratio
                aspect_ratio = load.width / load.height
                new_height = 60
                new_width = int(new_height * aspect_ratio)
                
                render = ImageTk.PhotoImage(load.resize((new_width, new_height), Image.LANCZOS))
                
                # Keep a reference so garbage collector doesn't delete it
                self.logo_image = render 
                
                # Display in a Label
                img_lbl = tk.Label(logo_frame, image=render, bg="white", bd=0)
                img_lbl.pack(pady=10)
                
            except Exception as e:
                print(f"Logo load error: {e}")
                tk.Label(logo_frame, text="SCADA TRACKER SUITE", bg="white", font=("Arial", 16, "bold")).pack(pady=20)
        else:
            # Fallback text if no logo found
            tk.Label(logo_frame, text="SCADA TRACKER SUITE", bg="white", font=("Arial", 16, "bold")).pack(pady=20)

        # --- EXISTING CONFIGURATION FRAME ---
        cfg = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        cfg.pack(fill="x", padx=10, pady=5)
        # Configuration
        ttk.Label(cfg, text="Root Folder:").pack(side="left")
        ttk.Entry(cfg, textvariable=self.folder_path, width=50).pack(side="left", padx=5)
        ttk.Button(cfg, text="Browse", command=self.browse).pack(side="left")
        ttk.Label(cfg, text="Date (YYYY-MM-DD):").pack(side="left", padx=(20, 5))
        ttk.Entry(cfg, textvariable=self.date_val, width=15).pack(side="left")
        ttk.Button(cfg, text="Refresh Status", command=self.check_status).pack(side="right")

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=5)
        
        # TAB 1: PIPELINE
        self.tab_pipe = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_pipe, text="Pipeline")
        
        btn_f = ttk.Frame(self.tab_pipe)
        btn_f.pack(fill="x", pady=10, padx=50)

        # Buttons
        self.btn_step1 = tk.Button(btn_f, text="1. EXTRACT", bg="#ddd", command=self.run_step1)
        self.btn_step1.pack(fill="x", pady=2)
        
        self.btn_step2 = tk.Button(btn_f, text="2. MERGE", bg="#ddd", state="disabled", command=self.run_step2)
        self.btn_step2.pack(fill="x", pady=2)
        
        ttk.Separator(btn_f, orient="horizontal").pack(fill="x", pady=10)
        
        split = ttk.Frame(btn_f)
        split.pack(fill="x")
        
        self.btn_step3 = tk.Button(split, text="3. GENERATE ALL PLOTS\n(Optional Batch)", bg="#ddd", state="disabled", command=self.run_step3)
        self.btn_step3.pack(side="left", fill="x", expand=True, padx=(0,5))
        
        self.btn_step4 = tk.Button(split, text="4. RUN HEALTH CHECK\n(Fast Analysis)", bg="#ddd", font=("Arial", 9, "bold"), state="disabled", command=self.run_step4)
        self.btn_step4.pack(side="right", fill="x", expand=True, padx=(5,0))

        self.log_text = tk.Text(self.tab_pipe, height=10, bg="#f0f0f0", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        # TAB 2: DASHBOARD
        self.tab_dash = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_dash, text="Health Dashboard")
        
        tk.Label(self.tab_dash, text="Double-click a row to see LIVE PLOT (even if Step 3 was skipped).", fg="blue").pack(pady=5)
        
        cols = ("NCU", "TCU", "Type", "Severity", "Details")
        self.tree = ttk.Treeview(self.tab_dash, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrl = ttk.Scrollbar(self.tab_dash, orient="vertical", command=self.tree.yview)
        scrl.pack(side="right", fill="y")
        self.tree.configure(yscroll=scrl.set)
        
        self.tree.bind("<Double-1>", self.on_double_click_plot)

    def browse(self):
        d = filedialog.askdirectory()
        if d: self.folder_path.set(d)

    def trigger_check(self, *args):
        self.root.after(500, self.check_status)

    def check_status(self):
        base, date = self.folder_path.get(), self.date_val.get()
        if not base or not date: return
        
        p_raw = os.path.join(base, "01_Original_files", date)
        p_down = os.path.join(base, "02_DownSampled_files", date)
        p_merged = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        
        # Step 1
        if os.path.exists(p_raw):
            self.btn_step1.config(state="normal", bg="#e1f5fe")
        else:
            self.btn_step1.config(state="disabled", bg="#ddd")

        # Step 2
        if os.path.exists(p_down) and glob.glob(os.path.join(p_down, "*.csv")):
            self.btn_step2.config(state="normal", bg="#e1f5fe")
            self.btn_step1.config(bg="#c8e6c9", text="1. EXTRACT (Done)")
        else:
            self.btn_step2.config(state="disabled", bg="#ddd")

        # Step 3 & 4
        if os.path.exists(p_merged):
            self.btn_step3.config(state="normal", bg="#e1f5fe")
            self.btn_step4.config(state="normal", bg="#4CAF50", fg="white")
            self.btn_step2.config(bg="#c8e6c9", text="2. MERGE (Done)")
        else:
            self.btn_step3.config(state="disabled", bg="#ddd")
            self.btn_step4.config(state="disabled", bg="#ddd")

    def run_threading(self, target): threading.Thread(target=target).start()
    def run_step1(self): self.run_threading(self.execute_step1)
    def run_step2(self): self.run_threading(self.execute_step2)
    def run_step3(self): self.run_threading(self.execute_step3)
    def run_step4(self): self.run_threading(self.execute_step4)

    def execute_step1(self):
        print("Starting Step 1...")
        base, date = self.folder_path.get(), self.date_val.get()
        in_d = os.path.join(base, "01_Original_files", date)
        out_d = os.path.join(base, "02_DownSampled_files", date)
        os.makedirs(out_d, exist_ok=True)
        files = glob.glob(os.path.join(in_d, "*.csv"))
        tasks = [(f, os.path.join(out_d, os.path.basename(f))) for f in files]
        with ProcessPoolExecutor(max_workers=self.cpu_cores) as exc:
            list(exc.map(worker_extract, tasks))
        print("Step 1 Done.")
        self.root.after(0, self.check_status)

    def execute_step2(self):
        print("Starting Step 2...")
        base, date = self.folder_path.get(), self.date_val.get()
        in_d = os.path.join(base, "02_DownSampled_files", date)
        out_d = os.path.join(base, "03_Merged_files")
        os.makedirs(out_d, exist_ok=True)
        files = glob.glob(os.path.join(in_d, "*.csv"))
        with ProcessPoolExecutor(max_workers=self.cpu_cores) as exc:
            dfs = list(exc.map(worker_read_csv, files))
        full = pd.concat(dfs, ignore_index=True)
        print("Resampling...")
        full["Timestamp"] = pd.to_datetime(full["Timestamp"], format="%d/%m/%Y %H:%M:%S.%f")
        full["Valore"] = pd.to_numeric(full["Valore"], errors="coerce")
        full["NCU"] = pd.to_numeric(full["NCU"]).astype(str).str.zfill(2)
        full["TCU"] = pd.to_numeric(full["TCU"]).astype(str).str.zfill(3)
        full["TC"] = pd.to_numeric(full["TC"]).astype(str).str.zfill(2)
        res = full.set_index("Timestamp").groupby(["NCU", "TCU", "TC", "Parametro"]).resample("1min")["Valore"].mean().reset_index()
        res.to_csv(os.path.join(out_d, f"{date}_1min_merged.csv"), index=False)
        print("Step 2 Done.")
        self.root.after(0, self.check_status)

    def execute_step3(self):
        print("Starting Step 3 (Batch Plots)...")
        base, date = self.folder_path.get(), self.date_val.get()
        csv_p = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        out_d = os.path.join(base, "04_Tracker_plots_angles", date, "each_tracker_plots")
        os.makedirs(out_d, exist_ok=True)
        df = pd.read_csv(csv_p)
        tasks = [(n, t, g.to_dict("list"), os.path.join(out_d, f"TX_{n}_TCU_{int(t)}.png")) for (n,t), g in df.groupby(["NCU", "TCU"])]
        with ProcessPoolExecutor(max_workers=4) as exc:
            list(exc.map(worker_plot_file, tasks))
        print("Step 3 Done.")
        self.root.after(0, self.check_status)

    def execute_step4(self):
        print("Starting Step 4 (Health Check)...")
        base, date = self.folder_path.get(), self.date_val.get()
        csv_p = os.path.join(base, "03_Merged_files", f"{date}_1min_merged.csv")
        issues = worker_health_check(csv_p, 28, 20)
        self.root.after(0, lambda: self.show_results(issues))

    def show_results(self, issues):
        self.tabs.select(self.tab_dash)
        for row in self.tree.get_children(): self.tree.delete(row)
        for i in issues:
            tag = "crit" if i["Sev"] == "Critical" else "high"
            self.tree.insert("", "end", values=(i["NCU"], i["TCU"], i["Type"], i["Sev"], i["Msg"]), tags=(tag,))
        self.tree.tag_configure("crit", background="#ffcccc")
        self.tree.tag_configure("high", background="#fff3e0")
        messagebox.showinfo("Done", f"Found {len(issues)} issues.")

    # ==========================================================
    #  FIXED: LIVE PLOTTING LOGIC
    # ==========================================================
    def on_double_click_plot(self, event):
        """
        Handle double-click on a dashboard row.
        Priority 1: Open existing PNG (if Step 3 was run).
        Priority 2: Generate Live Plot (if Step 3 was skipped or file missing).
        """
        item = self.tree.selection()
        if not item: return
        
        # Get Tracker ID from the selected row
        vals = self.tree.item(item[0], "values")
        ncu, tcu = vals[0], vals[1]

        # Construct path safely
        relative_path = os.path.join("04_Tracker_plots_angles", self.date_val.get(), "each_tracker_plots", f"TX_{ncu}_TCU_{int(tcu)}.png")
        png_path = os.path.join(self.folder_path.get(), relative_path)
        
        # CRITICAL FIX: Normalize path to fix mixed slashes (//S01/ vs \folder\)
        png_path = os.path.normpath(png_path) 

        try:
            # Check if file exists AND try to open it
            if os.path.exists(png_path):
                print(f"Opening existing plot: {png_path}")
                os.startfile(png_path)
            else:
                # If file doesn't exist, force the exception block to run
                raise FileNotFoundError("File missing, switching to Live Plot.")
                
        except (FileNotFoundError, OSError) as e:
            # CATCH THE ERROR -> Run Live Plotter instead of crashing
            print(f"PNG not found ({e}). Generating Live Plot for {ncu}-{tcu}...")
            self.plot_live_popup(ncu, tcu)

    def plot_live_popup(self, ncu, tcu):
        try:
            # Read CSV freshly
            csv_path = os.path.join(self.folder_path.get(), "03_Merged_files", f"{self.date_val.get()}_1min_merged.csv")
            df = pd.read_csv(csv_path, dtype=str)
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
            
            # Filter
            mask = (df["NCU"].astype(int) == int(ncu)) & (df["TCU"].astype(int) == int(tcu))
            subset = df[mask]
            
            target = subset[subset["TC"] == "04"].sort_values("Timestamp")
            actual = subset[subset["TC"] == "05"].sort_values("Timestamp")

            # Create Popup Window
            top = tk.Toplevel(self.root)
            top.title(f"LIVE VIEW: NCU {ncu} - TCU {tcu}")
            top.geometry("900x500")

            # Embed Matplotlib Figure
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

            canvas = FigureCanvasTkAgg(fig, master=top)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Plot Error", f"Could not generate live plot:\n{e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = TrackerSuiteApp(root)
    root.mainloop()