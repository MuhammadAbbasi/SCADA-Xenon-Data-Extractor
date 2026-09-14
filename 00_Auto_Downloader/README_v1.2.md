# 📖 SCADA Automation v1.2 - User Guide & System Overview

`scada_automation_v1.2.py` is an automated data extraction tool for SCADA Web Client systems. It uses computer vision (OpenCV edge matching) and GUI automation (`pyautogui`, `pygetwindow`) to filter, extract, and save hourly tracker reports into structured network directories (`YYYY/MM/YYYY-MM-DD/DD_MM_YYYY_HH_JJ.csv`).

> Copied from v1.1 — v1.1 file left untouched. All changes below are v1.2-only.

## 🆕 What's New in v1.2 (on top of v1.1)

1. **Single clock rule (`AVAILABILITY_LAG_MINUTES = 5`)**: hour `H` is downloadable from `(H+1):05`. `get_last_completed_datetime()`, `get_trigger_time_for_target()`, `generate_backfill_hours()`, `get_first_run_target()` and `get_next_trigger_time()` all share it (v1.1 had duplicated `now.hour - 1` copies).
2. **Trigger precision restored**: `get_next_trigger_time(now)` again returns the immediate `:05` when run during `:00-:04` (v1.1 always jumped to next hour).
3. **Pre-filter of existing files**: before touching SCADA, due hours are checked with `validate_existing_csv()` (threaded, 16 workers). Re-runs download only what's missing — e.g. `120 richiesti → 1 da scaricare, 119 già presenti`. `--dry-run` reports `da scaricare / già presenti / futuri`.
4. **Lazy SCADA start**: with `-c` and nothing due yet, v1.2 waits *before* opening SCADA instead of holding the SCADA window focused for hours. Also fixes the always-true `needs_scada_now` condition.
5. **Chunked load wait**: same `DELAY_LOAD_DATA` budget (default 90s) but in 5s chunks with progress logs; the overlay Avanti button still skips early when the table is visibly loaded.
6. **`--max-retries N`**: bounds continuous same-hour retry (default `0` = unlimited). On exceeding the bound it exits with error (fail-loud, never silently skips an hour).
7. **Timing logs**: per-hour and total range durations in the console.
8. **GUI smart defaults (from v1.0, kept v1.1 split view)**: end hour defaults to the last completed hour, `Recupera Oggi + Continua` preset restored next to `Giorno Singolo` (both date-aware), live due/future summary with validation, `cp1252`-safe `[OK]/[WAIT]/[WARN]` tags.
9. **Live overlay status**: the small status window title now shows the real pipeline phase (`SCADA v1.2 - SCARICO 3/11`, `ATTESA`, `CARICAMENTO DATI SCADA`, ...) with a colour badge (`ATTIVO` green / `ATTESA` yellow / `ERRORE` red / `COMPLETATO` grey) and a detail line (current file, sizes, wait target) instead of a static label.

Verify with (no SCADA needed):

```bash
python scada_automation_v1.2.py -sd 2026-09-14 -st 00 -et 23 --dry-run
python scada_automation_v1.2.py -sd 2026-09-14 -st 00 -et 23 -c --dry-run
python scada_automation_v1.2.py -sd 01/08/2026 -ed 05/08/2026 --dry-run
```

Note: `--dry-run` runs the disk pre-check, so it takes ~15-20s on the network share for large ranges (vs ~1s in v1.1) — the counts are exact in return.

---

## ⚙️ How It Works (Execution Architecture)

```mermaid
flowchart TD
    A[Start Program] --> B{CLI Arguments Provided?}
    B -- Yes --> C[Parse CLI Parameters]
    B -- No / --gui --> D[Launch Tkinter GUI Dialog]
    C --> E[Generate Target Date/Hour Matrix]
    D --> E
    E --> F[Split due vs future + Pre-filter existing files]
    F --> G{Dry Run Mode?}
    G -- Yes --> H[Print due / existing / future & Exit]
    G -- No --> I{Nothing due now?}
    I -- Yes + continuous --> J[Wait WITHOUT opening SCADA until first trigger]
    I -- Yes, no continuous --> Q[Finish & Exit]
    J --> K[Show Border Status Overlay & Hotkey Listener]
    I -- Work due --> K
    K --> L[Find & Focus SCADA Web Window]
    L --> M[Loop Through Missing Due Hours only]
    M --> N[Navigate Analisi -> Selezione Intervallo -> ORA]
    N --> O[Select Month, Year, Date & Hour in SCADA]
    O --> P[Export CSV & Save to Structured Folder]
    P --> R{More Missing Hours?}
    R -- Yes --> M
    R -- No --> S{Continuous Mode Active?}
    S -- Yes --> T[Sequential next_needed pointer: wait until H+1:05 & retry same hour on failure]
    S -- No --> Q[Finish & Exit]
```

### 1. Input Parsing (CLI vs. GUI)

