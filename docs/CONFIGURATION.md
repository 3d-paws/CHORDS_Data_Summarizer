# CHORDS Data Summarizer — Configuration Guide

This guide explains how to configure the **CHORDS Data Summarizer** for different stations, sensors, and environmental regions.

The summarizer uses JSON configuration profiles to define:

- CHORDS source-column mappings
- Output names and units
- Environmental QC ranges
- Temporal spike/dip QC
- Summary inclusion
- Variable completeness reporting
- Aggregation statistics

For details about the processing algorithms themselves, see [Technical Details](TECHNICAL_DETAILS.md).

---

# Configuration Profiles

Profiles are stored in:

```text
configs/
```

and follow the naming convention:

```text
summary_config_<profile>.json
```

Examples:

```text
summary_config_nadi.json
summary_config_addis.json
summary_config_adama.json
summary_config_nairobi.json
```

The profile is selected in `summary.env`:

```text
QC_PROFILE=nadi
```

which loads:

```text
configs/summary_config_nadi.json
```

Profiles allow the same code to support different:

- Station configurations
- Sensor combinations
- CHORDS variable names
- Climates
- Elevations
- Generations of 3D-PAWS hardware and firmware

---

# Top-Level Structure

A configuration file contains:

```json
{
  "_meta": {
    "profile_name": "Nadi, Fiji",
    "missing_value_threshold": -900
  },

  "variables": {
  }
}
```

---

# `_meta`

## `profile_name`

Human-readable name reported when the summarizer runs.

Example:

```json
"profile_name": "Nadi, Fiji"
```

## `missing_value_threshold`

Defines the global threshold used to identify sentinel or invalid values.

Example:

```json
"missing_value_threshold": -900
```

Values at or below this threshold are treated as missing.

This captures values such as:

```text
-999
-999.9
```

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

A typical definition looks like:

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

---

# `display_name`

```json
"display_name": "SHT31D Temperature"
```

Human-readable name used in outputs and the QC report.

The display name does not need to match the CHORDS source column.

---

# `unit`

```json
"unit": "degC"
```

Unit displayed in output-column names.

Examples:

```text
degC
%
hPa
m/s
deg
mm
mm H2O
```

The configuration does not perform unit conversion.

The configured unit should describe the source measurement.

---

# `source_columns`

```json
"source_columns": [
  "SHT31D Temperature (degC)",
  "SHT Temperature (degC)"
]
```

Lists CHORDS column names that may represent the variable.

This allows different station generations or firmware versions to map to the same internal variable.

For example:

```json
"source_columns": [
  "MCP9808 Temperature (degC)",
  "MCP Temperature 1 (degC)"
]
```

allows both names to map to:

```text
mt1
```

Legacy FEWS NET stations may contain names such as:

```text
BMX Temperature 1 (degC)
BMX Pressure 1 (hPa)
HTU Temperature 1 (degC)
HTU Humidity 1 (%)
```

These can be mapped through aliases without modifying the original CSV.

## Adding an Alias

If the summarizer reports:

```text
Unmapped source columns:
```

and the column represents a measurement already supported by the profile, add the exact CHORDS column name to `source_columns`.

For example:

```json
"source_columns": [
  "SHT31D Temperature (degC)",
  "SHT Temperature (degC)"
]
```

---

# `type`

```json
"type": "measurement"
```

Identifies the processing role of the variable.

Examples currently used include:

```text
measurement
derived
wind_speed
wind_direction
wind_gust
gust_direction
rain_increment
rain_total
rain_prior
soil_temperature
grass_temperature
status
system
```

Do not invent a new `type` unless `summarize_chords.py` supports it.

---

# `qc_enabled`

```json
"qc_enabled": true
```

Controls whether minimum/maximum range QC is applied.

When:

```json
"qc_enabled": false
```

environmental range checking is skipped.

Sentinel handling is independent of `qc_enabled`.

---

# `min` and `max`

Example:

```json
"min": 10,
"max": 45
```

A valid measurement satisfies:

```text
min <= value <= max
```

Values outside the configured range are converted to missing values before aggregation.

## Choosing QC Ranges

Ranges should identify clearly implausible values rather than define normal climatology.

They should generally be broad enough to preserve legitimate extremes.

Consider:

- Station elevation
- Regional climate
- Sensor measurement limits
- Expected environmental extremes

