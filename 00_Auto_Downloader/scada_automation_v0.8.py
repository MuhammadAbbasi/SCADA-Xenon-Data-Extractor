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

# --- Global stop flag (set by Ctrl+Alt+. hotkey) ---
stop_event = threading.Event()

# --- Configuration ---
# PATHS & DELAYS (User to configure these if needed)
PATH_TO_ORI_FOLDER = r"//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/01_Original_files" # Placeholder path
ASSETS_DIR = "assets"

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
DELAY_SAVE_FILE = 80
DELAY_CLOSE_SAVE = 20

# ---------------------------------------------------------------------------
# Screen border overlay + Ctrl+Alt+. stop hotkey
# ---------------------------------------------------------------------------

# --- Global status for overlay ---
current_status = "Inizializzazione..."

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

        OW, OH = 420, 90
        sw = root.winfo_screenwidth()
        root.geometry(f"{OW}x{OH}+{sw - OW - 20}+20")
        root.configure(bg=_C['bg'])

        # Rounded-look outer container
        outer = tk.Frame(root, bg=_C['accent'], bd=0)
        outer.pack(fill='both', expand=True, padx=2, pady=2)

        inner = tk.Frame(outer, bg=_C['panel'], bd=0)
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # Title row
        title_row = tk.Frame(inner, bg=_C['accent'])
        title_row.pack(fill='x')
        tk.Label(
            title_row, text="  SCADA  Automazione",
            font=('Segoe UI', 10, 'bold'), fg=_C['white'], bg=_C['accent'],
            anchor='w'
        ).pack(side='left', pady=4, padx=6)
        status_dot_label = tk.Label(
            title_row, text="ATTIVO  ●",
            font=('Segoe UI', 9, 'bold'), fg=_C['green'], bg=_C['accent'],
            anchor='e'
        )
        status_dot_label.pack(side='right', pady=4, padx=8)

        # Status text
        status_var = tk.StringVar(value=current_status)
        task_label = tk.Label(
            inner, textvariable=status_var,
            font=('Segoe UI', 9), fg=_C['yellow'], bg=_C['panel'],
            wraplength=400, justify='left', anchor='w'
        )
        task_label.pack(fill='x', padx=10, pady=(6, 2))

        # Hint row
        tk.Label(
            inner, text="Premi Ctrl+Alt+.  per interrompere",
            font=('Segoe UI', 7), fg='#888888', bg=_C['panel'], anchor='w'
        ).pack(fill='x', padx=10, pady=(0, 4))

        # Pulsing dot in title
        _tick = [0]
        def animate():
            _tick[0] ^= 1
            dot_color = _C['green'] if _tick[0] else _C['panel']
            # Rebuild the label text with toggled dot colour (simplest approach)
            status_dot_label.configure(foreground=dot_color)
            root.after(800, animate)

        def update_status():
            status_var.set(current_status)
            root.after(1000, update_status)

        def check_stop():
            if stop_event.is_set():
                root.destroy()
                return
            root.after(200, check_stop)

        root.after(800, animate)
        root.after(1000, update_status)
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


def interruptible_sleep(seconds, check_interval=0.5):
    """Like time.sleep() but wakes every check_interval seconds to honour stop_event."""
    deadline = time.time() + seconds
    while not stop_event.is_set():
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        time.sleep(min(check_interval, remaining))


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
    print(f"Grid calc: first_monday={first_visible_monday}, delta={delta}, row={row}, col={col} → ({int(x)}, {int(y)})")
    return (int(x), int(y))

