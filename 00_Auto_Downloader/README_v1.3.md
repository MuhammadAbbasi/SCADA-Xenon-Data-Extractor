# SCADA Auto Downloader v1.3

**Estrazione Automatica & Monitoraggio Report SCADA Tracker (Mazara 01 A2A)**

Software Python / Executable Windows per l'estrazione automatizzata dei report orari CSV dal sistema SCADA Web Client.

---

## 🚀 Novità Versione 1.3 (Verification, Backup & Grid Math)

1. **Modalità Verifica & Backup File Errati (`-vb` / `--verify-and-backup`)**:
   - Ispezione a 3 punti per i file esistenti (Dimensione >= 480 MB, Lock di scrittura, Corrispondenza Data e Ora all'interno dell'intestazione CSV).
   - Se un file sul disco risulta errato, corrotto o con data non corrispondente (causato ad es. da vecchie selezioni errate nel calendario SCADA), viene **automaticamente spostato** nella sottocartella `backup/`:
     `PATH_TO_ORI_FOLDER/YYYY/MM/YYYY-MM-DD/backup/DD_MM_YYYY_HH_JJ_reason_timestamp.csv`
   - L'ora corrispondente viene riaggiunta alla coda per il download automatico della versione corretta.

2. **Calcolo Matematico Griglia Calendario (`--grid-first`)**:
   - Risolve le ambiguità di riconoscimento visivo/OCR delle cifre del calendario SCADA (es. `16` vs `19`, `1` vs `11`).
   - Calcola direttamente le coordinate dello schermo della cella del giorno tramite formula matematica:
     `col = (day - 1 + weekday) % 7`, `row = (day - 1 + weekday) // 7`
     `X = start_x + col * cell_w`, `Y = start_y + row * cell_h`

3. **Data di Test (`-td YYYY-MM-DD` / `--test-date`)**:
   - Consente di eseguire rapidamente il test di verifica dei file su una specifica data prima di procedere con l'estrazione continua.

4. **Interfaccia Grafica GUI Aggiornata**:
   - Nuove opzioni spuntabili per attivare/disattivare l'ispezione approfondita e il calcolo griglia calendario direttamente dal dialogo Tkinter.
   - Icona applicazione 3D ad alta risoluzione integrata nel binario ed Executable.

---

## 🛠️ Comandi di Esempio

```bash
# 1. Verifica approfondita e backup file errati per una data specifica (Dry-Run):
python scada_automation_v1.3.py -td 2026-08-16 -vb --dry-run

# 2. Scarica data con griglia matematica e backup attivato:
python scada_automation_v1.3.py -sd 2026-08-16 -vb --grid-first

# 3. Intervallo di date con monitoraggio in tempo reale (Modalità Continua):
python scada_automation_v1.3.py -sd 01/08/2026 -ed 14/09/2026 -c -vb
```

---

## 📦 Compilazione Executable (.exe)

Compilato con PyInstaller tramite `scada_automation_v1.3.spec`:

```bash
pyinstaller --noconfirm scada_automation_v1.3.spec
```

Output: `dist/scada_automation_v1.3.exe` (~83 MB).
