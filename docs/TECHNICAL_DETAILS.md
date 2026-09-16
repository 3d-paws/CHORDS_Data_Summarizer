# CHORDS Data Summarizer — Technical Details

This document describes the processing, quality-control, completeness, wind, precipitation, and aggregation methods used by the **CHORDS Data Summarizer**.

For installation instructions, see the [Installation Guide](INSTALLATION.md).

For information about creating or modifying regional QC profiles, see the [Configuration Guide](CONFIGURATION.md).

---

# Processing Overview

The summarizer processes a CHORDS CSV in the following order:

1. Read the input CSV.
2. Parse the `Time` column.
3. Remove invalid timestamps.
4. Sort observations chronologically.
5. Remove duplicate timestamps.
6. Infer missing observations from timestamp gaps.
7. Map CHORDS columns to canonical variables.
8. Convert mapped measurements to numeric values.
9. Remove sentinel/missing measurements.
10. Apply environmental range QC.
11. Apply temporal spike/dip QC.
12. Prepare cumulative-rain diagnostics.
13. Create 15-minute meteorological summaries.
14. Create hourly meteorological summaries.
15. Create daily meteorological summaries.
16. Create a separate QC report.
17. Write all output files.

An important distinction is maintained between:

- a **missing observation**, and
- a **missing or invalid measurement**.

Missing observations affect station-level observation completeness.

Invalid individual measurements affect variable completeness and QC statistics.

---

# Input Timestamps

The input file must contain:

```text
Time
```

Timestamps are converted using pandas.

Invalid timestamps are removed.

The observations are then sorted chronologically.

Exact duplicate timestamps are removed before completeness calculations.

---

# Observation Cadence

Observation cadence is explicitly configured in:

```text
summary.env
```

For a one-minute station:

```text
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

For a 15-minute station:

```text
EXPECTED_INTERVAL_SECONDS=900
GAP_THRESHOLD_SECONDS=1800
```

---

# Why Cadence Is Explicit

The summarizer does not automatically infer the primary station measurement cadence.

3D-PAWS data loggers can continue collecting observations when communications are unavailable.

Stored observations may later be transmitted after communications recover.

Therefore:

```text
measurement cadence
```

and:

```text
data transmission cadence
```

are not necessarily the same.

Automatically inferring cadence from data gaps could mistake:

- communications outages,
- stored observations,
- backfilled measurements, or
- missing records

for intentional configuration changes.

The expected station cadence is therefore explicitly defined.

---

# Missing Observation Detection

Missing observations are inferred from the original timestamp sequence before sensor QC is applied.

For each pair of consecutive observations:

```text
previous observation → current observation
```

the elapsed time is calculated.

If:

```text
gap < GAP_THRESHOLD_SECONDS
```

the gap is treated as normal timing variation.

If:

```text
gap >= GAP_THRESHOLD_SECONDS
```

the number of expected measurement intervals is estimated.

Conceptually:

```text
estimated intervals =
    floor(gap / expected interval)

missed observations =
    max(1, estimated intervals - 1)
```

---

## Example: One-Minute Station

Using:

```text
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

the behavior is approximately:

| Gap | Missing Observations |
| ---: | ---: |
| 60 s | 0 |
| 65 s | 0 |
| 119 s | 0 |
| 120 s | 1 |
| 127 s | 1 |
| 180 s | 2 |
| 240 s | 3 |

This approach tolerates ordinary logger timestamp drift while still identifying real gaps.

---

# QC Report

Each run creates:

```text
<filename>_qc_report.csv
```

The QC report separates data-quality diagnostics from the main meteorological summary products.

The report currently contains four record types:

```text
Dataset
Variable
Daily Completeness
Rain QC
```

---

## `Dataset`

Provides whole-file observation information including:

```text
Observation Count
Estimated Missed Observations
Observation Completeness (%)
```

The notes field also records:

```text
EXPECTED_INTERVAL_SECONDS
GAP_THRESHOLD_SECONDS
```

---

## `Variable`

Provides whole-file sensor-level QC information.

Columns include:

```text
Variable
Source Column
Unit
Variable Completeness (%)
Raw Non-Missing
Sentinel Removed
Range QC Removed
Temporal QC Removed
Total QC Removed
Valid After QC
```

This provides an audit trail of what measurements were removed before summary statistics were calculated.

---

## `Daily Completeness`

Provides daily:

```text
Observation Count
Estimated Missed Observations
Observation Completeness (%)
Partial Day
```

The `Partial Day` field identifies input-file boundaries that do not represent a complete calendar day.

---

## `Rain QC`

Provides diagnostic comparison between:

```text
incremental rain sum
```

and:

```text
cumulative rain change
```

for each rain gauge where both values are available.

---

# Observation Completeness

Observation completeness is recorded in the QC report rather than the meteorological summary files.

Conceptually:

```text
Observation Completeness (%) =

    Observed
    -------------------------
    Observed + Estimated Missing
    × 100
```

