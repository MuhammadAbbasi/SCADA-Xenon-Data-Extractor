import os
import sys
import datetime
import time
import threading
import tkinter as tk
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
# Shifted right ~23px to EXCLUDE the Wo (week-number) column.
# The Wo column contains 14-19 which confuses template matching for days 14-19.
# Top-Left: (804, 557), Bottom-Right: (963, 702)
DATE_SEARCH_REGION = (804, 557, 159, 145) # (left, top, width, height) -- excludes Wo week-number column

# Optional override coordinates for specific dates.
# If a specific date needs a manual click coordinate, add the date here
# in ISO format and the function will bypass OpenCV matching.
DATE_COORDINATE_OVERRIDES = {
    "2026-05-04": (793, 588),
}

# Calendar grid layout for fallback coordinate calculation.
# Grid: Wo | Mo | Di | Mi | Do | Fr | Sa | So  (8 cols, 6 rows)
# Column width = 182/8 ≈ 22.75 → Mo center = 781 + 22.75 + 11.4 ≈ 815
# Row height   = 145/6 ≈ 24.2  → first row center = 557 + 12.1 ≈ 569
CALENDAR_GRID_MONDAY_X  = 815  # x-center of the Monday (Mo) column
CALENDAR_GRID_FIRST_ROW_Y = 569 # y-center of the first visible week row

CALENDAR_CELL_W = 23            # pixels per day column
CALENDAR_CELL_H = 24            # pixels per week row

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
DELAY_LOAD_DATA = 80
DELAY_SAVE_FILE = 80
DELAY_CLOSE_SAVE = 20

# ---------------------------------------------------------------------------
# Screen border overlay + Ctrl+Alt+. stop hotkey
# ---------------------------------------------------------------------------

# --- Global status for overlay ---
current_status = "Initializing..."