- **CLI Mode**: When command-line parameters (`-sd` / `--start-date`) are supplied, the script runs automatically without displaying input dialogs.
- **GUI Mode**: If no date arguments are passed (or `--gui` is specified), an Italian Tkinter dialog opens. End hour defaults to the **last completed hour** when the end date is today; presets `Giorno Singolo` (date-aware) and `Recupera Oggi + Continua` (00:00 → last completed + continuous ON) are one click.

### 2. Range, Availability Split & Pre-filter

- Single-day input (`-sd 2026-08-05`) generates all **24 hourly reports** (`00:00` to `23:00`).
- Date-range input generates a chronological sequence of all hours between start and end date/time.
- `split_targets_by_availability()` splits into `due` (target ≤ last completed hour) vs `future` (incomplete, available from `(H+1):05`).
- `filter_already_completed()` removes hours already valid on disk — SCADA is used only for what's actually missing.

### 3. Robust Image & Grid Date Selection (OpenCV)

- Excludes calendar week-number columns to avoid matching ambiguities.
- Uses **Canny Edge Detection** template matching to find date numbers regardless of UI selection background color (black-on-white or white-on-blue).
- Uses mathematical grid layout calculation as a fallback if visual matching is obscured.

### 4. File Saving, Validation & Corruption Recovery

- Target paths: `PATH_TO_ORI_FOLDER / YYYY / MM / YYYY-MM-DD / DD_MM_YYYY_HH_JJ.csv` (where `JJ` is `HH + 1`, `23 → 00`).
- **Automatic CSV Validation**: before skipping an existing file, validates non-empty, size ≥ 480 MB (~530 MB expected), and date/hour content match (encodings `utf-16le`, `utf-16`, `utf-8`, `latin-1`).
- **Corruption Recovery**: faulty files renamed to `*_incorrect.csv` (or `*_incorrect_N.csv`) and re-downloaded.
- Polling file checker verifies non-empty file creation and handles Windows overwrite dialogs.

### 5. Safety & Overlay Controls

- Top-right floating status panel mirrors the real pipeline state: title shows the live phase (`CONTROLLO FILE ESISTENTI`, `SCARICO 3/11`, `ATTESA`, `CARICAMENTO DATI SCADA`, `SCARICO CONTINUA 14:00`, `COMPLETATO`...), the badge shows `ATTIVO`/`ATTESA`/`ERRORE`/`COMPLETATO` with colour, and the detail line shows the current file, sizes or wait target.
- Single path builder `build_expected_csv_path()` shared by pre-check, guard and save.
- Press **`Ctrl` + `Alt` + `.`** to interrupt; overlay **Avanti >>** button skips the current wait.

---

## 💻 Terminal CLI Commands & Prompt Examples

### 1. Download Full Single Day (24 Hours)

```bash
python scada_automation_v1.2.py -sd 2026-08-05
```

*(Accepted date formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY/MM/DD`)*

---

### 2. Download Specific Hours for Single Day

```bash
python scada_automation_v1.2.py -sd 2026-08-05 -st 08 -et 18
```

---

### 3. Download Multi-Day Range

```bash
python scada_automation_v1.2.py -sd 01/08/2026 -st 08 -ed 05/08/2026 -et 18
```

---

### 4. Backfill Date Range + Continue Live Hourly Extraction

```bash
python scada_automation_v1.2.py -sd 2026-08-01 -ed 2026-08-05 -c
```

---

### 5. Preview Mode (Dry Run)

```bash
python scada_automation_v1.2.py -sd 2026-08-01 -ed 2026-08-05 --dry-run
```

---

### 6. Continuous Mode with Retry Bound

Retry the same hour at most 5 times, then exit with error instead of retrying forever:

```bash
python scada_automation_v1.2.py -sd 2026-08-05 -c --max-retries 5
```

---

### 7. Custom Destination Folder & Delays

```bash
python scada_automation_v1.2.py -sd 2026-08-05 -o "//S01/get/Custom_Folder" --delay-load 90 --delay-save 600
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
| `--delay-load` | | Seconds to wait for SCADA data table load (chunked, skippable) | `90` |
| `--delay-save` | | Max seconds of save inactivity before timeout | `600` |
| `--max-retries` | | Max consecutive retries of the SAME hour in continuous mode (`0` = unlimited) | `0` |
| `--dry-run` | | Print hour target list without running automation | `Disabled` |
| `--gui` | | Force GUI popup dialog | `Disabled` |

---

## 📦 Standalone Executable (no Python needed)

- Built with PyInstaller from `scada_automation_v1.2.spec` (onefile, windowed, `assets/` bundled):
  ```bash
  pyinstaller --noconfirm scada_automation_v1.2.spec
  ```
- Output: `dist/scada_automation_v1.2.exe` (~78 MB). Double-click opens the GUI dialog directly.
- `dist/` and `build/` are gitignored — the exe is distributed manually, not via git.
- Note: the windowed build has no console, so CLI/`--dry-run` output is only visible when running the `.py` with Python.
