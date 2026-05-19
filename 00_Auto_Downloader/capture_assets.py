
import pyautogui
import time
import os
import sys


# Constants
# Try to get a writable asset directory
# If on network, sometimes os.getcwd returns UNC which works if permissions are right
ASSETS_DIR = "assets" 
CAPTURE_SIZE = (60, 60) # Width, Height

def ensure_assets_dir():
    global ASSETS_DIR
    try:
        # Check current dir
        cwd = os.getcwd()
        full_path = os.path.join(cwd, ASSETS_DIR)
        print(f"Current Working Directory: {cwd}")
        
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
        
        # Test write permission
        test_file = os.path.join(full_path, "test_write.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("Write permission verified.")
        except Exception as e:
            print(f"CRITICAL: Cannot write to {full_path}. Error: {e}")
            print("Trying to use TEMP folder instead...")
            # Fallback to local temp
            import tempfile
            full_path = os.path.join(tempfile.gettempdir(), "scada_assets")
            if not os.path.exists(full_path):
                os.makedirs(full_path)
            print(f"USING TEMP FOLDER: {full_path}")
            
            # Update global ASSETS_DIR so capture_asset uses it
            ASSETS_DIR = full_path

    except Exception as e:
        print(f"CRITICAL ERROR in ensure_assets_dir: {e}")

def capture_asset(asset_name, instruction):
    # Resolve full path dynamically based on potentially changed ASSETS_DIR
    if os.path.isabs(ASSETS_DIR):
        full_dir = ASSETS_DIR
    else:
        full_dir = os.path.join(os.getcwd(), ASSETS_DIR)

    print(f"\n--- Capturing: {asset_name} ---")
    print(instruction)
    print(f"1. Hover your mouse over the CENTER of the '{asset_name}'.")
    try:
        input("2. Press ENTER when you are pointing at it... (Make sure this window is focused for input)")
    except Exception as e:
        print(f"Input error: {e}")

    # Get mouse position
    try:
        x, y = pyautogui.position()
        print(f"Mouse position: ({x}, {y})")
        
        # Calculate region: (left, top, width, height)
        left = int(x - CAPTURE_SIZE[0] / 2)
        top = int(y - CAPTURE_SIZE[1] / 2)
        
        # Capture screen
        screenshot = pyautogui.screenshot(region=(left, top, CAPTURE_SIZE[0], CAPTURE_SIZE[1]))
        
        filepath = os.path.join(full_dir, f"{asset_name}.png")
        print(f"Attempting to save to: {filepath}")
        
        screenshot.save(filepath)
        
        if os.path.exists(filepath):
            print(f"SUCCESS: Saved {asset_name}.png")
            return True
        else:
            print(f"ERROR: File was not created at {filepath}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION during capture of {asset_name}: {e}")
        return False

def main():
    print("=== SCADA Asset Capture Tool ===")
    print("This tool will help you capture the necessary images for automation.")
    print("Please make sure your SCADA window is OPEN and VISIBLE.")
    ensure_assets_dir()

    input("Press ENTER to start...")

    assets_to_capture = [
        ("month_dropdown", "The dropdown arrow or button to select the MONTH."),
        ("year_dropdown", "The dropdown arrow or button to select the YEAR."),
        ("prev_month_btn", "Button to go to previous month (if applicable) OR leave blank if not needed."), 
        ("next_month_btn", "Button to go to next month (if applicable)."),
        ("scroll_up", "The specified 'Scroll Up' button/arrow for the Time list."),
        ("scroll_down", "The specified 'Scroll Down' button/arrow for the Time list."),
        ("time_0600", "The text '06:00' in the time column. Identify a visible one or scroll to it first."),
        ("ora_text", "The text 'ORA' (Hour) option that you want to click.")
    ]

    for name, instruction in assets_to_capture:
        # Ask if user wants to skip
        # For simplicity, we just do them all.
        capture_asset(name, instruction)
        time.sleep(0.5)

    # Ask to capture days
    print("\nDo you want to capture Day images (1-31)? (y/n)")
    if input().lower().startswith('y'):
        for i in range(1, 32):
            capture_asset(f"day_{i}", f"Hover over Day {i} in the calendar grid.")
            time.sleep(0.2)

    print("\nAll captures complete!")
    print(f"Images are saved in: {os.path.abspath(ASSETS_DIR)}")

if __name__ == "__main__":
    main()
