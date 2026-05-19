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
        return True
    except Exception as e:
        print(f"Error focusing window: {e}")
        return False

def check_match(image_name, haystack_edges, haystack_gray, screen_bgr):
    path = os.path.join(ASSETS_DIR, f"{image_name}.png")
    if not os.path.exists(path):
        print(f"Asset missing: {path}")
        return
    
    template_bgr = cv2.imread(path)
    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    template_edges = cv2.Canny(template_gray, 50, 200)

    # Edge Match
    res_edge = cv2.matchTemplate(haystack_edges, template_edges, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res_edge)
    
    print(f"\n--- {image_name} DETECTION ---")
    print(f"EDGE Score: {max_val:.4f} at {max_loc}")
    
    # Draw on debug image (Red for Edge match)
    h, w = template_gray.shape[:2]
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    cv2.rectangle(screen_bgr, top_left, bottom_right, (0, 0, 255), 2)
    cv2.putText(screen_bgr, f"{image_name} Edge:{max_val:.2f}", (top_left[0], top_left[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

    # Standard Match
    res_std = cv2.matchTemplate(haystack_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val_s, max_val_s, min_loc_s, max_loc_s = cv2.minMaxLoc(res_std)
    
    print(f"STD Score : {max_val_s:.4f} at {max_loc_s}")
    
    # Draw on debug image (Green for Std match)
    top_left_s = max_loc_s
    bottom_right_s = (top_left_s[0] + w, top_left_s[1] + h)
    cv2.rectangle(screen_bgr, top_left_s, bottom_right_s, (0, 255, 0), 2)
    cv2.putText(screen_bgr, f"{image_name} Std:{max_val_s:.2f}", (top_left_s[0], top_left_s[1]+h+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

def run_debug():
    if not focus_scada_window():
        print("Window not found, capturing full screen anyway.")

    screenshot = pyautogui.screenshot()
    haystack_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    haystack_gray = cv2.cvtColor(haystack_bgr, cv2.COLOR_BGR2GRAY)
    haystack_edges = cv2.Canny(haystack_gray, 50, 200)
    
    debug_img = haystack_bgr.copy()

    check_match("day_16", haystack_edges, haystack_gray, debug_img)
    check_match("day_19", haystack_edges, haystack_gray, debug_img)
    
    cv2.imwrite("debug_16_vs_19.png", debug_img)
    print("\nSaved visualization to debug_16_vs_19.png")

if __name__ == "__main__":
    run_debug()