For example, normal station pressure at Addis Ababa or Nairobi is substantially lower than at a near-sea-level Fiji station.

The supplied limits are practical first-pass engineering QC thresholds rather than official climatological limits.

---

# `temporal_qc_enabled`

```json
"temporal_qc_enabled": true
```

Controls temporal spike/dip detection.

Temporal QC attempts to identify isolated anomalies such as:

```text
20.1
20.3
35.8
20.4
20.5
```

rather than sustained changes.

Four configuration fields control the test.

---

# `spike_threshold`

```json
"spike_threshold": 3.0
```

Minimum difference between the candidate observation and the neighboring valid measurements.

Larger values make the check less sensitive.

---

# `neighbor_tolerance`

```json
"neighbor_tolerance": 1.5
```

Maximum acceptable difference between the observations before and after a suspected spike.

If the surrounding observations agree closely but the center value differs substantially, the center value is more likely to represent an isolated error.

---

# `max_rate_change_per_minute`

```json
"max_rate_change_per_minute": 3.0
```

Rate-of-change threshold used by temporal QC.

Actual elapsed time between measurements is used in the calculation.

---

# `spike_max_neighbor_gap_seconds`

```json
"spike_max_neighbor_gap_seconds": 1200
```

Maximum time separating the candidate from the valid measurements used to evaluate it.

This prevents observations separated by very large data gaps from being treated as immediate temporal neighbors.

---

# `include_in_summary`

```json
"include_in_summary": true
```

Controls whether the measurement appears in the 15-minute, hourly, or daily meteorological files.

Use:

```json
"include_in_summary": false
```

for recognized variables that should not appear in the main meteorological products.

Examples can include:

- Health status
- Battery state
- Cellular signal
- Cumulative rain counters used only for diagnostics

---

# `include_completeness`

```json
"include_completeness": true
```

Controls whether the variable receives a:

```text
Variable Completeness (%)
```

value in:

```text
<filename>_qc_report.csv
```

Variable completeness accounts for:

- observations missing from the dataset, and
- individual measurements missing or removed by QC.

Operational or diagnostic variables that do not require completeness reporting can use:

```json
"include_completeness": false
```

Completeness values are stored in the QC report rather than in the 15-minute, hourly, or daily meteorological summary files.

---

# `statistics`

Example:

```json
"statistics": {
  "15min": ["mean"],
  "hourly": ["mean"],
  "daily": ["mean", "min", "max"]
}
```

Defines aggregation rules for each summary period.

Basic supported statistics include:

```text
mean
min
max
sum
```

Some specialized variables use additional processing.

---

## Air Temperature Example

```json
"statistics": {
  "15min": ["mean"],
  "hourly": ["mean"],
  "daily": ["mean", "min", "max"]
}
```

---

## Rain Example

```json
"statistics": {
  "15min": ["sum"],
  "hourly": ["sum"],
  "daily": ["sum"]
}
```

---

## WBT / WBGT Example

```json
"statistics": {
  "15min": ["max"],
  "hourly": ["max"],
  "daily": ["max"]
}
```

---

## Wind Direction

Wind direction typically uses:

```json
"statistics": {
  "15min": ["circular_mean", "compass"],
  "hourly": ["circular_mean", "compass"],
  "daily": ["circular_mean", "compass"]
}
```

---

## Wind Gust

Wind gust can use:

```json
"statistics": {
  "15min": ["mean", "max", "max_gust_direction"],
  "hourly": ["mean", "max", "max_gust_direction"],
  "daily": ["mean", "max", "max_gust_direction"]
}
```

See [Technical Details](TECHNICAL_DETAILS.md) for specialized wind processing.

---

# Typical Aggregation Rules

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
| Grass Temperature | Mean | Mean | Mean, Min, Max |

The configuration profile remains authoritative.

---

# Common Internal Variable Names

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
| `rgp` | Rain gauge 1 prior-day rain |
| `rg2` | Rain gauge 2 incremental rain |
| `rgt2` | Rain gauge 2 cumulative rain |
| `rgp2` | Rain gauge 2 prior-day rain |
| `htu_t1` | Legacy HTU temperature |
| `htu_h1` | Legacy HTU relative humidity |
| `hth` | Health status |
| `css` | Cellular signal strength |
| `bcs` | Battery charge/current state |
| `cfr` | Charger fault register |
| `bpc` | Battery percent charge |

