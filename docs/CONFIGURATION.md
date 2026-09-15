# Configuration Guide

This guide explains how to configure the **CHORDS Data Summarizer** for different stations, sensors, and environmental regions.

The summarizer uses JSON configuration profiles to define:

- How CHORDS columns map to measurements
- How measurements are named in summary files
- Which measurements receive quality control
- Acceptable environmental ranges
- Temporal spike/dip detection settings
- Which measurements appear in summaries
- Which measurements receive completeness calculations
- Which statistics are calculated at each summary interval

For details about how the underlying QC and aggregation algorithms work, see [Technical Details](TECHNICAL_DETAILS.md).

---

## Configuration Profiles

Configuration profiles are stored in:

```text
configs/
```

and follow the naming convention:

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

The profile used by the summarizer is selected in `summary.env`:

```text
QC_PROFILE=nadi
```

This loads:

```text
configs/summary_config_nadi.json
```

Profiles are intended to allow the same summarization code to be used with different:

- Station configurations
- Sensor combinations
- CHORDS variable names
- Climates
- Elevations
- Generations of 3D-PAWS hardware and firmware

---

# Variable Definitions

Each supported measurement has an internal variable name such as:

```text
st1
sh1
bp1
ws
wd
rg
```

These internal names correspond to the variable tags used by 3D-PAWS.

A typical configuration entry looks like:

```json
"st1": {
  "display_name": "SHT31D Temperature",
  "unit": "degC",
  "source_columns": [
    "SHT31D Temperature (degC)",
    "SHT Temperature (degC)"
  ],
  "type": "measurement",
  "qc_enabled": true,
  "temporal_qc_enabled": true,
  "include_in_summary": true,
  "include_completeness": true,
  "min": 10,
  "max": 45,
  "spike_threshold": 3.0,
  "neighbor_tolerance": 1.5,
  "max_rate_change_per_minute": 3.0,
  "spike_max_neighbor_gap_seconds": 1200,
  "statistics": {
    "15min": ["mean"],
    "hourly": ["mean"],
    "daily": ["mean", "min", "max"]
  }
}
```

The following sections explain each field.

---

# `display_name`

```json
"display_name": "SHT31D Temperature"
```

The human-readable name used when identifying the measurement and creating summary output columns.

The display name does not need to match the original CHORDS column name.

For example, several generations of a sensor may all be presented as:

```text
SHT31D Temperature
```

even if their source column names differ.

---

# `unit`

```json
"unit": "degC"
```

Defines the measurement unit used when naming summary columns.

Examples include:

```text
degC
%
hPa
m/s
deg
mm H2O
```

The configuration does **not** perform unit conversion. The configured unit should therefore describe the units of the mapped source measurement.

---

# `source_columns`

```json
"source_columns": [
  "SHT31D Temperature (degC)",
  "SHT Temperature (degC)"
]
```

Defines the CHORDS column names that may represent this measurement.

This is one of the most important parts of the configuration system.

3D-PAWS variable names have changed across different:

- Sensors
- Firmware versions
- Station generations
- Projects
- CHORDS instruments

Aliases allow these different names to map to a common internal variable.

For example:

```json
"source_columns": [
  "MCP9808 Temperature (degC)",
  "MCP Temperature 1 (degC)"
]
```

allows both newer and older MCP9808 measurements to map to:

```text
mt1
```

Similarly, legacy FEWS NET stations may contain names such as:

```text
BMX Temperature 1 (degC)
BMX Pressure 1 (hPa)
HTU Temperature 1 (degC)
HTU Humidity 1 (%)
```

These can be mapped to the appropriate internal measurements through aliases.

## Adding an Alias

If the summarizer reports:

```text
Unmapped source columns:
```

and the column represents a measurement already supported by the configuration, add its exact CHORDS column name to `source_columns`.

For example, changing:

```json
"source_columns": [
  "SHT31D Temperature (degC)"
]
```

to:

```json
"source_columns": [
  "SHT31D Temperature (degC)",
  "SHT Temperature (degC)"
]
```

adds support for the legacy name without changing the summarization code.

Do not create a new internal variable simply because a sensor has a different CHORDS display name if it represents the same measurement.

---

# `type`

```json
"type": "measurement"
```

Identifies the general role of the configured variable.

Environmental observations that are summarized normally use:

```text
measurement
```

