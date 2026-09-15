# CHORDS Data Summarizer — Technical Details

This document describes the processing, quality-control, completeness, and aggregation methods used by the **CHORDS Data Summarizer**.

For installation and basic usage, see the main [`README.md`](../README.md).

## Processing Overview

The summarizer processes a CHORDS CSV in the following general order:

1. Read and parse the CHORDS observations.
2. Map source columns to configured internal variables.
3. Identify missing observations from the original timestamps.
4. Convert measurements to numeric values where appropriate.
5. Remove configured missing/sentinel values.
6. Apply environmental range QC.
7. Apply temporal spike/dip QC where enabled.
8. Calculate observation and variable completeness.
9. Calculate precipitation changes and comparisons.
10. Aggregate observations into 15-minute, hourly, and daily periods.
11. Write the resulting summary CSV files.

An important distinction is maintained between a **missing observation** and a **missing or invalid measurement**.

A missing observation affects station-level observation completeness. A measurement rejected by QC affects the completeness of that variable but does not cause the entire observation to be considered missing.

For information about creating or modifying regional QC profiles, variable mappings, QC limits, and summary settings, see the [Configuration Guide](CONFIGURATION.md).

---

## Variable Configuration

Measurement behavior is defined by regional JSON configuration files stored in:

```text
configs/
```

Profiles follow the naming convention:

```text
summary_config_<profile>.json
```

The profile is selected through:

```text
QC_PROFILE=<profile>
```

in `summary.env`.

A typical variable definition is:

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
  "spike_threshold": 5,
  "neighbor_tolerance": 2,
  "max_rate_change_per_minute": 3,
  "spike_max_neighbor_gap_seconds": 180,
  "statistics": {
    "15min": ["mean"],
    "hourly": ["mean"],
    "daily": ["mean", "min", "max"]
  }
}
```

### Source Column Aliases

`source_columns` allows different CHORDS variable names to map to the same internal variable.

For example:

```json
"source_columns": [
  "SHT31D Temperature (degC)",
  "SHT Temperature (degC)"
]
```

allows both newer and legacy station configurations to map to `st1`.

This is also used for older FEWS NET variables such as:

```text
BMX Temperature 1
BMX Pressure 1
HTU Temperature 1
HTU Humidity 1
```

When a configured measurement is not present in the input CSV, it is omitted rather than treated as an error.

Unrecognized CHORDS columns are reported in the console so that new aliases can be identified.

---

## Observation Cadence

Observation cadence is explicitly configured in `summary.env`.

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

### Why Cadence Is Explicit

The summarizer intentionally does not infer the primary observation interval from the input data.

3D-PAWS data loggers can continue collecting observations when communications are unavailable. Stored observations can later be transmitted when connectivity returns.

As a result, the timing of data transmission is not necessarily the same as the timing of measurement.

Explicitly defining the expected measurement interval prevents communications outages, stored observations, and later backfills from being interpreted as changes in the station's measurement cadence.

---

## Missing Observation Detection

Missing observations are inferred from the original measurement timestamps before environmental QC is applied.

The timestamps are:

1. Sorted.
2. Deduplicated.
3. Compared sequentially.

For each pair of observations:

```text
previous observation → current observation
```

the elapsed time is calculated.

If:

```text
gap < GAP_THRESHOLD_SECONDS
```

no observation is considered missing.

If:

```text
gap >= GAP_THRESHOLD_SECONDS
```

the number of expected intervals within the gap is estimated.

Conceptually:

```text
estimated intervals =
    floor(gap / expected interval)

missed observations =
    max(1, estimated intervals - 1)
