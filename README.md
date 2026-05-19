# SCADA Xenon Data Extractor - Solar Tracker Suite

A Python-based suite for automated extraction, processing, analysis, and reporting of solar tracker angle data from a SCADA Xenon Web Client. Built for the A2A Mazara solar installation (Mazara del Vallo, Sicily, Italy).

---

## Overview

The system automates the full data pipeline:

```
SCADA Web Client -> Auto-Download -> Raw CSV -> Downsample -> Merge -> Plot -> PDF Report
```

## GUI Overview

![GET - SCADA Tracker Suite GUI](docs/gui_overview.png)

| Area | Label | Description |
|---|---|---|
| A | Configuration | Set the Root Folder path and the analysis date (year/month/day spinboxes). Click **Browse** to change folder or **Refresh Status** to re-check which steps are ready. |
| B | 1. EXTRACT | Reads raw semicolon-delimited CSVs from `01_Original_files/`, filters `Angolo Target` and `Angolo Attuale` columns, and saves cleaned files to `02_DownSampled_Files/`. Auto-renames `.txt` exports to `.csv`. |
| C | 2. MERGE | Combines all extracted files for the selected date into a single 1-minute resampled CSV saved to `03_Merged_files/`. Processed in memory-optimised batches. |
| D | 3. GENERATE OVERVIEW | Generates high-resolution (1800 dpi) angle overview plots for all trackers combined and per NCU group. Also exports a CSV of trackers below the 28-degree threshold. |
| E | 4. GENERATE INDIVIDUAL PLOTS | Produces one PNG plot per NCU-TCU pair showing target vs actual angle with Min/Max annotation. Saved to `each_tracker_plots/` subfolder. |
| F | 5. RUN HEALTH CHECK | Fast analysis across all trackers detecting: DATA LOSS, STUCK trackers, DEVIATION above 20 degrees, and LOW ANGLE below 28 degrees. Results appear in the Health Dashboard tab. |
| G | 6. EXPORT FULL PDF REPORT | Compiles a full PDF with all overview images followed by one page per tracker. Can exceed 370 pages depending on the site. |
| H | 7. EXPORT RANDOM PDF | Lighter PDF with overview images plus 5 randomly sampled TCUs per NCU. Useful for quick spot-checks. |
| I | Console Output | Live log of all processing activity. Errors and progress counters appear here during each step. |
| J | Health Dashboard tab | Table of issues found by Step 5. Double-click any row to open that tracker's angle plot. |

> Button colors reflect pipeline status: grey = not ready, light blue = ready, green = completed, yellow = Step 3 ready, orange/red = PDF export ready.

---

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

## Guida Utente (Italiano)

### Avvio dell'applicazione

Avviare il programma eseguendo `tracker_suite_v2.10_OPTIMIZED.py` oppure il file `.exe` compilato.
All'avvio comparira' la finestra principale **GET - SCADA Tracker Suite**.

### Configurazione iniziale

Prima di qualsiasi operazione impostare:

- **Root Folder** - cartella radice del progetto (percorso predefinito: `//S01/get/2025.01 Mazara 01 A2A/...`). Cliccare **Browse** per cambiarla.
- **Date Selection** - selezionare anno, mese e giorno tramite i selettori numerici. La data indica il giorno di cui si vuole elaborare i dati.

Dopo aver impostato la data, cliccare **Refresh Status** per aggiornare lo stato dei pulsanti. I pulsanti si colorano automaticamente in base ai dati disponibili:

| Colore | Significato |
|---|---|
| Grigio | Dati del passaggio non ancora disponibili |
| Azzurro | Passaggio pronto per essere eseguito |
| Verde | Passaggio gia' completato con successo |
| Giallo | Step 3 (Overview) disponibile |
| Arancione/Rosso | Export PDF completo disponibile |
| Blu | Export PDF campione disponibile |

---

### Pipeline - Passaggi in ordine

#### Passo 1 - EXTRACT

Legge i file CSV grezzi esportati dal SCADA (cartella `01_Original_files/YYYY/MM/DD/`).
Estrae solo le colonne **Angolo Target** e **Angolo Attuale** per ogni tracker.
I file `.txt` vengono rinominati automaticamente in `.csv` se presenti.
Output salvato in `02_DownSampled_Files/YYYY/MM/DD/`.

> Attenzione: durante l'estrazione non cliccare altri pulsanti. Il log mostrera' "per favore non cliccare piu... aspetti" per ogni file in elaborazione.

#### Passo 2 - MERGE

Legge tutti i file estratti e li unisce in un unico CSV ricampionato a **1 minuto** di risoluzione.
I dati vengono elaborati a batch per ridurre l'uso di memoria RAM.
Output: `03_Merged_files/YYYY/MM/{data}_1min_merged.csv`

