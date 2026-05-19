import cv2
import numpy as np
import pyautogui
import os
import time
import pygetwindow as gw

ASSETS_DIR = r"\\s01\get\2025.01 Mazara 01 A2A\03 - REPORT\Report\04 Tracker report\00_Auto_Downloader\assets"
SCADA_WINDOW_TITLE_PARTIAL = "SCADA Web Client Starter"

def focus_scada_window():
    """Focuses and maximizes the SCADA window."""
    try:
        windows = gw.getWindowsWithTitle(SCADA_WINDOW_TITLE_PARTIAL)
        if not windows:
            print(f"Window '{SCADA_WINDOW_TITLE_PARTIAL}' not found.")
            return False
        
        window = windows[0]
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(1)
        
        # Ensure maximization
        # window.maximize() 
        # time.sleep(1)
        return True
    except Exception as e:
        print(f"Error focusing window: {e}")
        return False

def debug_find_date(day_num):
    image_name = f"day_{day_num}"
    
    # 0. Focus Window
    if not focus_scada_window():
        print("Cannot find/focus SCADA window breakdown. Searching full screen anyway...")
    else:
        print("SCADA Window focused.")

    # 1. Capture Full Screen
    print(f"Debugging detection for: {image_name} on FULL SCREEN")
    
    try:
        screenshot = pyautogui.screenshot()
        # Save screenshot for verifying what the script "sees"
        screenshot.save("debug_screen_view.png")
        print("Captured debug_screen_view.png")

        haystack_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        haystack_gray = cv2.cvtColor(haystack_bgr, cv2.COLOR_BGR2GRAY)
        haystack_edges = cv2.Canny(haystack_gray, 50, 200)
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return

    # 2. Load Template
    path = os.path.join(ASSETS_DIR, f"{image_name}.png")
    if not os.path.exists(path):
        print(f"Asset missing: {path}")
        return
    
    template_bgr = cv2.imread(path)
    if template_bgr is None:
        print("Failed to load template image")
        return
        
    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    template_edges = cv2.Canny(template_gray, 50, 200)

    # 3. Match Edges
    try:
        res = cv2.matchTemplate(haystack_edges, template_edges, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        print(f"--- EDGE METHOD RESULTS ---")
        print(f"Max Score: {max_val:.4f}")
        print(f"Location: {max_loc}")
        
    except Exception as e:
        print(f"Match error (Edges): {e}")

    # 4. Match Standard Grayscale
    try:
        res = cv2.matchTemplate(haystack_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        print(f"--- GRAYSCALE METHOD RESULTS ---")
        print(f"Max Score: {max_val:.4f}")
        print(f"Location: {max_loc}")
        
    except Exception as e:
        print(f"Match error (Grayscale): {e}")

if __name__ == "__main__":
    debug_find_date(15)
