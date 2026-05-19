import os
import sys
import datetime
import time
import threading
import colorsys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkcalendar import DateEntry
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw

try:
    import keyboard as kb_lib
    KEYBOARD_AVAILABLE = True
except ImportError:
    kb_lib = None
    KEYBOARD_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration (same as original)
# ---------------------------------------------------------------------------
PATH_TO_ORI_FOLDER = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/01_Original_files"
ASSETS_DIR = "assets"
SCADA_WINDOW_TITLE_PARTIAL = "SCADA Web Client Starter"

COORDS_ANALISI = (943, 96)
COORDS_SELEZIONE_INTERVALLO_DROPDOWN = (1212, 176)
COORDS_SELEZIONE_INTERVALLO_SCROLL_UP = (1209, 201)
COORDS_SELEZIONE_INTERVALLO_ORA = (1057, 235)
COORDS_SELEZIONE_INTERVALLO_SELEZIONE_L_ORA = (1082, 200)
COORDS_FILTER_WINDOW_OK_BUTTON = (1153, 364)
COORDS_MONTH_DROPDOWN = (830, 430)
COORDS_MONTH_JAN = (830, 449); COORDS_MONTH_FEB = (830, 466); COORDS_MONTH_MAR = (830, 484)
COORDS_MONTH_APR = (830, 500); COORDS_MONTH_MAY = (830, 514); COORDS_MONTH_JUN = (830, 530)
COORDS_MONTH_JUL = (830, 544); COORDS_MONTH_AUG = (830, 560); COORDS_MONTH_SEP = (830, 578)
COORDS_MONTH_OCT = (830, 595); COORDS_MONTH_NOV = (830, 612); COORDS_MONTH_DEC = (830, 625)
MONTH_COORDS = {
    1: COORDS_MONTH_JAN, 2: COORDS_MONTH_FEB, 3: COORDS_MONTH_MAR,
    4: COORDS_MONTH_APR, 5: COORDS_MONTH_MAY, 6: COORDS_MONTH_JUN,
    7: COORDS_MONTH_JUL, 8: COORDS_MONTH_AUG, 9: COORDS_MONTH_SEP,
    10: COORDS_MONTH_OCT, 11: COORDS_MONTH_NOV, 12: COORDS_MONTH_DEC
}
COORDS_YEAR_DROPDOWN = (968, 431); COORDS_YEAR_SCROLL_DOWN = (999, 913)
COORDS_YEAR_2025 = (952, 514); COORDS_YEAR_2026 = (952, 531); COORDS_YEAR_2027 = (952, 548)
YEAR_COORDS = {2025: COORDS_YEAR_2025, 2026: COORDS_YEAR_2026, 2027: COORDS_YEAR_2027}
DATE_SEARCH_REGION = (804, 557, 159, 145)
CALENDAR_GRID_MONDAY_X = 815; CALENDAR_GRID_FIRST_ROW_Y = 569
CALENDAR_CELL_W = 23; CALENDAR_CELL_H = 24
COORDS_TIME_SCROLL_UP = (1043, 547); COORDS_TIME_SCROLL_DOWN = (1043, 677)
COORDS_TIME_SELECTION_BASE = (1011, 661)
COORDS_TIME_SELECTION_0000 = (1011, 563); COORDS_TIME_SELECTION_0100 = (1011, 585)
COORDS_TIME_SELECTION_0200 = (1011, 609); COORDS_TIME_SELECTION_0300 = (1011, 624)
COORDS_TIME_SELECTION_0400 = (1011, 644); COORDS_TIME_SELECTION_0500 = (1011, 661)
COORDS_ESPORTA_DATI_BUTTON = (1469, 158)
COORDS_FILE_SAVE_DIALOG_FILENAME = (1140, 700)
COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON = (1267, 702)
COORDS_FILE_SAVE_DIALOG_CLOSE_BUTTON = (867, 588)
DELAY_ACTION = 1.0; DELAY_LOAD_DATA = 80; DELAY_SAVE_FILE = 80; DELAY_CLOSE_SAVE = 20

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
stop_event = threading.Event()
_log_callback = None   # set by GUI to receive log lines


def _log(msg):
    print(msg)
    if _log_callback:
        _log_callback(msg)