def _overlay_worker():
    """Draws a professional status overlay with current task information."""
    try:
        root = tk.Tk()
        root.overrideredirect(True)          # no title bar / borders
        root.attributes('-topmost', True)    # always on top of everything
        root.attributes('-alpha', 0.9)       # slightly transparent
        
        # Position in top-right corner
        sw = root.winfo_screenwidth()
        overlay_width = 400
        overlay_height = 100
        x_pos = sw - overlay_width - 20
        y_pos = 20
        root.geometry(f"{overlay_width}x{overlay_height}+{x_pos}+{y_pos}")

        # Background frame
        frame = tk.Frame(root, bg='black', bd=2, relief='raised')
        frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Status label
        status_var = tk.StringVar(value=current_status)
        status_label = tk.Label(frame, text="SCADA Automation Status", font=('Arial', 12, 'bold'), fg='white', bg='black')
        status_label.pack(pady=(10,5))
        
        task_label = tk.Label(frame, textvariable=status_var, font=('Arial', 10), fg='yellow', bg='black', wraplength=380, justify='center')
        task_label.pack(pady=(0,10))

        # Animated border
        canvas = tk.Canvas(frame, width=overlay_width-10, height=overlay_height-10, bg='black', highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        T = 3  # thickness
        outer_rect = canvas.create_rectangle(2, 2, overlay_width-12, overlay_height-12, outline='red', width=T)
        inner_rect = canvas.create_rectangle(T+2, T+2, overlay_width-T-12, overlay_height-T-12, outline='blue', width=T)

        _tick = [0]

        def animate():
            _tick[0] ^= 1
            if _tick[0]:
                canvas.itemconfig(outer_rect, outline='red')
                canvas.itemconfig(inner_rect, outline='blue')
            else:
                canvas.itemconfig(outer_rect, outline='blue')
                canvas.itemconfig(inner_rect, outline='red')
            root.after(500, animate)

        def update_status():
            status_var.set(current_status)
            root.after(1000, update_status)  # Update every second

        def check_stop():
            if stop_event.is_set():
                root.destroy()
                return
            root.after(200, check_stop)

        root.after(500, animate)
        root.after(1000, update_status)
        root.after(200, check_stop)
        root.mainloop()
    except Exception as e:
        print(f"[Overlay] Error: {e}")

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
    """2. Maximize and focus."""
    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(1)
    except Exception as e:
        print(f"Error activating window: {e}")

    
    
    # Fallback: Press Win+Up to ensure maximization
    time.sleep(0.5)
    #pyautogui.hotkey('win', 'up')
    time.sleep(1)

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
    current_status = "Finding SCADA window..."
    max_attempts = 10  # Retry up to 10 times
    for attempt in range(max_attempts):
        window = find_scada_window()
        if window:
            current_status = "Activating SCADA window..."
            focus_scada_window(window)
            current_status = "SCADA window ready"
            return True
        print(f"SCADA window not found (attempt {attempt + 1}/{max_attempts}). Waiting 5 seconds...")
        time.sleep(5)
    current_status = "Failed to find SCADA window"
    print("Failed to find SCADA window after multiple attempts.")
    return False

def ensure_scada_window_active():
    """Ensure the SCADA window is active and in front."""
    global current_status
    current_status = "Ensuring SCADA window is active..."
    window = find_scada_window()
    if window:
        focus_scada_window(window)
        current_status = "SCADA window activated"
        return True
    else:
        current_status = "SCADA window not found"
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
    current_status = "Navigating to Analisi section..."
    pyautogui.click(COORDS_ANALISI)
    time.sleep(DELAY_ACTION)

    print("=== Step 4: Click Dropdown Selezione Intervallo ===")
    current_status = "Opening interval selection..."
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_DROPDOWN)
    time.sleep(0.5)

    print("=== Step 5: Click Scroll Up x5 ===")
    current_status = "Scrolling to ORA option..."
    for _ in range(5):
        pyautogui.click(COORDS_SELEZIONE_INTERVALLO_SCROLL_UP)
        time.sleep(0.1)
    
    print("=== Step 6: Click ORA ===")
    current_status = "Selecting ORA interval..."
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_ORA)
    time.sleep(DELAY_ACTION)
    current_status = "Interface prepared for report selection"
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
    print(f"Starting Process for {target_date} // {target_hour}:00")
    current_status = f"Processing report for {target_date} {target_hour}:00"

    # Calendar window should be open (or opens after ORA selection)
    
    print("=== Step 7: Click Month Dropdown ===")
    current_status = "Selecting month..."
    pyautogui.click(COORDS_MONTH_DROPDOWN)
    time.sleep(0.5)

    print(f"=== Step 8: Select Month ({target_date.month}) ===")
    month_coords = MONTH_COORDS.get(target_date.month)
    if month_coords:
        pyautogui.click(month_coords)
    else:
        current_status = f"Error: No coords for month {target_date.month}"
        print(f"Error: No coords for month {target_date.month}")
        return False
    time.sleep(0.5)

    print("=== Step 9: Select Year ===")
    current_status = "Selecting year..."
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
            current_status = f"Error: No coords for year {target_date.year}"
            print(f"Error: No coords for year {target_date.year}. Available: {list(YEAR_COORDS.keys())}")
            return False
    else:
        print(f"Year {target_date.year} is current year. No need to select.")
        
    time.sleep(0.5)

    print(f"=== Step 10: Select Date ({target_date.day}) ===")
    current_status = f"Selecting date {target_date.day}..."
    
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
            all_matches = find_all_matches_in_region(day_img, DATE_SEARCH_REGION, confidence=0.8)
            
            if all_matches:
                selected_match = select_best_date_match(all_matches, target_date)
                if selected_match:
                    pos = pyautogui.Point(selected_match[0], selected_match[1])
                    expected_x, expected_y = get_date_grid_coords(target_date)
                    distance = ((selected_match[0] - expected_x)**2 + (selected_match[1] - expected_y)**2) ** 0.5
                    print(f"Selected best match near expected grid ({expected_x},{expected_y}), distance={distance:.1f}, confidence={selected_match[2]:.2f}")
                else:
                    print(f"No best match could be chosen from {len(all_matches)} candidates.")
                    gx, gy = get_date_grid_coords(target_date)
                    pos = pyautogui.Point(gx, gy)
                    print(f"Grid fallback position: {pos}")
            else:
                # Fallback: calculate grid coordinates mathematically.
                # This avoids false matches with the week-number (Wo) column.
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
    current_status = "Resetting time selection..."
    # Click 20 times Scroll Up
    for _ in range(20):
        pyautogui.click(COORDS_TIME_SCROLL_UP)
        time.sleep(0.05)
    
    print(f"=== Step 13: Select Time {target_hour}:00 ===")
    current_status = f"Selecting time {target_hour}:00..."
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
            current_status = f"Error: No coords for hour {target_hour}"
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
    current_status = "Applying filters..."
    pyautogui.click(COORDS_FILTER_WINDOW_OK_BUTTON)

    print(f"=== Step 14: Wait for Load ({DELAY_LOAD_DATA}s) ===")
    current_status = f"Loading data... ({DELAY_LOAD_DATA}s)"
    interruptible_sleep(DELAY_LOAD_DATA)

    print("=== Step 15: Click Export ===")
    current_status = "Initiating export..."
    pyautogui.click(COORDS_ESPORTA_DATI_BUTTON)
    time.sleep(2.0) # Wait for dialog

    print("=== Step 16 & 17: Save File Logic ===")
    current_status = "Preparing save dialog..."
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

    pyautogui.write(full_path, interval=0.01)

    time.sleep(1.0)

    print("=== Step 18: Save and Wait ===")
    current_status = f"Saving... ({DELAY_SAVE_FILE}s)"
    pyautogui.click(COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON)
    interruptible_sleep(DELAY_SAVE_FILE)

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


