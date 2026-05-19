import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import csv
import glob
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import sys
import time

# ==============================================================================
# WORKER FUNCTIONS (Must be global for Multiprocessing)
# ==============================================================================

def worker_load_and_analyze(file_path, low_angle_th, dev_th):
    """
    Loads the merged CSV and performs vectorised health checks.
    """
    try:
        df = pd.read_csv(file_path, dtype=str)
        # Convert types
        df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df["NCU"] = pd.to_numeric(df["NCU"], errors="coerce")
        df["TCU"] = pd.to_numeric(df["TCU"], errors="coerce")
        df["TC"] = pd.to_numeric(df["TC"], errors="coerce")
        
        # Filter strictly for Target (4) and Actual (5)
        df = df[df["TC"].isin([4, 5])].dropna(subset=["Valore", "NCU", "TCU"])
        
        issues = []
        
        # Group by Tracker
        # We process each tracker to find specific behavioral issues
        for (ncu, tcu), group in df.groupby(["NCU", "TCU"]):
            # Split Target/Actual
            target = group[group["TC"] == 4]["Valore"]
            actual = group[group["TC"] == 5]["Valore"]
            
            # CHECK 1: DATA COMPLETENESS
            # If we have very few points, it's a comms issue
            if len(actual) < 10: 
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "DATA LOSS", 
                               "Message": f"Only {len(actual)} data points found", "Severity": "High"})
                continue
            
            # CHECK 2: STUCK TRACKER
            # Logic: If Target moves (std > 5) but Actual is flat (std < 0.2)
            t_std = target.std() if not target.empty else 0
            a_std = actual.std()
            
            if t_std > 5 and a_std < 0.5:
                issues.append({"NCU": ncu, "TCU": tcu, "Type": "STUCK", 
                               "Message": f"Tracker stuck. Target var: {t_std:.1f}, Actual var: {a_std:.1f}", "Severity": "Critical"})

            # CHECK 3: HIGH DEVIATION (AVG)
            # Re-align for diff calculation
            group_sorted = group.sort_values("Timestamp")
            t_pts = group_sorted[group_sorted["TC"] == 4].set_index("Timestamp")["Valore"]
            a_pts = group_sorted[group_sorted["TC"] == 5].set_index("Timestamp")["Valore"]
            
            # Merge indices to compute diff
            combined = pd.concat([t_pts, a_pts], axis=1, keys=['t', 'a']).dropna()
            if not combined.empty:
                combined['diff'] = (combined['t'] - combined['a']).abs()
                max_diff = combined['diff'].max()
                mean_diff = combined['diff'].mean()
                
                if mean_diff > float(dev_th):
                    issues.append({"NCU": ncu, "TCU": tcu, "Type": "DEVIATION", 
                                   "Message": f"Avg Deviation {mean_diff:.1f}° > {dev_th}°", "Severity": "Medium"})
                
                # CHECK 4: LOW ANGLE SAFETY
                # Check if any actual angle < low_angle_th
                min_angle = combined['a'].min()
                if min_angle < float(low_angle_th):
                     issues.append({"NCU": ncu, "TCU": tcu, "Type": "LOW ANGLE", 
                                   "Message": f"Min Angle {min_angle:.1f}° < {low_angle_th}°", "Severity": "High"})

        return issues
        
    except Exception as e:
        return [({"NCU": 0, "TCU": 0, "Type": "ERROR", "Message": str(e), "Severity": "Critical"})]

# ==============================================================================
# GUI UTILITIES
# ==============================================================================

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.see("end")
        self.widget.configure(state="disabled")
        self.widget.update_idletasks()

    def flush(self): pass

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

class AnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SCADA Advanced Tracker Health Monitor")
        self.root.geometry("1000x800")
        
        # State Variables
        self.folder_path = tk.StringVar()
        self.date_val = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.angle_thresh = tk.StringVar(value="28")
        self.dev_thresh = tk.StringVar(value="20")
        self.merged_file_path = None
        
        self.setup_ui()

    def setup_ui(self):
        # --- TAB STRUCTURE ---
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(expand=1, fill="both")
        
        # TAB 1: DASHBOARD
        self.tab_dash = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_dash, text="Main Dashboard")
        
        # TAB 2: LOGS
        self.tab_logs = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_logs, text="Process Logs")

        # --- CONTROLS SECTION (Top of Dashboard) ---
        frm_ctrl = ttk.LabelFrame(self.tab_dash, text="Configuration", padding=10)
        frm_ctrl.pack(fill="x", padx=10, pady=5)
        
        grid_opts = {'sticky': 'w', 'pady': 5, 'padx': 5}
        
        # Row 1: Folder
        ttk.Label(frm_ctrl, text="Report Folder:").grid(row=0, column=0, **grid_opts)
        ttk.Entry(frm_ctrl, textvariable=self.folder_path, width=60).grid(row=0, column=1, columnspan=3, **grid_opts)
        ttk.Button(frm_ctrl, text="Browse", command=self.browse_folder).grid(row=0, column=4, **grid_opts)
        
        # Row 2: Date & Thresholds
        ttk.Label(frm_ctrl, text="Date (YYYY-MM-DD):").grid(row=1, column=0, **grid_opts)
        ttk.Entry(frm_ctrl, textvariable=self.date_val, width=15).grid(row=1, column=1, **grid_opts)
        
        ttk.Label(frm_ctrl, text="Min Angle (°):").grid(row=1, column=2, **grid_opts)
        ttk.Entry(frm_ctrl, textvariable=self.angle_thresh, width=5).grid(row=1, column=3, **grid_opts)
        
        ttk.Label(frm_ctrl, text="Max Dev (°):").grid(row=1, column=4, **grid_opts)
        ttk.Entry(frm_ctrl, textvariable=self.dev_thresh, width=5).grid(row=1, column=5, **grid_opts)

        # --- ACTION BUTTONS ---
        frm_btn = ttk.Frame(self.tab_dash)
        frm_btn.pack(fill="x", padx=10, pady=5)
        
        self.btn_run_pipe = tk.Button(frm_btn, text="1. Run Full Processing Pipeline", bg="#DDDDDD", command=self.run_pipeline)
        self.btn_run_pipe.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_health = tk.Button(frm_btn, text="2. RUN DEEP HEALTH CHECK", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.run_health_check)
        self.btn_health.pack(side="left", fill="x", expand=True, padx=5)

        # --- RESULTS TABLE (Treeview) ---
        lbl_res = tk.Label(self.tab_dash, text="Detected Issues (Double-click row to visualize)", font=("Arial", 10, "bold"))
        lbl_res.pack(anchor="w", padx=15, pady=(10,0))
        
        columns = ("NCU", "TCU", "Type", "Severity", "Message")
        self.tree = ttk.Treeview(self.tab_dash, columns=columns, show="headings", height=15)
        
        # Column Config
        self.tree.heading("NCU", text="NCU")
        self.tree.column("NCU", width=50, anchor="center")
        self.tree.heading("TCU", text="TCU")
        self.tree.column("TCU", width=50, anchor="center")
        self.tree.heading("Type", text="Issue Type")
        self.tree.column("Type", width=100, anchor="center")
        self.tree.heading("Severity", text="Severity")
        self.tree.column("Severity", width=80, anchor="center")
        self.tree.heading("Message", text="Details")
        self.tree.column("Message", width=400)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tab_dash, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Bind Double Click
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        # --- EXPORT BUTTON ---
        tk.Button(self.tab_dash, text="Export Issues to CSV", command=self.export_csv).pack(pady=5)

        # --- LOGGING SETUP ---
        self.txt_log = tk.Text(self.tab_logs, state="disabled", bg="#f0f0f0", font=("Consolas", 9))
        self.txt_log.pack(fill="both", expand=True)
        sys.stdout = TextRedirector(self.txt_log)

    def browse_folder(self):
        f = filedialog.askdirectory()
        if f: self.folder_path.set(f)

    def run_pipeline(self):
        # Placeholder for the full pipeline (from previous script)
        # For this example, we assume pipeline has run or user wants to check existing files.
        messagebox.showinfo("Info", "Please ensure standard processing (Steps 1-3) is done first.\n\n(You can paste the logic from the previous 'HighPerfTrackerApp' here if needed).")

    def run_health_check(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "Select Root Folder")
            return
            
        date_str = self.date_val.get()
        # Locate the merged file
        self.merged_file_path = os.path.join(self.folder_path.get(), "03_Merged_files", f"{date_str}_1min_merged.csv")
        
        if not os.path.exists(self.merged_file_path):
            messagebox.showerror("Error", f"Merged file not found:\n{self.merged_file_path}\n\nPlease run the Processing Pipeline first.")
            return
            
        self.btn_health.config(state="disabled", text="Analyzing...")
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        threading.Thread(target=self.execute_analysis).start()

    def execute_analysis(self):
        print("\n--- STARTING DEEP HEALTH ANALYSIS ---")
        try:
            # We use a ThreadPool or direct call since it's one big CSV usually. 
            # If files were split, we'd use ProcessPool.
            # Here we call the worker logic directly to simplify passing data back to GUI.
            
            issues = worker_load_and_analyze(self.merged_file_path, self.angle_thresh.get(), self.dev_thresh.get())
            
            # Update GUI on main thread
            self.root.after(0, lambda: self.populate_results(issues))
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.root.after(0, lambda: self.btn_health.config(state="normal", text="2. RUN DEEP HEALTH CHECK"))

    def populate_results(self, issues):
        print(f"Analysis complete. Found {len(issues)} potential issues.")
        
        count = 0
        for i in issues:
            # Color coding
            tag = "normal"
            if i["Severity"] == "Critical": tag = "critical"
            elif i["Severity"] == "High": tag = "high"
            
            self.tree.insert("", "end", values=(i["NCU"], i["TCU"], i["Type"], i["Severity"], i["Message"]), tags=(tag,))
            count += 1

        self.tree.tag_configure("critical", background="#ffcccc") # Light Red
        self.tree.tag_configure("high", background="#fff4cc")     # Light Orange
        
        if count > 0:
            messagebox.showwarning("Issues Found", f"Analysis found {count} issues.\nCheck the table for details.")
            # Auto-save CSV
            self.save_csv_auto(issues)
        else:
            messagebox.showinfo("All Clear", "System Health Check Passed.\nNo anomalies detected based on current thresholds.")

    def save_csv_auto(self, issues):
        out_path = os.path.join(self.folder_path.get(), "04_Tracker_plots_angles", self.date_val.get(), "System_Health_Report.csv")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        pd.DataFrame(issues).to_csv(out_path, index=False, sep=";", encoding="utf-8-sig")
        print(f"Report saved to: {out_path}")

    def export_csv(self):
        # Manual export if needed
        pass # (Already handled by auto-save, but can add file dialog here)

    def on_tree_double_click(self, event):
        item = self.tree.selection()[0]
        vals = self.tree.item(item, "values")
        ncu, tcu = vals[0], vals[1]
        
        self.plot_specific_tracker(ncu, tcu)

    def plot_specific_tracker(self, ncu, tcu):
        """Generates a popup plot for the selected tracker"""
        try:
            # Quick read for plotting (Not efficient for bulk, but fine for single click)
            df = pd.read_csv(self.merged_file_path, dtype=str)
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
            
            # Filter
            part = df[(df["NCU"] == str(int(ncu)).zfill(2)) & (df["TCU"] == str(int(tcu)).zfill(3))]
            
            target = part[part["TC"] == "04"].sort_values("Timestamp")
            actual = part[part["TC"] == "05"].sort_values("Timestamp")

            # Popup Window
            top = tk.Toplevel(self.root)
            top.title(f"Visual Inspection: NCU {ncu} - TCU {tcu}")
            top.geometry("900x500")

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(target["Timestamp"], target["Valore"], label="Target", color="blue", linewidth=1.5)
            ax.plot(actual["Timestamp"], actual["Valore"], label="Actual", color="red", linewidth=1.5, linestyle="--")
            
            ax.set_title(f"Detail View: NCU {ncu} / TCU {tcu}")
            ax.set_ylabel("Angle (°)")
            ax.legend()
            ax.grid(True)

            canvas = FigureCanvasTkAgg(fig, master=top)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Plot Error", f"Could not plot data:\n{e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = AnalyticsApp(root)
    root.mainloop()