# ---------------------------------------------------------------------------
# Automation functions (same logic as original, using _log instead of print)
# ---------------------------------------------------------------------------

def interruptible_sleep(seconds, check_interval=0.5):
    deadline = time.time() + seconds
    while not stop_event.is_set():
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        time.sleep(min(check_interval, remaining))


def find_scada_window():
    windows = gw.getWindowsWithTitle(SCADA_WINDOW_TITLE_PARTIAL)
    if not windows:
        _log(f"Window '{SCADA_WINDOW_TITLE_PARTIAL}' not found.")
        return None
    return windows[0]


def focus_scada_window(window):
    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(1)
    except Exception as e:
        _log(f"Error activating window: {e}")
    time.sleep(0.5)
    time.sleep(1)


def find_image_in_region(image_name, region, confidence=0.6):
    try:
        screenshot = pyautogui.screenshot(region=region)
        haystack_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        haystack_gray = cv2.cvtColor(haystack_bgr, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        _log(f"Screenshot failed: {e}")
        return None

    path = os.path.join(ASSETS_DIR, f"{image_name}.png")
    if not os.path.exists(path):
        _log(f"Asset missing: {path}")
        return None

    template_bgr = cv2.imread(path)
    if template_bgr is None:
        return None
    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

    try:
        res_std = cv2.matchTemplate(haystack_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val_s, _, max_loc_s = cv2.minMaxLoc(res_std)
        _log(f"Search '{image_name}' (Standard): Score={max_val_s:.2f} at {max_loc_s}")
        if max_val_s >= 0.80:
            h, w = template_gray.shape[:2]
            gx = region[0] + max_loc_s[0] + w // 2
            gy = region[1] + max_loc_s[1] + h // 2
            _log(f"Found Standard match for {image_name} at ({gx}, {gy})")
            return pyautogui.Point(gx, gy)
    except Exception as e:
        _log(f"Standard Match error: {e}")

    try:
        haystack_edges = cv2.Canny(haystack_gray, 50, 200)
        template_edges = cv2.Canny(template_gray, 50, 200)
        res = cv2.matchTemplate(haystack_edges, template_edges, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        _log(f"Search '{image_name}' (Edges): Score={max_val:.2f} at {max_loc}")
        if max_val >= 0.80:
            h, w = template_gray.shape[:2]
            gx = region[0] + max_loc[0] + w // 2
            gy = region[1] + max_loc[1] + h // 2
            _log(f"Found Edge match for {image_name} at ({gx}, {gy})")
            return pyautogui.Point(gx, gy)
    except Exception as e:
        _log(f"Edge Match error: {e}")

    return None


def check_color_is_black_bg_white_text(x, y):
    try:
        screenshot = pyautogui.screenshot(region=(int(x) - 2, int(y) - 2, 5, 5))
        img = np.array(screenshot)
        avg_color = np.mean(img)
        _log(f"Color check at ({x},{y}): Avg Brightness = {avg_color}")
        if avg_color < 100:
            _log("Confirmed dark background.")
            return True
        else:
            _log("Warning: Background seems bright.")
            return False
    except Exception as e:
        _log(f"Color check failed: {e}")
        return False


def perform_initial_setup():
    _log("=== Step 1 & 2: Window Management ===")
    window = find_scada_window()
    if not window:
        return False
    focus_scada_window(window)
    return True


def perform_reset():
    _log("Resetting to normal selection mode.")
    pyautogui.press('esc')
    time.sleep(0.5)


def perform_scada_prep():
    _log("=== Step 3: Click ANALISI ===")
    pyautogui.click(COORDS_ANALISI)
    time.sleep(DELAY_ACTION)
    _log("=== Step 4: Click Dropdown Selezione Intervallo ===")
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_DROPDOWN)
    time.sleep(0.5)
    _log("=== Step 5: Click Scroll Up x5 ===")
    for _ in range(5):
        pyautogui.click(COORDS_SELEZIONE_INTERVALLO_SCROLL_UP)
        time.sleep(0.1)
    _log("=== Step 6: Click ORA ===")
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_ORA)
    time.sleep(DELAY_ACTION)
    return True


def get_date_grid_coords(target_date):
    # Calendar grid starts with Monday
    first_day = datetime.date(target_date.year, target_date.month, 1)
    # Find the Monday on or before the 1st of the month
    first_grid_day = first_day - datetime.timedelta(days=first_day.weekday())
    delta = (target_date - first_grid_day).days
    row = delta // 7
    col = delta % 7
    # No adjustment needed; row/col calculation is correct for Monday-starting grid
    x = CALENDAR_GRID_MONDAY_X + col * CALENDAR_CELL_W
    y = CALENDAR_GRID_FIRST_ROW_Y + row * CALENDAR_CELL_H
    _log(f"Grid calc: first_grid_day={first_grid_day}, delta={delta}, row={row}, col={col} → ({int(x)}, {int(y)})")
    return (int(x), int(y))


def process_hourly_report(target_date, target_hour):
    _log(f"Starting Process for {target_date} // {target_hour}:00")

    _log("=== Step 7: Click Month Dropdown ===")
    pyautogui.click(COORDS_MONTH_DROPDOWN)
    time.sleep(0.5)

    _log(f"=== Step 8: Select Month ({target_date.month}) ===")
    month_coords = MONTH_COORDS.get(target_date.month)
    if month_coords:
        pyautogui.click(month_coords)
    else:
        _log(f"Error: No coords for month {target_date.month}")
        return False
    time.sleep(0.5)

    _log("=== Step 9: Select Year ===")
    if target_date.year != datetime.date.today().year:
        pyautogui.click(COORDS_YEAR_DROPDOWN)
        time.sleep(0.5)
        _log("Scrolling Year to bottom (40 clicks)...")
        for _ in range(40):
            pyautogui.click(COORDS_YEAR_SCROLL_DOWN)
            time.sleep(0.02)
        year_coords = YEAR_COORDS.get(target_date.year)
        if year_coords:
            _log(f"Clicking Year {target_date.year}")
            pyautogui.click(year_coords)
        else:
            _log(f"Error: No coords for year {target_date.year}.")
            return False
    else:
        _log(f"Year {target_date.year} is current year. No need to select.")
    time.sleep(0.5)

    _log(f"=== Step 10: Select Date ({target_date.day}) ===")
    if target_date == datetime.date.today():
        _log(f"Target date {target_date} is TODAY. Skipping selection.")
    else:
        day_img = f"day_{target_date.day}"
        pos = find_image_in_region(day_img, DATE_SEARCH_REGION, confidence=0.65)
        if pos:
            _log(f"Found {day_img} at {pos}. Clicking...")
        else:
            _log(f"Image match failed for day {target_date.day}. Using grid fallback.")
            gx, gy = get_date_grid_coords(target_date)
            pos = pyautogui.Point(gx, gy)
        pyautogui.click(pos)
        time.sleep(0.5)
        _log("=== Step 11: Color Verification ===")
        check_color_is_black_bg_white_text(pos.x, pos.y)

    _log("=== Step 12: Time Selection - Reset to Min ===")
    for _ in range(20):
        pyautogui.click(COORDS_TIME_SCROLL_UP)
        time.sleep(0.05)

    _log(f"=== Step 13: Select Time {target_hour}:00 ===")
    if target_hour < 5:
        early_coords = {
            0: COORDS_TIME_SELECTION_0000, 1: COORDS_TIME_SELECTION_0100,
            2: COORDS_TIME_SELECTION_0200, 3: COORDS_TIME_SELECTION_0300,
            4: COORDS_TIME_SELECTION_0400
        }
        coords = early_coords.get(target_hour)
        if coords:
            pyautogui.click(coords)
        else:
            _log(f"Error: No coords for hour {target_hour}")
            return False
    else:
        scrolls_needed = max(0, target_hour - 5)
        if scrolls_needed > 0:
            _log(f"Scrolling down {scrolls_needed} times for {target_hour}:00")
            for _ in range(scrolls_needed):
                pyautogui.click(COORDS_TIME_SCROLL_DOWN)
                time.sleep(0.1)
        pyautogui.click(COORDS_TIME_SELECTION_BASE)
    time.sleep(0.5)

    _log("Clicking OK Filter Button...")
    pyautogui.click(COORDS_FILTER_WINDOW_OK_BUTTON)

    _log(f"=== Step 14: Wait for Load ({DELAY_LOAD_DATA}s) ===")
    interruptible_sleep(DELAY_LOAD_DATA)

    _log("=== Step 15: Click Export ===")
    pyautogui.click(COORDS_ESPORTA_DATI_BUTTON)
    time.sleep(2.0)

    _log("=== Step 16 & 17: Save File Logic ===")
    pyautogui.click(COORDS_FILE_SAVE_DIALOG_FILENAME)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)

    year_str = str(target_date.year)
    month_str = f"{target_date.month:02d}"
    day_str = f"{target_date.day:02d}"
    hh_str = f"{target_hour:02d}"
    jj = (target_hour + 1) % 24
    jj_str = f"{jj:02d}"
    date_dash = f"{year_str}-{month_str}-{day_str}"
    filename = f"{day_str}_{month_str}_{year_str}_{hh_str}_{jj_str}.csv"
    full_path = os.path.normpath(os.path.join(PATH_TO_ORI_FOLDER, year_str, month_str, date_dash, filename))
    _log(f"Saving to: {full_path}")

    dir_path = os.path.dirname(full_path)
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            _log(f"Error creating directory {dir_path}: {e}")

    pyautogui.write(full_path, interval=0.01)
    time.sleep(1.0)

    _log("=== Step 18: Save and Wait ===")
    pyautogui.click(COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON)
    interruptible_sleep(DELAY_SAVE_FILE)
    _log(f"Task Completed FOR {target_hour}:00")
    return True


