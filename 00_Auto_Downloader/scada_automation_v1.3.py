# created on 14/09/2026
import os
import sys
import datetime
import time
import threading
import tkinter as tk
from tkinter import simpledialog
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
#\\S01\get\2025.01 Mazara 01 A2A\03 - REPORT\Report\04 Tracker report\01_Original_files\2026\02

__version__ = "1.3"
VERIFY_AND_BACKUP = False
GRID_FIRST = True
TEST_DATE = None
# v1.2 changelog (improvements over v1.1, scheduling core unchanged):
# - Single clock rule: AVAILABILITY_LAG_MINUTES=5 — hour H downloadable from (H+1):05.
#   get_last_completed_datetime(), get_trigger_time_for_target(), generate_backfill_hours(),
#   get_first_run_target() and get_next_trigger_time() all share it (v1.1 had copies).
# - FIX: get_next_trigger_time(now) restores the :00-:04 -> immediate :05 precision.
# - ADD: pre-filter of already-valid CSVs before touching SCADA (fast re-runs).
# - ADD: lazy SCADA start — with -c and nothing due yet, wait BEFORE opening SCADA.
# - ADD: chunked data-load wait with progress (same total, operator can skip early).
# - ADD: --max-retries bound for continuous same-hour retry (0 = unlimited, default).
# - ADD: per-hour/total timing in range phase.
# - GUI: smart end-hour default (last completed hour), "Recupera Oggi + Continua"
#   preset and live due/future summary (cp1252-safe tags).

# --- Global stop and skip flags ---
stop_event = threading.Event()
skip_wait_event = threading.Event()

# --- Configuration ---
# PATHS & DELAYS (User to configure these if needed)
PATH_TO_ORI_FOLDER = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/01_Original_files" # Placeholder path
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# WINDOW
SCADA_WINDOW_TITLE_PARTIAL = "SCADA Web Client Starter"

# COORDINATES
# 3. Click ANALISI
COORDS_ANALISI = (943, 96) 

# 4. Dropdown Selezione Intervallo
COORDS_SELEZIONE_INTERVALLO_DROPDOWN = (1212, 176)

# 5. Scroll Up x5
COORDS_SELEZIONE_INTERVALLO_SCROLL_UP = (1209, 201)

# 6. Click ORA
COORDS_SELEZIONE_INTERVALLO_ORA = (1057, 235)
COORDS_SELEZIONE_INTERVALLO_SELEZIONE_L_ORA = (1082, 200)

COORDS_FILTER_WINDOW_OK_BUTTON = (1153, 364)
# 7. Month Dropdown
COORDS_MONTH_DROPDOWN = (830, 430)

# 8. Months Locations
COORDS_MONTH_JAN = (830, 449)
COORDS_MONTH_FEB = (830, 466)
COORDS_MONTH_MAR = (830, 484)
COORDS_MONTH_APR = (830, 500)
COORDS_MONTH_MAY = (830, 514)
COORDS_MONTH_JUN = (830, 530)
COORDS_MONTH_JUL = (830, 544)
COORDS_MONTH_AUG = (830, 560)
COORDS_MONTH_SEP = (830, 578)
COORDS_MONTH_OCT = (830, 595)
COORDS_MONTH_NOV = (830, 612)
COORDS_MONTH_DEC = (830, 625)

MONTH_COORDS = {
    1: COORDS_MONTH_JAN, 2: COORDS_MONTH_FEB, 3: COORDS_MONTH_MAR,
    4: COORDS_MONTH_APR, 5: COORDS_MONTH_MAY, 6: COORDS_MONTH_JUN,
    7: COORDS_MONTH_JUL, 8: COORDS_MONTH_AUG, 9: COORDS_MONTH_SEP,
    10: COORDS_MONTH_OCT, 11: COORDS_MONTH_NOV, 12: COORDS_MONTH_DEC
}

# 9. Year Selection
COORDS_YEAR_DROPDOWN = (968, 431)
COORDS_YEAR_SCROLL_DOWN = (999, 913) # To scroll to bottom
COORDS_YEAR_2025 = (952, 514)
COORDS_YEAR_2026 = (952, 531)
COORDS_YEAR_2027 = (952, 548)

YEAR_COORDS = {
    2025: COORDS_YEAR_2025,
    2026: COORDS_YEAR_2026,
    2027: COORDS_YEAR_2027
}

# 10. Date Search Area (Rectangle)
# Starts at Mo column (x=779) to exclude Wo week-number column
DATE_SEARCH_REGION = (779, 555, 188, 147) # (left, top, width, height)

# Optional override coordinates for specific dates.
DATE_COORDINATE_OVERRIDES = {}

# Calendar grid layout for fallback coordinate calculation (measured directly from 1080p screenshot).
CALENDAR_GRID_MONDAY_X  = 792   # x-center of the Monday (Mo) column
CALENDAR_GRID_FIRST_ROW_Y = 567 # y-center of the first visible week row
CALENDAR_CELL_W = 26.95         # pixels per day column
CALENDAR_CELL_H = 24.5          # pixels per week row

# 12. Time Selection
COORDS_TIME_SCROLL_UP = (1043, 547)
COORDS_TIME_SCROLL_DOWN = (1043, 677)

COORDS_TIME_SELECTION_BASE = (1011, 661)
COORDS_TIME_SELECTION_0000 = (1011, 563)
COORDS_TIME_SELECTION_0100 = (1011, 585)
COORDS_TIME_SELECTION_0200 = (1011, 609)
COORDS_TIME_SELECTION_0300 = (1011, 624)
COORDS_TIME_SELECTION_0400 = (1011, 644)
COORDS_TIME_SELECTION_0500 = (1011, 661)
COORDS_TIME_SELECTION_0600 = (1011, 661)    #click 1 time scroll down
COORDS_TIME_SELECTION_0700 = (1011, 661)    #click 2 time scroll down
COORDS_TIME_SELECTION_0800 = (1011, 661)    #click 3 time scroll down
COORDS_TIME_SELECTION_0900 = (1011, 661)    #click 4 time scroll down
COORDS_TIME_SELECTION_1000 = (1011, 661)    #click 5 time scroll down
COORDS_TIME_SELECTION_1100 = (1011, 661)    #click 6 time scroll down
COORDS_TIME_SELECTION_1200 = (1011, 661)    #click 7 time scroll down
COORDS_TIME_SELECTION_1300 = (1011, 661)    #click 8 time scroll down
COORDS_TIME_SELECTION_1400 = (1011, 661)    #click 9 time scroll down
COORDS_TIME_SELECTION_1500 = (1011, 661)    #click 10 time scroll down
COORDS_TIME_SELECTION_1600 = (1011, 661)    #click 11 time scroll down
COORDS_TIME_SELECTION_1700 = (1011, 661)    #click 12 time scroll down
COORDS_TIME_SELECTION_1800 = (1011, 661)    #click 13 time scroll down
COORDS_TIME_SELECTION_1900 = (1011, 661)    #click 14 time scroll down
COORDS_TIME_SELECTION_2000 = (1011, 661)    #click 15 time scroll down
COORDS_TIME_SELECTION_2100 = (1011, 661)    #click 16 time scroll down
COORDS_TIME_SELECTION_2200 = (1011, 661)    #click 17 time scroll down
COORDS_TIME_SELECTION_2300 = (1011, 661)    #click 18 time scroll down

COORDS_ESPORTA_DATI_BUTTON = (1469, 158)

# 16. Save Dialog
COORDS_FILE_SAVE_DIALOG_FILENAME = (1140, 700)
COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON = (1267, 702)
COORDS_FILE_SAVE_DIALOG_CLOSE_BUTTON = (867, 588)



# Time to wait between actions
DELAY_ACTION = 1.0
DELAY_LOAD_DATA = 90
DELAY_SAVE_FILE = 600
DELAY_CLOSE_SAVE = 20

# File size and download completion configuration
EXPECTED_FILE_SIZE_MB = 530           # Usually tracker report is around ~530MB (520-550MB)
MIN_FILE_SIZE_THRESHOLD_MB = 480      # Lower threshold to consider file in target completed range
STABLE_CHECK_SECONDS = 15             # Seconds size must remain identical to confirm write completion
SAVE_MAX_IDLE_TIMEOUT = 600           # Max seconds of NO size increase before declaring timeout
DELAY_POST_SAVE = 7.0                 # Seconds to wait after saving file before next action

# --- v1.2 unified clock rule ---
# SCADA hourly data for hour H is complete/available at (H+1):05 (grace lag for generation).
AVAILABILITY_LAG_MINUTES = 5
# Progress chunk for the data-load wait (same total as DELAY_LOAD_DATA, interruptible).
LOAD_POLL_SECONDS = 5
# Continuous-mode retry bound for the SAME hour (0 = retry forever, default).
MAX_CONTINUOUS_RETRIES = 0

# ---------------------------------------------------------------------------
# Screen border overlay + Ctrl+Alt+. stop hotkey
# ---------------------------------------------------------------------------

# --- Global status for overlay ---
# current_status: detail line (what exactly is happening right now).
# current_phase: short phase tag shown in the overlay title (e.g. "SCARICO 3/11").
# phase_state: one of run / wait / done / error / idle — drives the badge colour.
current_status = "Inizializzazione..."
current_phase = "AVVIO"
phase_state = "idle"

_PHASE_BADGE = {
    "run": ("ATTIVO", None),      # colour resolved at runtime (green)
    "wait": ("ATTESA", None),     # yellow
    "done": ("COMPLETATO", None), # grey
    "error": ("ERRORE", None),    # red
    "idle": ("PRONTO", None),     # grey
}


def set_phase(phase, state="run", status=None):
    """Single setter keeping overlay title, badge and detail line consistent."""
    global current_phase, phase_state, current_status
    current_phase = phase
    phase_state = state if state in _PHASE_BADGE else "run"
    if status is not None:
        current_status = status

# Colour palette
_C = {
    'bg':      '#2b2b2b',   # dark grey
    'panel':   '#3c3c3c',   # mid grey panel
    'accent':  '#1e6f9f',   # blue accent
    'green':   '#00d4aa',   # teal-green for running state
    'yellow':  '#ffd166',   # warm yellow for status text
    'white':   '#e0e0e0',
    'red':     '#ef233c',
    'border':  '#1e6f9f',
}

