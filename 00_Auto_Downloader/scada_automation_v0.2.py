import os
import sys
import datetime
import time
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw

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
# [(963,557),(963,682),(781,682),(781,557)]
# Top-Left: (781, 557), Bottom-Right: (963, 682)
DATE_SEARCH_REGION = (781, 557, 182, 125) # (left, top, width, height)

# 12. Time Selection
COORDS_TIME_SCROLL_UP = (1043, 547)
COORDS_TIME_SCROLL_DOWN = (1043, 677)

COORDS_TIME_SELECTION_BASE = (1011, 661)
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

COORDS_ESPORTA_DATI_BUTTON = (1469, 158)

# 16. Save Dialog
COORDS_FILE_SAVE_DIALOG_FILENAME = (1140, 700)
COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON = (1267, 702)
COORDS_FILE_SAVE_DIALOG_CLOSE_BUTTON = (867, 588)



# Time to wait between actions
DELAY_ACTION = 1.0
DELAY_LOAD_DATA = 180
DELAY_SAVE_FILE = 180
DELAY_CLOSE_SAVE = 180

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
    
    # Apply Canny Edge Detection to Template
    template_edges = cv2.Canny(template_gray, 50, 200)
    
    # 3. Match Edges
    try:
        res = cv2.matchTemplate(haystack_edges, template_edges, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        print(f"Search '{image_name}' (Edges): Score={max_val:.2f} at {max_loc}")
        
        if max_val >= confidence:
            h, w = template_gray.shape[:2]
            gx = region[0] + max_loc[0] + w//2
            gy = region[1] + max_loc[1] + h//2
            print(f"Found Edge match for {image_name} at ({gx}, {gy})")
            return pyautogui.Point(gx, gy)
            
    except Exception as e:
        print(f"Match template error: {e}")
        return None

    return None

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

def run_automation(target_date=None, target_hour=6):
    if target_date is None:
        target_date = datetime.date.today()

    print("=== Step 1 & 2: Window Management ===")
    window = find_scada_window()
    if not window:
        return
    focus_scada_window(window)

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

    # Calendar window should be open now

    print("=== Step 7: Click Month Dropdown ===")
    pyautogui.click(COORDS_MONTH_DROPDOWN)
    time.sleep(0.5)

    print(f"=== Step 8: Select Month ({target_date.month}) ===")
    month_coords = MONTH_COORDS.get(target_date.month)
    if month_coords:
        pyautogui.click(month_coords)
    else:
        print(f"Error: No coords for month {target_date.month}")
        return
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
            return
    else:
        print(f"Year {target_date.year} is current year. No need to select.")
        
    time.sleep(0.5)

    print(f"=== Step 10: Select Date ({target_date.day}) using OpenCV ===")
    day_img = f"day_{target_date.day}"
    # Search in specific rectangle
    pos = find_image_in_region(day_img, DATE_SEARCH_REGION, confidence=0.80)
    
    if pos:
        print(f"Found {day_img} at {pos}. Clicking...")
        pyautogui.click(pos)
        time.sleep(0.5)
        
        # Step 11: Color Check
        print("=== Step 11: Color Verification ===")
        check_color_is_black_bg_white_text(pos.x, pos.y)
    else:
        print(f"Error: Could not find image for day {target_date.day} in search region.")
        # Fallback or Exit? Proceeding might result in wrong data.
        print("Aborting to avoid wrong date selection.")
        return

    print("=== Step 12: Time Selection - Reset to Min ===")
    # Click 20 times Scroll Up
    for _ in range(20):
        pyautogui.click(COORDS_TIME_SCROLL_UP)
        time.sleep(0.05)
    
    print(f"=== Step 13: Select Time {target_hour}:00 ===")
    # Logic: Click Scroll Down (Hour - 6 + 1) times? 
    # Prompt says: "click 1 time COORDS_TIME_SCROLL_DOWN and then click selection... to select 06:00"
    # "if we need 07:00, click 2 times ... instead of one"
    # Base is 06:00 -> 1 click.
    # 07:00 -> 2 clicks.
    # Formula: clicks = (target_hour - 6) + 1
    # Assuming valid hours >= 6.
    
    clicks_needed = (target_hour - 6) + 1
    if clicks_needed < 1: 
        clicks_needed = 1 # Safety, though logic implies start at 6
    
    print(f"Scrolling down {clicks_needed} times for {target_hour}:00")
    for _ in range(clicks_needed):
        pyautogui.click(COORDS_TIME_SCROLL_DOWN)
        time.sleep(0.1)
    
    # Click the selection
    pyautogui.click(COORDS_TIME_SELECTION_BASE)
    time.sleep(0.5)
    
    print("Clicking OK Filter Button...")
    pyautogui.click(COORDS_FILTER_WINDOW_OK_BUTTON)

    print(f"=== Step 14: Wait for Load ({DELAY_LOAD_DATA}s) ===")
    time.sleep(DELAY_LOAD_DATA)

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
    jj_str = f"{jj:02d}"
    
    date_dash = f"{year_str}-{month_str}-{day_str}"
    filename = f"{day_str}_{month_str}_{year_str}_{hh_str}_{jj_str}.csv"
    
    full_path = os.path.join(PATH_TO_ORI_FOLDER, year_str, month_str, date_dash, filename)
    full_path = os.path.normpath(full_path) # Normalize for Windows (backslashes)
    print(f"Saving to: {full_path}")
    
    # Ensure directory exists? Automation usually types into "File Name" box.
    # If standard Windows save dialog, typing full path works IF the directory exists.
    # If the directory does NOT exist, Windows might error or ask to create.
    # Python script should probably ensure these dirs exist locally first?
    # User instruction says: "Write this path ... inside this folder, save the file"
    # This implies we type the full path into the dialog.
    # We should ensure the folder exists on disk if it's a local path.
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
    time.sleep(DELAY_SAVE_FILE)

    print("Task Completed FOR this file.")
    print("Resetting to normal selection mode.")
    pyautogui.press('esc')
    time.sleep(0.5)
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_DROPDOWN)
    time.sleep(0.5)
    for _ in range(5):
        pyautogui.click(COORDS_SELEZIONE_INTERVALLO_SCROLL_UP)
        time.sleep(0.1)
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO_SELEZIONE_L_ORA)
    time.sleep(0.5)

if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    # Example usage: Select Today at 06:00
    # or override: run_automation(datetime.date(2025, 2, 12), 7)
    run_automation(datetime.date(2026, 2, 11))
