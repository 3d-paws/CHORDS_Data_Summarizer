import sys
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv


# =====================================================================
# PATHS
# =====================================================================

SCRIPT_DIR = Path(__file__).resolve().parent

SUMMARY_ENV = SCRIPT_DIR / "summary.env"

TIMESTAMP_COLUMN = "Time"


# =====================================================================
# LOAD summary.env
# =====================================================================

if not SUMMARY_ENV.exists():
    raise FileNotFoundError(
        f"Missing configuration file: {SUMMARY_ENV}"
    )

load_dotenv(SUMMARY_ENV)


OUTPUT_PATH_RAW = os.getenv("OUTPUT_PATH")

if not OUTPUT_PATH_RAW:
    raise ValueError(
        "OUTPUT_PATH is missing from summary.env"
    )

OUTPUT_PATH = Path(OUTPUT_PATH_RAW)


# =====================================================================
# OBSERVATION CADENCE
# =====================================================================

EXPECTED_INTERVAL_SECONDS = int(
    os.getenv(
        "EXPECTED_INTERVAL_SECONDS",
        "60",
    )
)

GAP_THRESHOLD_SECONDS = int(
    os.getenv(
        "GAP_THRESHOLD_SECONDS",
        str(EXPECTED_INTERVAL_SECONDS * 2),
    )
)

if EXPECTED_INTERVAL_SECONDS <= 0:
    raise ValueError(
        "EXPECTED_INTERVAL_SECONDS must be greater than 0"
    )

if GAP_THRESHOLD_SECONDS <= EXPECTED_INTERVAL_SECONDS:
    raise ValueError(
        "GAP_THRESHOLD_SECONDS should be greater than "
        "EXPECTED_INTERVAL_SECONDS"
    )


# =====================================================================
# QC PROFILE
# =====================================================================

QC_PROFILE = (
    os.getenv(
        "QC_PROFILE",
        "nadi",
    )
    .strip()
    .lower()
)

SUMMARY_CONFIG = (
    SCRIPT_DIR
    / "configs"
    / f"summary_config_{QC_PROFILE}.json"
)


# =====================================================================
# LOAD PROFILE
# =====================================================================

if not SUMMARY_CONFIG.exists():
    raise FileNotFoundError(
        f"QC profile configuration not found: "
        f"{SUMMARY_CONFIG}"
    )

with open(
    SUMMARY_CONFIG,
    "r",
    encoding="utf-8",
) as file:
    CONFIG = json.load(file)


META = CONFIG.get(
    "_meta",
    {}
)

VARIABLES = CONFIG.get(
    "variables",
    {}
)

if not VARIABLES:
    raise ValueError(
        f'No "variables" section found in '
        f"{SUMMARY_CONFIG}"
    )


PROFILE_NAME = META.get(
    "profile_name",
    QC_PROFILE,
)

MISSING_VALUE_THRESHOLD = META.get(
    "missing_value_threshold",
    -900,
)


# =====================================================================
# SUMMARY PERIODS
# =====================================================================

SUMMARY_PERIODS = {
    "15min": "15min",
    "hourly": "1h",
    "daily": "1D",
}


# =====================================================================
# DISPLAY HELPERS
# =====================================================================

def variable_name(tag):
    config = VARIABLES[tag]

    return config.get(
        "display_name",
        tag,
    )


def variable_unit(tag):
    return VARIABLES[tag].get(
        "unit"
    )


def output_label(
    tag,
    statistic,
):
    name = variable_name(tag)
    unit = variable_unit(tag)

    if unit:
        return (
            f"{name} "
            f"{statistic} "
            f"({unit})"
        )

    return (
        f"{name} "
        f"{statistic}"
    )


# =====================================================================
# SOURCE COLUMN -> CANONICAL TAG MAPPING
# =====================================================================

def map_source_columns(df):

    original_columns = list(
        df.columns
    )

    rename_map = {}
    matched_tags = {}
    missing_tags = []

    for tag, config in VARIABLES.items():

        aliases = config.get(
            "source_columns",
            [],
        )

        matched_column = None

        for alias in aliases:

            if alias in df.columns:
                matched_column = alias
                break

        if matched_column is None:
            missing_tags.append(tag)
            continue

        rename_map[
            matched_column
        ] = tag

        matched_tags[
            tag
        ] = matched_column

    df = df.rename(
        columns=rename_map
    )

    mapped_source_columns = set(
        rename_map.keys()
    )

    unmapped_columns = [
        column
        for column in original_columns
        if (
            column != TIMESTAMP_COLUMN
            and column not in mapped_source_columns
        )
    ]

    print()
    print(
        f"QC profile: {PROFILE_NAME}"
    )

    print(
        f"Configuration: "
        f"{SUMMARY_CONFIG.name}"
    )

    print()
    print("Mapped CHORDS variables:")

    if matched_tags:

        for tag, source in matched_tags.items():

            print(
                f"  {tag:<12} <- {source}"
            )

    else:
        print("  None")

    print()
    print(
        f"Matched variables: "
        f"{len(matched_tags)}"
    )

    print(
        f"Configured variables not present: "
        f"{len(missing_tags)}"
    )

    if unmapped_columns:

        print()
        print("Unmapped source columns:")

        for column in unmapped_columns:

            print(
                f"  {column}"
            )

    return (
        df,
        matched_tags,
        missing_tags,
        unmapped_columns,
    )


