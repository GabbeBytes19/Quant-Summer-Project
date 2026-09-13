import polars as pl
from config import settings
def prob_market_v_model(p_model,df_result):
    P_Model = pl.Series(p_model)
    P_Market = df_result["p"]
    edge = P_Model - P_Market 

    df_final = df_result.with_columns(edge = edge ,p_model = P_Model)
    


    return df_final.drop_nulls()

def effective_edge(edge):
    
    # costs reduce the magnitude of the edge on whichever side is bet, so apply them to abs(edge) and keep the sign
    effect_edge = edge.with_columns(
        (pl.col("edge").sign() * (pl.col("edge").abs() - settings.ASSUMED_SPREAD / 2 - settings.FEE_RATE)).alias("effective_edge")
    )
    
    effect_edge = effect_edge.with_columns(pl.when((pl.col("edge").abs() >= settings.MIN_EDGE) & (pl.col("effective_edge").abs() >= settings.MIN_EFFECTIVE_EDGE)).then(True).otherwise(False).alias("effective_edge_flag"))
    return effect_edge



