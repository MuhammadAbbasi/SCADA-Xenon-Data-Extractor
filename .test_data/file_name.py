import os

# ======= CONFIG =======
ROOT_FOLDER = r"//S01/get/03 - REPORT/Report/Daily Reports/Humidity Reports"

# =======================

for folder_path, subfolders, files in os.walk(ROOT_FOLDER):
    for file_name in files:
        if file_name.lower().endswith(".txt"):
            old_path = os.path.join(folder_path, file_name)
            new_name = file_name[:-4] + ".csv"
            new_path = os.path.join(folder_path, new_name)

            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path}  -->  {new_path}")
            except Exception as e:
                print(f"Failed to rename {old_path}: {e}")

print("Done!")
