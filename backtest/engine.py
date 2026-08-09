from pricing.edge import (
    prob_market_v_model,
    effective_edge,
)
from config import settings
import polars as pl

def engine(p_model,df_result):
    edge = prob_market_v_model(p_model,df_result)
    #edge has date,marketprob,edge,stake, win/loss flag
    df_effective_edge = effective_edge(edge)

    df_effective_edge = df_effective_edge.filter ((pl.col("effective_edge_flag") == True).alias("Only_True_Flag"))

    df_side = df_effective_edge.with_columns(pl.when(pl.col("Only_True_Flag") > 0).then("Yes").otherwise("No").alias("side"))


    df_side = df_side.with_columns(pl.when(pl.col("side") == "Yes").then(df_side["market_prob"]).otherwise(1- df_side["market_prob"]).alias("price_paid"))

    stake = edge["stake"]

    df_side = df_side.with_columns(pl.when(((pl.col("side") == "Yes") & (pl.col("win/loss flag") == 1)) & ((pl.col("side") == "No") & (pl.col("win/loss flag") == 0))).then(stake * (1 / df_side["price_paid"] - 1) * (1 - settings.FEE_RATE)).otherwise(-stake).alias("profit"))
    df_final = df_side.with_columns(pl.col("profit").cumsum().alias("cumulative_profit"))

    return df_final.sort("date")