Operational variables such as station health, battery, and cellular information may also be mapped by the configuration even when they are not included in meteorological summaries.

Do not introduce a new `type` value unless it is supported by `summarize_chords.py`.

---

# `qc_enabled`

```json
"qc_enabled": true
```

Controls whether environmental range QC is applied to the measurement.

When:

```json
"qc_enabled": true
```

the configured `min` and `max` values are used to determine whether a measurement is within the accepted range.

When:

```json
"qc_enabled": false
```

the environmental range test is not applied.

Sentinel/missing-value handling is separate from environmental range QC.

---

# `min` and `max`

```json
"min": 10,
"max": 45
```

Define the accepted environmental range for the measurement.

A measurement is accepted when:

```text
min <= value <= max
```

Values outside this range are treated as invalid before aggregation.

For example:

```json
"min": 10,
"max": 45
```

would accept:

```text
10.0
25.3
45.0
```

but reject:

```text
9.9
46.0
```

## Choosing QC Ranges

QC ranges should represent values that are clearly unreasonable for the station environment rather than attempting to define the normal climatology.

The purpose is to identify likely:

- Sensor failures
- Invalid readings
- Electrical problems
- Parsing problems
- Physically unreasonable observations

The limits should generally be broad enough to retain legitimate extreme weather.

### Regional Differences

The same limits should not necessarily be used everywhere.

For example, station pressure at a high-elevation location such as Addis Ababa or Nairobi is naturally much lower than station pressure near sea level in Fiji.

This is one reason the summarizer uses regional profiles.

The existing profiles should be treated as **first-pass engineering QC configurations**, not official WMO or NMHS climatological standards.

---

# `temporal_qc_enabled`

```json
"temporal_qc_enabled": true
```

Controls whether temporal spike/dip detection is applied to the measurement.

Temporal QC attempts to identify an isolated measurement that changes rapidly and then returns close to its previous value.

For example:

```text
20.1
20.3
35.8   <- possible spike
20.4
20.5
```

Temporal QC is controlled by four additional parameters:

```text
spike_threshold
neighbor_tolerance
max_rate_change_per_minute
spike_max_neighbor_gap_seconds
```

These settings are ignored when temporal QC is disabled.

---

# `spike_threshold`

```json
"spike_threshold": 3.0
```

Defines how different the candidate measurement must be from its neighboring valid observations before it can be considered a spike or dip.

A larger value makes the temporal QC less sensitive.

A smaller value makes it more sensitive.

This value should be selected according to the natural variability and measurement characteristics of the variable.

---

# `neighbor_tolerance`

```json
"neighbor_tolerance": 1.5
```

Defines how closely the valid observations before and after a suspected spike must agree.

For example:

```text
20.1
35.8
20.4
```

has neighboring measurements that differ by only:

```text
0.3
```

The agreement between the neighboring observations provides evidence that `35.8` is an isolated anomaly rather than part of a sustained environmental change.

---

# `max_rate_change_per_minute`

```json
"max_rate_change_per_minute": 3.0
```

Defines the rate-of-change criterion used by temporal QC.

The calculation accounts for the actual elapsed time between observations rather than assuming that every observation arrived at exactly the configured station interval.

This is important for 3D-PAWS observations that may contain normal timestamp jitter.

The candidate must meet the configured temporal QC conditions before it is removed.

---

# `spike_max_neighbor_gap_seconds`

```json
"spike_max_neighbor_gap_seconds": 1200
```

Defines the maximum amount of time that may separate a candidate measurement from the valid observations used to evaluate it.

This prevents measurements separated by large data gaps from being treated as immediate temporal neighbors.

For example, observations several hours apart should generally not be used to determine whether an individual measurement represents a short-duration sensor spike.

---

# `include_in_summary`

```json
"include_in_summary": true
```

Controls whether the measurement appears in the generated meteorological summary files.

Use:

```json
"include_in_summary": false
```

for recognized measurements that should not currently appear in the 15-minute, hourly, or daily summaries.

This is useful for operational variables such as:

- Health status
- Cellular signal
- Battery state
- Charger status

These variables can remain mapped and recognized without being included in the meteorological products.

---

# `include_completeness`

```json
"include_completeness": true
```

Controls whether individual variable completeness is calculated and included in the summary output.

For environmental measurements, this is normally:

```json
true
```

Variable completeness helps distinguish between:

- A station-wide observation gap
- A sensor-specific data problem

