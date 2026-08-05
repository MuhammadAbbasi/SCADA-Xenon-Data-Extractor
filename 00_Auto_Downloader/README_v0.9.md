# 📖 SCADA Automation v0.9 — User Guide & System Overview

`scada_automation_v0.9.py` is an automated data extraction tool for SCADA Web Client systems. It uses computer vision (OpenCV edge matching) and GUI automation (`pyautogui`, `pygetwindow`) to filter, extract, and save hourly tracker reports into structured network directories (`YYYY/MM/YYYY-MM-DD/DD_MM_YYYY_HH_JJ.csv`).

---

## ⚙️ How It Works (Execution Architecture)

```mermaid
flowchart TD
    A[Start Program] --> B{CLI Arguments Provided?}
    B -- Yes --> C[Parse CLI Parameters]
    B -- No / --gui --> D[Launch Tkinter GUI Dialog]
    C --> E[Generate Target Date/Hour Matrix]
    D --> E
    E --> F{Dry Run Mode?}
    F -- Yes --> G[Print Target List & Exit]
    F -- No --> H[Show Border Status Overlay & Hotkey Listener]
    H --> I[Find & Focus SCADA Web Window]
    I --> J[Loop Through Target Hours]
    J --> K[Navigate Analisi -> Selezione Intervallo -> ORA]
    K --> L[Select Month, Year, Date & Hour in SCADA]
    L --> M[Export CSV & Save to Structured Folder]
    M --> N{More Hours in Range?}
    N -- Yes --> J
    N -- No --> O{Continuous Mode Active?}
    O -- Yes --> P[Wait Until Next Hour :05 & Repeat]
    O -- No --> Q[Finish & Exit]
```

### 1. Input Parsing (CLI vs. GUI)
- **CLI Mode**: When command-line parameters (`-sd` / `--start-date`) are supplied, the script runs automatically without displaying input dialogs.
- **GUI Mode**: If no date arguments are passed (or `--gui` is specified), an Italian Tkinter dialog opens to select date ranges, hours, single-day presets, and continuous mode.

### 2. Range & Hour Matrix Generation
- Single-day input (`-sd 2026-08-05`) generates all **24 hourly reports** (`00:00` to `23:00`).
- Date-range input (`-sd 2026-08-01 -ed 2026-08-05`) generates a chronological sequence of all hours between the start and end date/time.

### 3. Robust Image & Grid Date Selection (OpenCV)
- Excludes calendar week-number columns to avoid matching ambiguities.
- Uses **Canny Edge Detection** template matching to find date numbers regardless of UI selection background color (black-on-white or white-on-blue).
- Uses mathematical grid layout calculation as a fallback if visual matching is obscured.

### 4. File Saving, Validation & Corruption Recovery (New in v0.9)
- Constructs standard target paths automatically:
  `PATH_TO_ORI_FOLDER / YYYY / MM / YYYY-MM-DD / DD_MM_YYYY_HH_JJ.csv` (where `JJ` is `HH + 1`).
- **Automatic CSV Validation**: Before skipping an existing file, the script validates that it is non-empty and contains data corresponding to the target date and hour (handling multiple encoding formats: `utf-16le`, `utf-16`, `utf-8`, and `latin-1`).
- **Corruption Recovery**: If an existing file is found to be empty or contains incorrect/mismatched data, the script renames the faulty file to `*_incorrect.csv` (or `*_incorrect_N.csv`) and triggers a fresh download of that hour.
- Polling file checker verifies non-empty file creation on disk and handles Windows overwrite confirmation dialogs.

### 5. Safety & Overlay Controls
- Displays a top-right floating status panel on top of SCADA during execution.
- Press **`Ctrl` + `Alt` + `.`** at any time to immediately interrupt automation.

---

## 💻 Terminal CLI Commands & Prompt Examples

### 1. Download Full Single Day (24 Hours)
Downloads all 24 hours (`00:00` to `23:00`) for August 5, 2026 and exits when done:
```bash
python scada_automation_v0.9.py -sd 2026-08-05
```
*(Accepted date formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY/MM/DD`)*

---

### 2. Download Specific Hours for Single Day
Downloads hours `08:00` through `18:00` for August 5, 2026:
```bash
python scada_automation_v0.9.py -sd 2026-08-05 -st 08 -et 18
```

---

### 3. Download Multi-Day Range
Downloads all hours from August 1, 2026 `08:00` to August 5, 2026 `18:00`:
```bash
python scada_automation_v0.9.py -sd 01/08/2026 -st 08 -ed 05/08/2026 -et 18
```

---

### 4. Backfill Date Range + Continue Live Hourly Extraction
Downloads historical range first, then stays active and automatically downloads new hourly reports every hour at `:05`:
```bash
python scada_automation_v0.9.py -sd 2026-08-01 -ed 2026-08-05 -c
```

---

### 5. Preview Mode (Dry Run)
Check how many hours and which files would be downloaded without connecting to SCADA:
```bash
python scada_automation_v0.9.py -sd 2026-08-01 -ed 2026-08-05 --dry-run
```

---

### 6. Custom Destination Folder & Delays
Override the default save folder and customize page loading delays for slow network connections:
```bash
python scada_automation_v0.9.py -sd 2026-08-05 -o "//S01/get/Custom_Folder" --delay-load 90 --delay-save 90
```

---

## 📋 Full Parameter Reference Table

| Argument | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--start-date` | `-sd` | Start Date (`YYYY-MM-DD` or `DD/MM/YYYY`) | *Required for CLI* |
| `--start-time` | `-st` | Start Hour (`0`–`23` or `HH:MM`) | `0` (`00:00`) |
| `--end-date` | `-ed` | End Date (`YYYY-MM-DD` or `DD/MM/YYYY`) | Equal to `--start-date` |
| `--end-time` | `-et` | End Hour (`0`–`23` or `HH:MM`) | `23` (`23:00`) |
| `--continuous` | `-c` | Enable continuous live hourly extraction after range | `Disabled` |
| `--output-dir` | `-o` | Override default save directory | `PATH_TO_ORI_FOLDER` |
| `--delay-load` | | Seconds to wait for SCADA data table load | `80` |
| `--delay-save` | | Seconds to wait for file save on disk | `80` |
| `--dry-run` | | Print hour target list without running automation | `Disabled` |
| `--gui` | | Force GUI popup dialog | `Disabled` |
