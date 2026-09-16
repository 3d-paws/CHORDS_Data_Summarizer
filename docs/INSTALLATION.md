# CHORDS Data Summarizer — Installation Guide

This guide explains how to install and run the **CHORDS Data Summarizer** on Windows, macOS, or Linux.

The summarizer processes compatible CHORDS CSV files and creates:

```text
15-minute meteorological summaries
hourly meteorological summaries
daily meteorological summaries
a QC report
```

GitHub Repository:

https://github.com/3d-paws/CHORDS_Data_Summarizer

---

# Windows

The recommended Windows workflow uses **Windows PowerShell** and Python 3.10.

## 1. Install Python

Open Windows PowerShell and check which Python versions are installed:

```powershell
py --list
```

Python 3.10 is recommended for consistency with the CHORDS Data Downloader.

If Python 3.10 is not installed:

```powershell
winget install Python.Python.3.10
```

After installation, close and reopen PowerShell.

Confirm the installation:

```powershell
py -3.10 --version
```

---

## 2. Download the Repository

Go to:

https://github.com/3d-paws/CHORDS_Data_Summarizer

Select:

**Code → Download ZIP**

Extract the ZIP file to a convenient location.

For example:

```text
C:\Users\username\Documents\CHORDS\CHORDS_Data_Summarizer-main
```

Open PowerShell and navigate to the extracted repository:

```powershell
cd C:\Users\username\Documents\CHORDS\CHORDS_Data_Summarizer-main
```

### Using Git Instead

If Git is already installed:

```powershell
git clone https://github.com/3d-paws/CHORDS_Data_Summarizer.git
cd CHORDS_Data_Summarizer
```

Git is not required to use the summarizer.

---

## 3. Create the Python Virtual Environment

From inside the repository:

```powershell
py -3.10 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

The PowerShell prompt should now begin with:

```text
(.venv)
```

### If PowerShell Blocks the Activation Script

Run:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 4. Install the Required Packages

Make sure `(.venv)` is visible in the PowerShell prompt.

Run:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

These installation steps only need to be completed once for this virtual environment.

---

## 5. Create `summary.env`

The repository includes:

```text
summary.env.example
```

Copy it to:

```text
summary.env
```

using:

```powershell
Copy-Item ".\summary.env.example" ".\summary.env"
```

Confirm that the file exists:

```powershell
ls
```

---

## 6. Configure the Summarizer

Open the configuration file:

```powershell
notepad summary.env
```

A typical 1-minute configuration is:

```text
OUTPUT_PATH=C:/Users/username/Documents/CHORDS/Summaries
QC_PROFILE=nadi
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

For a 15-minute station:

```text
OUTPUT_PATH=C:/Users/username/Documents/CHORDS/Summaries
QC_PROFILE=nairobi
EXPECTED_INTERVAL_SECONDS=900
GAP_THRESHOLD_SECONDS=1800
```

For Windows paths in `summary.env`, forward slashes are recommended.

### `OUTPUT_PATH`

Directory where generated CSV files will be saved.

### `QC_PROFILE`

Selects the regional JSON profile from:

```text
configs/
```

For example:

```text
QC_PROFILE=nadi
```

loads:

```text
configs/summary_config_nadi.json
```

### `EXPECTED_INTERVAL_SECONDS`

Expected observation cadence.

Examples:

```text
60
```

for one-minute observations, or:

```text
900
```

for 15-minute observations.

### `GAP_THRESHOLD_SECONDS`

Gap required before observations are inferred to be missing.

Examples:

```text
120
```

for a one-minute station, or:

```text
1800
```

for a 15-minute station.

For more information about regional profiles, see the [Configuration Guide](CONFIGURATION.md).

---

## 7. Run the Summarizer

The input CSV must contain a timestamp column named:

```text
Time
```

Run:

```powershell
python summarize_chords.py "C:\path\to\station_data.csv"
```

For example:

```powershell
python summarize_chords.py "C:\Users\username\Documents\CHORDS\station_data.csv"
```

Quotes are recommended around the path.

A successful run creates:

```text
station_data_15min.csv
station_data_hourly.csv
station_data_daily.csv
station_data_qc_report.csv
```

in the directory specified by `OUTPUT_PATH`.