if __name__ == "__main__":
    pyautogui.FAILSAFE = True

    # Start the status overlay and the stop hotkey listener
    show_overlay()
    start_hotkey_listener()
    print("=" * 60)
    print("Overlay active: status panel visible while running.")
    print("Press Ctrl+Alt+.  at any time to stop the automation.")
    print("=" * 60)

    # Initial setup
    current_status = "Performing initial setup..."
    if not perform_initial_setup():
        current_status = "Initial setup failed"
        print("Initial setup failed.")
        sys.exit(1)

    today = datetime.date.today()
    print(f"Starting hourly automation for {today}")
    current_status = f"Starting hourly automation for {today}"

    # First execution immediately on startup
    first_date, first_hour = get_first_run_target()
    print(f"Running first report immediately for {first_date} {first_hour}:00")
    current_status = f"Running first report for {first_hour}:00"
    if not ensure_scada_window_active():
        current_status = "Failed to activate SCADA window"
        print("Failed to activate SCADA window, stopping")
        sys.exit(1)

    perform_scada_prep()
    if not process_hourly_report(first_date, first_hour):
        current_status = "Failed first report"
        print("Failed to process first hourly report.")
        sys.exit(1)
    perform_reset()
    print("First report completed. Waiting for next scheduled run.")
    current_status = "First report completed"

    while not stop_event.is_set():
        now = datetime.datetime.now()
        next_trigger = get_next_trigger_time()
        target_hour = (next_trigger.hour - 1) % 24
        target_date = now.date()
        if next_trigger.hour == 0:
            target_date = now.date() - datetime.timedelta(days=1)

        wait_seconds = (next_trigger - datetime.datetime.now()).total_seconds()
        if wait_seconds > 0:
            current_status = f"Waiting until {next_trigger.strftime('%H:%M')} for hour {target_hour}:00"
            print(f"Waiting until {next_trigger} to download for hour {target_hour}:00")
            interruptible_sleep(wait_seconds)

        if stop_event.is_set():
            current_status = "Automation stopped by user"
            break

        print(f"Downloading report for {target_date} {target_hour}:00")
        current_status = f"Downloading report for {target_hour}:00"
        if not ensure_scada_window_active():
            current_status = "Failed to activate SCADA window"
            print("Failed to activate SCADA window, stopping")
            break
        perform_scada_prep()
        success = process_hourly_report(target_date, target_hour)
        if success:
            current_status = "Resetting interface..."
            perform_reset()
            print("Waiting for reset animation...")
            time.sleep(2.0)
            current_status = "Ready for next report"
        else:
            current_status = "Failed to download report"
            print("Failed to download, stopping")
            break

        # Stop after 23:00
        if target_hour == 23:
            current_status = "Completed all hours for the day"
            print("Downloaded last hour of the day, stopping.")
            break

    current_status = "Automation completed"
    print("Automation completed.")