Una volta completato il merge, i passi 3, 4, 5, 6 e 7 diventano disponibili.

#### Passo 3 - GENERATE OVERVIEW (Merged)

Genera grafici panoramici ad alta risoluzione (1800 dpi) dal file merged:
- Un grafico con **tutti i tracker** sovrapposti
- Un grafico separato per ogni **NCU** (Node Control Unit)
- Un file CSV con tutti i tracker che hanno registrato un angolo sotto la soglia di **28 gradi**

Output salvato in `04_Tracker_plots_angles/YYYY/MM/DD/`.

#### Passo 4 - GENERATE INDIVIDUAL PLOTS

Genera un grafico PNG individuale per ogni coppia **NCU-TCU**, con:
- Curva blu: angolo target
- Curva rossa: angolo attuale
- Box con valori Min/Max dell'angolo attuale

I grafici vengono salvati in `04_Tracker_plots_angles/YYYY/MM/DD/each_tracker_plots/` con nome `TX_{NCU}_TCU_{TCU}.png`.

> Questo passo puo' richiedere diversi minuti in base al numero di tracker (tipicamente 370+).

#### Passo 5 - RUN HEALTH CHECK

Analisi rapida di tutti i tracker per rilevare anomalie. Vengono segnalati quattro tipi di problemi:

| Tipo | Severita' | Condizione |
|---|---|---|
| DATA LOSS | Alta | Meno di 10 punti dati registrati |
| STUCK | Critica | Il target si muove ma l'angolo attuale rimane fisso |
| DEVIATION | Media | Differenza media tra target e attuale superiore a 20° |
| LOW ANGLE | Alta | Angolo attuale minimo inferiore a 28° |

I risultati appaiono nella scheda **Health Dashboard**.
Fare **doppio click** su una riga per aprire il grafico del tracker corrispondente.
Se il file PNG non e' stato ancora generato, il grafico viene calcolato e visualizzato in tempo reale in una finestra popup.

#### Passo 6 - EXPORT FULL PDF REPORT

Genera un PDF completo contenente:
1. I grafici di panoramica (Overview) per tutti gli NCU
2. Una pagina per ogni tracker (NCU-TCU) con grafico angolo vs tempo

Output: `05_Tracker_Report_PDF/YYYY/MM/Tracker_Report_{data}.pdf`

> Attenzione: con 370+ tracker questo processo puo' richiedere diversi minuti e genera un file PDF di grandi dimensioni.

#### Passo 7 - EXPORT RANDOM PDF

Genera un PDF campione piu' leggero contenente:
1. I grafici di panoramica
2. **5 TCU scelti casualmente** per ogni NCU

Utile per una verifica rapida senza generare il report completo.
Output: `05_Tracker_Report_PDF/YYYY/MM/Tracker_Random_Sample_{data}.pdf`

---

### Scheda Health Dashboard

Mostra la tabella degli errori rilevati dallo Step 5 con colonne: NCU, TCU, Tipo, Severita', Dettagli.
- Righe **rosse** = problemi critici (STUCK)
- Righe **arancioni** = problemi di alta severita' (DATA LOSS, LOW ANGLE)
- Doppio click su una riga apre il grafico del tracker in una finestra separata

---

### Struttura delle cartelle dati

```
Root Folder/
├── 01_Original_files/YYYY/MM/DD/    # File CSV grezzi dal SCADA
├── 02_DownSampled_Files/YYYY/MM/DD/ # File estratti (solo angoli)
├── 03_Merged_files/YYYY/MM/         # File merged a 1 minuto
├── 04_Tracker_plots_angles/YYYY/MM/DD/
│   ├── NCU_TCU_{data}_ALL.png       # Overview tutti i tracker
│   ├── NCU_TCU_{data}_NCU1.png      # Overview NCU 1
│   ├── NCU_TCU_{data}_below_28deg.csv
│   └── each_tracker_plots/
│       └── TX_{NCU}_TCU_{TCU}.png
└── 05_Tracker_Report_PDF/YYYY/MM/
    ├── Tracker_Report_{data}.pdf
    └── Tracker_Random_Sample_{data}.pdf
```

---

## Notes

- Data folders (`01_` through `05_`) are excluded from version control (see `.gitignore`) - total raw data is ~2.1 TB
- Compiled `.exe` files, Office documents, and legacy code archives are also excluded
- `v2.10` is the current production release; `v2.11` is the next version in active development
- `restructure.py` is a personal local utility and is not part of the core application

---

## License

Internal project - Not for public redistribution.
