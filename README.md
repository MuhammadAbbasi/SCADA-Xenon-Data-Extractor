# SCADA Xenon Data Extractor - Solar Tracker Suite

A Python-based suite for automated extraction, processing, analysis, and reporting of solar tracker angle data from a SCADA Xenon Web Client. Built for the A2A Mazara solar installation (Mazara del Vallo, Sicily, Italy).

---

## Overview

The system automates the full data pipeline:

```
SCADA Web Client -> Auto-Download -> Raw CSV -> Downsample -> Merge -> Plot -> PDF Report
```

Two companion applications handle distinct responsibilities:

| Application | File | Status | Purpose |
|---|---|---|---|
| Tracker Suite v2.10 | `tracker_suite_v2.10_OPTIMIZED.py` | Production | Data processing, analysis, and PDF report generation |
| Tracker Suite v2.11 | `TRACKER_SUITE_V2.11.py` | In development | Next release with additional improvements |
| SCADA Auto-Downloader | `00_Auto_Downloader/scada_automation_gui.py` | Production | Automated daily/hourly data retrieval from SCADA UI |

---

## Project Structure

```
04 Tracker report/
├── 00_Auto_Downloader/          # SCADA GUI automation scripts and assets
├── 01_Original_files/           # Raw SCADA exports (CSV, by date) - NOT in repo
├── 02_DownSampled_Files/        # Downsampled processed data - NOT in repo
├── 03_Merged_files/             # Consolidated daily/weekly CSVs - NOT in repo
├── 04_Tracker_plots_angles/     # Generated PNG plots - NOT in repo
├── 05_Tracker_Report_PDF/       # Final PDF reports - NOT in repo
├── .test_data/                      # Development and test scripts
├── TRACKER_SUITE_V2.11.py           # Next version (in development)
├── tracker_suite_v2.10_OPTIMIZED.py # Current production version
├── coordinate_check.py              # Screen coordinate validation utility
├── restructure.py                   # Personal file management utility (local use only)
└── logo.png                         # Application logo
```

---

## Features

### Tracker Suite (`tracker_suite_v2.10_OPTIMIZED.py` - production)
- Extracts `Angolo Target` and `Angolo Attuale` (target vs. actual angle) per tracker unit
- Parses NCU / TCU / TC identifiers from raw SCADA CSV output
- Astronomical solar calculations (sunrise/sunset) via `astral` for precise daytime filtering
- Parallel processing with `ProcessPoolExecutor` for large dataset performance
- Generates one PNG plot per tracker unit (NCU-TCU pair)
- Aggregates plots into PDF reports
- Tkinter GUI with progress tracking

### SCADA Auto-Downloader (`00_Auto_Downloader/scada_automation_gui.py`)
- GUI-controlled automation of the SCADA Xenon Web Client
- Screen automation via `pyautogui` with OpenCV template matching for robust element detection
- Configurable date/time range selection
- Supports hourly or daily scheduled downloads
- Interruptible background threads

---

## Installation

### Requirements

Python 3.10+ recommended.

```bash
pip install pandas matplotlib astral pytz pyautogui pygetwindow opencv-python numpy tkcalendar
```

For the tracker suite only (no automation):

```bash
pip install pandas matplotlib astral pytz
```

### PyInstaller (optional - to build EXEs)

```bash
pip install pyinstaller
pyinstaller tracker_suite_v2.10_OPTIMIZED.spec
```

---

## Usage

### Run the Tracker Suite GUI

```bash
python tracker_suite_v2.10_OPTIMIZED.py
```

Processing pipeline triggered from the GUI:
1. Select input folder (`01_Original_files/`)
2. Run extraction -> downsampling -> merging
3. Generate plots -> compile PDF report

### Run the SCADA Auto-Downloader

```bash
python 00_Auto_Downloader/scada_automation_gui.py
```

- Set the target date range
- Ensure the SCADA Xenon Web Client is open and visible on screen
- Start the automated download sequence

---

## Site Configuration

| Parameter | Value |
|---|---|
| Site | Mazara del Vallo, Sicily |
| Latitude | 37.7717 N |
| Longitude | 12.6304 E |
| Timezone | Europe/Rome |
| Client | A2A (2025.01 project) |

Solar position calculations (sunrise/sunset filtering) use these coordinates via the `astral` library.

---

## Data Pipeline Details

### Step 1 - Raw Extraction
Input: semicolon-delimited CSVs from SCADA export
Output: angle-only CSVs in `01_Original_files/`

### Step 2 - Downsampling
Algorithm: `v3` downsampling preserving trend fidelity
Output: reduced-resolution CSVs in `02_DownSampled_Files/`

### Step 3 - Merging
Consolidates per-day files into weekly/monthly datasets
Output: `03_Merged_files/`

### Step 4 - Plotting
One PNG per NCU-TCU pair; angle vs. time with solar window overlay
Output: `04_Tracker_plots_angles/`

### Step 5 - PDF Report
Aggregates plots and performance metrics
Output: `05_Tracker_Report_PDF/`

---

## Utility Scripts

| Script | Purpose |
|---|---|
| `coordinate_check.py` | Validates screen coordinates used by the automation |
| `restructure.py` | Personal file management utility for local directory organization |
| `.test_data/*.py` | Standalone development and testing scripts |

---

## Future Optimizations

### Performance
- [ ] Replace `ProcessPoolExecutor` with `Dask` or `Ray` for distributed processing across large datasets (currently 2+ TB raw data)
- [ ] Stream CSV parsing instead of full in-memory `pd.read_csv()` to reduce peak RAM usage on large date ranges
- [ ] Add incremental processing: detect already-processed files and skip them (currently re-processes all)
- [ ] Cache downsampled outputs with a hash-based invalidation strategy

### SCADA Automation
- [ ] Replace hardcoded screen coordinates with dynamic element detection (OCR or accessibility API) to survive SCADA UI version changes
- [ ] Add headless/API-based extraction if the SCADA Xenon version exposes a REST interface, removing the need for screen automation entirely
- [ ] Secure credentials: move `credentials.txt` to OS keychain or environment variables (never commit plaintext credentials)

### Data Quality
- [ ] Add automated anomaly detection: flag trackers where `|Angolo Attuale - Angolo Target| > threshold` persistently
- [ ] Implement tracker health scoring per NCU-TCU pair with trend history
- [ ] Cross-validate downsampled data against originals to quantify information loss per algorithm version

### Reporting
- [ ] Add interactive HTML reports (Plotly / Bokeh) alongside static PDFs for web-based review
- [ ] Parameterize PowerPoint template population to automate full PPTX generation from analysis output
- [ ] Integrate humidity sensor data into the tracker health report (scripts exist in `.test_data/`)

### Code Quality
- [ ] Package the suite as a proper Python package (`setup.py` / `pyproject.toml`) with versioned dependencies
- [ ] Add unit tests for the downsampling algorithm and angle-parsing logic
- [ ] Replace `pyautogui` coordinate magic numbers with a configuration file (`automation_config.json`) editable without touching source code

---

## Notes

- Data folders (`01_` through `05_`) are excluded from version control (see `.gitignore`) - total raw data is ~2.1 TB
- Compiled `.exe` files, Office documents, and legacy code archives are also excluded
- `v2.10` is the current production release; `v2.11` is the next version in active development
- `restructure.py` is a personal local utility and is not part of the core application

---

## License

Internal project - A2A / a176lab.it. Not for public redistribution.