def _overlay_worker():
    """Draws a professional status overlay (Italian) with current task information."""
    try:
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        root.attributes('-alpha', 0.93)

        OW, OH = 520, 125
        sw = root.winfo_screenwidth()
        root.geometry(f"{OW}x{OH}+{sw - OW - 20}+20")
        root.configure(bg=_C['bg'])

        # Rounded-look outer container
        outer = tk.Frame(root, bg=_C['accent'], bd=0)
        outer.pack(fill='both', expand=True, padx=2, pady=2)

        inner = tk.Frame(outer, bg=_C['panel'], bd=0)
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # Title row: live phase tag + state badge (both follow the real pipeline state)
        title_row = tk.Frame(inner, bg=_C['accent'])
        title_row.pack(fill='x')
        title_var = tk.StringVar(value=f"  SCADA v{__version__} — {current_phase}")
        tk.Label(
            title_row, textvariable=title_var,
            font=('Segoe UI', 10, 'bold'), fg=_C['white'], bg=_C['accent'],
            anchor='w'
        ).pack(side='left', pady=4, padx=6)
        badge_var = tk.StringVar(value="PRONTO  ●")
        badge_label = tk.Label(
            title_row, textvariable=badge_var,
            font=('Segoe UI', 9, 'bold'), fg='#aaaaaa', bg=_C['accent'],
            anchor='e'
        )
        badge_label.pack(side='right', pady=4, padx=8)

        # Status text & Avanti button row
        status_frame = tk.Frame(inner, bg=_C['panel'])
        status_frame.pack(fill='x', padx=8, pady=(4, 4))

        status_var = tk.StringVar(value=current_status)
        task_label = tk.Label(
            status_frame, textvariable=status_var,
            font=('Segoe UI', 9), fg=_C['yellow'], bg=_C['panel'],
            wraplength=385, justify='left', anchor='w'
        )
        task_label.pack(side='left', fill='both', expand=True)

        def on_avanti_click():
            global current_status
            print("\n[AVANTI] Pulsante Avanti premuto — passaggio al passo successivo...")
            skip_wait_event.set()

        avanti_btn = tk.Button(
            status_frame, text="Avanti >>",
            font=('Segoe UI', 9, 'bold'), fg='#ffffff', bg=_C['accent'],
            activebackground='#15557d', activeforeground='#ffffff',
            bd=0, relief='flat', cursor='hand2', padx=8, pady=3,
            command=on_avanti_click
        )
        avanti_btn.pack(side='right', padx=(4, 0))

        # Hint row
        tk.Label(
            inner, text="Premi Ctrl+Alt+.  per interrompere",
            font=('Segoe UI', 8), fg='#888888', bg=_C['panel'], anchor='w'
        ).pack(fill='x', padx=10, pady=(2, 6))

        _BADGE_COLORS = {
            "run": _C['green'], "wait": _C['yellow'], "done": '#aaaaaa',
            "error": _C['red'], "idle": '#aaaaaa',
        }
        _tick = [0]

        def refresh_overlay():
            # Title mirrors the live pipeline phase; badge mirrors run/wait/done/error.
            title_var.set(f"  SCADA v{__version__} — {current_phase}")
            word, _ = _PHASE_BADGE.get(phase_state, ("ATTIVO", None))
            _tick[0] ^= 1
            base = _BADGE_COLORS.get(phase_state, _C['green'])
            # Blink only while actively running or waiting; steady otherwise.
            fg = base if (phase_state in ("run", "wait") and _tick[0]) or phase_state not in ("run", "wait") else _C['panel']
            badge_var.set(f"{word}  ●")
            badge_label.configure(foreground=fg)
            status_var.set(current_status)
            root.after(800, refresh_overlay)

        def check_stop():
            if stop_event.is_set():
                root.destroy()
                return
            root.after(200, check_stop)

        root.after(800, refresh_overlay)
        root.after(200, check_stop)
        root.mainloop()
    except Exception as e:
        print(f"[Overlay] Errore: {e}")

def show_overlay():
    """Start the screen border overlay in a background thread."""
    t = threading.Thread(target=_overlay_worker, daemon=True)
    t.start()


def start_hotkey_listener():
    """Register Ctrl+Alt+. as a global stop hotkey using the 'keyboard' library."""
    if not KEYBOARD_AVAILABLE:
        print("[Hotkey] 'keyboard' library not installed — Ctrl+Alt+. hotkey unavailable.")
        print("         Install with:  pip install keyboard")
        return

    assert kb_lib is not None

    def _stop():
        print("\n[STOP] Ctrl+Alt+. detected — stopping automation...")
        stop_event.set()

    kb_lib.add_hotkey('ctrl+alt+.', _stop)
    print("[Hotkey] Ctrl+Alt+. registered. Press it at any time to stop.")


def interruptible_sleep(seconds, check_interval=0.2):
    """Like time.sleep() but wakes every check_interval seconds to honour stop_event or skip_wait_event."""
    deadline = time.time() + seconds
    while not stop_event.is_set():
        if skip_wait_event.is_set():
            skip_wait_event.clear()
            print("\n[AVANTI] Skip attesa eseguito — passaggio al passo successivo!")
            break
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        time.sleep(min(check_interval, remaining))


def ensure_directory_exists(dir_path):
    """
    Ensures a directory (including SMB network shares) exists.
    Handles Windows network share quirks where os.makedirs can raise WinError 183
    or os.path.isdir fails to inspect uncached network folders immediately.
    """
    dir_path = os.path.normpath(dir_path)
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        return True

    # 1. Standard os.makedirs
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception:
        pass

    if os.path.exists(dir_path):
        return True

    # 2. Component iteration fallback ignoring WinError 183 / EEXIST
    try:
        parts = []
        curr = dir_path
        while curr and curr != os.path.dirname(curr):
            parts.append(curr)
            curr = os.path.dirname(curr)
        parts.reverse()

        for p in parts:
            if not os.path.exists(p):
                try:
                    os.mkdir(p)
                except OSError as err:
                    if getattr(err, 'winerror', None) == 183 or getattr(err, 'errno', None) == 17:
                        pass
                    else:
                        print(f"[DirCheck] Component notice on {p}: {err}")
    except Exception as ex:
        print(f"[DirCheck] Component creation fallback failed: {ex}")

    if os.path.exists(dir_path):
        return True

    # 3. PowerShell fallback for network shares
    try:
        import subprocess
        ps_cmd = f'if (!(Test-Path -Path "{dir_path}")) {{ New-Item -ItemType Directory -Path "{dir_path}" -Force }}'
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=10)
    except Exception as ps_err:
        print(f"[DirCheck] PowerShell fallback error: {ps_err}")

    return os.path.exists(dir_path)


# ---------------------------------------------------------------------------

def find_scada_window():
    """1. Search for SCADA window."""
    windows = gw.getWindowsWithTitle(SCADA_WINDOW_TITLE_PARTIAL)
    if not windows:
        print(f"Window '{SCADA_WINDOW_TITLE_PARTIAL}' not found.")
        return None
    return windows[0]

def focus_scada_window(window):
    """2. Restore, maximize, and focus SCADA window (v0.6 logic)."""
    if not window:
        return
    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(1)
    except Exception as e:
        print(f"Error activating window: {e}")

    time.sleep(0.5)

