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
    "2026-05-11": (793, 609),
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

def _overlay_worker():
    """Draws a red+blue animated border over the full screen while running."""
    try:
        root = tk.Tk()
        root.overrideredirect(True)          # no title bar / borders
        root.attributes('-topmost', True)    # always on top of everything
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{sw}x{sh}+0+0")

        # Use a unique colour as the transparency key so the interior is see-through
        TRANS = '#010203'
        root.wm_attributes('-transparentcolor', TRANS)
        root.configure(bg=TRANS)

        canvas = tk.Canvas(root, width=sw, height=sh, bg=TRANS, highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        T = 7  # thickness of each colour band
        outer = canvas.create_rectangle(1, 1, sw - 2, sh - 2,   outline='red',  width=T)
        inner = canvas.create_rectangle(T + 1, T + 1, sw - T - 2, sh - T - 2,
                                        outline='blue', width=T)

        _tick = [0]

        def animate():
            _tick[0] ^= 1
            if _tick[0]:
                canvas.itemconfig(outer, outline='red')
                canvas.itemconfig(inner, outline='blue')
            else:
                canvas.itemconfig(outer, outline='blue')
                canvas.itemconfig(inner, outline='red')
            root.after(500, animate)

        def check_stop():
            if stop_event.is_set():
                root.destroy()
                return
            root.after(200, check_stop)

        root.after(500, animate)
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
            print(f"Found Standard match for {image_name} at ({gx}, {gy})")
            return pyautogui.Point(gx, gy)
    except Exception as e:
        print(f"Standard Match error: {e}")

    # --- STRATEGY 2: Edge Detection (Fallback) ---
    # Used for "Selected" state (White Text on Dark BG) where pixel match fails.
    # WARNING: Can produce false positives (e.g. 19 matching 10). Needs STRICT confidence.
    try:
        # Calculate Edges
        haystack_edges = cv2.Canny(haystack_gray, 50, 200)
        template_edges = cv2.Canny(template_gray, 50, 200)

        res = cv2.matchTemplate(haystack_edges, template_edges, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        print(f"Search '{image_name}' (Edges): Score={max_val:.2f} at {max_loc}")
        
        # Must be strict (> 0.80) to avoid confusion (10 vs 19)
        if max_val >= 0.80:
            h, w = template_gray.shape[:2]
            gx = region[0] + max_loc[0] + w//2
            gy = region[1] + max_loc[1] + h//2
            print(f"Found Edge match for {image_name} at ({gx}, {gy})")
            return pyautogui.Point(gx, gy)
            
    except Exception as e:
        print(f"Edge Match error: {e}")

    return None

def find_all_matches_in_region(image_name, region, confidence=0.8):
    """
    Finds ALL matches of an image in a region.
    Returns a list of tuples: [(x, y, score), ...] sorted by position (top-left to bottom-right).
    This handles cases where the same date appears multiple times (e.g., calendar overflow from adjacent months).
    """
    matches = []
    
    # 1. Capture Screenshot
    try:
        screenshot = pyautogui.screenshot(region=region)
        haystack_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        haystack_gray = cv2.cvtColor(haystack_bgr, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return matches
    
    # 2. Load Template
    path = os.path.join(ASSETS_DIR, f"{image_name}.png")
    if not os.path.exists(path):
        print(f"Asset missing: {path}")
        return matches
    
    template_bgr = cv2.imread(path)
    if template_bgr is None: 
        return matches
    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    h, w = template_gray.shape[:2]
    
    # --- STRATEGY 1: Standard Template Matching ---
    try:
        res_std = cv2.matchTemplate(haystack_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        # Find all matches above threshold
        threshold = confidence
        locations = np.where(res_std >= threshold)
        
        for loc_idx in range(len(locations[0])):
            y_offset = locations[0][loc_idx]
            x_offset = locations[1][loc_idx]
            score = res_std[y_offset, x_offset]
            
            # Convert to screen coordinates
            gx = region[0] + x_offset + w // 2
            gy = region[1] + y_offset + h // 2
            matches.append((gx, gy, score))
        
        if matches:
            print(f"Standard match found {len(matches)} instance(s) of '{image_name}': {matches}")
            matches = dedupe_matches(matches)
            return matches
    except Exception as e:
        print(f"Standard Match error: {e}")
    
    # --- STRATEGY 2: Edge Detection (Fallback) ---
    try:
        haystack_edges = cv2.Canny(haystack_gray, 50, 200)
        template_edges = cv2.Canny(template_gray, 50, 200)
        
        res = cv2.matchTemplate(haystack_edges, template_edges, cv2.TM_CCOEFF_NORMED)
        threshold = confidence
        locations = np.where(res >= threshold)
        
        for loc_idx in range(len(locations[0])):
            y_offset = locations[0][loc_idx]
            x_offset = locations[1][loc_idx]
            score = res[y_offset, x_offset]
            
            # Convert to screen coordinates
            gx = region[0] + x_offset + w // 2
            gy = region[1] + y_offset + h // 2
            matches.append((gx, gy, score))
        
        if matches:
            print(f"Edge match found {len(matches)} instance(s) of '{image_name}': {matches}")
            matches = dedupe_matches(matches)
            return matches
    except Exception as e:
        print(f"Edge Match error: {e}")
    
    return matches

def dedupe_matches(matches, min_distance=16):
    """
    Remove duplicate or overlapping match positions by keeping the highest-confidence match
    within a minimum pixel distance.
    """
    unique = []
    for x, y, score in sorted(matches, key=lambda m: -m[2]):
        if not any((x - ux)**2 + (y - uy)**2 < min_distance**2 for ux, uy, _ in unique):
            unique.append((x, y, score))
    unique.sort(key=lambda m: (m[1], m[0]))
    return unique


def select_best_date_match(matches, target_date):
    """
    Choose the matched date position closest to the expected calendar grid position for the target date.
    """
    if not matches:
        return None
    expected_x, expected_y = get_date_grid_coords(target_date)
    best_match = min(matches, key=lambda m: (m[0] - expected_x)**2 + (m[1] - expected_y)**2)
    return best_match


def get_date_override_coords(target_date):
    """
    Return override click coordinates for a specific date if configured.
    """
    key = target_date.isoformat()
    coords = DATE_COORDINATE_OVERRIDES.get(key)
    if coords:
        print(f"Override coordinates found for {key}: {coords}")
    return coords


def check_color_is_black_bg_white_text(x, y):
    """
    11. Check pixels at (x,y) or nearby to confirm black background.
    Simple heuristic: Check if pixel is dark.
    """
    # Capture a small 5x5 patch around the click point
    try:
        screenshot = pyautogui.screenshot(region=(int(x)-2, int(y)-2, 5, 5))
        # Convert to numpy
        img = np.array(screenshot)
        # Check average brightness
        avg_color = np.mean(img)
        print(f"Color check at ({x},{y}): Avg Brightness = {avg_color}")
        
        # Heuristic: If background is black, brightness should be low.
        # However, text is white. If we clicked the center of text, it might be bright.
        # User said: "check if it's color is changed to black background and text in white background"
        # This implies standard state might be different (e.g. white bg, black text).
        # We will log it. Strict checking might fail without calibration.
        if avg_color < 100:
            print("Confirmed dark background.")
            return True
        else:
            print("Warning: Background seems bright. Selection might not have worked or text is dominant.")
            return False
            
    except Exception as e:
        print(f"Color check failed: {e}")
        return False

def perform_initial_setup():
    """Execute Steps 1-6 (Initial Setup to reach 'Ora' selection)."""
    # NOTE: The User says Steps 3-6 must be done *every time*.
    # So this function will do Steps 1-2 (Find/Focus) 
    # and then the MAIN loop will call Steps 3-6.
    
    print("=== Step 1 & 2: Window Management ===")
    window = find_scada_window()
    if not window:
        return False
    focus_scada_window(window)
    return True

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
    print("=== Step 3: Click ANALISI ===")
    pyautogui.click(COORDS_ANALISI)
    time.sleep(DELAY_ACTION)

    print("=== Step 4: Click Dropdown Selezione Intervallo ===")
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_DROPDOWN)
    time.sleep(0.5)

    print("=== Step 5: Click Scroll Up x5 ===")
    for _ in range(5):
        pyautogui.click(COORDS_SELEZIONE_INTERVALLO_SCROLL_UP)
        time.sleep(0.1)
    
    print("=== Step 6: Click ORA ===")
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_ORA)
    time.sleep(DELAY_ACTION)
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
    print(f"Starting Process for {target_date} // {target_hour}:00")

    # Calendar window should be open (or opens after ORA selection)
    
    print("=== Step 7: Click Month Dropdown ===")
    pyautogui.click(COORDS_MONTH_DROPDOWN)
    time.sleep(0.5)

    print(f"=== Step 8: Select Month ({target_date.month}) ===")
    month_coords = MONTH_COORDS.get(target_date.month)
    if month_coords:
        pyautogui.click(month_coords)
    else:
        print(f"Error: No coords for month {target_date.month}")
        return False
    time.sleep(0.5)

    print("=== Step 9: Select Year ===")
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
            print(f"Error: No coords for year {target_date.year}. Available: {list(YEAR_COORDS.keys())}")
            return False
    else:
        print(f"Year {target_date.year} is current year. No need to select.")
        
    time.sleep(0.5)

    print(f"=== Step 10: Select Date ({target_date.day}) ===")
    
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
    # Click 20 times Scroll Up
    for _ in range(20):
        pyautogui.click(COORDS_TIME_SCROLL_UP)
        time.sleep(0.05)
    
    print(f"=== Step 13: Select Time {target_hour}:00 ===")
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
    pyautogui.click(COORDS_FILTER_WINDOW_OK_BUTTON)

    print(f"=== Step 14: Wait for Load ({DELAY_LOAD_DATA}s) ===")
    interruptible_sleep(DELAY_LOAD_DATA)

    print("=== Step 15: Click Export ===")
    pyautogui.click(COORDS_ESPORTA_DATI_BUTTON)
    time.sleep(2.0) # Wait for dialog

    print("=== Step 16 & 17: Save File Logic ===")
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
    pyautogui.click(COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON)
    interruptible_sleep(DELAY_SAVE_FILE)

    print(f"Task Completed FOR {target_hour}:00")
    return True

def run_bulk_automation(start_date, num_days=1, start_hour=6, end_hour=19):
    """
    Run full automation loop for multiple dates and hours.
    
    Args:
        start_date: Starting date (datetime.date)
        num_days: Number of days to process (default: 1)
        start_hour: Starting hour (default: 6)
        end_hour: Ending hour, exclusive (default: 19)
    
    Example: run_bulk_automation(datetime.date(2026, 3, 23), num_days=5, start_hour=0, end_hour=24)
    """
    # 1. Initial Setup (Window Find/Focus) - only once
    if not perform_initial_setup():
        print("Initial setup failed.")
        return

    # 2. Main Loop - iterate through each date
    for day_offset in range(num_days):
        if stop_event.is_set():
            print("[STOP] Automation stopped by user (Ctrl+Alt+.).")
            break

        current_date = start_date + datetime.timedelta(days=day_offset)
        print(f"\n{'='*60}\n--- PROCESSING DATE {current_date} ---\n{'='*60}")

        # 3. Process each hour for this date
        for current_hour in range(start_hour, end_hour):
            if stop_event.is_set():
                print("[STOP] Automation stopped by user (Ctrl+Alt+.).")
                break

            print(f"\n--- PROCESSING HOUR {current_hour}:00 ---")

            # Ensure we wait a moment before starting the loop's actions
            time.sleep(1.0)

            # Perform Steps 3-6 EVERY TIME as requested
            perform_scada_prep()

            success = process_hourly_report(current_date, current_hour)
            if not success:
                print(f"Failed to process hour {current_hour}:00. Stopping loop.")
                break

            # Simple reset
            perform_reset()
            print("Waiting for reset animation...")
            time.sleep(2.0)

        print(f"Date {current_date} completed.")

    print(f"\n{'='*60}\nAll tasks completed ({num_days} days processed).\n{'='*60}")

if __name__ == "__main__":
    pyautogui.FAILSAFE = True

    # Start the red/blue screen border overlay and the stop hotkey listener
    show_overlay()
    start_hotkey_listener()
    print("=" * 60)
    print("Overlay active: red+blue border visible while running.")
    print("Press Ctrl+Alt+.  at any time to stop the automation.")
    print("=" * 60)

    # April 17: hours 18-23 (18:00 to 23:00)
    if not stop_event.is_set():
        run_bulk_automation(datetime.date(2026, 5, 15), num_days=4, start_hour=00, end_hour=24)

    # April 18 & 19: full day (00:00 to 23:00)
    #if not stop_event.is_set():
    #    run_bulk_automation(datetime.date(2026, 4, 26), num_days=2, start_hour=0, end_hour=24)

    # Signal overlay to close
    stop_event.set()
    print("All done. Overlay closed.")


"add the ogni ora this logic that should start downloading data from previous days "
"and when they are completed, it starts downloading the next day data, and so on until it reaches the "
"current day data. For example, if I start the script on 17 April 2026 at 18:00, it should start downloading data from 17 April 2026 at 18:00 to 23:00, then it should start downloading data from 18 April 2026 at 00:00 to 23:00, then it should start downloading data overy hour"