For example:

```text
Observation Count = 55
Estimated Missed Observations = 5
```

produces:

```text
Observation Completeness = 91.67%
```

Observation completeness is calculated independently of sensor QC.

A bad temperature measurement does not cause the whole station observation to be classified as missing.

---

# Partial Days

Completeness is based on the portion of the dataset actually represented by the input file.

The first or last calendar day may contain only part of a day.

For example:

```text
Period:                         2026-09-15
Partial Day:                    Yes
Observation Count:              79
Estimated Missed Observations:  0
Observation Completeness:       100%
```

does not mean that all observations expected during the full calendar day were received.

It means that no missing observations were detected during the portion of September 15 included in the input file.

The QC report therefore includes:

```text
Partial Day
```

for daily completeness records.

The script allows approximately one expected observation interval around midnight so ordinary timestamp offsets do not incorrectly identify a complete day as partial.

---

# Variable Completeness

Variable completeness describes the availability of usable values for an individual measurement.

It accounts for:

1. Station observations missing from the dataset.
2. Observations where the variable itself is missing.
3. Sentinel values removed by QC.
4. Range-QC failures.
5. Temporal-QC failures.

Conceptually:

```text
Variable Completeness (%) =

    Valid Values After QC
    -----------------------------
    Observed + Estimated Missing
    × 100
```

For example:

```text
Observation Completeness (%)      99.5
SHT Temperature Completeness (%)  99.3
HTU Humidity Completeness (%)      4.3
```

would indicate that station reporting is healthy while the HTU humidity measurement is largely unavailable.

---

# Sentinel / Missing Value QC

3D-PAWS sensors may report large negative numbers to represent unavailable or invalid readings.

A global threshold is configured in the regional JSON profile.

Example:

```json
"missing_value_threshold": -900
```

Values such as:

```text
-999
-999.9
```

are therefore converted to missing values before aggregation.

The number removed is stored in:

```text
Sentinel Removed
```

in the QC report.

---

# Environmental Range QC

Variables with:

```json
"qc_enabled": true
```

can define:

```json
"min": 10,
"max": 45
```

A measurement is retained when:

```text
min <= measurement <= max
```

Measurements outside that range are converted to missing.

The number removed is recorded under:

```text
Range QC Removed
```

---

# Regional QC

Environmental range QC is profile-specific.

Reasonable atmospheric pressure at a high-elevation station can differ substantially from pressure at a coastal station.

Likewise, plausible temperature or soil-temperature ranges differ by climate.

The regional limits should therefore be treated as:

```text
first-pass engineering QC
```

rather than definitive climatological limits.

---

# Temporal Spike/Dip QC

Temporal QC is designed to identify isolated anomalies rather than simply large changes.

A candidate observation is evaluated relative to the nearest valid observations before and after it.

The configuration uses:

```text
spike_threshold
neighbor_tolerance
max_rate_change_per_minute
spike_max_neighbor_gap_seconds
```

---

## `spike_threshold`

Minimum difference between the candidate and each neighboring observation.

---

## `neighbor_tolerance`

Maximum difference allowed between the observations surrounding the candidate.

This helps establish that the surrounding data agree while the candidate does not.

---

## `max_rate_change_per_minute`

Rate threshold used to determine whether the change occurred rapidly enough to be suspicious.

Actual elapsed time is used.

---

## `spike_max_neighbor_gap_seconds`

Maximum allowed time between the candidate and either neighboring valid observation.

This prevents distant observations across large gaps from being treated as immediate neighbors.

---

## Conceptual Example

Consider:

```text
20.1
20.3
35.8
20.4
20.5
```

The value:

```text
35.8
```

may be removed if:

- it differs sufficiently from both neighbors,
- the neighbors agree with each other,
- the rate threshold is exceeded, and
- the neighboring observations are close enough in time.

A sustained change such as:

```text
20
23
27
30
32
```

should not normally satisfy the isolated-spike criteria.

The number removed is recorded as:

```text
Temporal QC Removed
```

---

# QC Counts

For each mapped variable, the QC report preserves:

```text
Raw Non-Missing
Sentinel Removed
Range QC Removed
Temporal QC Removed
Total QC Removed
Valid After QC
```

`Total QC Removed` is calculated as:

```text
Sentinel Removed
+ Range QC Removed
+ Temporal QC Removed
```

These diagnostics make it possible to review how the final summarized values were produced.

---

# Meteorological Summary Files

Three meteorological files are generated:

```text
<filename>_15min.csv
<filename>_hourly.csv
<filename>_daily.csv
```

These files are intentionally focused on meteorological statistics.

Completeness and QC diagnostics are stored separately in:

```text
<filename>_qc_report.csv
```

---

# Aggregation Rules

Typical processing is:

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

The selected JSON profile remains the authoritative definition.

---

# Wind Direction