def find_image_in_region(image_name, region, confidence=0.6):
    """
    Finds image in region using Canny Edge Detection.
    This is extremely robust to color changes (e.g. Inverted/Selected Blue background).
    It matches the *shape* of the number.
    """
    # 1. Capture Screenshot
    try:
        screenshot = pyautogui.screenshot(region=region)
        haystack_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        haystack_gray = cv2.cvtColor(haystack_bgr, cv2.COLOR_BGR2GRAY)
        
        # Apply Canny Edge Detection to Screenshot
        haystack_edges = cv2.Canny(haystack_gray, 50, 200)
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None
    
    # 2. Load Template
    path = os.path.join(ASSETS_DIR, f"{image_name}.png")
    if not os.path.exists(path):
        print(f"Asset missing: {path}")
        return None
    
    template_bgr = cv2.imread(path)
    if template_bgr is None: return None
    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

    # --- STRATEGY 1: Standard Template Matching (Primary) ---
    # Best for unselected dates (Black Text on White BG) or consistent UI
    try:
        res_std = cv2.matchTemplate(haystack_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val_s, max_val_s, min_loc_s, max_loc_s = cv2.minMaxLoc(res_std)
        print(f"Search '{image_name}' (Standard): Score={max_val_s:.2f} at {max_loc_s}")
        
        # Lowered from 0.90 → 0.80: day_23 scored 0.81 (nearby highlighted day affects grayscale)
        if max_val_s >= 0.80:
            h, w = template_gray.shape[:2]
            gx = region[0] + max_loc_s[0] + w//2
            gy = region[1] + max_loc_s[1] + h//2
            return (gx, gy, max_val_s)
    except Exception as e:
        print(f"Standard matching failed: {e}")
    
    # --- STRATEGY 2: Edge-Based Matching (Fallback) ---
    # Best for selected dates (White Text on Blue BG) or inverted colors
    try:
        template_edges = cv2.Canny(template_gray, 50, 200)
        res_edge = cv2.matchTemplate(haystack_edges, template_edges, cv2.TM_CCOEFF_NORMED)
        min_val_e, max_val_e, min_loc_e, max_loc_e = cv2.minMaxLoc(res_edge)
        print(f"Search '{image_name}' (Edge): Score={max_val_e:.2f} at {max_loc_e}")
        
        if max_val_e >= 0.70:
            h, w = template_edges.shape[:2]
            gx = region[0] + max_loc_e[0] + w//2
            gy = region[1] + max_loc_e[1] + h//2
            return (gx, gy, max_val_e)
    except Exception as e:
        print(f"Edge matching failed: {e}")
    
    return None

def find_all_matches_in_region(image_name, region, confidence=0.8):
    """
    Finds ALL matches for an image in a region above a confidence threshold.
    Returns list of (x, y, confidence) tuples.
    """
    # 1. Capture Screenshot
    try:
        screenshot = pyautogui.screenshot(region=region)
        haystack_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        haystack_gray = cv2.cvtColor(haystack_bgr, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return []
    
    # 2. Load Template
    path = os.path.join(ASSETS_DIR, f"{image_name}.png")
    if not os.path.exists(path):
        print(f"Asset missing: {path}")
        return []
    
    template_bgr = cv2.imread(path)
    if template_bgr is None: return []
    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    h, w = template_gray.shape[:2]

    # Use standard matching for all matches
    try:
        res = cv2.matchTemplate(haystack_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # Find all locations above threshold
        loc = np.where(res >= confidence)
        matches = []
        for pt in zip(*loc[::-1]):  # pt is (x, y) in template position
            gx = region[0] + pt[0] + w//2
            gy = region[1] + pt[1] + h//2
            conf = res[pt[1], pt[0]]
            matches.append((gx, gy, conf))
        
        # Sort by confidence descending
        matches.sort(key=lambda x: x[2], reverse=True)
        return matches
    except Exception as e:
        print(f"Matching failed: {e}")
        return []

def select_best_date_match(all_matches, target_date):
    """
    From a list of (x, y, conf) matches, select the best one for the target date.
    Uses grid-based expected position to disambiguate.
    """
    if not all_matches:
        return None
    
    # Get expected grid position
    expected_x, expected_y = get_date_grid_coords(target_date)
    
    # Find the match closest to expected position
    best_match = None
    best_distance = float('inf')
    for match in all_matches:
        mx, my, conf = match
        distance = ((mx - expected_x)**2 + (my - expected_y)**2) ** 0.5
        if distance < best_distance:
            best_distance = distance
            best_match = match
    
    # If best distance is too far (e.g. > 50 pixels), reject
    if best_distance > 50:
        print(f"Best match too far from expected grid position ({expected_x},{expected_y}): distance={best_distance:.1f}")
        return None
    
    return best_match

def get_date_override_coords(target_date):
    """Check if target_date has a manual coordinate override."""
    date_str = target_date.isoformat()
    return DATE_COORDINATE_OVERRIDES.get(date_str)

def check_color_is_black_bg_white_text(x, y):
    """Verify the clicked position has the expected color (for debugging)."""
    try:
        x, y = int(x), int(y)
        # Capture a small region around the click point
        region = (x-5, y-5, 10, 10)  # 10x10 pixel region
        screenshot = pyautogui.screenshot(region=region)
        img = np.array(screenshot)
        
        # Get the color at the center
        center_color = img[5, 5]  # RGB tuple
        
        print(f"Color at ({x},{y}): RGB{center_color}")
        
        # Expected: Black text on white BG → RGB close to (0,0,0) or (255,255,255)
        # Selected: White text on blue BG → RGB close to (255,255,255) or (0,120,215)
        
        # Simple check: if mostly white or black, assume correct
        avg = sum(center_color) / 3
        if avg < 50:  # Dark (black text)
            print("Detected: Black text (unselected)")
        elif avg > 200:  # Light (white text)
            print("Detected: White text (selected)")
        else:
            print("Warning: Unexpected color, may be wrong selection")
    except Exception as e:
        print(f"Color check failed: {e}")

def perform_initial_setup():
    """Execute Steps 1-2 (Initial Setup to reach 'Ora' selection)."""
    global current_status
    # NOTE: The User says Steps 3-6 must be done *every time*.
    # So this function will do Steps 1-2 (Find/Focus) 
    # and then the MAIN loop will call Steps 3-6.
    
    print("=== Step 1 & 2: Window Management ===")
    current_status = "Ricerca finestra SCADA..."
    max_attempts = 10  # Retry up to 10 times
    for attempt in range(max_attempts):
        window = find_scada_window()
        if window:
            current_status = "Attivazione finestra SCADA..."
            focus_scada_window(window)
            current_status = "Finestra SCADA pronta"
            return True
        print(f"SCADA window not found (attempt {attempt + 1}/{max_attempts}). Waiting 5 seconds...")
        time.sleep(5)
    current_status = "Finestra SCADA non trovata"
    print("Failed to find SCADA window after multiple attempts.")
    return False

def ensure_scada_window_active():
    """Ensure the SCADA window is active and in front."""
    global current_status
    current_status = "Verifica finestra SCADA attiva..."
    window = find_scada_window()
    if window:
        focus_scada_window(window)
        current_status = "Finestra SCADA attivata"
        return True
    else:
        current_status = "Finestra SCADA non trovata"
        print("SCADA window not found.")
        return False

def perform_reset():
    """Execute Reset Logic provided by User."""
    print("Resetting to normal selection mode.")
    pyautogui.press('esc') # Close any potential dialogs
    time.sleep(0.5)
    
    # User said: "no. it skips these steps which are to be performed everytime: ... [Step 3-6]"
    # So we will NOT do the complex reset logic here anymore.
    # We will just ensure we are back at a state where clicking ANALISI works.
    # Pressing ESC is good.
    # The actual Steps 3-6 will happen via perform_scada_prep()

def perform_scada_prep():
    """Execute Steps 3-6 (Analisi -> ORA) every time."""
    global current_status
    print("=== Step 3: Click ANALISI ===")
    current_status = "Navigazione alla sezione Analisi..."
    pyautogui.click(COORDS_ANALISI)
    time.sleep(DELAY_ACTION)

    print("=== Step 4: Click Dropdown Selezione Intervallo ===")
    current_status = "Apertura selezione intervallo..."
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_DROPDOWN)
    time.sleep(0.5)

    print("=== Step 5: Click Scroll Up x5 ===")
    current_status = "Scorrimento verso opzione ORA..."
    for _ in range(5):
        pyautogui.click(COORDS_SELEZIONE_INTERVALLO_SCROLL_UP)
        time.sleep(0.1)
    
    print("=== Step 6: Click ORA ===")
    current_status = "Selezione intervallo ORA..."
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_ORA)
    time.sleep(DELAY_ACTION)
    current_status = "Interfaccia pronta per selezione report"
    return True

def get_date_grid_coords(target_date):
    """
    Calculate screen (x, y) for a date cell using the calendar grid layout.
    The calendar always starts on the Monday of the week containing the 1st of the month.
    col: 0=Mo, 1=Di, 2=Mi, 3=Do, 4=Fr, 5=Sa, 6=So
    """
    first_day = datetime.date(target_date.year, target_date.month, 1)
    first_visible_monday = first_day - datetime.timedelta(days=first_day.weekday())
    delta = (target_date - first_visible_monday).days
    row = delta // 7
    col = delta % 7
    x = CALENDAR_GRID_MONDAY_X + col * CALENDAR_CELL_W
    y = CALENDAR_GRID_FIRST_ROW_Y + row * CALENDAR_CELL_H
    print(f"Grid calc: first_monday={first_visible_monday}, delta={delta}, row={row}, col={col} -> ({int(x)}, {int(y)})")
    return (int(x), int(y))


def is_file_locked(file_path):
    """
    Checks if a file is currently locked or being written to by another process.
    Returns True if locked/inaccessible for read-write access, False otherwise.
    """
    if not os.path.exists(file_path):
        return True
    try:
        with open(file_path, 'r+b'):
            return False
    except (PermissionError, OSError):
        return True


def validate_existing_csv(file_path, target_date, target_hour):
    """
    Validates if an existing CSV file is non-empty, has expected size (~530MB),
    and contains data matching target_date and target_hour.
    Returns True if valid and correct, False otherwise.
    """
    if not os.path.exists(file_path):
        return False
    try:
        size_bytes = os.path.getsize(file_path)
    except OSError:
        return False

    if size_bytes == 0:
        return False

    size_mb = size_bytes / (1024 * 1024)
    if size_mb < MIN_FILE_SIZE_THRESHOLD_MB:
        print(f"  [Validazione] File '{os.path.basename(file_path)}' dimensione insufficiente ({size_mb:.1f} MB < {MIN_FILE_SIZE_THRESHOLD_MB} MB, atteso ~{EXPECTED_FILE_SIZE_MB} MB).")
        return False

    if is_file_locked(file_path):
        print(f"  [Validazione] File '{os.path.basename(file_path)}' è attualmente in uso/scrittura da un altro processo.")
        return False

    expected_date_str1 = target_date.strftime("%d/%m/%Y") # e.g. 01/08/2026
    expected_date_str2 = target_date.strftime("%Y-%m-%d") # e.g. 2026-08-01
    expected_hour_str1 = f"{target_hour:02d}:"            # e.g. 00:

    encodings_to_try = ['utf-16le', 'utf-16', 'utf-8', 'latin-1']
    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                lines = [f.readline() for _ in range(20)]
                file_text = "".join(lines)
                if not file_text.strip():
                    continue

                date_match = (expected_date_str1 in file_text) or (expected_date_str2 in file_text)
                hour_match = (expected_hour_str1 in file_text)

                if date_match and hour_match:
                    return True
                else:
                    print(f"  [Validazione] File '{os.path.basename(file_path)}' contiene dati non corrispondenti (date={date_match}, hour={hour_match}).")
                    return False
        except Exception as e:
            print(f"  [Validazione] Errore lettura '{file_path}' ({enc}): {e}")
            continue

    return False



def move_to_backup(file_path, reason="invalid"):
    """
    Moves an invalid, corrupted, or mismatched CSV file into a 'backup' subfolder
    under its date directory: PATH_TO_ORI_FOLDER/YYYY/MM/YYYY-MM-DD/backup/
    """
    if not os.path.exists(file_path):
        return None
    dir_name = os.path.dirname(file_path)
    backup_dir = os.path.join(dir_name, "backup")
    try:
        os.makedirs(backup_dir, exist_ok=True)
    except Exception as e:
        print(f"  [Backup] Errore creazione cartella backup '{backup_dir}': {e}")
        backup_dir = dir_name

    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{name}_{reason}_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        shutil.move(file_path, backup_path)
        print(f"  [Backup] File spostato in backup: '{filename}' -> '{backup_filename}' (motivo: {reason})")
        return backup_path
    except Exception as e:
        print(f"  [Backup] Impossibile spostare file in backup '{filename}': {e}")
        return None


def audit_csv_content(file_path, target_date, target_hour):
    """
    Performs a 3-point content audit on an existing CSV file:
    1. Size >= MIN_FILE_SIZE_THRESHOLD_MB
    2. File lock check
    3. Content header matching for date (DD/MM/YYYY or YYYY-MM-DD) and hour (HH:)
    """
    if not os.path.exists(file_path):
        return False, "missing"
    try:
        size_bytes = os.path.getsize(file_path)
    except OSError:
        return False, "os_error"

    if size_bytes == 0:
        return False, "empty_file"

    size_mb = size_bytes / (1024 * 1024)
    if size_mb < MIN_FILE_SIZE_THRESHOLD_MB:
        return False, f"undersized_{size_mb:.1f}MB"

    if is_file_locked(file_path):
        return False, "file_locked"

    expected_date_str1 = target_date.strftime("%d/%m/%Y")
    expected_date_str2 = target_date.strftime("%Y-%m-%d")
    expected_hour_str = f"{target_hour:02d}:"

    encodings_to_try = ['utf-16le', 'utf-16', 'utf-8', 'latin-1']
    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                lines = [f.readline() for _ in range(30)]
                file_text = "".join(lines)
                if not file_text.strip():
                    continue

                date_match = (expected_date_str1 in file_text) or (expected_date_str2 in file_text)
                hour_match = (expected_hour_str in file_text)

                if date_match and hour_match:
                    return True, "valid"
                else:
                    if not date_match and not hour_match:
                        return False, "mismatch_date_and_hour"
                    elif not date_match:
                        return False, "mismatch_date"
                    else:
                        return False, "mismatch_hour"
        except Exception:
            continue

    return False, "unreadable_format"

def handle_incorrect_file(file_path):
    """
    Renames an incorrect/corrupted file to file_name_incorrect.csv
    (or file_name_incorrect_1.csv if already exists).
    """
    if not os.path.exists(file_path):
        return
    dir_name = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)

    incorrect_filename = f"{name}_incorrect{ext}"
    incorrect_path = os.path.join(dir_name, incorrect_filename)

    counter = 1
    while os.path.exists(incorrect_path):
        incorrect_filename = f"{name}_incorrect_{counter}{ext}"
        incorrect_path = os.path.join(dir_name, incorrect_filename)
        counter += 1

    try:
        os.rename(file_path, incorrect_path)
        print(f"  [File Check] Rinominato file errato: '{filename}' -> '{incorrect_filename}'")
    except Exception as e:
        print(f"  [File Check] Impossibile rinominare file errato '{filename}': {e}")