# =====================================================================
# COMPASS / WIND HELPERS
# =====================================================================

def degrees_to_compass(degrees):

    if (
        degrees is None
        or pd.isna(degrees)
    ):
        return None

    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]

    index = int(
        (
            float(degrees)
            + 11.25
        )
        / 22.5
    ) % 16

    return directions[
        index
    ]


def circular_mean_deg(series):

    values = (
        series
        .dropna()
        .astype(float)
    )

    if values.empty:
        return np.nan

    radians = np.deg2rad(
        values
    )

    mean_sin = np.mean(
        np.sin(radians)
    )

    mean_cos = np.mean(
        np.cos(radians)
    )

    if (
        np.isclose(
            mean_sin,
            0.0,
        )
        and
        np.isclose(
            mean_cos,
            0.0,
        )
    ):
        return np.nan

    angle = np.rad2deg(
        np.arctan2(
            mean_sin,
            mean_cos,
        )
    )

    return angle % 360


# =====================================================================
# COMPLETENESS
# =====================================================================

def infer_missing_observation_times(index):
    """
    Infer missing observations from timestamp gaps.

    Timing variation below GAP_THRESHOLD_SECONDS is ignored.

    Example for a 60-second station with a 120-second threshold:

        65 sec   -> 0 missed
        119 sec  -> 0 missed
        120 sec  -> 1 missed
        127 sec  -> 1 missed
        180 sec  -> 2 missed
        240 sec  -> 3 missed
    """

    if len(index) < 2:
        return pd.DatetimeIndex([])

    timestamps = (
        pd.DatetimeIndex(index)
        .sort_values()
        .unique()
    )

    missing_times = []

    for previous, current in zip(
        timestamps[:-1],
        timestamps[1:],
    ):

        gap_seconds = (
            current - previous
        ).total_seconds()

        if gap_seconds < GAP_THRESHOLD_SECONDS:
            continue

        estimated_intervals = int(
            gap_seconds
            // EXPECTED_INTERVAL_SECONDS
        )

        missed_count = max(
            1,
            estimated_intervals - 1,
        )

        for missed_number in range(
            1,
            missed_count + 1,
        ):

            missing_time = (
                previous
                + pd.Timedelta(
                    seconds=(
                        EXPECTED_INTERVAL_SECONDS
                        * missed_number
                    )
                )
            )

            if missing_time < current:
                missing_times.append(
                    missing_time
                )

    return pd.DatetimeIndex(
        missing_times
    )


def missing_observations_by_period(
    missing_times,
    frequency,
):

    if len(missing_times) == 0:
        return pd.Series(
            dtype="int64"
        )

    missing = pd.Series(
        1,
        index=missing_times,
        dtype="int64",
    )

    return (
        missing
        .resample(
            frequency
        )
        .sum()
    )


def is_partial_day(
    day,
    first_observation,
    last_observation,
):
    """
    Determine whether a daily QC record represents only part
    of a calendar day.

    A tolerance equal to one expected observation interval is
    allowed at the beginning and end of the day so ordinary
    timestamp offsets do not incorrectly mark a day as partial.
    """

    day_start = pd.Timestamp(
        day
    ).normalize()

    day_end = (
        day_start
        + pd.Timedelta(
            days=1
        )
    )

    tolerance = pd.Timedelta(
        seconds=EXPECTED_INTERVAL_SECONDS
    )

    partial = False

    # First calendar day represented by the input file.
    if (
        day_start
        == first_observation.normalize()
    ):

        if (
            first_observation
            > day_start + tolerance
        ):
            partial = True

    # Last calendar day represented by the input file.
    if (
        day_start
        == last_observation.normalize()
    ):

        if (
            last_observation
            < day_end - tolerance
        ):
            partial = True

    return partial


# =====================================================================
# TEMPORAL SPIKE / DIP QC
# =====================================================================

def apply_temporal_qc(
    df,
    tag,
    config,
):

    if not config.get(
        "temporal_qc_enabled",
        False,
    ):
        return (
            df,
            0,
        )

    spike_threshold = config.get(
        "spike_threshold"
    )

    neighbor_tolerance = config.get(
        "neighbor_tolerance"
    )

    max_rate = config.get(
        "max_rate_change_per_minute"
    )

    max_neighbor_gap = config.get(
        "spike_max_neighbor_gap_seconds",
        1200,
    )

    if (
        spike_threshold is None
        or neighbor_tolerance is None
        or max_rate is None
    ):
        return (
            df,
            0,
        )

    valid = (
        df[
            tag
        ]
        .dropna()
    )

    if len(valid) < 3:
        return (
            df,
            0,
        )

    invalid_indices = []

    values = (
        valid
        .to_numpy()
    )

    times = (
        valid.index
    )

    for i in range(
        1,
        len(valid) - 1,
    ):

        previous = values[
            i - 1
        ]

        current = values[
            i
        ]

        following = values[
            i + 1
        ]

        previous_time = times[
            i - 1
        ]

        current_time = times[
            i
        ]

        following_time = times[
            i + 1
        ]

        gap_before = (
            current_time
            - previous_time
        ).total_seconds()

        gap_after = (
            following_time
            - current_time
        ).total_seconds()

        if (
            gap_before <= 0
            or gap_after <= 0
            or gap_before > max_neighbor_gap
            or gap_after > max_neighbor_gap
        ):
            continue

        difference_before = abs(
            current
            - previous
        )

        difference_after = abs(
            current
            - following
        )

        neighbor_difference = abs(
            previous
            - following
        )

        minutes_before = (
            gap_before
            / 60.0
        )

        minutes_after = (
            gap_after
            / 60.0
        )

        rate_before = (
            difference_before
            / minutes_before
        )

        rate_after = (
            difference_after
            / minutes_after
        )

        isolated_spike = (
            difference_before
            >= spike_threshold
            and
            difference_after
            >= spike_threshold
            and
            neighbor_difference
            <= neighbor_tolerance
            and
            (
                rate_before
                >= max_rate
                or
                rate_after
                >= max_rate
            )
        )

        if isolated_spike:
            invalid_indices.append(
                current_time
            )

    if invalid_indices:

        df.loc[
            invalid_indices,
            tag,
        ] = np.nan

    return (
        df,
        len(
            invalid_indices
        ),
    )


