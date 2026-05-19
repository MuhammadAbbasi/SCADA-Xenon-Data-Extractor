import pyautogui
import time

# 1. FAIL-SAFE: Move mouse to any corner of the screen to abort the script
pyautogui.FAILSAFE = True

def test_interface_interact():
    print("Moving mouse to the center of the screen...")
    # Get screen size
    width, height = pyautogui.size()
    print(f"Screen size: {width}x{height}")
    
    # Move mouse and click (example coordinates)
    # You can find your current mouse position by running: print(pyautogui.position())
    pyautogui.moveTo(width/2, height/2, duration=1)
    pyautogui.click()
    
    # Simulate keyboard shortcut (e.g., Ctrl+S to save or Tab to navigate)
    print("Simulating keyboard input...")
    pyautogui.press('tab')
    pyautogui.typewrite("Searching for Data...", interval=0.1)
    pyautogui.press('enter')

if __name__ == "__main__":
    # Give yourself 3 seconds to switch to the SCADA window Searching for Data...

    print("Switch to your SCADA tab now!")
    time.sleep(3)
    test_interface_interact()