def process_hourly_report(target_date, target_hour):
    """Execute Steps 7-18 for a specific date and hour."""
    global current_status

    # SAFETY GUARD: never download incomplete/future hours.
    # Hour H is only available starting at (H+1):05.
    if is_future_target(target_date, target_hour):
        last_ok = get_last_completed_datetime()
        trigger = get_trigger_time_for_target(target_to_datetime(target_date, target_hour))
        print(f"  [SKIP] Future/incomplete hour {target_date} {target_hour:02d}:00 "
              f"(last completed: {last_ok.strftime('%d/%m/%Y %H:00')}, "
              f"available from {trigger.strftime('%d/%m/%Y %H:%M')}).")
        current_status = f"Ora futura non ancora disponibile: {target_hour:02d}:00 del {target_date}"
        return True  # treated as skipped, not as error (caller continues)

    # Check if expected output CSV already exists and is non-empty
    check_path, filename = build_expected_csv_path(target_date, target_hour)
    
    if os.path.exists(check_path):
        is_ok, reason = audit_csv_content(check_path, target_date, target_hour)
        if is_ok:
            print(f"  [OK] Tracker file already exists and is valid for {target_date} {target_hour:02d}:00 ({filename}). Skipping!")
            current_status = f"File già presente e corretto: {filename}"
            return True
        else:
            if VERIFY_AND_BACKUP:
                print(f"  [WARN] Existing file '{filename}' failed audit (motivo: {reason}). Moving to backup and re-downloading...")
                current_status = f"File errato rilevato ({reason}): {filename}. Spostamento in backup..."
                move_to_backup(check_path, reason=reason)
            else:
                print(f"  [WARN] Existing file '{filename}' is incorrect or corrupted. Renaming to _incorrect and re-downloading...")
                current_status = f"File errato rilevato: {filename}. Rinominazione in corso..."
                handle_incorrect_file(check_path)

    print(f"Starting Process for {target_date} // {target_hour}:00")
    current_status = f"Elaborazione report {target_date} ore {target_hour}:00"

    # Calendar window should be open (or opens after ORA selection)
    
    print("=== Step 7: Click Month Dropdown ===")
    current_status = "Selezione mese..."
    pyautogui.click(COORDS_MONTH_DROPDOWN)
    time.sleep(0.5)

    print(f"=== Step 8: Select Month ({target_date.month}) ===")
    month_coords = MONTH_COORDS.get(target_date.month)
    if month_coords:
        pyautogui.click(month_coords)
    else:
        current_status = f"Errore: coordinate non trovate per mese {target_date.month}"
        print(f"Error: No coords for month {target_date.month}")
        return False
    time.sleep(0.5)

    print("=== Step 9: Select Year ===")
    current_status = "Selezione anno..."
    if (target_date.year != datetime.date.today().year):
        pyautogui.click(COORDS_YEAR_DROPDOWN)
        time.sleep(0.5)
        
        print("Scrolling Year to bottom (40 clicks)...")
        for _ in range(40):
            pyautogui.click(COORDS_YEAR_SCROLL_DOWN)
            time.sleep(0.02) # Fast scroll
        
        year_coords = YEAR_COORDS.get(target_date.year)
        if year_coords:
            print(f"Clicking Year {target_date.year}")
            pyautogui.click(year_coords)
        else:
            current_status = f"Errore: coordinate non trovate per anno {target_date.year}"
            print(f"Error: No coords for year {target_date.year}. Available: {list(YEAR_COORDS.keys())}")
            return False
    else:
        print(f"Year {target_date.year} is current year. No need to select.")
        
    time.sleep(0.5)

    print(f"=== Step 10: Select Date ({target_date.day}) ===")
    current_status = f"Selezione giorno {target_date.day}..."
    
    # Check if target date is today
    if target_date == datetime.date.today():
        print(f"Target date {target_date} is TODAY. Skipping selection (already selected).")
    else:
        override_coords = get_date_override_coords(target_date)
        if override_coords:
            pos = pyautogui.Point(*override_coords)
            print(f"Override coordinate found. Clicking directly at {pos} for {target_date}.")
        else:
            # Primary: image template matching (Wo column now excluded from search region)
            print(f"Searching for day {target_date.day} using OpenCV...")
            day_img = f"day_{target_date.day}"
            
            # Find ALL matches (handles calendar overflow dates from adjacent months)
            all_matches = find_all_matches_in_region(day_img, DATE_SEARCH_REGION, confidence=0.75)

            if all_matches:
                selected_match = select_best_date_match(all_matches, target_date)
                if selected_match:
                    pos = pyautogui.Point(int(selected_match[0]), int(selected_match[1]))
                    expected_x, expected_y = get_date_grid_coords(target_date)
                    distance = ((selected_match[0] - expected_x)**2 + (selected_match[1] - expected_y)**2) ** 0.5
                    print(f"Selected best match near expected grid ({expected_x},{expected_y}), distance={distance:.1f}, confidence={selected_match[2]:.2f}")
                else:
                    print(f"No best match could be chosen from {len(all_matches)} candidates.")
                    single_match = find_image_in_region(day_img, DATE_SEARCH_REGION, confidence=0.65)
                    if single_match:
                        pos = pyautogui.Point(single_match[0], single_match[1])
                        print(f"Edge/Template single match found at {pos} with confidence {single_match[2]:.2f}")
                    else:
                        gx, gy = get_date_grid_coords(target_date)
                        pos = pyautogui.Point(gx, gy)
                        print(f"Grid fallback position: {pos}")
            else:
                single_match = find_image_in_region(day_img, DATE_SEARCH_REGION, confidence=0.65)
                if single_match:
                    pos = pyautogui.Point(single_match[0], single_match[1])
                    print(f"Edge/Template single match found at {pos} with confidence {single_match[2]:.2f}")
                else:
                    print(f"Image match failed for day {target_date.day}. Using grid-based calculation.")
                    gx, gy = get_date_grid_coords(target_date)
                    pos = pyautogui.Point(gx, gy)
                    print(f"Grid fallback position: {pos}")

        print(f"Clicking on date {target_date.day} at position {pos}")
        pyautogui.click(pos)
        time.sleep(0.5)

        # Step 11: Color Check
        print("=== Step 11: Color Verification ===")
        check_color_is_black_bg_white_text(pos.x, pos.y)

    print("=== Step 12: Time Selection - Reset to Min ===")
    current_status = "Reset selezione orario..."
    # Click 20 times Scroll Up
    for _ in range(20):
        pyautogui.click(COORDS_TIME_SCROLL_UP)
        time.sleep(0.05)
    
    print(f"=== Step 13: Select Time {target_hour}:00 ===")
    current_status = f"Selezione orario {target_hour}:00..."
    # NEW Logic for v0.4
    # - 00:00 - 04:00: Click specific Y coords (No further scroll).
    # - 05:00: Click Base (No scroll, if it's visible).
    # - 06:00+: Scroll (target_hour - 5) times, then Click Base.
    
    if target_hour < 5:
        # Use specific coordinates for early hours
        early_coords = {
            0: COORDS_TIME_SELECTION_0000,
            1: COORDS_TIME_SELECTION_0100,
            2: COORDS_TIME_SELECTION_0200,
            3: COORDS_TIME_SELECTION_0300,
            4: COORDS_TIME_SELECTION_0400
        }
        coords = early_coords.get(target_hour)
        if coords:
            print(f"Clicking specific coord for {target_hour}:00")
            pyautogui.click(coords)
        else:
            current_status = f"Errore: coordinate non trovate per ora {target_hour}"
            print(f"Error: No coords for hour {target_hour}")
            return False
            
    else:
        # For hour >= 5 (05:00, 06:00...)
        # Logic: 05:00 is base (0 scrolls). 06:00 is base + 1 scroll.
        scrolls_needed = target_hour - 5
        if scrolls_needed < 0: scrolls_needed = 0 # Should effectively mean 05:00
        
        if scrolls_needed > 0:
            print(f"Scrolling down {scrolls_needed} times for {target_hour}:00")
            for _ in range(scrolls_needed):
                pyautogui.click(COORDS_TIME_SCROLL_DOWN)
                time.sleep(0.1)
        else:
            print(f"No scrolling needed for {target_hour}:00 (05:00 Base)")

        # Click the selection
        pyautogui.click(COORDS_TIME_SELECTION_BASE)
        
    time.sleep(0.5)
    
    print("Clicking OK Filter Button...")
    current_status = "Applicazione filtri..."
    pyautogui.click(COORDS_FILTER_WINDOW_OK_BUTTON)

    print(f"=== Step 14: Wait for Load ({DELAY_LOAD_DATA}s) ===")
    current_status = f"Caricamento dati... ({DELAY_LOAD_DATA}s)"
    wait_for_data_load()

    print("=== Step 15: Click Export ===")
    current_status = "Avvio esportazione..."
    pyautogui.click(COORDS_ESPORTA_DATI_BUTTON)
    time.sleep(2.0) # Wait for dialog

    print("=== Step 16 & 17: Save File Logic ===")
    current_status = "Preparazione finestra di salvataggio..."
    # Click filename field
    pyautogui.click(COORDS_FILE_SAVE_DIALOG_FILENAME)
    time.sleep(0.5)
    
    # Delete existing text
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    # Construct Path (single source of truth — same as the pre-check above)
    # PATH_TO_ORI_FOLDER / YYYY / MM / YYYY-MM-DD / DD_MM_YYYY_HH_JJ.csv
    # JJ = HH + 1
    full_path, filename = build_expected_csv_path(target_date, target_hour)
    print(f"Saving to: {full_path}")
    current_status = f"Saving file: {filename}"
    
    # Ensure directory exists
    dir_path = os.path.dirname(full_path)
    if not ensure_directory_exists(dir_path):
        print(f"[WARN] Creazione cartella fallita o non confermata: {dir_path}")

    # Write full absolute path to save file directly into target folder
    pyautogui.write(full_path, interval=0.01)

    time.sleep(1.0)

    print("=== Step 18: Save and Wait ===")
    current_status = f"Salvataggio {filename}..."
    pyautogui.click(COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON)
    time.sleep(0.5)

    # Automatically confirm Windows 'File already exists / Overwrite?' dialog if shown
    pyautogui.press('y')
    pyautogui.press('enter')

    # Continuous file size check until download completes (~530MB)
    file_saved = False
    target_check = full_path

    # Phase 1: Wait for file to appear on disk (up to 60 seconds)
    file_detected = False
    wait_create_start = time.time()
    while time.time() - wait_create_start < 60 and not stop_event.is_set():
        if skip_wait_event.is_set():
            skip_wait_event.clear()
            print("\n[AVANTI] Skip attesa creazione file eseguito!")
            file_saved = True
            break

        target_check = full_path if os.path.exists(full_path) else os.path.join(PATH_TO_ORI_FOLDER, filename)
        if os.path.exists(target_check):
            file_detected = True
            break

        elapsed_detect = time.time() - wait_create_start
        # If overwrite dialog appeared late, re-send confirm keys
        if 4.0 <= elapsed_detect <= 5.0 or 12.0 <= elapsed_detect <= 13.0:
            pyautogui.press('y')
            pyautogui.press('enter')

        current_status = f"Attesa creazione {filename}... ({int(elapsed_detect)}s)"
        for _ in range(5):
            if skip_wait_event.is_set() or stop_event.is_set():
                break
            time.sleep(0.2)

    if not file_detected and not file_saved:
        print(f"[WARN] File '{filename}' non ancora rilevato su disco dopo 60s. Continuo il monitoraggio...")

    # Phase 2: Continuously monitor file size until download is complete
    if not file_saved:
        last_change_time = time.time()
        last_size = -1
        last_log_time = 0

        while not stop_event.is_set():
            if skip_wait_event.is_set():
                skip_wait_event.clear()
                print("\n[AVANTI] Skip attesa salvataggio eseguito — passaggio al passo successivo!")
                file_saved = True
                break

            target_check = full_path if os.path.exists(full_path) else os.path.join(PATH_TO_ORI_FOLDER, filename)
            if not os.path.exists(target_check):
                time.sleep(1.0)
                continue

            try:
                current_size = os.path.getsize(target_check)
            except OSError:
                current_size = last_size if last_size >= 0 else 0

            size_mb = current_size / (1024 * 1024)
            now_ts = time.time()

            if current_size > last_size:
                # File is actively growing (downloading/writing)
                delta_str = ""
                if last_size >= 0:
                    delta_mb = (current_size - last_size) / (1024 * 1024)
                    delta_str = f" (+{delta_mb:.1f} MB)"

                last_size = current_size
                last_change_time = now_ts

                if now_ts - last_log_time >= 2.0:
                    print(f"  [Salvataggio] File size currently {size_mb:.1f} MB{delta_str} / ~{EXPECTED_FILE_SIZE_MB} MB...")
                    last_log_time = now_ts

                current_status = f"Scrittura {filename}: {size_mb:.1f} MB / ~{EXPECTED_FILE_SIZE_MB} MB"

            else:
                # File size has not changed since last check
                stable_seconds = now_ts - last_change_time
                current_status = f"Scrittura {filename}: {size_mb:.1f} MB (stabile da {int(stable_seconds)}s)"

                # Condition A: Reached expected target size (~530MB, threshold >= 480MB) and stable
                if size_mb >= MIN_FILE_SIZE_THRESHOLD_MB:
                    if stable_seconds >= STABLE_CHECK_SECONDS:
                        if not is_file_locked(target_check):
                            print(f"[OK] File '{filename}' download completato con successo! Dimensione finale: {size_mb:.1f} MB (stabile da {int(stable_seconds)}s).")
                            current_status = f"Download completato: {filename} ({size_mb:.0f} MB)"
                            file_saved = True
                            break
                        else:
                            if now_ts - last_log_time >= 3.0:
                                print(f"  [Salvataggio] Dimensione target {size_mb:.1f} MB raggiunta. Attesa chiusura file handle SCADA...")
                                last_log_time = now_ts

                # Condition B: File stopped growing below expected threshold (< 480MB)
                else:
                    if stable_seconds >= 60 and not is_file_locked(target_check):
                        print(f"[WARN] File '{filename}' scrittura terminata a {size_mb:.1f} MB (inferiore ai consueti ~{EXPECTED_FILE_SIZE_MB} MB, stabile da {int(stable_seconds)}s).")
                        current_status = f"Salvataggio terminato: {filename} ({size_mb:.0f} MB)"
                        file_saved = True
                        break
                    elif stable_seconds >= SAVE_MAX_IDLE_TIMEOUT:
                        print(f"[WARN] Timeout salvataggio: nessun incremento per {int(stable_seconds)}s. File fermo a {size_mb:.1f} MB.")
                        file_saved = True
                        break
                    else:
                        if now_ts - last_log_time >= 5.0:
                            print(f"  [Salvataggio] File size {size_mb:.1f} MB (stabile da {int(stable_seconds)}s, attesa ~{EXPECTED_FILE_SIZE_MB} MB)...")
                            last_log_time = now_ts

            # Polling delay: 2.0s with responsive stop/skip checks
            for _ in range(10):
                if skip_wait_event.is_set() or stop_event.is_set():
                    break
                time.sleep(0.2)

    if not file_saved and stop_event.is_set():
        print(f"[STOP] Salvataggio interrotto dall'utente per {target_hour}:00.")
        return False

    # Ensure file is at target full_path
    if not os.path.exists(full_path):
        try:
            import shutil
            alt_path = os.path.join(PATH_TO_ORI_FOLDER, filename)
            if os.path.exists(alt_path):
                shutil.move(alt_path, full_path)
        except Exception as e:
            print(f"[WARN] Errore spostamento file da {alt_path} a {full_path}: {e}")

    print(f"Task Completed FOR {target_hour}:00")
    current_status = f"Report salvato per {target_hour}:00. Attesa {int(DELAY_POST_SAVE)}s..."
    print(f"Attesa {int(DELAY_POST_SAVE)} secondi dopo il salvataggio prima del passo successivo...")
    interruptible_sleep(DELAY_POST_SAVE)
    current_status = f"Report salvato per {target_hour}:00"
    return True