Operational variables that are not part of the meteorological summaries may use:

```json
false
```

---

# `statistics`

The `statistics` object determines how a measurement is aggregated.

Example:

```json
"statistics": {
  "15min": ["mean"],
  "hourly": ["mean"],
  "daily": ["mean", "min", "max"]
}
```

Each summary interval can have its own aggregation rules.

## Common Statistics

Currently used statistics include:

```text
mean
min
max
sum
```

Only statistics supported by the summarizer should be used.

### Example: Air Temperature

```json
"statistics": {
  "15min": ["mean"],
  "hourly": ["mean"],
  "daily": ["mean", "min", "max"]
}
```

### Example: Rain

```json
"statistics": {
  "15min": ["sum"],
  "hourly": ["sum"],
  "daily": ["sum"]
}
```

### Example: WBT or WBGT

```json
"statistics": {
  "15min": ["max"],
  "hourly": ["max"],
  "daily": ["max"]
}
```

Some specialized measurements, particularly wind and precipitation, receive additional processing by the summarizer beyond these basic statistics.

See [Technical Details](TECHNICAL_DETAILS.md) for those algorithms.

---

# Typical Aggregation Rules

The current configurations generally use:

| Measurement | 15-Minute | Hourly | Daily |
| --- | --- | --- | --- |
| Air Temperature | Mean | Mean | Mean, Min, Max |
| Relative Humidity | Mean | Mean | Mean, Min, Max |
| Station Pressure | Mean | Mean | Mean, Min, Max |
| MSLP | Mean | Mean | Mean, Min, Max |
| Wind Speed | Mean, Max | Mean, Max | Mean, Max |
| Wind Direction | Circular Mean | Circular Mean | Circular Mean |
| Wind Gust | Mean, Max | Mean, Max | Mean, Max |
| Rain | Sum | Sum | Sum |
| WBT | Max | Max | Max |
| WBGT | Max | Max | Max |
| Soil Temperature | Mean | Mean | Mean, Min, Max |
| Grass Minimum Temperature | Mean | Mean | Mean, Min, Max |

The configuration file and summarizer code remain authoritative if this table differs from a specific profile.

---

# Internal Variable Names

Common 3D-PAWS internal variables include:

| Variable | Measurement |
| --- | --- |
| `st1` | SHT temperature |
| `sh1` | SHT relative humidity |
| `bt1` | BMP/BMX temperature |
| `bp1` | BMP/BMX station pressure |
| `mt1` | MCP9808 temperature |
| `hi` | Heat index |
| `wbt` | Wet Bulb Temperature |
| `wbgt` | Wet Bulb Globe Temperature |
| `mslp` | Mean Sea Level Pressure |
| `ws` | Wind speed |
| `wd` | Wind direction |
| `wg` | Wind gust |
| `wgd` | Wind gust direction |
| `rg` | Rain gauge 1 incremental rain |
| `rgt` | Rain gauge 1 cumulative rain |
| `rgp` | Rain gauge 1 prior cumulative rain |
| `rg2` | Rain gauge 2 incremental rain |
| `rgt2` | Rain gauge 2 cumulative rain |
| `rgp2` | Rain gauge 2 prior cumulative rain |
| `gt1` | Grass minimum temperature |
| `htu_t1` | Legacy HTU temperature |
| `htu_h1` | Legacy HTU relative humidity |
| `hth` | Health status |
| `css` | Cellular signal strength |
| `bcs` | Battery charge/current state |
| `cfr` | Charger fault register |
| `bpc` | Battery percent charge |

Additional soil and other environmental variables may also be defined by the profiles.

---

# Creating a New Regional Profile

The easiest way to create a new profile is to start from the existing profile that most closely resembles the new station.

For example:

```bash
cp configs/summary_config_nadi.json \
   configs/summary_config_suva.json
```

Then review and modify the new file.

## 1. Set the Profile Metadata

Update the profile name or regional information contained in the configuration.

The profile should clearly identify the environment for which its QC limits were developed.

## 2. Review Source Columns

Compare the station's CHORDS CSV headers with the configured `source_columns`.

When the summarizer runs, pay particular attention to:

```text
Mapped CHORDS variables:
```

and:

```text
Unmapped source columns:
```

Add aliases where necessary.

## 3. Review Environmental Ranges

Review every configured:

```text
min
max
```

value for the new region.

Consider:

- Elevation
- Climate
- Expected temperature extremes
- Expected humidity range
- Typical station pressure
- Sensor measurement limits

Do not make ranges unnecessarily narrow.

The purpose is to reject clearly invalid measurements, not unusual but legitimate weather.

## 4. Review Temporal QC

For variables using temporal QC, review:

```text
spike_threshold
neighbor_tolerance
max_rate_change_per_minute
spike_max_neighbor_gap_seconds
```

Temporal QC should remove obvious isolated sensor anomalies without suppressing legitimate rapid environmental changes.

## 5. Review Summary Statistics

Verify that:

```text
statistics
```

contains the desired aggregation behavior for each measurement.

## 6. Select the Profile

Update `summary.env`:

```text
QC_PROFILE=suva
```

The summarizer will then load:

```text
configs/summary_config_suva.json
```

## 7. Run a Test Dataset

Run the summarizer on a representative station dataset:

```bash
python summarize_chords.py /path/to/station.csv
```

Review the console output carefully.

---

# Validating a New Profile

Before using a new profile operationally, check the following.

### Variable Mapping

- Are all expected sensors mapped?
- Are important columns unexpectedly listed as unmapped?
- Are aliases mapping to the correct internal variables?

### Range QC

- Are large numbers of apparently valid measurements being removed?
- Are known invalid or sentinel values removed?
- Are the pressure limits appropriate for the station elevation?
- Are legitimate environmental extremes retained?

### Temporal QC

- Are only isolated anomalies being removed?
- Are legitimate weather changes preserved?
- Are large data gaps being handled appropriately?

### Summary Output

- Do 15-minute values look reasonable?
- Do hourly values agree with the underlying observations?
- Do daily minimum and maximum values make sense?
- Does circular wind direction behave correctly?
- Is maximum gust direction associated with the maximum gust?

### Precipitation

For stations with cumulative rain:

- Does incremental rain approximately agree with cumulative change?
- Are cumulative resets handled correctly?

For dual-gauge stations:

- Do both gauges appear?
- Are signed gauge differences reasonable?

### Completeness

- Does observation completeness correspond to known data gaps?
- Does sensor completeness reveal known failed or missing sensors?
- Is the correct `EXPECTED_INTERVAL_SECONDS` being used?

---

# Common Configuration Problems

## A Measurement Appears Under `Unmapped source columns`

The CHORDS column name is probably not included in any `source_columns` list.

If it represents an existing supported measurement, add the exact column name as an alias.

---

## A Valid Measurement Is Being Removed by QC

Check:

```text
min
max
```

for that variable.

If temporal QC is responsible, review:

```text
spike_threshold
neighbor_tolerance
max_rate_change_per_minute
spike_max_neighbor_gap_seconds
```

Do not simply disable QC without first determining why the observation was rejected.

---

## A Sensor Does Not Appear in the Summary

Check:

```json
"include_in_summary": true
```

and verify that the source column was successfully mapped.

Also confirm that appropriate statistics are defined.

---

## Completeness Looks Incorrect

Observation cadence is configured in `summary.env`, not in the regional JSON profile.

Check:

```text
EXPECTED_INTERVAL_SECONDS
GAP_THRESHOLD_SECONDS
```

For example, processing a 15-minute station as a 1-minute station will produce incorrect completeness estimates.

---

## A Legacy Station Uses Different Sensor Names

Add the legacy CHORDS column name to the appropriate `source_columns` list rather than changing the CSV.

For example:

```json
"source_columns": [
  "BMP390 Pressure (hPa)",
  "BMX Pressure 1 (hPa)"
]
```

allows both sensor naming conventions to map to the same pressure variable.

---

# Configuration Philosophy

Configuration profiles should be designed conservatively.

The goal is not to automatically decide whether every unusual environmental observation is correct or incorrect.

Instead, the configuration should:

1. Map known CHORDS variables consistently.
2. Remove clearly invalid sensor values.
3. Identify obvious isolated sensor anomalies.
4. Preserve legitimate environmental extremes.
5. Apply appropriate meteorological aggregation.
6. Make missing or problematic measurements visible through completeness statistics.
7. Remain understandable and editable by network operators.

When uncertain, prefer retaining a questionable but physically possible measurement over creating an overly aggressive QC rule.

More sophisticated persistence, climatological, cross-variable, or network-level QC can be added separately without making the regional configuration profiles unnecessarily restrictive.
