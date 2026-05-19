import os
import shutil
import re
import glob

# Base config
BASE_DIR = r"\\s01\get\2025.01 Mazara 01 A2A\03 - REPORT\Report\04 Tracker report"
# Dirs to process
# Format: (DirName, "folder" or "file")
DIRS = [
    ("01_Original_files", "folder"),
    ("02_DownSampled_Files", "folder"),
    ("03_Merged_files", "file"),
    ("04_Tracker_plots_angles", "folder"),
    ("05_Tracker_Report_PDF", "file")
]

DATE_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

def process_directory(dir_name, item_type):
    full_path = os.path.join(BASE_DIR, dir_name)
    if not os.path.exists(full_path):
        print(f"Directory not found: {full_path}")
        return

    print(f"Processing {dir_name}...")
    
    items = os.listdir(full_path)
    for item in items:
        item_path = os.path.join(full_path, item)
        
        # Skip if it is the script itself or unrelated
        if item == "restructure.py": continue

        # Check if item type matches (file vs dir)
        curr_is_dir = os.path.isdir(item_path)
        if item_type == "folder" and not curr_is_dir:
            continue
        if item_type == "file" and curr_is_dir:
            # Note: For 05, we have files. For 03, files.
            # But wait, 03/05 might have other folders? E.g. 'archive'? 
            # If so, we should skip them if they don't match date pattern.
            pass

        # Find date in item name
        match = DATE_PATTERN.search(item)
        if match:
            year, month, day = match.group(1), match.group(2), match.group(3)
            
            # Target dir structure: Year/Month
            # item goes into Year/Month/item
            
            target_year_dir = os.path.join(full_path, year)
            target_month_dir = os.path.join(target_year_dir, month)
            
            # Destination
            dest_path = os.path.join(target_month_dir, item)
            
            # Avoid moving if already there (e.g. strict subset of name)
            # But here we are creating year/month folders at the root of dir_name.
            # We must be careful not to move year folder into itself.
            if item == year: continue
            
            # Create dirs
            if not os.path.exists(target_year_dir):
                os.makedirs(target_year_dir)
            if not os.path.exists(target_month_dir):
                os.makedirs(target_month_dir)
                
            # Move
            # Handle collision
            if os.path.exists(dest_path):
                print(f"  [SKIP] Destination exists: {dest_path}")
            else:
                try:
                    shutil.move(item_path, dest_path)
                    print(f"  [MOVE] {item} -> {year}/{month}/{item}")
                except Exception as e:
                    print(f"  [ERROR] Moving {item}: {e}")

if __name__ == "__main__":
    for d, t in DIRS:
        process_directory(d, t)
    print("Done.")