# =====================================================================
# BASIC QC
# =====================================================================

def apply_qc(
    df,
    matched_tags,
):
    """
    Apply QC and preserve QC counts for the QC report.
    """

    print()
    print("Applying QC...")

    qc_stats = {}

    # -------------------------------------------------------------
    # Numeric conversion, sentinel QC, and range QC
    # -------------------------------------------------------------

    for tag, config in VARIABLES.items():

        if tag not in df.columns:
            continue

        df[
            tag
        ] = pd.to_numeric(
            df[
                tag
            ],
            errors="coerce",
        )

        qc_stats[tag] = {
            "source_column":
                matched_tags.get(
                    tag,
                    "",
                ),

            "raw_non_missing":
                int(
                    df[
                        tag
                    ]
                    .notna()
                    .sum()
                ),

            "sentinel_removed":
                0,

            "range_removed":
                0,

            "temporal_removed":
                0,
        }

        # ---------------------------------------------------------
        # Sentinel / missing values
        # ---------------------------------------------------------

        missing_mask = (
            df[
                tag
            ]
            <= MISSING_VALUE_THRESHOLD
        )

        missing_count = int(
            missing_mask.sum()
        )

        qc_stats[
            tag
        ][
            "sentinel_removed"
        ] = missing_count

        if missing_count:

            print(
                f"  {tag:<10} "
                f"{variable_name(tag)}: "
                f"{missing_count} "
                f"sentinel/missing values removed"
            )

            df.loc[
                missing_mask,
                tag,
            ] = np.nan

        # ---------------------------------------------------------
        # Environmental range QC
        # ---------------------------------------------------------

        if not config.get(
            "qc_enabled",
            False,
        ):
            continue

        minimum = config.get(
            "min"
        )

        maximum = config.get(
            "max"
        )

        range_mask = pd.Series(
            False,
            index=df.index,
        )

        if minimum is not None:

            range_mask |= (
                df[
                    tag
                ]
                < minimum
            )

        if maximum is not None:

            range_mask |= (
                df[
                    tag
                ]
                > maximum
            )

        range_count = int(
            range_mask.sum()
        )

        qc_stats[
            tag
        ][
            "range_removed"
        ] = range_count

        if range_count:

            print(
                f"  {tag:<10} "
                f"{variable_name(tag)}: "
                f"{range_count} values outside "
                f"{minimum} to {maximum} removed"
            )

            df.loc[
                range_mask,
                tag,
            ] = np.nan

    # -------------------------------------------------------------
    # Temporal QC
    # -------------------------------------------------------------

    print()
    print(
        "Applying temporal spike/dip QC..."
    )

    for tag, config in VARIABLES.items():

        if tag not in df.columns:
            continue

        if not config.get(
            "temporal_qc_enabled",
            False,
        ):
            continue

        (
            df,
            count,
        ) = apply_temporal_qc(
            df,
            tag,
            config,
        )

        qc_stats[
            tag
        ][
            "temporal_removed"
        ] = count

        if count:

            print(
                f"  {tag:<10} "
                f"{variable_name(tag)}: "
                f"{count} isolated "
                f"spikes/dips removed"
            )

    # -------------------------------------------------------------
    # Final valid counts
    # -------------------------------------------------------------

    for tag in qc_stats:

        qc_stats[
            tag
        ][
            "valid_after_qc"
        ] = int(
            df[
                tag
            ]
            .notna()
            .sum()
        )

    return (
        df,
        qc_stats,
    )


# =====================================================================
# GENERIC STATISTICS
# =====================================================================

def add_standard_statistic(
    summary,
    grouped,
    tag,
    statistic,
):

    grouped_column = (
        grouped[
            tag
        ]
    )

    if statistic == "mean":

        values = (
            grouped_column
            .mean()
        )

        label = "Mean"

    elif statistic == "min":

        values = (
            grouped_column
            .min()
        )

        label = "Min"

    elif statistic == "max":

        values = (
            grouped_column
            .max()
        )

        label = "Max"

    elif statistic == "sum":

        values = (
            grouped_column
            .sum(
                min_count=1
            )
        )

        label = "Sum"

    else:
        return

    summary[
        output_label(
            tag,
            label,
        )
    ] = values


