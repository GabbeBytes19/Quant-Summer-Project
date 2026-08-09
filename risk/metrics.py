from config import settings
import numpy as np
import polars as pl

from numpy.lib.stride_tricks import as_strided
import pandas as pd
import matplotlib.pyplot as plt

def value_at_risk(df):
    if df["profit"].is_empty():
        raise ValueError("The 'profit' column is empty.")

    var_95 = -df.select(pl.col("profit").quantile(settings.ALPHA)).item()
    return var_95

def expected_shortfall(df,var_95):
    cvar_95 = -df.filter(pl.col("profit") <= -var_95).select(pl.col("profit").mean()).item()  
    return cvar_95




# Source - https://stackoverflow.com/a/21059308
# Posted by Warren Weckesser, modified by community. See post 'Timeline' for change history
# Retrieved 8/6/2026, License - CC BY-SA 3.0



def rolling_max_dd(df):

    df_roll_max = df.with_columns(( pl.col("cumulative_profit").cum_max()-pl.col("cumulative_profit")).alias("rolling_max"))
    return df_roll_max