def run_bulk_automation(start_date, end_date, start_hour, end_hour):
    """Run automation from start_date to end_date (inclusive), start_hour to end_hour-1."""
    delta_days = (end_date - start_date).days + 1

    if not perform_initial_setup():
        _log("Initial setup failed.")
        return

    for day_offset in range(delta_days):
        if stop_event.is_set():
            _log("[STOP] Automation stopped by user.")
            break

        current_date = start_date + datetime.timedelta(days=day_offset)
        _log(f"\n{'='*60}\n--- PROCESSING DATE {current_date} ---\n{'='*60}")

        for current_hour in range(start_hour, end_hour):
            if stop_event.is_set():
                _log("[STOP] Automation stopped by user.")
                break

            _log(f"\n--- PROCESSING HOUR {current_hour}:00 ---")
            time.sleep(1.0)
            perform_scada_prep()
            success = process_hourly_report(current_date, current_hour)
            if not success:
                _log(f"Failed to process hour {current_hour}:00. Stopping loop.")
                break
            perform_reset()
            _log("Waiting for reset animation...")
            time.sleep(2.0)

        _log(f"Date {current_date} completed.")

    _log(f"\n{'='*60}\nAll tasks completed.\n{'='*60}")


# ---------------------------------------------------------------------------
# Overlay (unchanged from original)
# ---------------------------------------------------------------------------

