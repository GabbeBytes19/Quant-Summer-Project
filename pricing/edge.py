import polars as pl
from config import settings
def prob_market_v_model(p_model,df_result):
    P_Model = pl.Series(p_model)
    P_Market = df_result["p"]
    edge = P_Model - P_Market 

    df_final = df_result.with_columns(edge = edge )
    return df_final.drop_nulls()

def effective_edge(edge):
    spread = edge["outcomePrices"].max() - edge["outcomePrices"].min()
    effect_edge = edge.with_columns(pl.col("edge") - spread/2 - settings.FEE_RATE)
    if effect_edge["edge"].max() < settings.MIN_EFFECTIVE_EDGE: #or 0 ? 
        return None
    return effect_edge
    