```

Missing timestamps are then generated at the expected measurement cadence between the two real observations.

### Example: 1-Minute Station

With:

```text
EXPECTED_INTERVAL_SECONDS=60
GAP_THRESHOLD_SECONDS=120
```

the behavior is:

| Time Between Observations | Estimated Missing |
| ------------------------: | ----------------: |
|                      60 s |                 0 |
|                      65 s |                 0 |
|                     119 s |                 0 |
|                     120 s |                 1 |
|                     127 s |                 1 |
|                     180 s |                 2 |
|                     240 s |                 3 |

This allows normal timestamp jitter without incorrectly counting observations as missing.

### Assigning Missing Observations to Summary Periods

The inferred missing timestamps are generated before aggregation.

They can therefore be assigned to the appropriate:

* 15-minute period
* hourly period
* daily period

rather than assigning the entire gap to the period containing the observation following the gap.

---

## Observation Completeness

Each summary period contains:

```text
Observation Count
Estimated Missed Observations
Observation Completeness (%)
```

Observation completeness is calculated from the number of observations actually present and the number inferred to be missing.

Conceptually:

```text
Observation Completeness (%) =
    Observation Count
    ---------------------------------------------
    Observation Count + Estimated Missed Observations
    × 100
```

For example, if a period contains:

```text
Observation Count = 55
Estimated Missed Observations = 5
```

then:

```text
Observation Completeness = 91.67%
```

Observation completeness is calculated independently of sensor QC.

---

## Variable Completeness

Variable completeness describes the availability of valid measurements for an individual sensor or derived variable.

It accounts for:

1. Observations missing entirely from the dataset.
2. Observations present in the dataset where that measurement is missing or rejected by QC.

This allows the summaries to distinguish between a station-wide data gap and an individual sensor problem.

For example:

```text
Observation Completeness (%)        99.5
SHT Temperature Completeness (%)    99.3
HTU Humidity Completeness (%)        4.3
```

would indicate that the station itself is reporting normally while the HTU humidity measurement is largely unavailable.

---

## Missing and Sentinel Value QC

3D-PAWS measurements may use large negative numbers to represent unavailable or invalid sensor readings.

A global missing-value threshold is used so that values at or below the configured threshold are converted to missing values before aggregation.

A typical threshold is:

```text
-900
```

This captures values such as:

```text
-999
-999.9
```

without requiring every possible sentinel value to be listed individually.

---

## Environmental Range QC

Measurements with `qc_enabled` can define an acceptable range:

```json
"min": 10,
"max": 45
```

Measurements outside that range are converted to missing values before summary statistics are calculated.

The range is inclusive:

```text
min <= valid measurement <= max
```

### Regional Profiles

Range QC is configured regionally because reasonable environmental values differ substantially between locations.

For example, station pressure at a high-elevation location such as Addis Ababa or Nairobi is naturally much lower than station pressure at a near-sea-level station in Fiji.

For this reason, QC ranges should be treated as practical first-pass engineering limits rather than universal environmental or climatological limits.

---

## Temporal Spike/Dip QC

Temporal QC is designed to identify an **isolated measurement spike or dip**, not simply a large environmental change.

For a candidate measurement, the algorithm evaluates the nearest valid measurement before it and the nearest valid measurement after it.

The candidate can be rejected when all applicable conditions indicate that it is inconsistent with otherwise stable neighboring observations.

The configured parameters include:

### `spike_threshold`

Minimum difference between the candidate measurement and its neighboring measurements.

### `neighbor_tolerance`

Maximum acceptable difference between the observations before and after the candidate.

This helps establish that the surrounding observations agree with each other even though the candidate does not.

### `max_rate_change_per_minute`

Minimum rate of change required for the candidate to be considered an implausibly rapid change.

The rate is evaluated using the actual elapsed time between observations.

### `spike_max_neighbor_gap_seconds`

Maximum allowed time between the candidate and neighboring valid measurements.

This prevents observations separated by large data gaps from being used to identify an isolated spike.

### Conceptual Example

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

may be rejected if:

* its difference from the preceding value exceeds the spike threshold,
* its difference from the following value exceeds the spike threshold,
* the preceding and following values agree within the neighbor tolerance,
* the rate of change exceeds the configured threshold, and
* the neighboring observations are sufficiently close in time.

By contrast, a sustained environmental change such as:

```text
20
23
27
30
32
```

should not be treated as an isolated spike because the neighboring measurements do not return to approximately the previous value.

### Bridging Missing Measurements

Temporal QC operates on valid neighboring measurements rather than requiring them to occupy immediately adjacent CSV rows.

This allows the algorithm to bridge over measurements already identified as missing or invalid.

The maximum-neighbor-gap setting limits how far the algorithm is allowed to bridge.

---

## Aggregation

After QC, measurements are resampled into:

```text
15-minute
hourly
daily
```

periods.

Aggregation rules are configured independently for each measurement.

Typical rules are:

| Measurement               | 15-Minute     | Hourly        | Daily          |
| ------------------------- | ------------- | ------------- | -------------- |
| Temperature               | Mean          | Mean          | Mean, Min, Max |
| Relative Humidity         | Mean          | Mean          | Mean, Min, Max |
| Station Pressure          | Mean          | Mean          | Mean, Min, Max |
| Mean Sea Level Pressure   | Mean          | Mean          | Mean, Min, Max |
| Wind Speed                | Mean, Max     | Mean, Max     | Mean, Max      |
| Wind Gust                 | Mean, Max     | Mean, Max     | Mean, Max      |
| Wind Direction            | Circular Mean | Circular Mean | Circular Mean  |
| Rain                      | Sum           | Sum           | Sum            |
| WBT                       | Max           | Max           | Max            |
| WBGT                      | Max           | Max           | Max            |
| Soil Temperature          | Mean          | Mean          | Mean, Min, Max |
| Grass Minimum Temperature | Mean          | Mean          | Mean, Min, Max |

The JSON profile remains the authoritative definition of the statistics applied to individual variables.

---

## Wind Direction

Wind direction cannot be correctly averaged using a normal arithmetic mean because direction wraps at 360°.

For example:

```text
359°
1°
```

has an arithmetic mean of:

```text
180°
```

which is incorrect.

The summarizer instead converts directions into circular components, averages those components, and converts the result back to degrees.

The resulting circular mean is approximately:

```text
0°
```

or North.

### Compass Direction

Mean wind direction is also converted into a compass-direction label for easier interpretation.

Outputs can therefore contain both:

```text
Wind Direction Mean (deg)
Wind Direction Mean (Compass)
```

---

## Maximum Wind Gust Direction

Wind gust direction is treated differently from mean wind direction.

For each summary period:

1. Find the maximum valid wind gust.
2. Identify the exact source observation containing that gust.
3. Retrieve the gust direction from that same observation.

This produces:

```text
Wind Gust Maximum
Maximum Wind Gust Direction (deg)
Maximum Wind Gust Direction (Compass)
```

The gust direction is therefore associated with the actual maximum gust rather than being independently averaged.

---

## Precipitation

3D-PAWS stations may provide both incremental and cumulative precipitation measurements.

The summarizer processes these independently so they can be compared.

### Incremental Rain

Incremental rain measurements are summed within each aggregation period.

The calculation uses behavior equivalent to:

```python
sum(min_count=1)
```

This is important because a period containing no valid rain observations should remain missing rather than being incorrectly reported as zero rainfall.

---

## Cumulative Rain

Cumulative precipitation is processed by calculating the change between consecutive cumulative observations.

For normal increasing values:

```text
Previous cumulative = 12.4 mm
Current cumulative  = 12.8 mm
Increment            = 0.4 mm
```

### Counter Resets

A cumulative counter can reset.

For example:

```text
Previous cumulative = 15.2 mm
Current cumulative  = 0.6 mm
```

A simple difference would produce:

```text
-14.6 mm
```

which is not meaningful rainfall.

When the cumulative difference is negative, the summarizer assumes a reset and uses the current cumulative value as the post-reset increment:

```text
Increment = 0.6 mm
```

These reset-aware increments are then summed within each summary period.

### First Observation Limitation

The first cumulative observation in an input file has no preceding observation.

The summarizer therefore cannot determine how much rainfall occurred between that observation and the final observation before the beginning of the file.

The first cumulative increment is consequently treated as unknown.

---

## Incremental vs. Cumulative Rain Comparison

When both incremental and cumulative rain measurements are available, the summaries include independent calculations such as:

```text
Rain Gauge 1 Sum
Rain Gauge 1 Cumulative Rain Total
Rain Gauge 1 Cumulative Total Change
Rain Gauge 1 Sum vs Cumulative Change Difference
```

The comparison difference is signed.

Conceptually:

```text
Incremental Sum - Cumulative Change
```

A value near zero indicates agreement between the independently reported precipitation measurements.

The comparison is intended as a diagnostic and does not automatically determine which measurement is correct when they disagree.

---

## Dual Rain Gauges

Some 3D-PAWS configurations contain two independent rain gauges.

When both are available, the summarizer processes each gauge independently and calculates signed comparisons.

For example:

```text
Rain Gauge 1 Sum - Rain Gauge 2 Sum
```

This preserves the direction of disagreement rather than reporting only the absolute difference.

Dual-gauge comparisons can help identify:

* blocked gauges,
* mechanical problems,
* configuration errors,
* transmission problems, or
* disagreement requiring further inspection.

The summarizer does not automatically identify which gauge is correct.

---

## System and Status Variables

3D-PAWS observations can include operational variables such as:

```text
Health
Cell Signal Strength
Battery Current State
Charger Fault Register
Battery Percent Charge
Battery Voltage
```

These variables can be mapped by the configuration profiles so they are recognized by the software.

They are currently excluded from the meteorological summary outputs.

They may be used by future station-health or diagnostic processing.

---

## Console Diagnostics

The summarizer reports processing information to the console, including:

* selected QC profile,
* expected observation interval,
* missing-observation gap threshold,
* inferred missing observations,
* mapped source variables,
* configured variables not present,
* unmapped source columns,
* sentinel values removed,
* range failures,
* temporal QC failures,
* source observation count,
* observation period, and
* generated output files.

These diagnostics are intended to make configuration problems visible rather than silently ignoring unexpected data.

---

## Historical Cadence Changes

The current implementation assumes that:

```text
EXPECTED_INTERVAL_SECONDS
```

represents the expected cadence for the entire input file.

A historical dataset containing multiple intentional station cadences can therefore produce misleading completeness results if processed as one file.

For example, a file containing several weeks of 15-minute observations followed by a change to 1-minute observations should not be evaluated using a single cadence without accounting for that change.

Automatic cadence detection is intentionally not used because data gaps and backfilled observations can make cadence inference unreliable.

Support for explicit cadence-change periods may be added in the future.

---

## Persistence and Stuck Sensors

The current QC does not automatically flag a measurement merely because it remains constant for an extended period.

This is intentional.

Some environmental variables can legitimately remain unchanged for significant periods, while others remaining exactly constant—particularly at zero—may indicate a failed or disconnected sensor.

A future persistence QC system could identify conditions such as:

```text
STUCK_ZERO
STUCK_VALUE
```

over configurable periods.

The preferred initial implementation would be **report-only**, rather than automatically removing the measurements.

This would allow persistent values to be investigated without incorrectly rejecting legitimate observations.

---

## Design Principles

The summarizer follows several general principles:

1. **Preserve the distinction between missing observations and bad measurements.**
2. **Use measurement timestamps rather than transmission timing.**
3. **Make expected station cadence explicit.**
4. **Apply measurement-appropriate aggregation methods.**
5. **Keep QC thresholds configurable.**
6. **Support multiple generations of 3D-PAWS variable naming.**
7. **Expose unexpected mappings and QC results rather than silently ignoring them.**
8. **Treat regional QC as engineering screening rather than definitive climatological validation.**
9. **Prefer diagnostic comparisons over automatically deciding which redundant sensor is correct.**
10. **Avoid removing questionable data unless the QC condition is sufficiently well defined.**

These principles are intended to make the output useful for operational 3D-PAWS networks while keeping the processing behavior understandable and configurable.

