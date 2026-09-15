# CHORDS Data Summarizer

A Python tool for creating quality-controlled meteorological summaries from observational data exported from a CHORDS portal.

The CHORDS Data Summarizer is designed primarily for **3D-PAWS weather stations** and related environmental monitoring networks. It converts raw CHORDS observations into standardized 15-minute, hourly, and daily summary files while applying configurable quality-control checks and evaluating data completeness.

The tool is designed to accommodate different station configurations, reporting intervals, sensor combinations, climates, and generations of 3D-PAWS hardware.

## Features

The summarizer currently supports:

* 15-minute, hourly, and daily meteorological summaries
* Configurable regional quality-control profiles
* Explicit station observation intervals
* Observation completeness estimates
* Variable-level completeness
* Missing and sentinel value handling
* Environmental range QC
* Temporal spike/dip QC
* Circular averaging of wind direction
* Maximum wind gust and corresponding gust direction
* Incremental and cumulative precipitation comparisons
* Dual rain gauge stations
* Soil and grass temperature measurements
* Wet Bulb Temperature (WBT)
* Wet Bulb Globe Temperature (WBGT)
* Different station sensor configurations
* Legacy and current 3D-PAWS variable names
* 1-minute and 15-minute observation intervals

Stations do not need to contain every supported measurement. Variables that are not present in the source data are omitted from the resulting summaries.

---

# Requirements

The tool requires Python 3 and the Python packages used by `summarize_chords.py`.

A Python virtual environment is recommended.

For example:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required dependencies for the tool, including:

```bash
pip install pandas numpy python-dotenv
```

---

# Files

A typical installation contains:

```text
summarize_chords.py
summary.env
summary_config_nadi.json
summary_config_addis.json
summary_config_adama.json
summary_config_nairobi.json
```

### `summarize_chords.py`

The main processing script.

### `summary.env`

Defines the output directory, QC profile, expected observation interval, and missing-observation gap threshold.

### `summary_config_*.json`

Regional configuration files containing variable definitions, CHORDS column mappings, QC limits, temporal QC settings, and aggregation rules.

---

# Input Data

The summarizer accepts a CSV containing observations exported from CHORDS.

The file must contain a timestamp column named:

```text
Time
```

The remaining columns contain the environmental measurements available for that CHORDS instrument.

For example:

```text
Time
SHT31D Temperature (degC)
SHT31D Relative Humidity (%)
BMP390 Pressure (hPa)
Wind Speed (m/s)
Wind Direction (deg)
Rain Gauge (mm H2O)
...
```

Older 3D-PAWS and FEWS NET stations may use different names, such as:

```text
SHT Temperature (degC)
BMX Pressure 1 (hPa)
MCP Temperature 1 (degC)
Rain Gauge 1 (mm)
Rain Gauge 1 Total Today (mm/day)
```

Multiple source-column names can be mapped to the same internal measurement through the regional JSON configuration.

This allows the summarizer to process data from different generations of station hardware without requiring the source CSV to be modified.

---

# Running the Summarizer

Run:

```bash
python summarize_chords.py /path/to/file.csv
```

For example:

```bash
python summarize_chords.py \
  /Users/username/Documents/CHORDS/station_data.csv
```

The script reads its settings from:

```text
summary.env
```

---

# Configuration

A typical `summary.env` file looks like:

```text
OUTPUT_PATH=/Users/username/Documents/CHORDS/Summaries

QC_PROFILE=nadi

EXPECTED_INTERVAL_SECONDS=60

GAP_THRESHOLD_SECONDS=120
```

## Output Path

`OUTPUT_PATH` determines where the generated summary CSV files are saved.

For example:

```text
OUTPUT_PATH=/Users/username/Documents/CHORDS/Summaries
```

## QC Profile

`QC_PROFILE` selects the regional JSON configuration used for variable mapping and quality control.

For example:

```text
QC_PROFILE=nadi
```

loads:

```text
summary_config_nadi.json
```

Current profiles include:

```text
nadi
addis
adama
nairobi
```

Regional profiles allow reasonable environmental ranges to be adjusted for different climates and elevations.

For example, station pressure expected at a high-elevation site such as Addis Ababa or Nairobi is substantially lower than station pressure expected near sea level in Fiji.

## Expected Observation Interval

`EXPECTED_INTERVAL_SECONDS` defines how frequently the station is expected to record an observation.

For a 1-minute station:

```text
EXPECTED_INTERVAL_SECONDS=60
```

For a 15-minute station:

```text
EXPECTED_INTERVAL_SECONDS=900
```

The expected interval is intentionally configured rather than automatically inferred.

Stations can experience communications outages while continuing to collect observations locally. Stored observations may later be transmitted after communications are restored.

Automatically inferring the station cadence from gaps in the dataset could therefore mistake a communications or data gap for a change in station configuration.

The configured observation interval represents the intended measurement cadence.

## Gap Threshold

