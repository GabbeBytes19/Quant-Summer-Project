from config import settings
import numpy as np


def value_at_risk(df):
    returns = df["outcomePrices"]
    if df["outcomePrices"].is_empty():
        raise ValueError("The 'outcomePrices' column is empty.")

    df_returns = df["outcomePrices"].to_list()
    for res in df_returns:
        if res <= settings.ALPHA:
            
    var = -np.precentile(returns, settings.ALPHA * 100)