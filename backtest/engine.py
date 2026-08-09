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

    df_effective_edge = df_effective_edge.filter(pl.col("effective_edge_flag") == True)

    df_side = df_effective_edge.with_columns(pl.when(pl.col("edge") > 0).then(pl.lit("Yes")).otherwise(pl.lit("No")).alias("side"))


    df_side = df_side.with_columns(pl.when(pl.col("side") == "Yes").then(df_side["p"]).otherwise(1- df_side["p"]).alias("price_paid"))

    #stake = df_side["stake"]
    stake = 0.05

    df_side = df_side.filter( (pl.col("price_paid") != 0) & (pl.col("price_paid") != 1)  )
    df_side = df_side.with_columns(pl.when(((pl.col("side") == "Yes") & (pl.col("win/loss flag") == 1))| ((pl.col("side") == "No") & (pl.col("win/loss flag") == 0))).then(stake * (1 / df_side["price_paid"] - 1) * (1 - settings.FEE_RATE)).otherwise(-stake).alias("profit"))
    df_side = df_side.sort("date")
    df_final = df_side.with_columns(pl.col("profit").cum_sum().alias("cumulative_profit"))

    return df_final