# =====================================================================
# WIND
# =====================================================================

def add_wind_direction_statistics(
    summary,
    grouped,
    tag,
    requested_statistics,
):

    if (
        "circular_mean"
        not in requested_statistics
    ):
        return

    mean_direction = (
        grouped[
            tag
        ]
        .apply(
            circular_mean_deg
        )
    )

    summary[
        "Wind Direction Mean (deg)"
    ] = mean_direction

    if (
        "compass"
        in requested_statistics
    ):

        summary[
            "Wind Direction Mean Compass"
        ] = (
            mean_direction
            .apply(
                degrees_to_compass
            )
        )


def get_max_gust_direction(
    group
):

    if (
        "wg"
        not in group.columns
        or
        "wgd"
        not in group.columns
    ):
        return (
            np.nan,
            None,
        )

    valid = (
        group
        .dropna(
            subset=[
                "wg",
                "wgd",
            ]
        )
    )

    if valid.empty:

        return (
            np.nan,
            None,
        )

    max_index = (
        valid[
            "wg"
        ]
        .idxmax()
    )

    direction = (
        valid.loc[
            max_index,
            "wgd",
        ]
    )

    return (
        direction,
        degrees_to_compass(
            direction
        ),
    )


def add_max_gust_direction(
    summary,
    grouped,
):

    records = []

    for timestamp, group in grouped:

        (
            direction,
            compass,
        ) = get_max_gust_direction(
            group
        )

        records.append(
            {
                "Time":
                    timestamp,

                "Max Gust Direction (deg)":
                    direction,

                "Max Gust Direction Compass":
                    compass,
            }
        )

    if not records:
        return

    result = (
        pd.DataFrame(
            records
        )
        .set_index(
            "Time"
        )
    )

    summary[
        "Max Gust Direction (deg)"
    ] = result[
        "Max Gust Direction (deg)"
    ]

    summary[
        "Max Gust Direction Compass"
    ] = result[
        "Max Gust Direction Compass"
    ]


# =====================================================================
# CUMULATIVE RAIN
# =====================================================================

def cumulative_rain_increment(
    series
):
    """
    Convert a cumulative rain counter into increments.

    Normal increase:
        4.2 -> 4.4 = 0.2

    Counter reset:
        12.6 -> 0.2 = 0.2
    """

    difference = (
        series
        .diff()
    )

    increments = (
        difference
        .copy()
    )

    reset_mask = (
        difference
        < 0
    )

    increments.loc[
        reset_mask
    ] = (
        series.loc[
            reset_mask
        ]
    )

    if len(
        increments
    ) > 0:

        increments.iloc[
            0
        ] = np.nan

    return increments


def prepare_cumulative_rain_changes(
    df
):

    for tag in [
        "rgt",
        "rgt2",
    ]:

        if tag not in df.columns:
            continue

        helper = (
            f"__{tag}_change"
        )

        df[
            helper
        ] = cumulative_rain_increment(
            df[
                tag
            ]
        )

    return df


def add_rain_gauge_comparison(
    summary
):
    """
    Primary meteorological summaries retain:

      Rain Gauge 1 Sum
      Rain Gauge 2 Sum
      Rain Gauge 1 vs 2 Difference

    Cumulative-rain diagnostics are written to the QC report.
    """

    if (
        "rg"
        not in VARIABLES
        or
        "rg2"
        not in VARIABLES
    ):
        return

    rg1_column = output_label(
        "rg",
        "Sum",
    )

    rg2_column = output_label(
        "rg2",
        "Sum",
    )

    if (
        rg1_column not in summary.columns
        or
        rg2_column not in summary.columns
    ):
        return

    unit = (
        variable_unit(
            "rg"
        )
        or "mm"
    )

    comparison_column = (
        "Rain Gauge 1 vs 2 "
        f"Difference ({unit})"
    )

    summary[
        comparison_column
    ] = (
        summary[
            rg1_column
        ]
        - summary[
            rg2_column
        ]
    )


# =====================================================================
# COLUMN ORDER
# =====================================================================