def get_next_trigger_time(now=None):
    """
    Calculate the next trigger time: next occurrence of :05.
    If current minute < AVAILABILITY_LAG_MINUTES, the trigger for the hour just
    completed is at this hour's :05; otherwise at next hour's :05.
    """
    if now is None:
        now = datetime.datetime.now()
    if now.minute < AVAILABILITY_LAG_MINUTES:
        return now.replace(minute=AVAILABILITY_LAG_MINUTES, second=0, microsecond=0)
    next_hour = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    return next_hour.replace(minute=AVAILABILITY_LAG_MINUTES)


def get_first_run_target():
    """Return the first report target date and hour for immediate execution."""
    last_ok = get_last_completed_datetime()
    return last_ok.date(), last_ok.hour


# ---------------------------------------------------------------------------
# Future-time guards (hour H downloadable only from (H+1):05)
# ---------------------------------------------------------------------------
# E.g. hour 10:00 can only be downloaded starting at 11:05.
def get_last_completed_datetime(now=None):
    """Return datetime (minute=0) of the last fully completed/available hour."""
    if now is None:
        now = datetime.datetime.now()
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    trigger_today = hour_start + datetime.timedelta(minutes=AVAILABILITY_LAG_MINUTES)
    if now >= trigger_today:
        return hour_start - datetime.timedelta(hours=1)
    else:
        return hour_start - datetime.timedelta(hours=2)


def target_to_datetime(target_date, target_hour):
    """Combine (date, hour) tuple into a datetime at minute=0."""
    return datetime.datetime(target_date.year, target_date.month, target_date.day, target_hour)


def is_future_target(target_date, target_hour, now=None):
    """True if the requested hour is not yet complete (future/incomplete)."""
    return target_to_datetime(target_date, target_hour) > get_last_completed_datetime(now)


def split_targets_by_availability(hours_list, now=None):
    """
    Split a [(date, hour)] list into (due, future).
    - due:    target_dt <= last completed hour → safe to download now.
    - future: target_dt >  last completed hour → incomplete, must not download yet.
    """
    if not hours_list:
        return [], []
    last_ok = get_last_completed_datetime(now)
    due, future = [], []
    for d, h in hours_list:
        if target_to_datetime(d, h) <= last_ok:
            due.append((d, h))
        else:
            future.append((d, h))
    return due, future


def get_trigger_time_for_target(target_dt):
    """Wall-clock time when target hour H becomes available: (H+1):05."""
    return target_dt + datetime.timedelta(hours=1, minutes=AVAILABILITY_LAG_MINUTES)


def build_expected_csv_path(target_date, target_hour):
    """Centralized expected output path builder (single source of truth).

    Layout: PATH_TO_ORI_FOLDER / YYYY / MM / YYYY-MM-DD / DD_MM_YYYY_HH_JJ.csv
    where JJ = HH + 1 (00 wrap). Returns (full_path, filename).
    """
    year_str = str(target_date.year)
    month_str = f"{target_date.month:02d}"
    day_str = f"{target_date.day:02d}"
    hh_str = f"{target_hour:02d}"
    jj = (target_hour + 1) % 24
    jj_str = f"{jj:02d}"
    date_dash = f"{year_str}-{month_str}-{day_str}"
    filename = f"{day_str}_{month_str}_{year_str}_{hh_str}_{jj_str}.csv"
    full_path = os.path.normpath(os.path.join(PATH_TO_ORI_FOLDER, year_str, month_str, date_dash, filename))
    return full_path, filename


def filter_already_completed(hours_list, max_workers=16):
    """Split [(date, hour)] into (todo, already_done) via validate_existing_csv.

    Pure disk check — no SCADA interaction. Lets re-runs exit fast without
    opening the SCADA window when everything is already on disk.
    Network-share latency is hidden with a thread pool (I/O-bound work).
    """
    items = list(hours_list or [])
    if not items:
        return [], []

    def _check(item):
        d, h = item
        try:
            path, _ = build_expected_csv_path(d, h)
        except Exception:
            return (item, False)
        try:
            if os.path.exists(path):
                ok, reason = audit_csv_content(path, d, h)
                if not ok and VERIFY_AND_BACKUP:
                    move_to_backup(path, reason=reason)
            else:
                ok = False
        except Exception:
            ok = False
        return (item, bool(ok))

    todo, done = [], []
    try:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(max_workers, len(items))) as ex:
            for item, ok in ex.map(_check, items):
                (done if ok else todo).append(item)
    except Exception:
        # Fallback: sequential check (threads unavailable for any reason).
        for item in items:
            _, ok = _check(item)
            (done if ok else todo).append(item)
    # Preserve chronological order (threads may complete out of order).
    order = {item: i for i, item in enumerate(items)}
    todo.sort(key=lambda x: order[x])
    done.sort(key=lambda x: order[x])
    return todo, done


def wait_for_data_load(max_wait=None, poll=None):
    """Chunked data-table load wait (same total budget, operator-friendly).

    SCADA exposes no ready-signal, so the budget stays DELAY_LOAD_DATA-based;
    chunking only adds progress logs and keeps stop/skip responsive. The
    overlay 'Avanti' button (skip_wait_event) still skips the remainder when
    the table is visibly loaded early.
    """
    global current_status
    total = DELAY_LOAD_DATA if max_wait is None else max_wait
    step = LOAD_POLL_SECONDS if poll is None else poll
    set_phase("CARICAMENTO DATI SCADA", "run")
    print(f"=== Step 14: Wait for Load ({total}s, chunks of {step}s) ===")
    waited = 0
    while waited < total:
        if stop_event.is_set() or skip_wait_event.is_set():
            break
        chunk = min(step, total - waited)
        current_status = f"Caricamento dati... ({int(waited)}/{int(total)}s)"
        interruptible_sleep(chunk)
        waited += chunk
        if waited < total and not stop_event.is_set() and not skip_wait_event.is_set():
            print(f"  [Caricamento] {int(waited)}s/{int(total)}s...")
    current_status = "Caricamento dati completato (o saltato)"


def wait_until_wallclock(trigger, label=""):
    """Sleep until a wall-clock datetime, honouring stop/skip. Returns False if stopped."""
    set_phase("ATTESA", "wait")
    while not stop_event.is_set():
        wait_seconds = (trigger - datetime.datetime.now()).total_seconds()
        if wait_seconds <= 0:
            return True
        global current_status
        current_status = f"In attesa fino alle {trigger.strftime('%d/%m %H:%M')} {label}".strip()
        print(f"In attesa fino alle {trigger.strftime('%d/%m/%Y %H:%M')} {label}".rstrip()
              + f" ({int(wait_seconds)}s rimanenti)")
        interruptible_sleep(min(wait_seconds, 60))
        if skip_wait_event.is_set():
            skip_wait_event.clear()
            print("[AVANTI] Attesa saltata dall'operatore.")
            return True
    return False


def parse_date_string(date_str):
    """
    Parses date string in formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD.
    Returns datetime.date object.
    """
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Formato data non valido '{date_str}'. Formati accettati: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY.")


def parse_time_string(time_str):
    """
    Parses time string in formats: HH, HH:MM, integer string.
    Returns integer hour (0-23).
    """
    if time_str is None:
        return None
    time_str = str(time_str).strip()
    if ":" in time_str:
        parts = time_str.split(":")
        hour = int(parts[0])
    else:
        hour = int(time_str)
    if not (0 <= hour <= 23):
        raise ValueError(f"Ora non valida '{time_str}'. L'ora deve essere compresa tra 0 e 23.")
    return hour


def generate_target_hours(start_date, start_hour=0, end_date=None, end_hour=23):
    """
    Generate list of (date, hour) tuples between start and end date/time (inclusive).
    If end_date is None, defaults to start_date (single day mode).
    """
    if end_date is None:
        end_date = start_date
    if start_hour is None:
        start_hour = 0
    if end_hour is None:
        end_hour = 23

    start_dt = datetime.datetime(start_date.year, start_date.month, start_date.day, start_hour)
    end_dt = datetime.datetime(end_date.year, end_date.month, end_date.day, end_hour)

    if end_dt < start_dt:
        raise ValueError(f"La data/ora di fine ({end_dt.strftime('%d/%m/%Y %H:%M')}) non può essere antecedente alla data/ora di inizio ({start_dt.strftime('%d/%m/%Y %H:%M')}).")

    hours_list = []
    curr_dt = start_dt
    while curr_dt <= end_dt:
        hours_list.append((curr_dt.date(), curr_dt.hour))
        curr_dt += datetime.timedelta(hours=1)

    return hours_list


def generate_backfill_hours(start_date, start_hour):
    """Generate hours from start_date:start_hour up to the last completed hour (:05 rule)."""
    last_ok = get_last_completed_datetime()
    end_date, end_hour = last_ok.date(), last_ok.hour

    start_dt = datetime.datetime(start_date.year, start_date.month, start_date.day, start_hour)
    end_dt = datetime.datetime(end_date.year, end_date.month, end_date.day, end_hour)
    if start_dt > end_dt:
        return []
    return generate_target_hours(start_date, start_hour, end_date, end_hour)