def _overlay_worker():
    try:
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{sw}x{sh}+0+0")
        TRANS = '#010203'
        root.wm_attributes('-transparentcolor', TRANS)
        root.configure(bg=TRANS)
        canvas = tk.Canvas(root, width=sw, height=sh, bg=TRANS, highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        T = 7         # border thickness in pixels
        N = 300       # number of gradient segments around the perimeter
        SPEED = 0.004 # hue shift per frame (controls flow speed)

        perimeter = 2.0 * (sw + sh)
        top_f   = sw / perimeter
        right_f = sh / perimeter
        bot_f   = sw / perimeter

        def border_point(t):
            """Map t in [0,1) to (x,y) going clockwise: top→right→bottom→left."""
            t = t % 1.0
            if t < top_f:
                return t / top_f * sw, T / 2
            t -= top_f
            if t < right_f:
                return sw - T / 2, t / right_f * sh
            t -= right_f
            if t < bot_f:
                return (1 - t / bot_f) * sw, sh - T / 2
            t -= bot_f
            left_f = 1.0 - top_f - right_f - bot_f
            return T / 2, (1 - t / left_f) * sh

        def hsv_hex(h):
            r, g, b = colorsys.hsv_to_rgb(h % 1.0, 0.55, 0.85)
            return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

        # Pre-create line segments on the canvas
        segments = []
        for i in range(N):
            x0, y0 = border_point(i / N)
            x1, y1 = border_point((i + 1) / N)
            seg = canvas.create_line(x0, y0, x1, y1, fill='red', width=T,
                                     capstyle='round', joinstyle='round')
            segments.append(seg)

        phase = [0.0]

        def animate():
            phase[0] = (phase[0] + SPEED) % 1.0
            for i, seg in enumerate(segments):
                hue = (i / N + phase[0]) % 1.0
                canvas.itemconfig(seg, fill=hsv_hex(hue))
            root.after(16, animate)  # ~60 fps

        def check_stop():
            if stop_event.is_set():
                root.destroy()
                return
            root.after(200, check_stop)

        root.after(0, animate)
        root.after(200, check_stop)
        root.mainloop()
    except Exception as e:
        _log(f"[Overlay] Error: {e}")


def show_overlay():
    t = threading.Thread(target=_overlay_worker, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class ScadaGUI:
    def __init__(self, root):
        self.root = root
        root.title("SCADA Automation")
        root.resizable(True, True)
        root.minsize(640, 500)

        self._automation_thread = None

        self._build_ui()
        self._redirect_stdout()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        today = datetime.date.today()
        hour_labels = [f"{h:02d}:00" for h in range(24)]
        end_hour_labels = [f"{h:02d}:00" for h in range(1, 25)]

        # ---- Settings frame ----
        frm_settings = ttk.LabelFrame(self.root, text="Settings", padding=8)
        frm_settings.pack(fill='x', padx=10, pady=(10, 4))

        # Row 0: Start date
        ttk.Label(frm_settings, text="Start Date:").grid(row=0, column=0, sticky='w', padx=8, pady=6)
        self.cal_start = DateEntry(
            frm_settings, width=13, date_pattern='yyyy-mm-dd',
            year=today.year, month=today.month, day=today.day,
            showweeknumbers=False, firstweekday='monday'
        )
        self.cal_start.grid(row=0, column=1, sticky='w', padx=8, pady=6)

        # Row 1: End date
        ttk.Label(frm_settings, text="End Date:").grid(row=1, column=0, sticky='w', padx=8, pady=6)
        self.cal_end = DateEntry(
            frm_settings, width=13, date_pattern='yyyy-mm-dd',
            year=today.year, month=today.month, day=today.day,
            showweeknumbers=False, firstweekday='monday'
        )
        self.cal_end.grid(row=1, column=1, sticky='w', padx=8, pady=6)

        # Separator
        ttk.Separator(frm_settings, orient='vertical').grid(row=0, column=2, rowspan=2, sticky='ns', padx=12, pady=4)

        # Row 0: Start hour dropdown
        ttk.Label(frm_settings, text="Start Hour:").grid(row=0, column=3, sticky='w', padx=8, pady=6)
        self.cmb_start_hour = ttk.Combobox(frm_settings, values=hour_labels, state='readonly', width=7)
        self.cmb_start_hour.current(0)   # default 00:00
        self.cmb_start_hour.grid(row=0, column=4, sticky='w', padx=8, pady=6)

        # Row 1: End hour dropdown
        ttk.Label(frm_settings, text="End Hour:").grid(row=1, column=3, sticky='w', padx=8, pady=6)
        self.cmb_end_hour = ttk.Combobox(frm_settings, values=end_hour_labels, state='readonly', width=7)
        self.cmb_end_hour.current(24-1)    # default 24:00 (index 23)
        self.cmb_end_hour.grid(row=1, column=4, sticky='w', padx=8, pady=6)

        # ---- Control buttons ----
        frm_ctrl = ttk.Frame(self.root, padding=(10, 4))
        frm_ctrl.pack(fill='x')

        self.btn_start = ttk.Button(frm_ctrl, text="▶  Start", command=self._on_start)
        self.btn_start.pack(side='left', padx=4)

        self.btn_stop = ttk.Button(frm_ctrl, text="■  Stop", command=self._on_stop, state='disabled')
        self.btn_stop.pack(side='left', padx=4)

        self.btn_clear = ttk.Button(frm_ctrl, text="Clear Log", command=self._clear_log)
        self.btn_clear.pack(side='right', padx=4)

        self.lbl_status = ttk.Label(frm_ctrl, text="Idle", foreground='gray')
        self.lbl_status.pack(side='left', padx=12)

        # ---- Log output ----
        frm_log = ttk.LabelFrame(self.root, text="Output Log", padding=4)
        frm_log.pack(fill='both', expand=True, padx=10, pady=(4, 10))

        self.log_text = scrolledtext.ScrolledText(
            frm_log, state='disabled', wrap='word',
            font=('Consolas', 9), background='#1e1e1e', foreground='#d4d4d4',
            insertbackground='white'
        )
        self.log_text.pack(fill='both', expand=True)

        # Colour tags
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('step',  foreground='#9cdcfe')
        self.log_text.tag_config('ok',    foreground='#4ec9b0')
        self.log_text.tag_config('warn',  foreground='#dcdcaa')

    # ------------------------------------------------------------------
    # Stdout redirect
    # ------------------------------------------------------------------

    def _redirect_stdout(self):
        global _log_callback
        _log_callback = self._append_log

        class _Writer:
            def __init__(self, cb):
                self._cb = cb
            def write(self, msg):
                if msg.strip():
                    self._cb(msg.rstrip())
            def flush(self):
                pass

        sys.stdout = _Writer(self._append_log)

    def _append_log(self, msg):
        """Thread-safe log append."""
        self.root.after(0, self._do_append, msg)

    def _do_append(self, msg):
        self.log_text.configure(state='normal')
        tag = ''
        low = msg.lower()
        if 'error' in low or 'fail' in low or '[stop]' in low:
            tag = 'error'
        elif '===' in msg or '---' in msg:
            tag = 'step'
        elif 'completed' in low or 'found' in low or 'saving' in low:
            tag = 'ok'
        elif 'warn' in low or 'fallback' in low:
            tag = 'warn'

        self.log_text.insert('end', msg + '\n', tag)
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def _clear_log(self):
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_start(self):
        start_date = self.cal_start.get_date()
        end_date   = self.cal_end.get_date()
        if end_date < start_date:
            messagebox.showerror("Invalid range", "End date must be >= start date.")
            return

        start_hour = int(self.cmb_start_hour.get().split(':')[0])
        end_hour   = int(self.cmb_end_hour.get().split(':')[0])
        if end_hour <= start_hour:
            messagebox.showerror("Invalid hours", "End hour must be greater than start hour.")
            return

        stop_event.clear()
        self.btn_start.configure(state='disabled')
        self.btn_stop.configure(state='normal')
        self.lbl_status.configure(text="Running…", foreground='#4ec9b0')

        show_overlay()

        if KEYBOARD_AVAILABLE and kb_lib:
            def _stop_hotkey():
                self._append_log("\n[STOP] Ctrl+Alt+. detected — stopping automation...")
                stop_event.set()
            def _stop_hotkey_shift_s():
                self._append_log("\n[STOP] Ctrl+Shift+S detected — stopping automation...")
                stop_event.set()
            try:
                kb_lib.add_hotkey('ctrl+alt+.', _stop_hotkey)
                kb_lib.add_hotkey('ctrl+shift+s', _stop_hotkey_shift_s)
                self._append_log("[INFO] Keyboard hotkeys registered: Ctrl+Alt+. and Ctrl+Shift+S")
            except Exception as e:
                self._append_log(f"[WARN] Failed to register hotkeys: {e}")

        self._automation_thread = threading.Thread(
            target=self._run_automation,
            args=(start_date, end_date, start_hour, end_hour),
            daemon=True
        )
        self._automation_thread.start()

    def _on_stop(self):
        stop_event.set()
        self.lbl_status.configure(text="Stopping…", foreground='#f48771')
        self.btn_stop.configure(state='disabled')

    def _run_automation(self, start_date, end_date, start_hour, end_hour):
        try:
            run_bulk_automation(start_date, end_date, start_hour, end_hour)
        except Exception as e:
            self._append_log(f"[ERROR] Unhandled exception: {e}")
        finally:
            stop_event.set()
            self.root.after(0, self._on_automation_done)

    def _on_automation_done(self):
        self.btn_start.configure(state='normal')
        self.btn_stop.configure(state='disabled')
        self.lbl_status.configure(text="Done", foreground='gray')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    root = tk.Tk()
    app = ScadaGUI(root)
    root.mainloop()