`GAP_THRESHOLD_SECONDS` determines when the time between observations becomes large enough to infer that one or more observations are missing.

For a nominal 1-minute station:

```text
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

For a nominal 15-minute station:

```text
EXPECTED_INTERVAL_SECONDS=900
GAP_THRESHOLD_SECONDS=1800
```

The gap threshold allows normal timestamp variation without incorrectly identifying observations as missing.

---

# Output Files

For each input file, the summarizer creates:

```text
<filename>_15min.csv
<filename>_hourly.csv
<filename>_daily.csv
```

For example:

```text
station_data_15min.csv
station_data_hourly.csv
station_data_daily.csv
```

The exact measurements included in each file depend on the sensors available in the input data and the selected configuration profile.

---

# Observation Completeness

Each summary period contains:

```text
Observation Count
Estimated Missed Observations
Observation Completeness (%)
```

Observation completeness describes whether the station produced the expected number of observations.

Missing observations are inferred from the measurement timestamps in the original dataset using the configured expected observation interval and gap threshold.

Importantly, missing observations are determined **before environmental QC is applied**.

This distinguishes between:

* an observation that was never recorded or is absent from the dataset, and
* an observation that exists but contains an invalid sensor measurement.

For example, if the station reports normally but one temperature measurement contains `-999.9`, the observation itself is still counted as received. The temperature measurement will instead affect the completeness of that individual variable.

---

# Variable Completeness

The summarizer can also calculate completeness for individual environmental variables.

Variable completeness accounts for both:

* observations missing from the dataset, and
* measurements removed by QC.

For example:

```text
Observation Completeness (%)       98.0
SHT Temperature Completeness (%)   97.5
Wind Direction Completeness (%)    91.2
```

This makes it possible to distinguish between a station-level data outage and a problem affecting an individual sensor.

---

# Quality Control

Quality control is applied before meteorological summary statistics are calculated.

QC behavior is defined in the selected regional JSON configuration.

## Missing and Sentinel Values

3D-PAWS sensors may use large negative values to represent missing measurements or sensor errors.

For example:

```text
-999.9
```

The configuration defines a missing-value threshold:

```json
"missing_value_threshold": -900
```

Numeric measurements at or below this threshold are treated as missing and excluded from summary calculations.

## Range QC

Individual measurements can have configurable minimum and maximum acceptable values.

For example:

```json
"min": 10,
"max": 45
```

Values outside this range are converted to missing values before aggregation.

QC ranges are defined by profile because reasonable environmental limits vary by climate and station elevation.

These limits are intended as practical first-pass engineering QC rather than universal climatological limits.

## Temporal Spike/Dip QC

Selected variables can also be checked for isolated temporal spikes or dips.

The algorithm compares a measurement with valid observations immediately before and after it.

A measurement can be rejected when:

* it differs substantially from the preceding observation,
* it differs substantially from the following observation,
* the observations on either side remain reasonably consistent with each other,
* the change occurs rapidly enough to meet the configured rate threshold, and
* the neighboring observations are sufficiently close in time.

This allows isolated sensor errors to be removed without rejecting legitimate gradual environmental changes.

Temporal QC parameters are configured independently for each measurement.

---

# Summary Statistics

Different meteorological variables require different aggregation methods.

The aggregation rules are defined in the regional configuration files.

## Temperature

For primary air-temperature measurements:

**15-minute**

```text
Mean
```

**Hourly**

```text
Mean
```

**Daily**

```text
Mean
Minimum
Maximum
```

This applies to supported temperature measurements such as SHT, BMP/BMX, MCP, soil temperature, and grass temperature where configured.

## Relative Humidity

**15-minute:** mean
**Hourly:** mean
**Daily:** mean, minimum, maximum

## Atmospheric Pressure

Station pressure and mean sea level pressure use:

**15-minute:** mean
**Hourly:** mean
**Daily:** mean, minimum, maximum

## Wet Bulb Temperature

WBT is summarized using the maximum value for each period:

```text
Maximum
```

## Wet Bulb Globe Temperature

WBGT is also summarized using:

```text
Maximum
```

---

# Wind

Wind direction requires circular rather than arithmetic averaging.

For example, the arithmetic mean of:

```text
359°
1°
```

would incorrectly produce approximately:

```text
180°
```

The summarizer instead calculates a circular mean, correctly producing a direction near:

```text
0° / North
```

Wind-direction summaries include both degrees and a compass direction.

Wind speed includes:

```text
Mean
Maximum
```

Wind gust includes:

```text
Mean
Maximum
```

The direction associated with the maximum gust is taken from the same source observation as the maximum gust.

This produces outputs such as:

```text
Wind Gust Maximum (m/s)
Maximum Wind Gust Direction (deg)
Maximum Wind Gust Direction (Compass)
```

---

# Precipitation

The summarizer supports both single- and dual-rain-gauge stations.

Incremental rain measurements are summed within each summary period.

For example:

```text
Rain Gauge 1 Sum (mm H2O)
```

When cumulative rain counters are available, the summarizer independently calculates the change in the cumulative counter.

This allows the incremental and cumulative measurements to be compared.

Outputs can include:

```text
Rain Gauge 1 Sum
Rain Gauge 1 Cumulative Rain Total
Rain Gauge 1 Cumulative Total Change
Rain Gauge 1 Sum vs Cumulative Change Difference
```

## Cumulative Counter Resets

Cumulative rain counters can reset.

When the cumulative value decreases, the summarizer interprets the new cumulative value as rainfall accumulated after a counter reset rather than treating the decrease as negative rainfall.

## Dual Rain Gauges

Stations with two gauges additionally include comparisons between the gauges.

For example:

```text
Rain Gauge 1 Sum
Rain Gauge 2 Sum
Rain Gauge 1 vs 2 Difference
```

The difference is calculated as:

```text
Rain Gauge 1 - Rain Gauge 2
```

Similar comparisons are made between the cumulative rain measurements when available.

These comparisons can help identify disagreement between redundant precipitation sensors.

---

# Regional QC Profiles

Regional profiles are JSON files named:

```text
summary_config_<profile>.json
```

For example:

```text
summary_config_nadi.json
summary_config_addis.json
summary_config_adama.json
summary_config_nairobi.json
```

Each profile defines:

* accepted source-column names
* internal variable mapping
* display names
* units
* measurement type
* QC enable/disable settings
* acceptable ranges
* temporal QC parameters
* summary inclusion
* completeness inclusion
* aggregation statistics

A new regional profile can be created by copying an existing configuration and adjusting its environmental QC limits as appropriate.

---

# Variable Mapping

CHORDS variable names have changed across different versions of 3D-PAWS firmware and station configurations.

The summarizer uses aliases in the configuration files to map these different names to common internal variables.

For example:

```json
"mt1": {
  "display_name": "MCP Temperature",
  "source_columns": [
    "MCP9808 Temperature (degC)",
    "MCP Temperature 1 (degC)"
  ]
}
```

Both source columns are therefore treated as the same type of measurement.

This approach allows older FEWS NET stations and newer 3D-PAWS stations to use the same summarization software.

---

# Console Output

While processing a file, the summarizer reports information including:

```text
Expected observation interval
Missing-observation gap threshold
Inferred missing observations
QC profile
Mapped CHORDS variables
Configured variables not present
Unmapped source columns
QC values removed
Temporal spikes/dips removed
Source observation count
Observation period
Generated output files
```

The mapping output is particularly useful when processing a station configuration for the first time.

Unexpected entries under:

```text
Unmapped source columns
```

may indicate that an additional source-column alias should be added to the configuration.

---

# Design Philosophy

The CHORDS Data Summarizer is intended as a practical first-pass processing and quality-control tool for operational environmental monitoring data.

It is designed to:

* preserve valid observations,
* identify obvious sensor errors,
* handle different station configurations,
* make data gaps visible,
* produce meteorologically meaningful summary statistics, and
* avoid silently making assumptions about station behavior.

QC thresholds are configurable and should be reviewed for the environment and station network in which they are used.

The output should not be interpreted as a replacement for network-specific climatological QC or expert review.

---

# Known Limitations

The expected observation interval currently applies to the entire input file.

If a station's configured measurement interval changed historically—for example, from 15-minute to 1-minute observations—the file should be processed with consideration of the appropriate configuration periods.

The first cumulative precipitation observation in a file cannot determine how much rainfall occurred between that observation and an observation preceding the beginning of the file.

Sensor availability and variable naming can differ between station generations. New aliases may occasionally need to be added to a configuration profile.

QC thresholds are regional engineering thresholds and are not intended to represent official WMO climatological limits.

---

# Possible Future Improvements

Potential future enhancements include:

* Persistence or stuck-sensor detection
* Identification of measurements that remain exactly zero for extended periods
* Identification of measurements that remain unchanged for a configurable period
* Report-only QC flags in addition to removing invalid measurements
* Explicit support for historical changes in station observation cadence
* Additional regional QC profiles
* Additional environmental sensors
* Expanded QC reporting and diagnostics

Persistence/stuck-value detection would initially be most useful as a **diagnostic flag rather than an automatic data-removal rule**, since some measurements can legitimately remain constant for extended periods.

---

# Status

The summarizer has been tested with:

* 1-minute station observations
* 15-minute station observations
* timestamp jitter
* missing observations and communications gaps
* standard 3D-PAWS stations
* legacy FEWS NET station variable names
* full weather-station configurations
* sparse sensor configurations
* single and dual rain gauges
* wind speed, direction, gust, and gust direction
* soil and grass temperature sensors
* missing/sentinel sensor values
* environmental range QC
* temporal spike/dip QC
* regional QC profiles
* observation and variable completeness calculations

The tool is currently intended for operational testing and continued development.