def reorder_columns(
    summary,
    period,
):

    all_columns = list(
        summary.columns
    )

    ordered = []

    def add(column):

        if (
            column
            in all_columns
            and
            column
            not in ordered
        ):
            ordered.append(
                column
            )

    # -------------------------------------------------------------
    # Air temperature means
    # -------------------------------------------------------------

    for tag in [
        "st1",
        "bt1",
        "mt1",
        "htu_t1",
    ]:

        if tag in VARIABLES:

            add(
                output_label(
                    tag,
                    "Mean",
                )
            )

    # -------------------------------------------------------------
    # Daily air temperature minimums
    # -------------------------------------------------------------

    if period == "daily":

        for tag in [
            "st1",
            "bt1",
            "mt1",
            "htu_t1",
        ]:

            if tag in VARIABLES:

                add(
                    output_label(
                        tag,
                        "Min",
                    )
                )

        # ---------------------------------------------------------
        # Daily air temperature maximums
        # ---------------------------------------------------------

        for tag in [
            "st1",
            "bt1",
            "mt1",
            "htu_t1",
        ]:

            if tag in VARIABLES:

                add(
                    output_label(
                        tag,
                        "Max",
                    )
                )

    # -------------------------------------------------------------
    # Humidity
    # -------------------------------------------------------------

    for tag in [
        "sh1",
        "htu_h1",
    ]:

        if tag not in VARIABLES:
            continue

        humidity_stats = (
            [
                "Mean",
                "Min",
                "Max",
            ]
            if period == "daily"
            else [
                "Mean",
            ]
        )

        for statistic in humidity_stats:

            add(
                output_label(
                    tag,
                    statistic,
                )
            )

    # -------------------------------------------------------------
    # Pressure
    # -------------------------------------------------------------

    for tag in [
        "bp1",
        "mslp",
    ]:

        if tag not in VARIABLES:
            continue

        pressure_stats = (
            [
                "Mean",
                "Min",
                "Max",
            ]
            if period == "daily"
            else [
                "Mean",
            ]
        )

        for statistic in pressure_stats:

            add(
                output_label(
                    tag,
                    statistic,
                )
            )

    # -------------------------------------------------------------
    # Wind
    # -------------------------------------------------------------

    for column in [
        "Wind Speed Mean (m/s)",
        "Wind Speed Max (m/s)",
        "Wind Direction Mean (deg)",
        "Wind Direction Mean Compass",
        "Wind Gust Mean (m/s)",
        "Wind Gust Max (m/s)",
        "Max Gust Direction (deg)",
        "Max Gust Direction Compass",
    ]:

        add(
            column
        )

    # -------------------------------------------------------------
    # Rain
    # -------------------------------------------------------------

    if "rg" in VARIABLES:

        add(
            output_label(
                "rg",
                "Sum",
            )
        )

    if "rg2" in VARIABLES:

        add(
            output_label(
                "rg2",
                "Sum",
            )
        )

    if (
        "rg" in VARIABLES
        and
        "rg2" in VARIABLES
    ):

        unit = (
            variable_unit(
                "rg"
            )
            or "mm"
        )

        add(
            "Rain Gauge 1 vs 2 "
            f"Difference ({unit})"
        )

    # -------------------------------------------------------------
    # WBT / WBGT
    # -------------------------------------------------------------

    if "wbt" in VARIABLES:

        add(
            output_label(
                "wbt",
                "Max",
            )
        )

    if "wbgt" in VARIABLES:

        add(
            output_label(
                "wbgt",
                "Max",
            )
        )

    # -------------------------------------------------------------
    # Grass
    # -------------------------------------------------------------

    if (
        "grass_temp"
        in VARIABLES
    ):

        grass_stats = (
            [
                "Mean",
                "Min",
                "Max",
            ]
            if period == "daily"
            else [
                "Mean",
            ]
        )

        for statistic in grass_stats:

            add(
                output_label(
                    "grass_temp",
                    statistic,
                )
            )

    # -------------------------------------------------------------
    # Soil
    # -------------------------------------------------------------

    for tag in [
        "soil20",
        "soil30",
        "soil40",
        "soil50",
    ]:

        if tag not in VARIABLES:
            continue

        soil_stats = (
            [
                "Mean",
                "Min",
                "Max",
            ]
            if period == "daily"
            else [
                "Mean",
            ]
        )

        for statistic in soil_stats:

            add(
                output_label(
                    tag,
                    statistic,
                )
            )

    # -------------------------------------------------------------
    # Anything else configured for summary
    # -------------------------------------------------------------

    remaining = [
        column
        for column in all_columns
        if (
            column not in ordered
            and
            not column.startswith(
                "__"
            )
        )
    ]

    ordered.extend(
        remaining
    )

    return summary[
        ordered
    ]


# =====================================================================
# METEOROLOGICAL SUMMARY GENERATION
# =====================================================================

def summarize(
    df,
    period,
):

    frequency = (
        SUMMARY_PERIODS[
            period
        ]
    )

    grouped = (
        df
        .resample(
            frequency
        )
    )

    summary = pd.DataFrame(
        index=(
            grouped
            .size()
            .index
        )
    )

    max_gust_direction_needed = False

    for tag, config in VARIABLES.items():

        if tag not in df.columns:
            continue

        if not config.get(
            "include_in_summary",
            False,
        ):
            continue

        variable_type = config.get(
            "type",
            "measurement",
        )

        # Cumulative rain totals are retained for QC diagnostics
        # rather than included in meteorological summary files.
        if (
            variable_type
            == "rain_total"
        ):
            continue

        statistics = (
            config
            .get(
                "statistics",
                {}
            )
            .get(
                period,
                [],
            )
        )

        # ---------------------------------------------------------
        # Wind direction
        # ---------------------------------------------------------

        if (
            variable_type
            == "wind_direction"
        ):

            add_wind_direction_statistics(
                summary,
                grouped,
                tag,
                statistics,
            )

            continue

        # ---------------------------------------------------------
        # Standard statistics
        # ---------------------------------------------------------

        for statistic in statistics:

            if statistic in [
                "mean",
                "min",
                "max",
                "sum",
            ]:

                add_standard_statistic(
                    summary,
                    grouped,
                    tag,
                    statistic,
                )

            elif (
                statistic
                == "max_gust_direction"
            ):

                max_gust_direction_needed = True

    # -------------------------------------------------------------
    # Gust direction corresponding to max gust
    # -------------------------------------------------------------

    if (
        max_gust_direction_needed
        and
        "wg"
        in df.columns
        and
        "wgd"
        in df.columns
    ):

        add_max_gust_direction(
            summary,
            grouped,
        )

    # -------------------------------------------------------------
    # Dual rain gauge comparison
    # -------------------------------------------------------------

    add_rain_gauge_comparison(
        summary
    )

    # -------------------------------------------------------------
    # Round numeric output
    # -------------------------------------------------------------

    for column in summary.columns:

        if (
            "Compass"
            in column
        ):
            continue

        if (
            pd.api.types
            .is_numeric_dtype(
                summary[
                    column
                ]
            )
        ):

            summary[
                column
            ] = (
                summary[
                    column
                ]
                .round(
                    2
                )
            )

    return reorder_columns(
        summary,
        period,
    )


