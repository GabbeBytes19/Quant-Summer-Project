import polars as pl


def synthetic_actual_df() -> pl.DataFrame:
    """Matches fetch_data()'s output shape: one row per day."""
    return pl.DataFrame({
        "time": [f"2024-06-{d:02d}" for d in range(1, 11)],
        "temperature_2m_max": [30.1, 31.4, 29.8, 32.0, 33.1, 30.5, 29.2, 31.8, 32.6, 30.9],
        "temperature_2m_min": [25.0, 26.1, 24.5, 26.8, 27.4, 25.2, 24.0, 26.5, 27.0, 25.6],
        "precipitation_sum": [0.0, 2.3, 0.0, 0.0, 5.1, 0.0, 1.2, 0.0, 0.0, 0.4],
    })


def synthetic_previous_df() -> pl.DataFrame:
    """Matches fetch_previous_forecast_data()'s output shape: hourly rows, previous_day1-5 columns.

    Each previous_dayN is built from the same daily peak used in synthetic_actual_df(),
    with a small fixed warm bias baked in (larger for longer lead times) so the data
    behaves like a real forecast - close to actual, not identical.
    """
    daily_max = [30.1, 31.4, 29.8, 32.0, 33.1, 30.5, 29.2, 31.8, 32.6, 30.9]
    bias_by_lead = [0.8, 1.0, 1.1, 1.2, 1.4]

    times, day1, day2, day3, day4, day5 = [], [], [], [], [], []
    columns = [day1, day2, day3, day4, day5]

    for d, peak in enumerate(daily_max, start=1):
        for h in range(24):
            times.append(f"2024-06-{d:02d}T{h:02d}:00")
            hour_shape = -4 + 4 * (1 - abs(h - 14) / 14)
            for col, bias in zip(columns, bias_by_lead):
                col.append(round(peak + hour_shape + bias, 1))

    return pl.DataFrame({
        "time": times,
        "temperature_2m_previous_day1": day1,
        "temperature_2m_previous_day2": day2,
        "temperature_2m_previous_day3": day3,
        "temperature_2m_previous_day4": day4,
        "temperature_2m_previous_day5": day5,
    })