def process_hourly_report(target_date, target_hour):
    """Execute Steps 7-18 for a specific date and hour."""
    global current_status
    
    # Check if expected output CSV already exists and is non-empty
    year_str = str(target_date.year)
    month_str = f"{target_date.month:02d}"
    day_str = f"{target_date.day:02d}"
    hh_str = f"{target_hour:02d}"
    jj = (target_hour + 1) if (target_hour + 1) < 24 else 0
    jj_str = f"{jj:02d}"
    date_dash = f"{year_str}-{month_str}-{day_str}"
    filename = f"{day_str}_{month_str}_{year_str}_{hh_str}_{jj_str}.csv"
    check_path = os.path.join(PATH_TO_ORI_FOLDER, year_str, month_str, date_dash, filename)
    
    if os.path.exists(check_path) and os.path.getsize(check_path) > 0:
        print(f"  ✓ Tracker file already exists for {target_date} {target_hour:02d}:00 ({filename}). Skipping!")
        current_status = f"File già presente: {filename}"
        return True

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
                    pos = pyautogui.Point(selected_match[0], selected_match[1])
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
    interruptible_sleep(DELAY_LOAD_DATA)

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
    
    # Construct Path
    # PATH_TO_ORI_FOLDER / YYYY / MM / YYYY-MM-DD / DD_MM_YYYY_HH_JJ.csv
    # JJ = HH + 1
    year_str = str(target_date.year)
    month_str = f"{target_date.month:02d}"
    day_str = f"{target_date.day:02d}"
    hh_str = f"{target_hour:02d}"
    jj = target_hour + 1
    if jj == 24: jj = 0 # Wrap around if needed, though format might expect 24 or next day 00
    jj_str = f"{jj:02d}"
    
    date_dash = f"{year_str}-{month_str}-{day_str}"
    filename = f"{day_str}_{month_str}_{year_str}_{hh_str}_{jj_str}.csv"
    
    full_path = os.path.join(PATH_TO_ORI_FOLDER, year_str, month_str, date_dash, filename)
    full_path = os.path.normpath(full_path) # Normalize for Windows (backslashes)
    print(f"Saving to: {full_path}")
    current_status = f"Saving file: {filename}"
    
    # Ensure directory exists
    dir_path = os.path.dirname(full_path)
    if not os.path.exists(dir_path):
        print(f"Creating directory: {dir_path}")
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")

    # Write full absolute path to save file directly into target folder
    pyautogui.write(full_path, interval=0.01)

    time.sleep(1.0)

    print("=== Step 18: Save and Wait ===")
    current_status = f"Salvataggio..."
    pyautogui.click(COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON)
    time.sleep(0.5)

    # Automatically confirm Windows 'File already exists / Overwrite?' dialog if shown
    pyautogui.press('y')
    pyautogui.press('enter')

    # Polled wait: check for file creation on disk up to DELAY_SAVE_FILE seconds
    deadline = time.time() + DELAY_SAVE_FILE
    file_saved = False
    while time.time() < deadline and not stop_event.is_set():
        if (os.path.exists(full_path) and os.path.getsize(full_path) > 0) or \
           os.path.exists(os.path.join(PATH_TO_ORI_FOLDER, filename)):
            print(f"✓ File save confirmed: {filename}")
            file_saved = True
            time.sleep(1.0)
            break
        time.sleep(0.5)

    # Ensure file is at target full_path
    if not os.path.exists(full_path):
        try:
            import shutil
            alt_path = os.path.join(PATH_TO_ORI_FOLDER, filename)
            if os.path.exists(alt_path):
                shutil.move(alt_path, full_path)
        except Exception:
            pass

    print(f"Task Completed FOR {target_hour}:00")
    current_status = f"Report saved for {target_hour}:00"
    return True

def get_next_trigger_time():
    """Calculate the next trigger time: next hour at :05."""
    now = datetime.datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    return next_hour + datetime.timedelta(minutes=5)