Profiles may also define soil, grass, and other measurements.

---

# Creating a New Regional Profile

Start by copying the closest existing profile.

For example:

```bash
cp configs/summary_config_nadi.json \
   configs/summary_config_suva.json
```

Then review the new file.

---

## 1. Update Profile Metadata

Set the profile name so the region or station environment is clearly identified.

---

## 2. Review Source Columns

Run the summarizer against representative station data.

Review:

```text
Mapped CHORDS variables:
```

and:

```text
Unmapped source columns:
```

Add aliases where appropriate.

---

## 3. Review Environmental Ranges

Review all:

```text
min
max
```

settings.

Consider:

- Elevation
- Climate
- Sensor limits
- Legitimate extremes

Avoid unnecessarily narrow ranges.

---

## 4. Review Temporal QC

For variables using temporal QC, review:

```text
spike_threshold
neighbor_tolerance
max_rate_change_per_minute
spike_max_neighbor_gap_seconds
```

The goal is to remove isolated artifacts while retaining real environmental changes.

---

## 5. Review Summary Statistics

Verify:

```text
statistics
```

for each variable.

---

## 6. Select the Profile

In `summary.env`:

```text
QC_PROFILE=suva
```

The summarizer will load:

```text
configs/summary_config_suva.json
```

---

## 7. Test the Profile

Run:

```bash
python summarize_chords.py /path/to/station.csv
```

Review both the meteorological outputs and the QC report.

---

# Validating a New Profile

## Variable Mapping

Check that:

- Expected sensors are mapped
- Unexpected important columns are not left unmapped
- Aliases map to the correct internal variables

---

## Range QC

Check that:

- Known invalid values are removed
- Large numbers of apparently valid observations are not removed
- Pressure limits are appropriate for station elevation
- Legitimate extremes remain

---

## Temporal QC

Check that:

- Isolated anomalies are removed
- Real weather changes remain
- Temporal QC is not bridging excessively large gaps

---

## Meteorological Output

Check that:

- 15-minute values are reasonable
- Hourly values agree with the source data
- Daily min/max values make sense
- Wind direction behaves correctly
- Maximum gust direction corresponds to the maximum gust
- Rain totals are reasonable

---

## QC Report and Completeness

Review:

```text
<filename>_qc_report.csv
```

Check that:

- Observation completeness corresponds to known data gaps
- Partial first or last days are identified correctly
- Variable completeness identifies failed or missing sensors
- Sentinel-removal counts are reasonable
- Range-QC counts are reasonable
- Temporal-QC counts are reasonable
- The correct expected observation cadence is being used
- Rain increment and cumulative-change diagnostics agree when both are available

---

# Common Configuration Problems

## Measurement Appears Under `Unmapped source columns`

The exact CHORDS name may not be listed in `source_columns`.

Add the appropriate alias.

---

## Valid Measurements Are Being Removed

Check:

```text
min
max
```

If temporal QC is responsible, review:

```text
spike_threshold
neighbor_tolerance
max_rate_change_per_minute
spike_max_neighbor_gap_seconds
```

Determine why the measurement is being rejected before simply disabling QC.

---

## Sensor Does Not Appear in the Summary

Check:

```json
"include_in_summary": true
```

Verify that:

- the source column mapped successfully, and
- the desired statistics are configured.

---

## Variable Completeness Does Not Appear

Check:

```json
"include_completeness": true
```

Variable completeness is reported in the QC report rather than the meteorological summary files.

---

## Completeness Looks Incorrect

Observation cadence is configured in:

```text
summary.env
```

Check:

```text
EXPECTED_INTERVAL_SECONDS
GAP_THRESHOLD_SECONDS
```

A 15-minute station processed as a one-minute station will produce misleading completeness statistics.

---

# Configuration Philosophy

Profiles should be conservative.

Their goal is to:

1. Map known CHORDS variables consistently.
2. Remove clearly invalid sensor values.
3. Identify obvious isolated artifacts.
4. Preserve legitimate environmental extremes.
5. Apply meteorologically appropriate aggregation.
6. Make missing/problematic measurements visible through the QC report.
7. Remain understandable and editable by network operators.

When uncertain, prefer retaining a physically possible observation over adding an overly aggressive QC rule.

More advanced persistence, climatological, cross-variable, or network-level QC can be added separately.