def show_time_selection_dialog():
    """
    Show an Italian dialog to select starting & ending date/hour and mode.
    Returns tuple: (start_date, start_hour, end_date, end_hour, continuous)
    or (None, None, None, None, False) if cancelled.
    """
    dialog = tk.Tk()
    dialog.title(f"SCADA v{__version__} — Estrazione Dati Intervallo")
    icon_p = os.path.join(ASSETS_DIR, "icon.ico")
    if os.path.exists(icon_p):
        try:
            dialog.iconbitmap(icon_p)
        except Exception:
            pass
    dialog.resizable(False, False)

    DW, DH = 530, 660
    sw = dialog.winfo_screenwidth()
    sh = dialog.winfo_screenheight()
    dialog.geometry(f"{DW}x{DH}+{(sw - DW)//2}+{(sh - DH)//2}")
    dialog.configure(bg=_C['bg'])

    result = [None, None, None, None, False]

    # ── Header bar ─────────────────────────────────────────────────────────────
    header = tk.Frame(dialog, bg=_C['accent'], height=54)
    header.pack(fill='x')
    header.pack_propagate(False)
    tk.Label(
        header, text=f"SCADA v{__version__}  |  Estrazione Dati Storici & Continua",
        font=('Segoe UI', 13, 'bold'), fg=_C['white'], bg=_C['accent']
    ).pack(expand=True)

    # ── Body ───────────────────────────────────────────────────────────────────
    body = tk.Frame(dialog, bg=_C['bg'])
    body.pack(fill='both', expand=True, padx=20, pady=12)

    today = datetime.date.today()
    try:
        _gui_last_ok = get_last_completed_datetime()
    except Exception:
        _gui_last_ok = None
    # Smart default: if the end day is today, cap the end hour at the last
    # completed hour instead of offering future 23:00.
    _default_end_hour = _gui_last_ok.hour if _gui_last_ok is not None else 23

    # ── START DATE & HOUR ROW ──────────────────────────────────────────────────
    start_box = tk.LabelFrame(body, text=" INIZIO INTERVALLO ", font=('Segoe UI', 9, 'bold'),
                              fg=_C['yellow'], bg=_C['bg'], bd=1, relief='solid')
    start_box.pack(fill='x', pady=4, ipadx=6, ipady=6)

    # Start Date
    s_date_frame = tk.Frame(start_box, bg=_C['bg'])
    s_date_frame.pack(side='left', padx=10)
    tk.Label(s_date_frame, text="Data Inizio:", font=('Segoe UI', 8), fg=_C['white'], bg=_C['bg']).pack(anchor='w')
    start_date_entry = DateEntry(
        s_date_frame, width=14,
        background=_C['accent'], foreground=_C['white'],
        selectbackground=_C['green'], selectforeground='black',
        normalbackground='white', normalforeground='#111111',
        headersbackground=_C['accent'], headersforeground=_C['white'],
        weekendbackground='white', weekendforeground='#cc2222',
        othermonthbackground='#f0f0f0', othermonthforeground='#999999',
        borderwidth=0, font=('Segoe UI', 10),
        year=today.year, month=today.month, day=today.day,
        date_pattern='dd/mm/yyyy', locale='it_IT'
    )
    start_date_entry.pack(pady=2)

    # Start Hour
    s_hour_frame = tk.Frame(start_box, bg=_C['bg'])
    s_hour_frame.pack(side='right', padx=10)
    tk.Label(s_hour_frame, text="Ora Inizio:", font=('Segoe UI', 8), fg=_C['white'], bg=_C['bg']).pack(anchor='w')
    start_hour_var = tk.IntVar(value=0)

    sh_ctrl = tk.Frame(s_hour_frame, bg=_C['panel'])
    sh_ctrl.pack(pady=2)

    btn_style = dict(font=('Segoe UI', 11, 'bold'), fg=_C['white'],
                     bg=_C['accent'], activebackground=_C['green'],
                     activeforeground='black', bd=0, width=2, cursor='hand2')

    def _dec_sh():
        if start_hour_var.get() > 0:
            start_hour_var.set(start_hour_var.get() - 1)
            _update_total()

    def _inc_sh():
        if start_hour_var.get() < 23:
            start_hour_var.set(start_hour_var.get() + 1)
            _update_total()

    tk.Button(sh_ctrl, text="−", command=_dec_sh, **btn_style).pack(side='left')
    sh_disp = tk.Label(sh_ctrl, text="00:00", font=('Segoe UI', 11, 'bold'),
                       fg=_C['yellow'], bg=_C['panel'], width=5)
    sh_disp.pack(side='left', padx=2)
    tk.Button(sh_ctrl, text="+", command=_inc_sh, **btn_style).pack(side='left')

    # ── END DATE & HOUR ROW ────────────────────────────────────────────────────
    end_box = tk.LabelFrame(body, text=" FINE INTERVALLO ", font=('Segoe UI', 9, 'bold'),
                            fg=_C['yellow'], bg=_C['bg'], bd=1, relief='solid')
    end_box.pack(fill='x', pady=4, ipadx=6, ipady=6)

    # End Date
    e_date_frame = tk.Frame(end_box, bg=_C['bg'])
    e_date_frame.pack(side='left', padx=10)
    tk.Label(e_date_frame, text="Data Fine:", font=('Segoe UI', 8), fg=_C['white'], bg=_C['bg']).pack(anchor='w')
    end_date_entry = DateEntry(
        e_date_frame, width=14,
        background=_C['accent'], foreground=_C['white'],
        selectbackground=_C['green'], selectforeground='black',
        normalbackground='white', normalforeground='#111111',
        headersbackground=_C['accent'], headersforeground=_C['white'],
        weekendbackground='white', weekendforeground='#cc2222',
        othermonthbackground='#f0f0f0', othermonthforeground='#999999',
        borderwidth=0, font=('Segoe UI', 10),
        year=today.year, month=today.month, day=today.day,
        date_pattern='dd/mm/yyyy', locale='it_IT'
    )
    end_date_entry.pack(pady=2)

    # End Hour
    e_hour_frame = tk.Frame(end_box, bg=_C['bg'])
    e_hour_frame.pack(side='right', padx=10)
    tk.Label(e_hour_frame, text="Ora Fine:", font=('Segoe UI', 8), fg=_C['white'], bg=_C['bg']).pack(anchor='w')
    end_hour_var = tk.IntVar(value=_default_end_hour)

    eh_ctrl = tk.Frame(e_hour_frame, bg=_C['panel'])
    eh_ctrl.pack(pady=2)

    def _dec_eh():
        if end_hour_var.get() > 0:
            end_hour_var.set(end_hour_var.get() - 1)
            _update_total()

    def _inc_eh():
        if end_hour_var.get() < 23:
            end_hour_var.set(end_hour_var.get() + 1)
            _update_total()

    tk.Button(eh_ctrl, text="−", command=_dec_eh, **btn_style).pack(side='left')
    eh_disp = tk.Label(eh_ctrl, text=f"{_default_end_hour:02d}:00", font=('Segoe UI', 11, 'bold'),
                       fg=_C['yellow'], bg=_C['panel'], width=5)
    eh_disp.pack(side='left', padx=2)
    tk.Button(eh_ctrl, text="+", command=_inc_eh, **btn_style).pack(side='left')

    # Quick action row: presets (date-aware — today caps at last completed hour)
    quick_frame = tk.Frame(body, bg=_C['bg'])
    quick_frame.pack(fill='x', pady=4)

    def _set_single_day():
        s_d = start_date_entry.get_date()
        end_date_entry.set_date(s_d)
        start_hour_var.set(0)
        try:
            cur_ok = get_last_completed_datetime()
            end_hour_var.set(cur_ok.hour if s_d == cur_ok.date() else 23)
        except Exception:
            end_hour_var.set(23)
        _update_total()

    def _set_today_catchup():
        try:
            cur_ok = get_last_completed_datetime()
        except Exception:
            cur_ok = None
        if cur_ok is not None:
            start_date_entry.set_date(cur_ok.date())
            end_date_entry.set_date(cur_ok.date())
            start_hour_var.set(0)
            end_hour_var.set(cur_ok.hour)
        else:
            t = datetime.date.today()
            start_date_entry.set_date(t)
            end_date_entry.set_date(t)
            start_hour_var.set(0)
            end_hour_var.set(23)
        continuous_var.set(True)
        _update_total()

    tk.Button(
        quick_frame, text="Giorno Singolo",
        command=_set_single_day,
        font=('Segoe UI', 9), fg=_C['white'], bg=_C['panel'],
        activebackground=_C['accent'], activeforeground=_C['white'],
        bd=0, pady=4, padx=8, cursor='hand2'
    ).pack(side='left', expand=True, fill='x', padx=(0, 4))

    tk.Button(
        quick_frame, text="Recupera Oggi + Continua",
        command=_set_today_catchup,
        font=('Segoe UI', 9, 'bold'), fg=_C['yellow'], bg=_C['panel'],
        activebackground=_C['accent'], activeforeground=_C['white'],
        bd=0, pady=4, padx=8, cursor='hand2'
    ).pack(side='right', expand=True, fill='x', padx=(4, 0))

    # Continuous mode checkbox
    continuous_var = tk.BooleanVar(value=True)
    chk_cont = tk.Checkbutton(
        body, text="Continua automazione oraria dopo l'estrazione dell'intervallo",
        variable=continuous_var,
        font=('Segoe UI', 9), fg=_C['white'], bg=_C['bg'],
        activebackground=_C['bg'], activeforeground=_C['green'],
        selectcolor=_C['panel'], cursor='hand2',
        command=lambda: _update_total()
    )
    chk_cont.pack(anchor='w', pady=(6, 2))

    # Summary box
    summary_frame = tk.Frame(body, bg='#0d2137', bd=0)
    summary_frame.pack(fill='x', pady=(6, 0))
    total_lbl = tk.Label(
        summary_frame, text="", font=('Segoe UI', 9, 'bold'),
        fg='#88ccee', bg='#0d2137', justify='left', anchor='w'
    )
    total_lbl.pack(padx=10, pady=8)

    error_var = tk.StringVar()
    error_label = tk.Label(body, textvariable=error_var, font=('Segoe UI', 9),
                           fg=_C['red'], bg=_C['bg'])
    error_label.pack(pady=(4, 0))

    def _update_total(*args):
        sh_disp.configure(text=f"{start_hour_var.get():02d}:00")
        eh_disp.configure(text=f"{end_hour_var.get():02d}:00")
        try:
            s_d = start_date_entry.get_date()
            e_d = end_date_entry.get_date()
            s_h = start_hour_var.get()
            e_h = end_hour_var.get()
            s_dt = datetime.datetime(s_d.year, s_d.month, s_d.day, s_h)
            e_dt = datetime.datetime(e_d.year, e_d.month, e_d.day, e_h)
            if e_dt < s_dt:
                raise ValueError(f"Data/ora fine ({e_dt.strftime('%d/%m %H:%M')}) anteriore a data/ora inizio ({s_dt.strftime('%d/%m %H:%M')}).")
            try:
                last_ok = get_last_completed_datetime()
            except Exception:
                last_ok = None
            if last_ok is not None:
                last_ok_dt = datetime.datetime(last_ok.year, last_ok.month, last_ok.day, last_ok.hour)
                if s_dt > last_ok_dt:
                    raise ValueError(f"Data/ora inizio nel futuro. Ultimo report completato: {last_ok.strftime('%d/%m/%Y ore %H:00')}.")
            hours = generate_target_hours(s_d, s_h, e_d, e_h)
            # Split into immediately-downloadable vs future (incomplete) hours.
            try:
                _due, _future = split_targets_by_availability(hours)
            except Exception:
                _due, _future = hours, []
                last_ok = None
            is_cont = continuous_var.get()
            if s_d == e_d:
                base_txt = f"[i] Giorno singolo ({s_d.strftime('%d/%m/%Y')}): {len(hours)} report orari."
            else:
                base_txt = f"[i] Dal {s_d.strftime('%d/%m/%Y')} al {e_d.strftime('%d/%m/%Y')}: {len(hours)} report orari totali."
            if _future and last_ok is not None:
                base_txt += (f"\n[OK] {len(_due)} disponibili ora (fino a {last_ok.strftime('%d/%m %H:00')})"
                             f"  -  [WAIT] {len(_future)} futuri/non ancora disponibili"
                             f" (scaricati solo con 'Continua' quando completati).")
                if not _due:
                    base_txt += "\n[WARN] Nessuna ora ancora disponibile — con 'Continua' attende l'orario."
            elif _future:
                base_txt += f"\n[WAIT] {len(_future)} ore future (richiedono 'Continua')."
            if is_cont:
                base_txt += "\n[CONTINUA] Al termine: monitoraggio continuo attivo (ogni ora a :05)."
            total_lbl.configure(text=base_txt)
            error_var.set("")
        except Exception as e:
            total_lbl.configure(text="[WARN] Intervallo non valido")
            error_var.set(str(e))

    start_date_entry.bind("<<DateEntrySelected>>", _update_total)
    end_date_entry.bind("<<DateEntrySelected>>", _update_total)
    _update_total()

    def on_ok():
        try:
            s_d = start_date_entry.get_date()
            e_d = end_date_entry.get_date()
            s_h = start_hour_var.get()
            e_h = end_hour_var.get()
            generate_target_hours(s_d, s_h, e_d, e_h)
            result[0] = s_d
            result[1] = s_h
            result[2] = e_d
            result[3] = e_h
            result[4] = continuous_var.get()
            dialog.destroy()
        except Exception as ex:
            error_var.set(str(ex))

    def on_cancel():
        dialog.destroy()

    btn_frame = tk.Frame(dialog, bg=_C['bg'])
    btn_frame.pack(fill='x', padx=20, pady=(4, 16))

    tk.Button(
        btn_frame, text="▶   Avvia Estrazione Report",
        command=on_ok,
        font=('Segoe UI', 11, 'bold'), fg='black', bg=_C['green'],
        activebackground='#00ffcc', activeforeground='black',
        bd=0, pady=10, cursor='hand2', relief='flat'
    ).pack(fill='x', pady=(0, 6))

    tk.Button(
        btn_frame, text="Annulla",
        command=on_cancel,
        font=('Segoe UI', 10), fg='#aaaaaa', bg=_C['panel'],
        activebackground='#2a2a4a', activeforeground=_C['white'],
        bd=0, pady=6, cursor='hand2', relief='flat'
    ).pack(fill='x')

    dialog.mainloop()
    return result[0], result[1], result[2], result[3], result[4]


