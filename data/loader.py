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
