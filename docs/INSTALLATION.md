# CHORDS Data Summarizer — Installation Guide

This guide explains how to install and run the **CHORDS Data Summarizer** on Windows, macOS, or Linux.

The summarizer is a Python program that processes CHORDS CSV files and creates quality-controlled 15-minute, hourly, and daily meteorological summaries.

GitHub Repository:

https://github.com/3d-paws/CHORDS_Data_Summarizer

---

# Windows

The recommended way to run the CHORDS Data Summarizer on Windows is using **Windows PowerShell** and Python 3.10.

## 1. Install Python

Open **Windows PowerShell** and check which Python versions are installed:

```powershell
py --list
```

Look for Python 3.10 in the list.

If Python 3.10 is not installed, install it with:

```powershell
winget install Python.Python.3.10
```

After installation, close and reopen PowerShell.

Confirm that Python 3.10 is available:

```powershell
py -3.10 --version
```

You should see a Python 3.10 version reported.

---

## 2. Download the CHORDS Data Summarizer

Go to:

https://github.com/3d-paws/CHORDS_Data_Summarizer

Select:

**Code → Download ZIP**

Extract the ZIP file to a convenient location, such as your Documents folder.

For example:

```text
C:\Users\username\Documents\CHORDS\CHORDS_Data_Summarizer-main
```

Open PowerShell and navigate to the extracted repository:

```powershell
cd C:\Users\username\Documents\CHORDS\CHORDS_Data_Summarizer-main
```

The exact path will depend on where you extracted the repository.

### Using Git Instead

If Git is already installed, you can clone the repository instead:

```powershell
git clone https://github.com/3d-paws/CHORDS_Data_Summarizer.git
```

Then enter the repository:

```powershell
cd CHORDS_Data_Summarizer
```

Git is not required to use the summarizer.

---

## 3. Create the Python Virtual Environment

A Python virtual environment keeps the packages required by the summarizer separate from other Python software installed on the computer.

From inside the CHORDS Data Summarizer directory, create the environment using Python 3.10:

```powershell
py -3.10 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the PowerShell prompt should begin with:

```text
(.venv)
```

For example:

```text
(.venv) PS C:\Users\username\Documents\CHORDS\CHORDS_Data_Summarizer-main>
```

### If PowerShell Blocks the Activation Script

PowerShell may display an error stating that running scripts is disabled.

Run:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Confirm the change if prompted.

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 4. Install the Required Python Packages

Make sure `(.venv)` appears at the beginning of the PowerShell prompt.

Upgrade `pip`:

```powershell
python -m pip install --upgrade pip
```

Install the packages required by the summarizer:

```powershell
pip install -r requirements.txt
```

The required packages are:

- pandas
- numpy
- python-dotenv

These installation steps only need to be completed once for this virtual environment.

---

## 5. Create the Configuration File

The repository includes an example configuration file:

```text
summary.env.example
```

The summarizer reads its local settings from a file named:

```text
summary.env
```

From the top-level repository directory, create it by running:

```powershell
Copy-Item ".\summary.env.example" ".\summary.env"
```

Confirm that the new file exists:

```powershell
ls
```

You should see both:

```text
summary.env
summary.env.example
```

---

## 6. Configure the Summarizer

Open the configuration file in Notepad:

```powershell
notepad summary.env
```

A configuration for a 1-minute station might look like:

```text
OUTPUT_PATH=C:/Users/username/Documents/CHORDS/Summaries
QC_PROFILE=nadi
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

For Windows paths in `summary.env`, forward slashes are recommended:

```text
C:/Users/username/Documents/CHORDS/Summaries
```

rather than:

```text
C:\Users\username\Documents\CHORDS\Summaries
```

### `OUTPUT_PATH`

The folder where the generated summary CSV files will be saved.

For example:

```text
OUTPUT_PATH=C:/Users/username/Documents/CHORDS/Summaries
```

### `QC_PROFILE`

Selects the regional configuration profile.

For example:

```text
QC_PROFILE=nadi
```

loads:

```text
configs/summary_config_nadi.json
```

Current profiles include:

```text
nadi
addis
adama
nairobi
```

See the [Configuration Guide](CONFIGURATION.md) for information about these profiles and how to create or modify one.

### `EXPECTED_INTERVAL_SECONDS`

The expected time between station observations.

For a station reporting every minute:

```text
EXPECTED_INTERVAL_SECONDS=60
```

For a station reporting every 15 minutes:

```text
EXPECTED_INTERVAL_SECONDS=900
```

### `GAP_THRESHOLD_SECONDS`

The time gap at which the summarizer begins identifying missing observations.

For a 1-minute station:

```text
GAP_THRESHOLD_SECONDS=120
```

For a 15-minute station:

```text
GAP_THRESHOLD_SECONDS=1800
```

### Example 15-Minute Configuration

```text
OUTPUT_PATH=C:/Users/username/Documents/CHORDS/Summaries
QC_PROFILE=nairobi
EXPECTED_INTERVAL_SECONDS=900
GAP_THRESHOLD_SECONDS=1800
```

Save and close Notepad when finished.

---

## 7. Run the Summarizer

The summarizer processes a CSV file exported from CHORDS.

The CSV must contain a timestamp column named:

```text
Time
```

With the virtual environment active, run:

```powershell
python summarize_chords.py "C:\path\to\station_data.csv"
```

For example:

```powershell
python summarize_chords.py "C:\Users\username\Documents\CHORDS\station_data.csv"
```

Quotes are recommended around the input path, especially if any folder or filename contains spaces.

The summarizer will display information about:

- The selected QC profile
- CHORDS variables that were mapped
- Configured variables that were not present
- Unmapped source columns
- QC results
- Missing observations
- Observation period
- Generated summary files

A successful run will create:

```text
station_data_15min.csv
station_data_hourly.csv
station_data_daily.csv
```

in the folder specified by `OUTPUT_PATH`.

---

# Running the Summarizer Next Time on Windows

The Python installation, virtual environment, package installation, and creation of `summary.env` only need to be completed once.

For future runs:

## 1. Open PowerShell and Navigate to the Summarizer

```powershell
cd C:\Users\username\Documents\CHORDS\CHORDS_Data_Summarizer-main
```

## 2. Activate the Existing Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Edit the Configuration if Necessary

If you need to change the output location, QC profile, or expected station cadence:

```powershell
notepad summary.env
```

If the existing settings are correct, this step can be skipped.

## 4. Run the Summarizer

```powershell
python summarize_chords.py "C:\path\to\station_data.csv"
```

The normal workflow after initial setup is therefore:

```text
Open PowerShell → Activate → Summarize
```

or, when changing configurations:

```text
Open PowerShell → Activate → Configure → Summarize
```

---

# macOS / Linux

## 1. Install Python

Check that Python 3 is installed:

```bash
python3 --version
```

If Python is not installed, install a current Python 3 version using the normal installation method for your operating system.

---

## 2. Download the CHORDS Data Summarizer

The repository can be downloaded from:

https://github.com/3d-paws/CHORDS_Data_Summarizer

Select:

**Code → Download ZIP**

Extract the repository and navigate to it in Terminal.

If Git is installed, you can instead clone it:

```bash
git clone https://github.com/3d-paws/CHORDS_Data_Summarizer.git
cd CHORDS_Data_Summarizer
```

---

## 3. Create the Python Virtual Environment

From the repository directory:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

The Terminal prompt should now begin with:

```text
(.venv)
```

---

## 4. Install the Required Python Packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

These steps only need to be completed once.

---

## 5. Create the Configuration File

Run:

```bash
cp summary.env.example summary.env
```

Open `summary.env` in your preferred text editor.

For example:

```text
OUTPUT_PATH=/Users/username/Documents/CHORDS/Summaries
QC_PROFILE=nadi
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

See the [Configuration Guide](CONFIGURATION.md) for detailed configuration information.

---

## 6. Run the Summarizer

With the virtual environment active:

```bash
python summarize_chords.py /path/to/station_data.csv
```

If the path contains spaces, place it in quotes:

```bash
python summarize_chords.py "/path/to/station data.csv"
```

The generated summary files will be written to the directory specified by `OUTPUT_PATH`.

---

# Running the Summarizer Next Time on macOS / Linux

Navigate to the repository:

```bash
cd /path/to/CHORDS_Data_Summarizer
```

Activate the existing virtual environment:

```bash
source .venv/bin/activate
```

Then run the summarizer:

```bash
python summarize_chords.py /path/to/station_data.csv
```

Edit `summary.env` first if the profile or station cadence needs to change.

---

# Updating the Summarizer

How the summarizer is updated depends on how it was downloaded.

## If You Downloaded a ZIP File

Download the latest ZIP file from:

https://github.com/3d-paws/CHORDS_Data_Summarizer

The new copy will contain the latest:

- Python code
- Configuration profiles
- Documentation
- Requirements

Your existing `summary.env` contains your local settings and can be used as a reference when configuring the new copy.

After downloading a new version, create a new virtual environment and install the current requirements rather than copying the old `.venv` directory.

## If You Used Git

Navigate to the repository and run:

```bash
git pull
```

Activate the virtual environment and update the requirements:

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

# Troubleshooting

## `py` Is Not Recognized on Windows

Check that Python is installed.

Python 3.10 can be installed with:

```powershell
winget install Python.Python.3.10
```

Close and reopen PowerShell after installation.

Then check:

```powershell
py --list
```

---

## PowerShell Says Running Scripts Is Disabled

Run:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## `ModuleNotFoundError`

Make sure the virtual environment is active.

The prompt should begin with:

```text
(.venv)
```

Then install the requirements again:

```bash
pip install -r requirements.txt
```

---

## The Configuration File Cannot Be Found

Confirm that the file is named exactly:

```text
summary.env
```

and is located in the top-level repository directory alongside:

```text
README.md
summarize_chords.py
requirements.txt
```

On Windows, you can check with:

```powershell
ls
```

---

## A QC Profile Cannot Be Found

Check the value of:

```text
QC_PROFILE
```

in `summary.env`.

For example:

```text
QC_PROFILE=nadi
```

requires:

```text
configs/summary_config_nadi.json
```

The profile name should not include:

```text
summary_config_
```

or:

```text
.json
```

See the [Configuration Guide](CONFIGURATION.md) for more information.

---

## The Input CSV Cannot Be Found

Check the path passed to the summarizer.

On Windows, using quotes around the full path is recommended:

```powershell
python summarize_chords.py "C:\Users\username\Documents\CHORDS\station_data.csv"
```

---

## The Output Directory Is Incorrect

Check:

```text
OUTPUT_PATH
```

in `summary.env`.

On Windows, use forward slashes:

```text
OUTPUT_PATH=C:/Users/username/Documents/CHORDS/Summaries
```

---

# Additional Documentation

For information about configuring regional profiles, variables, aliases, and QC thresholds, see:

[Configuration Guide](CONFIGURATION.md)

For details about the QC, completeness, wind, precipitation, and aggregation algorithms, see:

[Technical Details](TECHNICAL_DETAILS.md)

For a shorter introduction and quick-start workflow, return to:

[README](../README.md)