# =====================================================================
# QC REPORT
# =====================================================================

def build_qc_report(
    df,
    qc_stats,
    matched_tags,
    missing_observation_times,
):
    """
    Build one QC report containing:

      Dataset-wide observation completeness
      Variable-level completeness and QC counts
      Daily observation completeness
      Partial-day identification
      Rain consistency diagnostics
    """

    rows = []

    observed_count = len(
        df
    )

    missed_count = len(
        missing_observation_times
    )

    expected_count = (
        observed_count
        + missed_count
    )

    if expected_count > 0:

        overall_observation_completeness = (
            observed_count
            / expected_count
            * 100.0
        )

    else:
        overall_observation_completeness = np.nan

    first_observation = (
        df.index.min()
    )

    last_observation = (
        df.index.max()
    )

    # -------------------------------------------------------------
    # Dataset summary
    # -------------------------------------------------------------

    rows.append(
        {
            "Record Type":
                "Dataset",

            "Period":
                "Entire File",

            "Partial Day":
                "",

            "Variable":
                "",

            "Source Column":
                "",

            "Unit":
                "",

            "Observation Count":
                observed_count,

            "Estimated Missed Observations":
                missed_count,

            "Observation Completeness (%)":
                overall_observation_completeness,

            "Variable Completeness (%)":
                np.nan,

            "Raw Non-Missing":
                np.nan,

            "Sentinel Removed":
                np.nan,

            "Range QC Removed":
                np.nan,

            "Temporal QC Removed":
                np.nan,

            "Total QC Removed":
                np.nan,

            "Valid After QC":
                np.nan,

            "Rain Increment Sum":
                np.nan,

            "Rain Cumulative Change":
                np.nan,

            "Rain Difference":
                np.nan,

            "Notes":
                (
                    f"Observed-period completeness. "
                    f"Expected interval: "
                    f"{EXPECTED_INTERVAL_SECONDS} seconds; "
                    f"gap threshold: "
                    f"{GAP_THRESHOLD_SECONDS} seconds"
                ),
        }
    )

    # -------------------------------------------------------------
    # Variable QC rows
    # -------------------------------------------------------------

    variable_denominator = (
        observed_count
        + missed_count
    )

    for tag, stats in qc_stats.items():

        config = VARIABLES.get(
            tag,
            {},
        )

        valid_after = stats.get(
            "valid_after_qc",
            0,
        )

        if (
            config.get(
                "include_completeness",
                False,
            )
            and
            variable_denominator > 0
        ):

            variable_completeness = (
                valid_after
                / variable_denominator
                * 100.0
            )

        else:
            variable_completeness = np.nan

        sentinel_removed = stats.get(
            "sentinel_removed",
            0,
        )

        range_removed = stats.get(
            "range_removed",
            0,
        )

        temporal_removed = stats.get(
            "temporal_removed",
            0,
        )

        total_removed = (
            sentinel_removed
            + range_removed
            + temporal_removed
        )

        rows.append(
            {
                "Record Type":
                    "Variable",

                "Period":
                    "Entire File",

                "Partial Day":
                    "",

                "Variable":
                    variable_name(
                        tag
                    ),

                "Source Column":
                    stats.get(
                        "source_column",
                        "",
                    ),

                "Unit":
                    variable_unit(
                        tag
                    )
                    or "",

                "Observation Count":
                    np.nan,

                "Estimated Missed Observations":
                    np.nan,

                "Observation Completeness (%)":
                    np.nan,

                "Variable Completeness (%)":
                    variable_completeness,

                "Raw Non-Missing":
                    stats.get(
                        "raw_non_missing",
                        np.nan,
                    ),

                "Sentinel Removed":
                    sentinel_removed,

                "Range QC Removed":
                    range_removed,

                "Temporal QC Removed":
                    temporal_removed,

                "Total QC Removed":
                    total_removed,

                "Valid After QC":
                    valid_after,

                "Rain Increment Sum":
                    np.nan,

                "Rain Cumulative Change":
                    np.nan,

                "Rain Difference":
                    np.nan,

                "Notes":
                    "",
            }
        )

    # -------------------------------------------------------------
    # Daily observation completeness
    # -------------------------------------------------------------

    daily_observed = (
        df
        .resample(
            "1D"
        )
        .size()
    )

    daily_missing = (
        missing_observations_by_period(
            missing_observation_times,
            "1D",
        )
    )

    daily_missing = (
        daily_missing
        .reindex(
            daily_observed.index,
            fill_value=0,
        )
    )

    for timestamp in daily_observed.index:

        observed = int(
            daily_observed.loc[
                timestamp
            ]
        )

        missed = int(
            daily_missing.loc[
                timestamp
            ]
        )

        expected = (
            observed
            + missed
        )

        if expected > 0:

            observation_completeness = (
                observed
                / expected
                * 100.0
            )

        else:
            observation_completeness = np.nan

        partial_day = is_partial_day(
            timestamp,
            first_observation,
            last_observation,
        )

        if partial_day:

            notes = (
                "Partial calendar day. Completeness applies "
                "only to the observed portion of the dataset."
            )

        else:
            notes = ""

        rows.append(
            {
                "Record Type":
                    "Daily Completeness",

                "Period":
                    timestamp.strftime(
                        "%Y-%m-%d"
                    ),

                "Partial Day":
                    (
                        "Yes"
                        if partial_day
                        else "No"
                    ),

                "Variable":
                    "",

                "Source Column":
                    "",

                "Unit":
                    "",

                "Observation Count":
                    observed,

                "Estimated Missed Observations":
                    missed,

                "Observation Completeness (%)":
                    observation_completeness,

                "Variable Completeness (%)":
                    np.nan,

                "Raw Non-Missing":
                    np.nan,

                "Sentinel Removed":
                    np.nan,

                "Range QC Removed":
                    np.nan,

                "Temporal QC Removed":
                    np.nan,

                "Total QC Removed":
                    np.nan,

                "Valid After QC":
                    np.nan,

                "Rain Increment Sum":
                    np.nan,

                "Rain Cumulative Change":
                    np.nan,

                "Rain Difference":
                    np.nan,

                "Notes":
                    notes,
            }
        )

    # -------------------------------------------------------------
    # Rain consistency diagnostics
    # -------------------------------------------------------------

    rain_pairs = [
        (
            "rg",
            "rgt",
            "Rain Gauge 1",
        ),
        (
            "rg2",
            "rgt2",
            "Rain Gauge 2",
        ),
    ]

    for (
        rain_tag,
        total_tag,
        gauge_name,
    ) in rain_pairs:

        helper = (
            f"__{total_tag}_change"
        )

        if (
            rain_tag not in df.columns
            or
            helper not in df.columns
        ):
            continue

        increment_sum = (
            df[
                rain_tag
            ]
            .sum(
                min_count=1
            )
        )

        cumulative_change = (
            df[
                helper
            ]
            .sum(
                min_count=1
            )
        )

        if (
            pd.notna(
                increment_sum
            )
            and
            pd.notna(
                cumulative_change
            )
        ):

            difference = (
                increment_sum
                - cumulative_change
            )

        else:
            difference = np.nan

        rows.append(
            {
                "Record Type":
                    "Rain QC",

                "Period":
                    "Entire File",

                "Partial Day":
                    "",

                "Variable":
                    gauge_name,

                "Source Column":
                    matched_tags.get(
                        rain_tag,
                        "",
                    ),

                "Unit":
                    variable_unit(
                        rain_tag
                    )
                    or "",

                "Observation Count":
                    np.nan,

                "Estimated Missed Observations":
                    np.nan,

                "Observation Completeness (%)":
                    np.nan,

                "Variable Completeness (%)":
                    np.nan,

                "Raw Non-Missing":
                    np.nan,

                "Sentinel Removed":
                    np.nan,

                "Range QC Removed":
                    np.nan,

                "Temporal QC Removed":
                    np.nan,

                "Total QC Removed":
                    np.nan,

                "Valid After QC":
                    np.nan,

                "Rain Increment Sum":
                    increment_sum,

                "Rain Cumulative Change":
                    cumulative_change,

                "Rain Difference":
                    difference,

                "Notes":
                    (
                        "Rain Difference = "
                        "incremental rain sum - "
                        "cumulative rain change"
                    ),
            }
        )

    qc_report = pd.DataFrame(
        rows
    )

    # -------------------------------------------------------------
    # Round numeric fields
    # -------------------------------------------------------------

    numeric_columns = [
        "Observation Completeness (%)",
        "Variable Completeness (%)",
        "Rain Increment Sum",
        "Rain Cumulative Change",
        "Rain Difference",
    ]

    for column in numeric_columns:

        if column in qc_report.columns:

            qc_report[
                column
            ] = (
                pd.to_numeric(
                    qc_report[
                        column
                    ],
                    errors="coerce",
                )
                .round(
                    2
                )
            )

    return qc_report


