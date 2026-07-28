from config import settings
import polars as pl

def clean_data(df):
    # If the data is not correct format or are missing values , we need to clean the data and return a clean dataframe
    # If its less than 5 nulls in a row --> interpolate , else --> discard the data
    orignal_length = len(df)
    if df[
        "time", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"
    ].is_empty():
        return None

    if (
        df["time", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"]
        .null_count().pipe(sum).item() > 0
    ):
        df = df.interpolate()
        df = df.drop_nulls()

    if orignal_length - len(df) > settings.MAX_NULL_GAP:
        return None

    return df

def clean_polymarket_data(df_poly_market):
    df_selected = df_poly_market.select(
        pl.col("markets").struct.unnest()
    ).select(
        pl.col("endDateIso").alias("date"),
        "groupItemTitle", "groupItemThreshold", "outcomes",
        "outcomePrices", "slug", "umaResolutionStatus", "closed","clobTokenIds", "endDate"
    )
    df_selected = df_selected.with_columns(pl.col("clobTokenIds").str.json_decode(dtype=pl.List(pl.String)))
    df_selected = df_selected.with_columns(pl.col("outcomePrices").str.json_decode(dtype=pl.List(pl.String)).cast(pl.List(pl.Float64)))
    df_selected = df_selected.with_columns(pl.col("outcomes").str.json_decode(dtype=pl.List(pl.String)))
    df_selected = df_selected.with_columns(pl.col("groupItemThreshold").str.to_integer(strict=False))
    df_selected = df_selected.with_columns(pl.col("endDate").str.to_datetime(time_zone = 'UTC'))
    df_selected = df_selected.with_columns(pl.col("endDate").dt.offset_by('-1d').dt.epoch(time_unit="s").alias("target"))

    df_selected = df_selected.sort("date", "groupItemThreshold")

    return df_selected


# Source - https://stackoverflow.com/a/78350448
# Posted by Hericks, modified by community. See post 'Timeline' for change history
# Retrieved 6/30/2026, License - CC BY-SA 4.0