def parse_cli_args():
    import argparse
    parser = argparse.ArgumentParser(
        description=f"SCADA Automation v{__version__} — Estrazione automatizzata report SCADA via GUI / CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  # Giorno singolo (scarica tutte le 24 ore del 2026-08-05):
  python scada_automation_v1.2.py -sd 2026-08-05

  # Intervallo di date con ore specifiche:
  python scada_automation_v1.2.py -sd 2026-08-01 -st 08 -ed 2026-08-05 -et 18

  # Anteprima senza esecuzione (dry-run):
  python scada_automation_v1.2.py -sd 01/08/2026 -ed 05/08/2026 --dry-run

  # Modalità continua (scarica l'intervallo e continua il monitoraggio ogni ora):
  python scada_automation_v1.2.py -sd 2026-08-05 -c

Nota v1.2: le ore future/incomplete (disponibili solo da (H+1):05) non vengono mai
scaricate subito: con -c vengono attese, senza -c vengono saltate.
"""
    )
    parser.add_argument("-sd", "--start-date", dest="start_date", help="Data di inizio (es. YYYY-MM-DD o DD/MM/YYYY)")
    parser.add_argument("-st", "--start-time", dest="start_time", help="Ora/Orario di inizio (0-23 o HH:MM). Default: 0")
    parser.add_argument("-ed", "--end-date", dest="end_date", help="Data di fine (es. YYYY-MM-DD o DD/MM/YYYY). Se omessa, equivale alla data di inizio (giorno singolo)")
    parser.add_argument("-et", "--end-time", dest="end_time", help="Ora/Orario di fine (0-23 o HH:MM). Default: 23")
    parser.add_argument("-c", "--continuous", action="store_true", help="Continua l'automazione oraria dopo l'estrazione dell'intervallo")
    parser.add_argument("-o", "--output-dir", dest="output_dir", help="Cartella di destinazione salvataggio file (sovrascrive PATH_TO_ORI_FOLDER)")
    parser.add_argument("--delay-load", type=int, dest="delay_load", help="Tempo di attesa caricamento dati in secondi (default: 90)")
    parser.add_argument("--delay-save", type=int, dest="delay_save", help="Tempo massimo di inattività salvataggio in secondi (default: 600)")
    parser.add_argument("--max-retries", type=int, dest="max_retries", default=0, help="Tentativi massimi sulla STESSA ora in continua prima di uscire con errore (0 = infiniti, default)")
    parser.add_argument("-vb", "--verify-and-backup", action="store_true", help="Attiva l'ispezione approfondita dei file esistenti e il backup dei file errati")
    parser.add_argument("-td", "--test-date", type=str, help="Esegue il test di verifica dei file su una specifica data (formato YYYY-MM-DD o DD/MM/YYYY)")
    parser.add_argument("--grid-first", action="store_true", help="Forza il calcolo matematico della griglia del calendario per evitare errori OCR")
    parser.add_argument("--dry-run", action="store_true", help="Mostra l'elenco dei report che verrebbero scaricati ed esce senza avviare SCADA")
    parser.add_argument("--gui", action="store_true", help="Forza l'apertura dell'interfaccia grafica (GUI) anche se sono passati parametri da riga di comando")

    return parser.parse_args()


if __name__ == "__main__":
    pyautogui.FAILSAFE = False
    args = parse_cli_args()

    # Override configurable parameters if passed
    if args.output_dir:
        PATH_TO_ORI_FOLDER = os.path.normpath(args.output_dir)
        print(f"[Config] Cartella output impostata a: {PATH_TO_ORI_FOLDER}")
    if args.verify_and_backup:
        VERIFY_AND_BACKUP = True
        print("[Config] Modalità Verifica & Backup attivata: i file errati verranno spostati nella cartella backup/")
    if args.grid_first:
        GRID_FIRST = True
        print("[Config] Calcolo griglia calendario prioritario attivato (bypassa ambiguità OCR).")
    if args.test_date:
        parsed_td = parse_date_string(args.test_date)
        if parsed_td:
            args.start_date = args.test_date
            args.end_date = args.test_date
            print(f"[Config] Data di test impostata: {parsed_td.strftime('%d/%m/%Y')}")
    if args.delay_load is not None:
        DELAY_LOAD_DATA = args.delay_load
        print(f"[Config] DELAY_LOAD_DATA impostato a: {DELAY_LOAD_DATA}s")
    if args.delay_save is not None:
        SAVE_MAX_IDLE_TIMEOUT = args.delay_save
        DELAY_SAVE_FILE = args.delay_save
        print(f"[Config] SAVE_MAX_IDLE_TIMEOUT impostato a: {SAVE_MAX_IDLE_TIMEOUT}s")
    if getattr(args, "max_retries", 0):
        MAX_CONTINUOUS_RETRIES = int(args.max_retries)
        print(f"[Config] MAX_CONTINUOUS_RETRIES impostato a: {MAX_CONTINUOUS_RETRIES}")

    # Determine whether to use CLI params or GUI
    use_cli = bool(args.start_date) and not args.gui

    if use_cli:
        print("\n=== Modalità Riga di Comando (CLI) ===")
        set_phase("AVVIO CLI", "run", "Lettura parametri riga di comando...")
        try:
            start_date = parse_date_string(args.start_date)
            start_hour = parse_time_string(args.start_time) if args.start_time is not None else 0

            if args.end_date:
                end_date = parse_date_string(args.end_date)
            else:
                end_date = start_date # Single day mode

            end_hour = parse_time_string(args.end_time) if args.end_time is not None else 23
            continuous_mode = args.continuous
        except Exception as e:
            print(f"[Errore CLI] Parametri non validi: {e}")
            sys.exit(1)
    else:
        # Show GUI dialog
        show_overlay()
        start_hotkey_listener()
        print("=" * 60)
        print("Overlay attivo: pannello di stato visibile durante l'esecuzione.")
        print("Premi Ctrl+Alt+. in qualsiasi momento per interrompere l'automazione.")
        print("=" * 60)

        current_status = "In attesa di input utente..."
        set_phase("ATTESA INPUT UTENTE", "wait", "In attesa di input utente...")
        print("\nApertura finestra di selezione date/ore...")
        start_date, start_hour, end_date, end_hour, continuous_mode = show_time_selection_dialog()

        if start_date is None or start_hour is None:
            set_phase("ANNULLATO", "idle", "Operazione annullata dall'utente")
            print("Selezione annullata dall'utente. Uscita.")
            sys.exit(0)

    # Generate target hours list
    try:
        hours_to_process = generate_target_hours(start_date, start_hour, end_date, end_hour)
    except Exception as e:
        print(f"[Errore] Impossibile generare l'intervallo orario: {e}")
        sys.exit(1)

    # v1.2: respect wall-clock time — never schedule future/incomplete hours now.
    # Hour H is downloadable only from (H+1):05 (AVAILABILITY_LAG_MINUTES).
    _now_for_split = datetime.datetime.now()
    _last_ok = get_last_completed_datetime(_now_for_split)
    due_hours, future_hours = split_targets_by_availability(hours_to_process, _now_for_split)

    # v1.2: pre-filter hours already valid on disk (no SCADA needed for those).
    set_phase("CONTROLLO FILE ESISTENTI", "run", "Controllo file gia' presenti su disco...")
    due_todo, already_done = filter_already_completed(due_hours)
    if already_done:
        print(f"[Pre-check] {len(already_done)} report gia' presenti e validi — saltati senza SCADA.")

    print("\n" + "=" * 60)
    print(f"Riepilogo Intervallo Dati (v{__version__}, rispetto orario reale):")
    print(f"  Data Inizio : {start_date} ore {start_hour:02d}:00")
    print(f"  Data Fine   : {end_date} ore {end_hour:02d}:00")
    print(f"  Ora attuale : {_now_for_split.strftime('%d/%m/%Y %H:%M')}")
    print(f"  Ultima ora completa disponibile: {_last_ok.strftime('%d/%m/%Y %H:00')} "
          f"(disponibile dal {(_last_ok + datetime.timedelta(hours=1, minutes=AVAILABILITY_LAG_MINUTES)).strftime('%H:%M')})")
    print(f"  Totale richiesti: {len(hours_to_process)} | Scaricabili ora: {len(due_hours)} "
          f"(da scaricare: {len(due_todo)}, gia' presenti: {len(already_done)}) | Futuri: {len(future_hours)}")
    print(f"  Modalità continua dopo download : {'ATTIVA' if continuous_mode else 'DISATTIVA'}")
    if future_hours:
        if continuous_mode:
            print(f"  [FUTURE] {len(future_hours)} ore future saranno scaricate automaticamente quando completate (modalita' continua).")
            print(f"     Prima ora futura: {future_hours[0][0]} {future_hours[0][1]:02d}:00 -> "
                  f"disponibile dal {get_trigger_time_for_target(target_to_datetime(*future_hours[0])).strftime('%d/%m/%Y %H:%M')}")
        else:
            print(f"  [WARN] {len(future_hours)} ore future NON saranno scaricate (dati non ancora esistenti).")
            print(f"    Usa -c / spunta 'Continua' per attenderle, oppure riduci l'ora di fine a {_last_ok.strftime('%H:00 del %d/%m/%Y')}.")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY-RUN] Report da scaricare ORA:")
        for d, h in due_todo:
            print(f"  - {d} {h:02d}:00")
        if already_done:
            print(f"[DRY-RUN] Gia' presenti e validi ({len(already_done)}) — saltati:")
            for d, h in already_done:
                print(f"  - {d} {h:02d}:00 (presente)")
        if future_hours:
            print(f"[DRY-RUN] Report FUTURI ({len(future_hours)}) — {'verrebbero attesi con -c' if continuous_mode else 'verrebbero SALTATI senza -c'}:")
            for d, h in future_hours:
                trig = get_trigger_time_for_target(target_to_datetime(d, h))
                print(f"  - {d} {h:02d}:00 (disponibile dal {trig.strftime('%d/%m %H:%M')})")
        print(f"[DRY-RUN] Totale richiesti: {len(hours_to_process)} | Da scaricare ora: {len(due_todo)} "
              f"| Gia' presenti: {len(already_done)} | Futuri: {len(future_hours)}. Uscita completata.")
        sys.exit(0)

    # Nothing to download right now?
    if not due_todo and not stop_event.is_set():
        if future_hours and continuous_mode:
            # v1.2 LAZY WAIT: do NOT open SCADA yet — wait for the first
            # requested future hour to become available first.
            first_dt = min(target_to_datetime(d, h) for d, h in future_hours)
            first_trigger = get_trigger_time_for_target(first_dt)
            print(f"\n[INFO v{__version__}] Nessuna ora ancora disponibile — attendo senza aprire SCADA "
                  f"fino alle {first_trigger.strftime('%d/%m/%Y %H:%M')} (prima ora: {first_dt.strftime('%d/%m %H:00')}).")
            if not wait_until_wallclock(first_trigger, f"per ora {first_dt.hour:02d}:00"):
                print("Attesa interrotta dall'utente. Uscita.")
                sys.exit(0)
            # Re-evaluate after the wait (clock moved; files may have appeared).
            _now2 = datetime.datetime.now()
            due_hours, future_hours = split_targets_by_availability(hours_to_process, _now2)
            due_todo, already_done = filter_already_completed(due_hours)
            print(f"[INFO] Dopo l'attesa: da scaricare ora={len(due_todo)}, futuri={len(future_hours)}.")
        elif future_hours:
            print("\n[INFO v1.2] Nessuna ora disponibile e modalità continua DISATTIVA — niente da scaricare. Esco.")
            print(f"       Suggerimento: riprova dopo il {get_trigger_time_for_target(target_to_datetime(*future_hours[0])).strftime('%d/%m/%Y %H:%M')} "
                  f"oppure usa -c per attendere.")
            sys.exit(0)
        else:
            if already_done and not future_hours:
                print(f"\n[OK] Tutti i {len(already_done)} report richiesti sono gia' presenti e validi. Niente da fare.")
            else:
                print("Nessun report da scaricare per l'intervallo specificato.")
            if not continuous_mode:
                sys.exit(0)

    # If running in CLI mode without overlay yet, start overlay & hotkey listener
    if use_cli:
        show_overlay()
        start_hotkey_listener()
        print("=" * 60)
        print("Overlay attivo: pannello di stato visibile durante l'esecuzione.")
        print("Premi Ctrl+Alt+. in qualsiasi momento per interrompere l'automazione.")
        print("=" * 60)

    current_status = f"Estrazione {len(due_todo)} report disponibili (v{__version__})..."
    set_phase("AVVIO SCARICO", "run",
              f"Avvio: {len(due_todo)} da scaricare, {len(already_done)} presenti, {len(future_hours)} futuri")
    print(f"\nAvvio elaborazione per {len(due_todo)} report orari da scaricare "
          f"(gia' presenti: {len(already_done)}, futuri: {len(future_hours)})...")

    # Initial setup (only if there is something to do now or continuous waiting
    # for an already-due hour — never just to sit on a far-future trigger).
    needs_scada_now = bool(due_todo) or (continuous_mode and bool(due_hours))
    if needs_scada_now:
        set_phase("CONFIGURAZIONE SCADA", "run", "Configurazione iniziale: ricerca e attivazione finestra SCADA...")
        if not perform_initial_setup():
            set_phase("ERRORE CONFIGURAZIONE", "error", "Configurazione iniziale fallita")
            print("Configurazione iniziale della finestra SCADA fallita.")
            sys.exit(1)
    else:
        print("Niente da fare — esco senza aprire SCADA.")
        sys.exit(0)

    # Process only due (already-completed) hours in specified range,
    # minus files already valid on disk (v1.2 pre-filter).
    success_count = 0
    range_completed_cleanly = True
    range_start_ts = time.perf_counter()
    if due_todo:
        set_phase(f"SCARICO 0/{len(due_todo)}", "run", f"Recupero: 0/{len(due_todo)}")
        for idx, (target_date, target_hour) in enumerate(due_todo):
            if stop_event.is_set():
                set_phase("INTERROTTO", "error", "Recupero interrotto dall'utente")
                print("Operazione interrotta dall'utente.")
                range_completed_cleanly = False
                break

            _todo_path, _todo_file = build_expected_csv_path(target_date, target_hour)
            set_phase(f"SCARICO {idx + 1}/{len(due_todo)}", "run",
                      f"Recupero {idx + 1}/{len(due_todo)} — {_todo_file} ({target_date} ore {target_hour:02d}:00)")

            if not ensure_scada_window_active():
                set_phase("ERRORE FINESTRA SCADA", "error", "Impossibile attivare finestra SCADA")
                print("Impossibile attivare la finestra SCADA, arresto in corso.")
                range_completed_cleanly = False
                break

            perform_scada_prep()
            hour_start_ts = time.perf_counter()
            if process_hourly_report(target_date, target_hour):
                success_count += 1
                hour_elapsed = time.perf_counter() - hour_start_ts
                print(f"[Tempo] Ora {target_date} {target_hour:02d}:00 completata in {hour_elapsed/60:.1f} min.")
                set_phase(f"SCARICO {success_count}/{len(due_todo)}", "run", "Reset interfaccia...")
                perform_reset()
                print("Attesa ripristino interfaccia...")
                time.sleep(2.0)
            else:
                hour_elapsed = time.perf_counter() - hour_start_ts
                set_phase("ERRORE DOWNLOAD", "error", f"Errore report {target_date} {target_hour:02d}:00")
                print(f"Errore durante il download del report {target_date} {target_hour:02d}:00 "
                      f"(dopo {hour_elapsed/60:.1f} min)")
                range_completed_cleanly = False
                break

        range_elapsed = time.perf_counter() - range_start_ts
        print(f"\nDownload intervallo completato: {success_count}/{len(due_todo)} report elaborati "
              f"(richiesti totali: {len(hours_to_process)}, gia' presenti: {len(already_done)}, "
              f"futuri differiti/saltati: {len(future_hours)}) in {range_elapsed/60:.1f} min.")
        set_phase("INTERVALLO COMPLETATO", "done", f"Completato: {success_count}/{len(due_todo)} report")
        time.sleep(2)
    else:
        print("Nessun report disponibile ora per l'intervallo specificato (tutte ore future).")
        range_completed_cleanly = True

    # Continue with continuous hourly automation if requested — sequential logic
    if continuous_mode and not stop_event.is_set():
        print(f"\nAvvio automazione oraria continua (v{__version__}: sequenziale, senza salti, senza futuri)...")
        set_phase("AVVIO CONTINUA", "run", "Avvio automazione oraria continua")

        # Determine the next hour to download after the range phase.
        # Note: due_hours includes pre-existing files (already done); due_todo
        # is the subset actually processed above, so resume indexes into due_todo.
        if hours_to_process:
            if due_hours and range_completed_cleanly and success_count >= len(due_todo):
                # Range fully done (downloaded + pre-existing) → hour after last due.
                next_needed_dt = max(target_to_datetime(d, h) for d, h in due_hours) + datetime.timedelta(hours=1)
            elif due_todo and success_count < len(due_todo):
                # Range interrupted/failed → resume from the first non-completed todo hour.
                next_needed_dt = target_to_datetime(*due_todo[success_count])
                print(f"[Continua] Riprendo dall'ora interrotta: {next_needed_dt.strftime('%d/%m/%Y %H:00')}")
            elif due_hours:
                next_needed_dt = max(target_to_datetime(d, h) for d, h in due_hours) + datetime.timedelta(hours=1)
            else:
                # All requested hours were future → wait for the first requested one.
                next_needed_dt = min(target_to_datetime(d, h) for d, h in future_hours)
                print(f"[Continua] Prima ora richiesta futura: {next_needed_dt.strftime('%d/%m/%Y %H:00')} "
                      f"(disponibile dal {get_trigger_time_for_target(next_needed_dt).strftime('%d/%m/%Y %H:%M')})")
        else:
            next_needed_dt = get_last_completed_datetime() + datetime.timedelta(hours=1)

        consecutive_failures = 0
        while not stop_event.is_set():
            last_available = get_last_completed_datetime()
            if next_needed_dt > last_available:
                # Requested hour not complete yet → wait until (H+1):05.
                trigger = get_trigger_time_for_target(next_needed_dt)
                if not wait_until_wallclock(trigger, f"per ora {next_needed_dt.hour:02d}:00 del {next_needed_dt.date()}"):
                    break  # stopped by user
                continue  # re-evaluate availability (handles stop/skip correctly)

            # next_needed_dt <= last_available → due now (catch-up or live). Download it.
            target_date = next_needed_dt.date()
            target_hour = next_needed_dt.hour
            print(f"Download report automatico per {target_date} {target_hour:02d}:00 "
                  f"(sequenza continua, ultima completa: {last_available.strftime('%d/%m %H:00')})")
            _cont_path, _cont_file = build_expected_csv_path(target_date, target_hour)
            set_phase(f"SCARICO CONTINUA {target_hour:02d}:00", "run",
                      f"Download continua: {_cont_file} (ultima completa: {last_available.strftime('%d/%m %H:00')})")
            try:
                if not ensure_scada_window_active():
                    set_phase("ERRORE FINESTRA SCADA", "error",
                              "Finestra SCADA non attivabile — riprovo tra 60s senza saltare l'ora")
                    print("[WARN] Impossibile attivare la finestra SCADA. Riprovo tra 60s senza saltare l'ora.")
                    interruptible_sleep(60)
                    continue  # retry SAME hour (never skip)
                perform_scada_prep()
                success = process_hourly_report(target_date, target_hour)
                if success:
                    set_phase(f"SCARICO CONTINUA {target_hour:02d}:00", "run", "Reset interfaccia...")
                    perform_reset()
                    print("Attesa ripristino interfaccia...")
                    time.sleep(2.0)
                    set_phase("CONTINUA PRONTA", "wait", "Pronto per il prossimo report")
                    next_needed_dt += datetime.timedelta(hours=1)
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    if MAX_CONTINUOUS_RETRIES and consecutive_failures >= MAX_CONTINUOUS_RETRIES:
                        print(f"[ERROR] {consecutive_failures} fallimenti consecutivi sulla stessa ora "
                              f"({target_date} {target_hour:02d}:00) — esco con errore (fail-loud, nessun salto).")
                        sys.exit(1)
                    set_phase("ERRORE — RIPROVO STESSA ORA", "error",
                              f"Download {target_hour:02d}:00 fallito (tentativo {consecutive_failures}) — riprovo tra 60s")
                    print(f"[WARN] Download report automatico fallito (tentativo {consecutive_failures}). "
                          f"Riprovo la STESSA ora tra 60s (nessun salto)...")
                    try:
                        perform_reset()
                    except Exception as re:
                        print(f"[WARN] Errore durante il reset dell'interfaccia: {re}")
                    interruptible_sleep(60)
                    # do NOT advance next_needed_dt → retry same hour
            except Exception as ex:
                consecutive_failures += 1
                if MAX_CONTINUOUS_RETRIES and consecutive_failures >= MAX_CONTINUOUS_RETRIES:
                    print(f"[ERROR] {consecutive_failures} errori consecutivi sulla stessa ora "
                          f"({target_date} {target_hour:02d}:00): {ex} — esco con errore.")
                    sys.exit(1)
                print(f"[ERROR] Eccezione durante il download automatico ({target_date} {target_hour:02d}:00): {ex}")
                set_phase("ERRORE — RIPROVO STESSA ORA", "error", f"Errore ciclo {target_hour:02d}:00 — riprovo tra 60s")
                try:
                    perform_reset()
                except Exception:
                    pass
                interruptible_sleep(60)
                # do NOT advance → retry same hour

    set_phase("COMPLETATO", "done", "Automazione completata")
    print("Automazione completata.")