Direction is circular data and cannot be averaged correctly with an ordinary arithmetic mean.

For example:

```text
359°
1°
```

should average to approximately:

```text
0°
```

rather than:

```text
180°
```

The summarizer therefore calculates a circular mean using sine and cosine components.

Outputs include:

```text
Wind Direction Mean (deg)
Wind Direction Mean Compass
```

---

# Maximum Gust Direction

The maximum gust direction is not independently averaged.

For each summary period:

1. Find the maximum valid gust speed.
2. Identify the original observation containing that gust.
3. Retrieve the gust direction from that same observation.

The result is reported as:

```text
Wind Gust Max
Max Gust Direction (deg)
Max Gust Direction Compass
```

---

# Precipitation

The summarizer supports both:

```text
incremental precipitation
```

and:

```text
cumulative precipitation
```

Incremental precipitation is used in the main meteorological summaries.

Cumulative precipitation is retained primarily for diagnostic QC.

---

# Incremental Rain

Incremental rain values are summed over each period.

Conceptually:

```python
sum(min_count=1)
```

is used.

This prevents a period with no valid rain measurements from automatically becoming:

```text
0 mm
```

when the correct state is unknown.

---

# Cumulative Rain

Changes in cumulative rain are calculated between consecutive observations.

Example:

```text
12.4 → 12.8
```

produces:

```text
0.4 mm
```

---

# Cumulative Counter Resets

If the cumulative value decreases, the script assumes the counter reset.

Example:

```text
15.2 → 0.6
```

would ordinarily produce:

```text
-14.6
```

but that is not meaningful rainfall.

The summarizer instead treats:

```text
0.6
```

as the amount accumulated after the reset.

---

# First Cumulative Observation

The first cumulative value in a file has no preceding observation.

Therefore, the summarizer cannot determine how much rain occurred between that measurement and the last observation before the file begins.

The first cumulative increment is treated as unknown.

---

# Rain QC

When both incremental and cumulative rain are available, the QC report calculates:

```text
Rain Increment Sum
Rain Cumulative Change
Rain Difference
```

where:

```text
Rain Difference =
    Incremental Rain Sum
    - Cumulative Rain Change
```

A value near zero indicates agreement.

This comparison is diagnostic.

The script does not automatically decide which source is correct when they disagree.

---

# Dual Rain Gauges

When both gauges are present, the meteorological summary includes:

```text
Rain Gauge 1 Sum
Rain Gauge 2 Sum
Rain Gauge 1 vs 2 Difference
```

The difference is signed:

```text
Gauge 1 - Gauge 2
```

Cumulative rain comparisons are intentionally kept out of the main meteorological files and are handled through the QC report.

---

# System and Status Variables

Profiles may map operational variables such as:

```text
Health
Cellular Signal Strength
Battery State
Battery Percent Charge
Battery Voltage
Charger Fault Register
```

These can be recognized and QC'd without being included in the meteorological summaries.

They may support future station-health diagnostics.

---

# Console Diagnostics

While running, the script reports:

- Expected observation interval
- Gap threshold
- Inferred missing observations
- Selected QC profile
- Mapped variables
- Configured variables not present
- Unmapped columns
- Sentinel values removed
- Range-QC failures
- Temporal-QC removals
- Source observation count
- Observation period
- Generated files

These messages make configuration and data problems visible during processing.

---

# Historical Cadence Changes

The current implementation assumes that:

```text
EXPECTED_INTERVAL_SECONDS
```

applies to the complete input file.

A historical file containing an intentional change from:

```text
15-minute observations
```

to:

```text
1-minute observations
```

should not be evaluated with a single cadence unless that change is accounted for.

Automatic cadence detection is intentionally avoided because communications outages and backfilled observations can make inference unreliable.

Support for explicitly defined cadence-change periods may be added later.

---

# Persistence / Stuck-Sensor QC

The current implementation does not automatically flag a measurement simply because it remains unchanged for a long period.

A future QC feature could detect conditions such as:

```text
STUCK_ZERO
STUCK_VALUE
```

over configurable periods.

The preferred first implementation would be report-only rather than automatically deleting those measurements.

This is particularly useful for unused or failed sensors that continuously report zero.

---

# Design Principles

The summarizer follows these principles:

1. Preserve the distinction between missing observations and invalid individual measurements.
2. Use measurement timestamps rather than data-transmission timing.
3. Explicitly configure expected station cadence.
4. Keep meteorological statistics separate from QC diagnostics.
5. Preserve a QC audit trail.
6. Use measurement-appropriate aggregation.
7. Keep environmental limits configurable.
8. Support multiple generations of 3D-PAWS variable naming.
9. Make unexpected mappings visible.
10. Treat regional QC as engineering screening rather than definitive climatological validation.
11. Prefer diagnostic comparisons over automatically deciding which redundant sensor is correct.
12. Avoid removing questionable but physically possible observations without a sufficiently strong QC rule.