# =====================================================================
# MAIN
# =====================================================================

def main():

    if (
        len(sys.argv)
        != 2
    ):

        print()
        print("Usage:")
        print(
            "  python summarize_chords.py "
            "<input_csv>"
        )
        print()

        print("Example:")
        print(
            '  python summarize_chords.py '
            '"/path/to/station_data.csv"'
        )

        print()

        sys.exit(
            1
        )

    input_path = Path(
        sys.argv[
            1
        ]
    )

    if not input_path.exists():

        raise FileNotFoundError(
            f"Input CSV not found: "
            f"{input_path}"
        )

    OUTPUT_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -------------------------------------------------------------
    # Read CSV
    # -------------------------------------------------------------

    print()
    print(
        f"Reading: "
        f"{input_path}"
    )

    df = pd.read_csv(
        input_path
    )

    # -------------------------------------------------------------
    # Timestamp
    # -------------------------------------------------------------

    if (
        TIMESTAMP_COLUMN
        not in df.columns
    ):

        raise ValueError(
            'Missing required "Time" column'
        )

    df[
        TIMESTAMP_COLUMN
    ] = pd.to_datetime(
        df[
            TIMESTAMP_COLUMN
        ],
        errors="coerce",
    )

    invalid_times = (
        df[
            TIMESTAMP_COLUMN
        ]
        .isna()
        .sum()
    )

    if invalid_times:

        print(
            f"Removing "
            f"{invalid_times} "
            f"invalid timestamps."
        )

    df = (
        df
        .dropna(
            subset=[
                TIMESTAMP_COLUMN
            ]
        )
    )

    df = (
        df
        .sort_values(
            TIMESTAMP_COLUMN
        )
    )

    duplicates = (
        df[
            TIMESTAMP_COLUMN
        ]
        .duplicated()
        .sum()
    )

    if duplicates:

        print(
            f"Removing "
            f"{duplicates} "
            f"duplicate timestamps."
        )

        df = (
            df
            .drop_duplicates(
                subset=[
                    TIMESTAMP_COLUMN
                ],
                keep="first",
            )
        )

    df = (
        df
        .set_index(
            TIMESTAMP_COLUMN
        )
    )

    # -------------------------------------------------------------
    # Infer missing observations BEFORE sensor QC
    # -------------------------------------------------------------

    missing_observation_times = (
        infer_missing_observation_times(
            df.index
        )
    )

    print()
    print(
        f"Expected observation interval: "
        f"{EXPECTED_INTERVAL_SECONDS} seconds"
    )

    print(
        f"Missing-observation gap threshold: "
        f"{GAP_THRESHOLD_SECONDS} seconds"
    )

    print(
        f"Inferred missing observations: "
        f"{len(missing_observation_times)}"
    )

    # -------------------------------------------------------------
    # Map CHORDS names to canonical tags
    # -------------------------------------------------------------

    (
        df,
        matched_tags,
        missing_tags,
        unmapped_columns,
    ) = map_source_columns(
        df
    )

    # -------------------------------------------------------------
    # QC
    # -------------------------------------------------------------

    (
        df,
        qc_stats,
    ) = apply_qc(
        df,
        matched_tags,
    )

    # -------------------------------------------------------------
    # Prepare cumulative-rain diagnostics
    # -------------------------------------------------------------

    df = prepare_cumulative_rain_changes(
        df
    )

    # -------------------------------------------------------------
    # Dataset information
    # -------------------------------------------------------------

    print()
    print(
        f"Source observations: "
        f"{len(df)}"
    )

    print(
        f"Period: "
        f"{df.index.min()} "
        f"to "
        f"{df.index.max()}"
    )

    # -------------------------------------------------------------
    # Meteorological summaries
    # -------------------------------------------------------------

    outputs = {}

    for period in [
        "15min",
        "hourly",
        "daily",
    ]:

        print()
        print(
            f"Creating "
            f"{period} summary..."
        )

        outputs[
            period
        ] = summarize(
            df,
            period,
        )

    # -------------------------------------------------------------
    # QC report
    # -------------------------------------------------------------

    print()
    print(
        "Creating QC report..."
    )

    qc_report = build_qc_report(
        df,
        qc_stats,
        matched_tags,
        missing_observation_times,
    )

    # -------------------------------------------------------------
    # Output filenames
    # -------------------------------------------------------------

    base_name = (
        input_path
        .stem
    )

    output_files = {
        "15min":
            OUTPUT_PATH
            / (
                f"{base_name}"
                f"_15min.csv"
            ),

        "hourly":
            OUTPUT_PATH
            / (
                f"{base_name}"
                f"_hourly.csv"
            ),

        "daily":
            OUTPUT_PATH
            / (
                f"{base_name}"
                f"_daily.csv"
            ),

        "qc_report":
            OUTPUT_PATH
            / (
                f"{base_name}"
                f"_qc_report.csv"
            ),
    }

    # -------------------------------------------------------------
    # Write meteorological summaries
    # -------------------------------------------------------------

    for period in [
        "15min",
        "hourly",
        "daily",
    ]:

        outputs[
            period
        ].to_csv(
            output_files[
                period
            ],
            index_label="Time",
        )

    # -------------------------------------------------------------
    # Write QC report
    # -------------------------------------------------------------

    qc_report.to_csv(
        output_files[
            "qc_report"
        ],
        index=False,
    )

    # -------------------------------------------------------------
    # Finished
    # -------------------------------------------------------------

    print()
    print("Finished.")
    print()

    print(
        f"QC profile: "
        f"{PROFILE_NAME}"
    )

    print(
        f"Expected interval: "
        f"{EXPECTED_INTERVAL_SECONDS} seconds"
    )

    print(
        f"Gap threshold: "
        f"{GAP_THRESHOLD_SECONDS} seconds"
    )

    print()

    for (
        label,
        path,
    ) in output_files.items():

        print(
            f"{label:<10}: "
            f"{path}"
        )

    print()


if __name__ == "__main__":
    main()
