# CHORDS Data Summarizer

The **CHORDS Data Summarizer** is a Python tool for creating quality-controlled meteorological summaries from observational data exported from a CHORDS portal.

It was developed primarily for **3D-PAWS (3D-Printed Automatic Weather Station)** networks and supports both current and legacy 3D-PAWS / FEWS NET station data.

The summarizer:

- Applies configurable quality control
- Identifies missing observations and calculates data completeness
- Produces 15-minute, hourly, and daily summaries
- Handles meteorological processing for temperature, humidity, pressure, wind, precipitation, soil temperature, WBT, WBGT, and other supported measurements
- Supports regional QC profiles and multiple generations of 3D-PAWS variable names

It is developed as a companion to the [CHORDS Data Downloader](https://github.com/3d-paws/CHORDS_Data_Downloader), but either tool can be used independently.

---

## Quick Start

The summarizer requires Python and the packages listed in `requirements.txt`.

### Windows

Open **PowerShell** and navigate to the downloaded or cloned repository.

Create a Python 3.10 virtual environment:

```powershell
py -3.10 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create your local configuration file:

```powershell
Copy-Item ".\summary.env.example" ".\summary.env"
```

Open it for editing:

```powershell
notepad summary.env
```

Then run the summarizer:

```powershell
python summarize_chords.py "C:\path\to\station_data.csv"
```

> If Python 3.10 is not installed or PowerShell prevents virtual environment activation, see the [Installation Guide](docs/INSTALLATION.md).

### macOS / Linux

From the repository directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp summary.env.example summary.env
```

Edit `summary.env`, then run:

```bash
python summarize_chords.py /path/to/station_data.csv
```

---

## Configure the Summarizer

The local `summary.env` file controls the output location, regional QC profile, and expected station observation cadence.

For a 1-minute station:

```text
OUTPUT_PATH=/path/to/CHORDS/Summaries
QC_PROFILE=nadi
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

For a 15-minute station:

```text
OUTPUT_PATH=/path/to/CHORDS/Summaries
QC_PROFILE=nairobi
EXPECTED_INTERVAL_SECONDS=900
GAP_THRESHOLD_SECONDS=1800
```

On Windows, an output path can be written as:

```text
OUTPUT_PATH=C:/Users/username/Documents/CHORDS/Summaries
```

Regional QC profiles are stored in:

```text
configs/
```

For information about selecting, modifying, or creating a profile, see the [Configuration Guide](docs/CONFIGURATION.md).

---

## Output

For an input file such as:

```text
station_data.csv
```

the summarizer creates:

```text
station_data_15min.csv
station_data_hourly.csv
station_data_daily.csv
```

in the directory specified by `OUTPUT_PATH`.

---

## Running It Again

The virtual environment and dependencies only need to be created once.

### Windows

```powershell
cd C:\path\to\CHORDS_Data_Summarizer
.\.venv\Scripts\Activate.ps1
notepad summary.env
python summarize_chords.py "C:\path\to\station_data.csv"
```

### macOS / Linux

```bash
cd /path/to/CHORDS_Data_Summarizer
source .venv/bin/activate
python summarize_chords.py /path/to/station_data.csv
```

If your configuration has not changed, you do not need to edit `summary.env` before every run.

---

## Documentation

Additional documentation is available in the [`docs/`](docs/) directory.

### [Installation Guide](docs/INSTALLATION.md)

Detailed setup instructions for Windows, macOS, and Linux, including Python installation, virtual environments, PowerShell configuration, and troubleshooting.

### [Configuration Guide](docs/CONFIGURATION.md)

Reference for the JSON regional profiles, including:

- Variable mappings and aliases
- QC ranges
- Temporal QC settings
- Summary inclusion
- Completeness settings
- Aggregation statistics
- Creating profiles for new regions or station configurations

### [Technical Details](docs/TECHNICAL_DETAILS.md)

Detailed explanation of how the summarizer processes data, including:

- Missing observation detection
- Observation and variable completeness
- Sentinel and range QC
- Temporal spike/dip QC
- Wind direction and gust processing
- Precipitation processing
- Dual rain gauge comparisons
- Meteorological aggregation

---

## Relationship to the CHORDS Data Downloader

A typical 3D-PAWS workflow is:

```text
CHORDS Portal
      ↓
CHORDS Data Downloader
      ↓
CHORDS CSV
      ↓
CHORDS Data Summarizer
      ↓
15-Minute / Hourly / Daily Summary CSVs
```

The Downloader and Summarizer are maintained separately so that either can be used independently.

---

## Related Projects

- [CHORDS Data Downloader](https://github.com/3d-paws/CHORDS_Data_Downloader)
- [3D-PAWS GitHub Organization](https://github.com/3d-paws)
- [3D-PAWS Manual](https://3dpaws.comet.ucar.edu/)

---

## License

See [LICENSE](LICENSE) for license information.
