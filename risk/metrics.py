from config import settings
import numpy as np
import polars as pl

from numpy.lib.stride_tricks import as_strided
import pandas as pd
import matplotlib.pyplot as plt

def value_at_risk(df):
    returns = df["outcomePrices"]
    if df["outcomePrices"].is_empty():
        raise ValueError("The 'outcomePrices' column is empty.")

    var_95 = -df.select(pl.col("outcomePrices").quantile(settings.ALPHA)).item()
    return var_95

def expected_shortfall(df,var_95):
    cvar_95 = -df.filter(pl.col("outcomePrices") <= -var_95).select(pl.col("outcomePrices").mean()).item()  
    return cvar_95




# Source - https://stackoverflow.com/a/21059308
# Posted by Warren Weckesser, modified by community. See post 'Timeline' for change history
# Retrieved 8/6/2026, License - CC BY-SA 3.0



def rolling_max_dd(df):
    df_roll_max = df.with_columns(rolling_row_max=pl.col("outcomePrices").rolling_max_by("date",window_size="1h"))
    return df_roll_max
