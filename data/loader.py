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

def get_separate_summer_months(df):
    filtered_df = filter_summer(df)
    df_june = filtered_df.filter(pl.col("month") == 6)
    df_july = filtered_df.filter(pl.col("month") == 7)
    df_august= filtered_df.filter(pl.col("month") == 8)
    
    return df_june, df_july, df_august

def add_market_prob_column(df):
    #take clean_polymarket_data
    if not df["outcomes"].list.first().eq("Yes").all():
        raise ValueError("First outcome is not 'Yes' for all rows")
    df = df.with_columns(pl.col("outcomePrices").list.first().alias("market_prob"))
    df = df.with_columns(pl.col("clobTokenIds").list.first().alias("yes_token_id"))
    df = df.sort("yes_token_id")
    return df


def filter_resolved(df_selected):
    df_selected = df_selected.filter(pl.col("closed") == True)
    return df_selected
