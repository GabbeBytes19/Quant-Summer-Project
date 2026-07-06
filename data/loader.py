import polars as pl

from config import settings

"""
So the function:
- Takes a clean DataFrame as input
- Adds a new column called event — 1 if temperature_2m_max > settings.EVENT_THRESHOLD, else 0
- Returns the DataFrame with that column added

In Polars, adding a new column is done with with_columns. Go open VS Code and write it.
"""


def add_event_column(df):

    df = df.with_columns(
        (df["temperature_2m_max"] > settings.EVENT_THRESHOLD)
        .cast(pl.Int8)
        .alias("event")
    )

    return df


def filter_summer(df):
    summer_months = [6,7,8]
    df_months = df.with_columns(
    pl.col("time").str.to_date().alias("date")
    ).with_columns(
    pl.col("date").dt.month().alias("month")
    )
    return df_months.filter(pl.col("month").is_in(summer_months))
