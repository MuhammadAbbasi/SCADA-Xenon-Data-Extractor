import os
import sys
import datetime
import pygetwindow as gw
import pyautogui
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2
import time

# --- Configuration ---
SCADA_WINDOW_TITLE_PARTIAL = "SCADA Web Client Starter"  
# Coordinates provided by user - These are initial clicks to open the popup
COORDS_ANALISI_TAB = (943, 96)
COORDS_SELEZIONE_INTERVALLO = (1212, 184)
COORDS_ORA_OPTION = (1057, 238)
COORDS_OK_BUTTON = (1060, 360)

# Time to wait between actions
ACTION_DELAY = 1.0

def find_scada_window(title_part):
    windows = gw.getWindowsWithTitle(title_part)
    if not windows:
        return None
    return windows[0]

def focus_scada_window(window):
    if window.isMinimized:
        window.restore()
    window.activate()
    time.sleep(1) # Wait for window to restore/activate
    # Maximize to ensure coordinates are correct relative to screen
    try:
        window.maximize()
    except:
        pass # Some windows might not support maximize
    time.sleep(1) 



# Image Recognition Settings
ASSETS_DIR = "assets"

def find_image(image_name, confidence=0.8):
    """Finds an image center on screen."""
    path = os.path.join(ASSETS_DIR, f"{image_name}.png")
    if not os.path.exists(path):
        print(f"Warning: Asset {image_name} not found at {path}")
        return None
    try:
        return pyautogui.locateCenterOnScreen(path, confidence=confidence)
    except Exception as e:
        # print(f"Error locating {image_name}: {e}")
        return None

def click_image(image_name, retries=3):
    """Finds and clicks an image."""
    for _ in range(retries):
        pos = find_image(image_name)
        if pos:
            print(f"Clicking {image_name} at {pos}")
            pyautogui.click(pos)
            return True
        time.sleep(0.5)
    print(f"Failed to find {image_name}")
    return False

def select_date_and_time(target_date=None, target_time="06:00"):
    """
    Selects date and time using image recognition and scrolling logic.
    """
    if target_date is None:
        target_date = datetime.date.today()
    
    print(f"Goal: Select date {target_date} and time {target_time}")

    # --- DATE SELECTION ---
    # 1. Select Month
    print("Selecting Month...")
    if click_image("month_dropdown"):
        time.sleep(0.5)
        # Assuming standard dropdown, we can type the month name
        month_name = target_date.strftime("%B") # Full month name e.g., "October"
        # Note: Locale might matter here. If Italian, we need Italian month names.
        # User is likely Italian (Mazara, A2A).
        # Mapping for now (expand as needed or rely on user system locale)
        months_it = {
            1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
        }
        month_str = months_it.get(target_date.month, month_name)
        
        pyautogui.write(month_str, interval=0.1)
        pyautogui.press('enter')
        time.sleep(0.5)

    # 2. Select Year
    print("Selecting Year...")
    if click_image("year_dropdown"):
        time.sleep(0.5)
        pyautogui.write(str(target_date.year), interval=0.3)
        pyautogui.press('enter')
        time.sleep(0.5)

    # 3. Select Day
    # User: "select the day as seen in the calender window"
    # To click the specific number, we ideally need an image of that number.
    # FALLBACK: Typing the full date often works if focus is right, but here we try logic.
    # If we don't have images for days, we might fallback to just clicking "Today" if available,
    # or relying on the user to have clicked it if manual intervention is okay.
    # IMPLEMENTATION: Try to click the specific day image if it exists (e.g., "day_27.png").
    day_img = f"day_{target_date.day}"
    if find_image(day_img):
        click_image(day_img)
    else:
        print(f"Day image '{day_img}.png' not found. Trying to type date as fallback...")
        # Try finding a generic "Date Input" field if possible, or just type blind
        # click_image("date_input_field") 
        pyautogui.write(target_date.strftime(f"{target_date.day}/{target_date.month}/{target_date.year}"))

    # --- TIME SELECTION ---
    # User: "search for it by going up or down using scroll buttons"
    print(f"Selecting Time: {target_time}")
    
    # 1. Check if visible immediately
    if click_image("time_0600"):
        print("Time selected found immediately.")
        return

    # 2. Strategy: Scroll UP to top to reset, then scroll DOWN searching.
    # Finds scroll buttons
    scroll_up = find_image("scroll_up")
    scroll_down = find_image("scroll_down")
    
    if not (scroll_up and scroll_down):
        print("Scroll buttons not found! Attempting blind PageUp/PageDown...")
        # Blind scroll
        # Pyautogui scroll might work if mouse is over the list
        # pyautogui.scroll(1000) 
        pass

    # Reset to top (optional, but safer)
    print("Scrolling to top...")
    if scroll_up:
         for _ in range(10): # Arbitrary limit
            pyautogui.click(scroll_up)
            time.sleep(0.1)
    
    # Scroll Down and Search
    print("Scrolling down to find time...")
    max_scrolls = 20
    for i in range(max_scrolls):
        if click_image("time_0600"):
           print("Time found and clicked.")
           return
        
        # Scroll down
        if scroll_down:
            pyautogui.click(scroll_down)
            time.sleep(0.2) # Wait for UI update
        else:
            pyautogui.press('down') # Fallback

    print(f"Could not find {target_time} after scrolling.")


def main():
    print("=== SCADA Automation Started ===")
    
    # Verify assets exist
    if not os.path.exists(ASSETS_DIR) or not os.listdir(ASSETS_DIR):
        print(f"\nCRITICAL: '{ASSETS_DIR}' folder is missing or empty!")
        print("Please run 'capture_assets.py' FIRST to capture the required buttons.")
        return

    print("Checking for SCADA window...")
    window = find_scada_window(SCADA_WINDOW_TITLE_PARTIAL)
    
    if not window:
        print(f"Error: Window containing '{SCADA_WINDOW_TITLE_PARTIAL}' not found.")
        print("Available titles:")
        for t in gw.getAllTitles():
            if t.strip(): print(f" - {t}")
        return

    print(f"Found window: {window.title}")
    focus_scada_window(window)
    
    # 1. Click ANALISI
    print(f"Clicking ANALISI at {COORDS_ANALISI_TAB}")
    pyautogui.click(COORDS_ANALISI_TAB)
    time.sleep(ACTION_DELAY)

    # 2. Click Dropdown "Selezione Intervallo"
    print(f"Clicking Selezione Intervallo at {COORDS_SELEZIONE_INTERVALLO}")
    pyautogui.click(COORDS_SELEZIONE_INTERVALLO)
    time.sleep(ACTION_DELAY)


    # 3. Select "ORA"
    print(f"Clicking ORA...")
    if not click_image("ora_text"):
        print(f"Image 'ora_text' not found. Clicking coordinate {COORDS_ORA_OPTION} as fallback.")
        pyautogui.click(COORDS_ORA_OPTION)
    
    time.sleep(2.0) # Wait for valid calendar window to appear
    
    # 4. Handle Calendar & Time
    target_date = datetime.date.today() 
    select_date_and_time(target_date, target_time="06:00")
    
    # 5. Click OK
    print(f"Clicking OK at {COORDS_OK_BUTTON}")
    pyautogui.click(COORDS_OK_BUTTON)
    
    print("Done.")

if __name__ == "__main__":
    # Fail-safe: moving mouse to corner will abort
    pyautogui.FAILSAFE = True
    main()
