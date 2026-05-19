import csv

def get_unique_values(filename):
    unique_values = set()

    try:
        # Changed encoding to 'utf-16'
        with open(filename, mode='r', encoding='utf-16') as f:
            # Added delimiter=';'
            reader = csv.reader(f, delimiter=';')
            
            # Optional: Skip header
            # next(reader, None) 

            for row in reader:
                if row:  # Ensure row is not empty
                    unique_values.add(row[0])
                    
        return list(unique_values)

    except UnicodeError:
        print("Error: Encoding issue. Try 'utf-16-le' or 'utf-16-be' if 'utf-16' fails.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Usage
filename = '//S01/get/2025.01 Mazara 01 A2A/03 - REPORT/Report/04 Tracker report/01_Original_files/2025-11-12/12_11_2025_06_07.csv'
values = get_unique_values(filename)
print(f"Unique values: {set(values)}")