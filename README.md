# CHORDS Data Summarizer

A Python tool for creating quality-controlled meteorological summaries from observational data exported from CHORDS.

The CHORDS Data Summarizer is designed primarily for **3D-PAWS weather stations** and related environmental monitoring networks. It converts CHORDS CSV observations into standardized **15-minute, hourly, and daily summaries** while applying configurable quality-control checks and evaluating data completeness.

## Features

* 15-minute, hourly, and daily meteorological summaries
* Configurable regional quality-control profiles
* Observation and variable-level completeness
* Missing/sentinel value and environmental range QC
* Temporal spike/dip QC
* Circular wind-direction averaging and maximum gust direction
* Incremental and cumulative precipitation comparisons
* Single and dual rain gauge support
* Soil and grass temperature support
* Wet Bulb Temperature (WBT) and Wet Bulb Globe Temperature (WBGT)
* Support for current and legacy 3D-PAWS variable names
* Configurable observation intervals, including 1-minute and 15-minute stations

Stations do not need to contain every supported measurement. Variables that are not present in the source data are omitted from the resulting summaries.

## Installation

Clone the repository:

```bash id="66icw2"
git clone https://github.com/3d-paws/CHORDS_Data_Summarizer.git
cd CHORDS_Data_Summarizer
```

Create and activate a Python virtual environment:

```bash id="dpx0sa"
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash id="rj5p2v"
.venv\Scripts\activate
```

Install the required packages:

```bash id="0a89e8"
pip install -r requirements.txt
```

## Configuration

Copy the example environment file:

```bash id="fjx33k"
cp summary.env.example summary.env
```

Then edit `summary.env` for the station being processed.

For a station recording observations approximately once per minute:

```text id="z04ycp"
OUTPUT_PATH=/path/to/CHORDS/Summaries
QC_PROFILE=nadi
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

For a station recording observations every 15 minutes:

```text id="7fj3zs"
OUTPUT_PATH=/path/to/CHORDS/Summaries
QC_PROFILE=nairobi
EXPECTED_INTERVAL_SECONDS=900
GAP_THRESHOLD_SECONDS=1800
```

### Configuration Options

* **`OUTPUT_PATH`** — Directory where summary files will be saved.
* **`QC_PROFILE`** — Regional QC configuration to use.
* **`EXPECTED_INTERVAL_SECONDS`** — Expected time between station observations.
* **`GAP_THRESHOLD_SECONDS`** — Gap required before missing observations are inferred.

The expected observation interval is explicitly configured rather than automatically inferred so that communications outages, stored observations, and later data backfills are not mistaken for changes in station measurement cadence.

## Regional QC Profiles

Regional QC profiles are stored in:

```text id="k5v9pb"
configs/
```

Current profiles include:

| Profile   | Region                |
| --------- | --------------------- |
| `nadi`    | Nadi, Fiji            |
| `addis`   | Addis Ababa, Ethiopia |
| `adama`   | Adama, Ethiopia       |
| `nairobi` | Nairobi, Kenya        |

Profiles define variable mappings, acceptable environmental ranges, temporal QC settings, summary statistics, and other variable-specific behavior.

Different profiles allow QC limits to account for differences in climate and station elevation.

## Usage

Run the summarizer with a CHORDS CSV file:

```bash id="nd7ljj"
python summarize_chords.py /path/to/station_data.csv
```

For example:

```bash id="hh0sxw"
python summarize_chords.py \
  /Users/username/Documents/CHORDS/station_data.csv
```

The input CSV must contain a CHORDS timestamp column named:

```text id="ql1zj2"
Time
```

The script automatically maps supported CHORDS measurement columns using the selected QC profile.

During processing, the console reports variable mappings, missing observations, QC results, unmapped columns, and generated output files.

## Output

Each input file produces:

```text id="8duj6k"
<filename>_15min.csv
<filename>_hourly.csv
<filename>_daily.csv
```

The exact output columns depend on the measurements available for the station.

Summary files can include:

* Temperature, relative humidity, and pressure statistics
* Wind speed, direction, gust, and gust direction
* Incremental and cumulative precipitation
* Dual rain gauge comparisons
* Soil and grass temperature
* WBT and WBGT
* Observation completeness
* Individual variable completeness

## Quality Control

Quality control is applied before summary statistics are calculated.

The summarizer currently supports:

* Missing and sentinel value detection
* Configurable environmental range checks
* Temporal spike/dip detection

QC settings are defined independently for each measurement in the selected regional profile.

The regional limits are intended as practical **first-pass engineering QC** and are not a replacement for network-specific climatological QC or expert review.

## Observation Completeness

Each summary period includes:

```text id="1lnb6j"
Observation Count
Estimated Missed Observations
Observation Completeness (%)
```

Missing observations are determined from measurement timestamps using the configured observation interval.

Individual variables can also report their own completeness. This helps distinguish between a station-level data gap and a problem affecting an individual sensor.

## Meteorological Processing

The summarizer uses measurement-appropriate aggregation methods.

Examples include:

* Mean temperature, humidity, and pressure for 15-minute and hourly summaries
* Mean, minimum, and maximum temperature, humidity, and pressure for daily summaries
* Circular averaging for wind direction
* Mean and maximum wind speed and gust
* Wind direction corresponding to the maximum gust
* Maximum WBT and WBGT
* Summed incremental precipitation
* Reset-aware cumulative precipitation changes
* Comparisons between redundant rain gauges

Detailed calculation and QC methods are documented in [`docs/TECHNICAL_DETAILS.md`](docs/TECHNICAL_DETAILS.md).

## Legacy Station Support

3D-PAWS variable names have changed across different hardware, firmware, and station configurations.

Regional configuration files can define multiple CHORDS column aliases for the same measurement. This allows newer 3D-PAWS stations and older configurations, including legacy FEWS NET stations, to use the same summarization tool.

## Known Limitations

* The configured observation interval currently applies to the entire input file.
* The first cumulative precipitation observation cannot determine rainfall that occurred before the beginning of the file.
* New station configurations may require additional CHORDS column aliases.
* Regional QC limits should be reviewed before applying a profile to substantially different environmental conditions.
* Persistence/stuck-sensor QC is not currently implemented.

## Technical Documentation

For details about the processing algorithms, QC logic, completeness calculations, precipitation handling, wind calculations, and regional configuration format, see:

[`docs/TECHNICAL_DETAILS.md`](docs/TECHNICAL_DETAILS.md)

## Related Projects

The CHORDS Data Summarizer operates independently on compatible CHORDS CSV files.

Tools for downloading 3D-PAWS observations from CHORDS are available separately in the [3D-PAWS GitHub organization](https://github.com/3d-paws).
