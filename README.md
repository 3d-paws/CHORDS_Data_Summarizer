# CHORDS Data Summarizer

A Python tool for creating quality-controlled meteorological summaries from observational data exported from CHORDS.

The CHORDS Data Summarizer is designed primarily for **3D-PAWS weather stations** and related environmental monitoring networks. It converts CHORDS CSV observations into standardized **15-minute, hourly, and daily summaries** while applying configurable quality-control checks and evaluating data completeness.

This tool was developed as a companion to the [CHORDS Data Downloader](https://github.com/3d-paws/CHORDS_Data_Downloader).

## Features

- 15-minute, hourly, and daily meteorological summaries
- Configurable regional quality-control profiles
- Observation and variable-level completeness
- Missing/sentinel value and environmental range QC
- Temporal spike/dip QC
- Circular wind-direction averaging
- Maximum wind gust and corresponding gust direction
- Incremental and cumulative precipitation comparisons
- Single and dual rain gauge support
- Soil and grass temperature support
- Wet Bulb Temperature (WBT) and Wet Bulb Globe Temperature (WBGT)
- Support for current and legacy 3D-PAWS variable names
- Configurable observation intervals, including 1-minute and 15-minute stations

Stations do not need to contain every supported measurement. Variables that are not present in the source data are omitted from the resulting summaries.

## Installation

Clone the repository:

```bash
git clone https://github.com/3d-paws/CHORDS_Data_Summarizer.git
cd CHORDS_Data_Summarizer
```

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

Copy the example environment file:

```bash
cp summary.env.example summary.env
```

Then edit `summary.env` for the station being processed.

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

### Configuration Options

- **`OUTPUT_PATH`** — Directory where summary files will be saved.
- **`QC_PROFILE`** — Regional QC configuration to use.
- **`EXPECTED_INTERVAL_SECONDS`** — Expected time between station observations.
- **`GAP_THRESHOLD_SECONDS`** — Gap required before missing observations are inferred.

The expected observation interval is explicitly configured so that communications outages, stored observations, and later data backfills are not mistaken for changes in station measurement cadence.

## Regional QC Profiles

Regional QC profiles are stored in the `configs/` directory.

Current profiles include:

| Profile | Region |
| --- | --- |
| `nadi` | Nadi, Fiji |
| `addis` | Addis Ababa, Ethiopia |
| `adama` | Adama, Ethiopia |
| `nairobi` | Nairobi, Kenya |

Profiles define variable mappings, environmental QC ranges, temporal QC settings, summary statistics, and other variable-specific behavior.

## Usage

Run the summarizer with a CHORDS CSV file:

```bash
python summarize_chords.py /path/to/station_data.csv
```

For example:

```bash
python summarize_chords.py /Users/username/Documents/CHORDS/station_data.csv
```

The input CSV must contain a CHORDS timestamp column named `Time`.

During processing, the script reports variable mappings, missing observations, QC results, unmapped columns, and generated output files.

## Output

Each input file produces:

```text
<filename>_15min.csv
<filename>_hourly.csv
<filename>_daily.csv
```

Depending on the station configuration, summaries can include:

- Temperature, relative humidity, and pressure
- Wind speed, direction, gust, and gust direction
- Incremental and cumulative precipitation
- Dual rain gauge comparisons
- Soil and grass temperature
- WBT and WBGT
- Observation completeness
- Individual variable completeness

## Quality Control

Quality control is applied before summary statistics are calculated.

The summarizer currently supports:

- Missing and sentinel value detection
- Configurable environmental range checks
- Temporal spike/dip detection

Regional QC limits are intended as practical **first-pass engineering QC** and are not a replacement for network-specific climatological QC or expert review.

## Observation Completeness

Each summary period includes:

- **Observation Count**
- **Estimated Missed Observations**
- **Observation Completeness (%)**

Individual variables can also report their own completeness. This helps distinguish between a station-level data gap and a problem affecting an individual sensor.

## Meteorological Processing

The summarizer uses measurement-appropriate aggregation methods, including:

- Mean temperature, humidity, and pressure
- Daily minimum and maximum values
- Circular averaging of wind direction
- Mean and maximum wind speed and gust
- Wind direction corresponding to the maximum gust
- Maximum WBT and WBGT
- Summed incremental precipitation
- Reset-aware cumulative precipitation changes
- Comparisons between redundant rain gauges

For details about these calculations and QC methods, see [Technical Details](docs/TECHNICAL_DETAILS.md).

## Relationship to the CHORDS Data Downloader

The CHORDS Data Summarizer was developed as a companion to the [CHORDS Data Downloader](https://github.com/3d-paws/CHORDS_Data_Downloader).

The two tools serve different parts of the workflow:

- **CHORDS Data Downloader** — retrieves observational data from CHORDS portals and exports it to CSV.
- **CHORDS Data Summarizer** — processes compatible CHORDS CSV files into quality-controlled meteorological summaries.

They are maintained separately so that either tool can be used independently. The summarizer can process compatible CHORDS CSV files regardless of how they were obtained.

## Documentation

More detailed information about completeness calculations, QC algorithms, wind processing, precipitation handling, and configuration profiles is available in:

**[Technical Details](docs/TECHNICAL_DETAILS.md)**

## Known Limitations

- The configured observation interval currently applies to the entire input file.
- The first cumulative precipitation observation cannot determine rainfall that occurred before the beginning of the file.
- New station configurations may require additional CHORDS column aliases.
- Regional QC limits should be reviewed before applying a profile to substantially different environmental conditions.
- Persistence/stuck-sensor QC is not currently implemented.

## Related Projects

- [CHORDS Data Downloader](https://github.com/3d-paws/CHORDS_Data_Downloader)
- [3D-PAWS GitHub Organization](https://github.com/3d-paws)