def get_first_run_target():
    """Return the first report target date and hour for immediate execution."""
    now = datetime.datetime.now()
    if now.hour == 0:
        target_date = now.date() - datetime.timedelta(days=1)
        target_hour = 23
    else:
        target_date = now.date()
        target_hour = now.hour - 1
    return target_date, target_hour


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
    """Legacy helper: generate hours from start_date:start_hour up to now."""
    now = datetime.datetime.now()
    if now.hour == 0:
        end_date = now.date() - datetime.timedelta(days=1)
        end_hour = 23
    else:
        end_date = now.date()
        end_hour = now.hour - 1

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
    dialog.title("SCADA — Estrazione Dati Intervallo")
    dialog.resizable(False, False)

    DW, DH = 520, 620
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
        header, text="SCADA  |  Estrazione Dati Storici",
        font=('Segoe UI', 13, 'bold'), fg=_C['white'], bg=_C['accent']
    ).pack(expand=True)

    # ── Body ───────────────────────────────────────────────────────────────────
    body = tk.Frame(dialog, bg=_C['bg'])
    body.pack(fill='both', expand=True, padx=20, pady=12)

    today = datetime.date.today()

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
    end_hour_var = tk.IntVar(value=23)

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
    eh_disp = tk.Label(eh_ctrl, text="23:00", font=('Segoe UI', 11, 'bold'),
                       fg=_C['yellow'], bg=_C['panel'], width=5)
    eh_disp.pack(side='left', padx=2)
    tk.Button(eh_ctrl, text="+", command=_inc_eh, **btn_style).pack(side='left')

    # Quick action row: Giorno Singolo button
    quick_frame = tk.Frame(body, bg=_C['bg'])
    quick_frame.pack(fill='x', pady=4)

    def _set_single_day():
        s_d = start_date_entry.get_date()
        end_date_entry.set_date(s_d)
        start_hour_var.set(0)
        end_hour_var.set(23)
        _update_total()

    tk.Button(
        quick_frame, text="📅  Imposta Giorno Singolo (24 ore)",
        command=_set_single_day,
        font=('Segoe UI', 9), fg=_C['white'], bg=_C['panel'],
        activebackground=_C['accent'], activeforeground=_C['white'],
        bd=0, pady=4, cursor='hand2'
    ).pack(fill='x')

    # Continuous mode checkbox
    continuous_var = tk.BooleanVar(value=True)
    chk_cont = tk.Checkbutton(
        body, text="Continua automazione oraria dopo l'estrazione dell'intervallo",
        variable=continuous_var,
        font=('Segoe UI', 9), fg=_C['white'], bg=_C['bg'],
        activebackground=_C['bg'], activeforeground=_C['green'],
        selectcolor=_C['panel'], cursor='hand2'
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
            hours = generate_target_hours(s_d, start_hour_var.get(), e_d, end_hour_var.get())
            if s_d == e_d:
                total_lbl.configure(text=f"ℹ  Giorno singolo ({s_d.strftime('%d/%m/%Y')}): {len(hours)} report orari da scaricare.")
            else:
                total_lbl.configure(text=f"ℹ  Dal {s_d.strftime('%d/%m/%Y')} al {e_d.strftime('%d/%m/%Y')}: {len(hours)} report orari totali.")
            error_var.set("")
        except Exception as e:
            total_lbl.configure(text="⚠ Intervallo non valido")
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
        description="SCADA Automation v0.8 — Estrazione automatizzata report SCADA via GUI / CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  # Giorno singolo (scarica tutte le 24 ore del 2026-08-05):
  python scada_automation_v0.8.py -sd 2026-08-05

  # Intervallo di date con ore specifiche:
  python scada_automation_v0.8.py -sd 2026-08-01 -st 08 -ed 2026-08-05 -et 18

  # Anteprima senza esecuzione (dry-run):
  python scada_automation_v0.8.py -sd 01/08/2026 -ed 05/08/2026 --dry-run

  # Modalità continua (scarica l'intervallo e continua il monitoraggio ogni ora):
  python scada_automation_v0.8.py -sd 2026-08-05 -c
"""
    )
    parser.add_argument("-sd", "--start-date", dest="start_date", help="Data di inizio (es. YYYY-MM-DD o DD/MM/YYYY)")
    parser.add_argument("-st", "--start-time", dest="start_time", help="Ora/Orario di inizio (0-23 o HH:MM). Default: 0")
    parser.add_argument("-ed", "--end-date", dest="end_date", help="Data di fine (es. YYYY-MM-DD o DD/MM/YYYY). Se omessa, equivale alla data di inizio (giorno singolo)")
    parser.add_argument("-et", "--end-time", dest="end_time", help="Ora/Orario di fine (0-23 o HH:MM). Default: 23")
    parser.add_argument("-c", "--continuous", action="store_true", help="Continua l'automazione oraria dopo l'estrazione dell'intervallo")
    parser.add_argument("-o", "--output-dir", dest="output_dir", help="Cartella di destinazione salvataggio file (sovrascrive PATH_TO_ORI_FOLDER)")
    parser.add_argument("--delay-load", type=int, dest="delay_load", help="Tempo di attesa caricamento dati in secondi (default: 80)")
    parser.add_argument("--delay-save", type=int, dest="delay_save", help="Tempo di attesa salvataggio file in secondi (default: 80)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra l'elenco dei report che verrebbero scaricati ed esce senza avviare SCADA")
    parser.add_argument("--gui", action="store_true", help="Forza l'apertura dell'interfaccia grafica (GUI) anche se sono passati parametri da riga di comando")

    return parser.parse_args()


if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    args = parse_cli_args()

    # Override configurable parameters if passed
    if args.output_dir:
        PATH_TO_ORI_FOLDER = os.path.normpath(args.output_dir)
        print(f"[Config] Cartella output impostata a: {PATH_TO_ORI_FOLDER}")
    if args.delay_load is not None:
        DELAY_LOAD_DATA = args.delay_load
        print(f"[Config] DELAY_LOAD_DATA impostato a: {DELAY_LOAD_DATA}s")
    if args.delay_save is not None:
        DELAY_SAVE_FILE = args.delay_save
        print(f"[Config] DELAY_SAVE_FILE impostato a: {DELAY_SAVE_FILE}s")

    # Determine whether to use CLI params or GUI
    use_cli = bool(args.start_date) and not args.gui

    if use_cli:
        print("\n=== Modalità Riga di Comando (CLI) ===")
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
        print("\nApertura finestra di selezione date/ore...")
        start_date, start_hour, end_date, end_hour, continuous_mode = show_time_selection_dialog()

        if start_date is None or start_hour is None:
            current_status = "Operazione annullata dall'utente"
            print("Selezione annullata dall'utente. Uscita.")
            sys.exit(0)

    # Generate target hours list
    try:
        hours_to_process = generate_target_hours(start_date, start_hour, end_date, end_hour)
    except Exception as e:
        print(f"[Errore] Impossibile generare l'intervallo orario: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"Riepilogo Intervallo Dati:")
    print(f"  Data Inizio : {start_date} ore {start_hour:02d}:00")
    print(f"  Data Fine   : {end_date} ore {end_hour:02d}:00")
    print(f"  Totale report orari da scaricare: {len(hours_to_process)}")
    print(f"  Modalità continua dopo download : {'ATTIVA' if continuous_mode else 'DISATTIVA'}")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY-RUN] Report che verrebbero elaborati:")
        for d, h in hours_to_process:
            print(f"  - {d} {h:02d}:00")
        print(f"[DRY-RUN] Totale: {len(hours_to_process)} report. Uscita completata.")
        sys.exit(0)

    # If running in CLI mode without overlay yet, start overlay & hotkey listener
    if use_cli:
        show_overlay()
        start_hotkey_listener()
        print("=" * 60)
        print("Overlay attivo: pannello di stato visibile durante l'esecuzione.")
        print("Premi Ctrl+Alt+. in qualsiasi momento per interrompere l'automazione.")
        print("=" * 60)

    current_status = f"Estrazione {len(hours_to_process)} report..."
    print(f"\nAvvio elaborazione per {len(hours_to_process)} report orari...")

    # Initial setup
    current_status = "Configurazione iniziale..."
    if not perform_initial_setup():
        current_status = "Configurazione iniziale fallita"
        print("Configurazione iniziale della finestra SCADA fallita.")
        sys.exit(1)

    # Process all hours in specified range
    if hours_to_process:
        current_status = f"Recupero: 0/{len(hours_to_process)}"
        success_count = 0
        for idx, (target_date, target_hour) in enumerate(hours_to_process):
            if stop_event.is_set():
                current_status = "Recupero interrotto dall'utente"
                print("Operazione interrotta dall'utente.")
                break

            current_status = f"Recupero {idx + 1}/{len(hours_to_process)} — {target_date} ore {target_hour:02d}:00"

            if not ensure_scada_window_active():
                current_status = "Impossibile attivare finestra SCADA"
                print("Impossibile attivare la finestra SCADA, arresto in corso.")
                break

            perform_scada_prep()
            if process_hourly_report(target_date, target_hour):
                success_count += 1
                perform_reset()
                print("Attesa ripristino interfaccia...")
                time.sleep(2.0)
            else:
                current_status = f"Errore report {target_date} {target_hour:02d}:00"
                print(f"Errore durante il download del report {target_date} {target_hour:02d}:00")
                break

        print(f"\nDownload completato: {success_count}/{len(hours_to_process)} report elaborati.")
        current_status = f"Completato: {success_count}/{len(hours_to_process)} report"
        time.sleep(2)
    else:
        print("Nessun report da scaricare per l'intervallo specificato.")

    # Continue with continuous hourly automation if requested
    if continuous_mode and not stop_event.is_set():
        print("\nAvvio automazione oraria continua...")
        current_status = "Avvio automazione oraria continua"

        while not stop_event.is_set():
            next_trigger = get_next_trigger_time()
            target_hour = (next_trigger.hour - 1) % 24

            wait_seconds = (next_trigger - datetime.datetime.now()).total_seconds()
            if wait_seconds > 0:
                current_status = f"In attesa fino alle {next_trigger.strftime('%H:%M')} per ora {target_hour:02d}:00"
                print(f"In attesa fino alle {next_trigger.strftime('%H:%M')} per ora {target_hour:02d}:00")
                interruptible_sleep(wait_seconds)

            if stop_event.is_set():
                current_status = "Automazione interrotta dall'utente"
                break

            now = datetime.datetime.now()
            if next_trigger.hour == 0:
                target_date = now.date() - datetime.timedelta(days=1)
            else:
                target_date = now.date()

            print(f"Download report automatico per {target_date} {target_hour:02d}:00")
            current_status = f"Download report {target_date} {target_hour:02d}:00"
            if not ensure_scada_window_active():
                current_status = "Impossibile attivare finestra SCADA"
                print("Impossibile attivare la finestra SCADA, arresto in corso.")
                break
            perform_scada_prep()
            success = process_hourly_report(target_date, target_hour)
            if success:
                current_status = "Reset interfaccia..."
                perform_reset()
                print("Attesa ripristino interfaccia...")
                time.sleep(2.0)
                current_status = "Pronto per il prossimo report"
            else:
                current_status = "Download report fallito"
                print("Download report automatico fallito, arresto in corso.")
                break

    current_status = "Automazione completata"
    print("Automazione completata.")