import os
import datetime
import time
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw

# ---------------------------------------------------------------------------
# Configuration
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
    1: COORDS_MONTH_JAN,  2: COORDS_MONTH_FEB,  3: COORDS_MONTH_MAR,
    4: COORDS_MONTH_APR,  5: COORDS_MONTH_MAY,  6: COORDS_MONTH_JUN,
    7: COORDS_MONTH_JUL,  8: COORDS_MONTH_AUG,  9: COORDS_MONTH_SEP,
    10: COORDS_MONTH_OCT, 11: COORDS_MONTH_NOV, 12: COORDS_MONTH_DEC,
}

COORDS_YEAR_DROPDOWN    = (968, 431)
COORDS_YEAR_SCROLL_DOWN = (999, 913)
COORDS_YEAR_2025 = (952, 514)
COORDS_YEAR_2026 = (952, 531)
COORDS_YEAR_2027 = (952, 548)

YEAR_COORDS = {
    2025: COORDS_YEAR_2025,
    2026: COORDS_YEAR_2026,
    2027: COORDS_YEAR_2027,
}

# Full calendar region including week-number column — same as working version
DATE_SEARCH_REGION = (781, 557, 182, 145)

COORDS_TIME_SCROLL_UP   = (1043, 547)
COORDS_TIME_SCROLL_DOWN = (1043, 677)

COORDS_TIME_SELECTION_BASE = (1011, 661)
COORDS_TIME_SELECTION_0000 = (1011, 563)
COORDS_TIME_SELECTION_0100 = (1011, 585)
COORDS_TIME_SELECTION_0200 = (1011, 609)
COORDS_TIME_SELECTION_0300 = (1011, 624)
COORDS_TIME_SELECTION_0400 = (1011, 644)
COORDS_TIME_SELECTION_0500 = (1011, 661)

COORDS_ESPORTA_DATI_BUTTON       = (1469, 158)
COORDS_FILE_SAVE_DIALOG_FILENAME = (1140, 700)
COORDS_FILE_SAVE_DIALOG_SAVE_BUTTON = (1267, 702)
COORDS_FILE_SAVE_DIALOG_CLOSE_BUTTON = (867, 588)

DELAY_ACTION    = 1.0
DELAY_LOAD_DATA = 80
DELAY_SAVE_FILE = 80
DELAY_CLOSE_SAVE = 20


# ---------------------------------------------------------------------------

def find_scada_window():
    windows = gw.getWindowsWithTitle(SCADA_WINDOW_TITLE_PARTIAL)
    if not windows:
        print(f"Window '{SCADA_WINDOW_TITLE_PARTIAL}' not found.")
        return None
    return windows[0]


def focus_scada_window(window):
    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(1)
    except Exception as e:
        print(f"Error activating window: {e}")
    time.sleep(0.5)
    time.sleep(1)