The first three files contain meteorological statistics.

The QC report contains:

- Observation completeness
- Variable completeness
- Daily completeness
- Partial-day status
- Sentinel removals
- Range QC removals
- Temporal QC removals
- Valid values remaining after QC
- Rain consistency diagnostics

---

# Running the Summarizer Next Time on Windows

The virtual environment and package installation only need to be completed once.

For future runs:

## 1. Navigate to the Repository

```powershell
cd C:\Users\username\Documents\CHORDS\CHORDS_Data_Summarizer-main
```

## 2. Activate the Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Edit Configuration if Necessary

```powershell
notepad summary.env
```

If the existing settings are correct, this step can be skipped.

## 4. Run

```powershell
python summarize_chords.py "C:\path\to\station_data.csv"
```

Normal workflow:

```text
Open PowerShell → Activate → Summarize
```

When changing profiles or cadence:

```text
Open PowerShell → Activate → Configure → Summarize
```

---

# macOS / Linux

## 1. Check Python

```bash
python3 --version
```

---

## 2. Download or Clone the Repository

Using Git:

```bash
git clone https://github.com/3d-paws/CHORDS_Data_Summarizer.git
cd CHORDS_Data_Summarizer
```

Alternatively, download the ZIP file from GitHub and extract it.

---

## 3. Create the Virtual Environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

---

## 4. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Create the Configuration File

```bash
cp summary.env.example summary.env
```

Edit `summary.env` using your preferred text editor.

Example:

```text
OUTPUT_PATH=/Users/username/Documents/CHORDS/Summaries
QC_PROFILE=nadi
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

---

## 6. Run

```bash
python summarize_chords.py /path/to/station_data.csv
```

If the path contains spaces:

```bash
python summarize_chords.py "/path/to/station data.csv"
```

---

# Running the Summarizer Next Time on macOS / Linux

Navigate to the repository:

```bash
cd /path/to/CHORDS_Data_Summarizer
```

Activate the existing environment:

```bash
source .venv/bin/activate
```

Run:

```bash
python summarize_chords.py /path/to/station_data.csv
```

Edit `summary.env` first if the regional profile or observation cadence needs to change.

---

# Updating the Summarizer

## ZIP Installation

Download the newest ZIP file from:

https://github.com/3d-paws/CHORDS_Data_Summarizer

Extract it and configure the new copy.

Do not copy the old `.venv` directory into the new version. Create a new virtual environment and install the current requirements.

Your old `summary.env` can be used as a reference.

---

## Git Installation

From the repository:

```bash
git pull
```

Then activate the virtual environment and update the requirements.

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

# Troubleshooting

## `py` Is Not Recognized on Windows

Install Python 3.10:

```powershell
winget install Python.Python.3.10
```

Close and reopen PowerShell.

Then run:

```powershell
py --list
```

---

## PowerShell Says Running Scripts Is Disabled

Run:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## `ModuleNotFoundError`

Confirm that the virtual environment is active.

The prompt should begin with:

```text
(.venv)
```

Then:

```bash
pip install -r requirements.txt
```

---

## `summary.env` Cannot Be Found

The file must be named exactly:

```text
summary.env
```

and must be in the top-level repository directory alongside:

```text
README.md
summarize_chords.py
requirements.txt
```

---

## QC Profile Cannot Be Found

Check:

```text
QC_PROFILE
```

For example:

```text
QC_PROFILE=nadi
```

requires:

```text
configs/summary_config_nadi.json
```

Do not include:

```text
summary_config_
```

or:

```text
.json
```

in the `QC_PROFILE` value.

---

## Input CSV Cannot Be Found

Check the supplied path.

Windows example:

```powershell
python summarize_chords.py "C:\Users\username\Documents\CHORDS\station_data.csv"
```

---

## Output Is Going to the Wrong Folder

Check:

```text
OUTPUT_PATH
```

in `summary.env`.

Windows example:

```text
OUTPUT_PATH=C:/Users/username/Documents/CHORDS/Summaries
```

---

# Additional Documentation

For profile configuration:

[Configuration Guide](CONFIGURATION.md)

For processing and QC algorithms:

[Technical Details](TECHNICAL_DETAILS.md)

For the short introduction:

[README](../README.md)