def find_image_in_region(image_name, region, confidence=0.6):
    try:
        screenshot = pyautogui.screenshot(region=region)
        haystack_bgr  = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        haystack_gray = cv2.cvtColor(haystack_bgr, cv2.COLOR_BGR2GRAY)
        haystack_edges = cv2.Canny(haystack_gray, 50, 200)
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None

    path = os.path.join(ASSETS_DIR, f"{image_name}.png")
    if not os.path.exists(path):
        print(f"Asset missing: {path}")
        return None

    template_bgr  = cv2.imread(path)
    if template_bgr is None:
        return None
    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

    # Strategy 1: standard grayscale
    try:
        res_std = cv2.matchTemplate(haystack_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val_s, max_val_s, min_loc_s, max_loc_s = cv2.minMaxLoc(res_std)
        print(f"Search '{image_name}' (Standard): Score={max_val_s:.2f} at {max_loc_s}")
        if max_val_s >= 0.80:
            h, w = template_gray.shape[:2]
            gx = region[0] + max_loc_s[0] + w // 2
            gy = region[1] + max_loc_s[1] + h // 2
            print(f"Found Standard match for {image_name} at ({gx}, {gy})")
            return pyautogui.Point(gx, gy)
    except Exception as e:
        print(f"Standard Match error: {e}")

    # Strategy 2: Canny edge fallback
    try:
        haystack_edges = cv2.Canny(haystack_gray, 50, 200)
        template_edges = cv2.Canny(template_gray, 50, 200)
        res = cv2.matchTemplate(haystack_edges, template_edges, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        print(f"Search '{image_name}' (Edges): Score={max_val:.2f} at {max_loc}")
        if max_val >= 0.80:
            h, w = template_gray.shape[:2]
            gx = region[0] + max_loc[0] + w // 2
            gy = region[1] + max_loc[1] + h // 2
            print(f"Found Edge match for {image_name} at ({gx}, {gy})")
            return pyautogui.Point(gx, gy)
    except Exception as e:
        print(f"Edge Match error: {e}")

    return None


def check_color_is_black_bg_white_text(x, y):
    try:
        screenshot = pyautogui.screenshot(region=(int(x) - 2, int(y) - 2, 5, 5))
        img = np.array(screenshot)
        avg_color = np.mean(img)
        print(f"Color check at ({x},{y}): Avg Brightness = {avg_color}")
        if avg_color < 100:
            print("Confirmed dark background.")
            return True
        else:
            print("Warning: Background seems bright.")
            return False
    except Exception as e:
        print(f"Color check failed: {e}")
        return False


def perform_initial_setup():
    print("=== Step 1 & 2: Window Management ===")
    window = find_scada_window()
    if not window:
        return False
    focus_scada_window(window)
    return True


def perform_reset():
    print("Resetting to normal selection mode.")
    pyautogui.press('esc')
    time.sleep(0.5)


def perform_scada_prep():
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


def process_hourly_report(target_date, target_hour):
    print(f"Starting Process for {target_date} // {target_hour}:00")

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
    if target_date.year != datetime.date.today().year:
        pyautogui.click(COORDS_YEAR_DROPDOWN)
        time.sleep(0.5)
        print("Scrolling Year to bottom (40 clicks)...")
        for _ in range(40):
            pyautogui.click(COORDS_YEAR_SCROLL_DOWN)
            time.sleep(0.02)
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
    if target_date == datetime.date.today():
        print(f"Target date {target_date} is TODAY. Skipping selection (already selected).")
    else:
        print(f"Searching for day {target_date.day} using OpenCV...")
        day_img = f"day_{target_date.day}"
        pos = find_image_in_region(day_img, DATE_SEARCH_REGION, confidence=0.65)
        if pos:
            print(f"Found {day_img} at {pos}. Clicking...")
            pyautogui.click(pos)
            time.sleep(0.5)
            print("=== Step 11: Color Verification ===")
            check_color_is_black_bg_white_text(pos.x, pos.y)
        else:
            print(f"Error: Could not find image for day {target_date.day} in search region.")
            print("Aborting to avoid wrong date selection.")
            return False

    print("=== Step 12: Time Selection - Reset to Min ===")
    for _ in range(20):
        pyautogui.click(COORDS_TIME_SCROLL_UP)
        time.sleep(0.05)

    print(f"=== Step 13: Select Time {target_hour}:00 ===")
    if target_hour < 5:
        early_coords = {
            0: COORDS_TIME_SELECTION_0000,
            1: COORDS_TIME_SELECTION_0100,
            2: COORDS_TIME_SELECTION_0200,
            3: COORDS_TIME_SELECTION_0300,
            4: COORDS_TIME_SELECTION_0400,
        }
        coords = early_coords.get(target_hour)
        if coords:
            print(f"Clicking specific coord for {target_hour}:00")
            pyautogui.click(coords)
        else:
            print(f"Error: No coords for hour {target_hour}")
            return False
    else:
        scrolls_needed = target_hour - 5
        if scrolls_needed < 0:
            scrolls_needed = 0
        if scrolls_needed > 0:
            print(f"Scrolling down {scrolls_needed} times for {target_hour}:00")
            for _ in range(scrolls_needed):
                pyautogui.click(COORDS_TIME_SCROLL_DOWN)
                time.sleep(0.1)
        else:
            print(f"No scrolling needed for {target_hour}:00 (05:00 Base)")
        pyautogui.click(COORDS_TIME_SELECTION_BASE)
    time.sleep(0.5)

    print("Clicking OK Filter Button...")
    pyautogui.click(COORDS_FILTER_WINDOW_OK_BUTTON)

    print(f"=== Step 14: Wait for Load ({DELAY_LOAD_DATA}s) ===")
    time.sleep(DELAY_LOAD_DATA)

    print("=== Step 15: Click Export ===")
    pyautogui.click(COORDS_ESPORTA_DATI_BUTTON)
    time.sleep(2.0)

    print("=== Step 16 & 17: Save File Logic ===")
    pyautogui.click(COORDS_FILE_SAVE_DIALOG_FILENAME)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)

    year_str  = str(target_date.year)
    month_str = f"{target_date.month:02d}"
    day_str   = f"{target_date.day:02d}"
    hh_str    = f"{target_hour:02d}"
    jj = target_hour + 1
    if jj == 24:
        jj = 0
    jj_str = f"{jj:02d}"

    date_dash = f"{year_str}-{month_str}-{day_str}"
    filename  = f"{day_str}_{month_str}_{year_str}_{hh_str}_{jj_str}.csv"
    full_path = os.path.join(PATH_TO_ORI_FOLDER, year_str, month_str, date_dash, filename)
    full_path = os.path.normpath(full_path)
    print(f"Saving to: {full_path}")

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

    print(f"Task Completed FOR {target_hour}:00")
    return True


def run_bulk_automation(target_date, start_hour=0, end_hour=24):
    if not perform_initial_setup():
        print("Initial setup failed.")
        return

    for current_hour in range(start_hour, end_hour):
        print(f"\n--- PROCESSING HOUR {current_hour}:00 ---")
        time.sleep(1.0)
        perform_scada_prep()
        success = process_hourly_report(target_date, current_hour)
        if not success:
            print(f"Failed to process hour {current_hour}:00. Stopping loop.")
            break
        perform_reset()
        print("Waiting for reset animation...")
        time.sleep(2.0)

    print("All tasks completed.")


def run_multiple_dates(start_date, num_days):
    """
    Run bulk automation for multiple consecutive dates.
    
    Args:
        start_date: datetime.date object for the first date to process
        num_days: Number of consecutive days to process
    """
    for i in range(num_days):
        current_date = start_date + datetime.timedelta(days=i)
        print(f"\n\n========== PROCESSING {current_date} ==========\n")
        try:
            run_bulk_automation(current_date, start_hour=0, end_hour=24)
            print(f"✓ Completed {current_date}")
        except Exception as e:
            print(f"✗ Failed on {current_date}: {e}")
            break

    print(f"\n\n========== ALL {num_days} DATES COMPLETED ==========\n")


if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    # Single date example:
    # run_bulk_automation(datetime.date(2026, 4, 28), start_hour=0, end_hour=24)
    
    # Multiple dates example:
    run_multiple_dates(datetime.date(2026, 4, 29), num_days=6)  # Runs Apr 28-29
