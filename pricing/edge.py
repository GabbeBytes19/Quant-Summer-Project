import polars as pl
from config import settings
def prob_market_v_model(p_model,df_result):
    P_Model = pl.Series(p_model)
    P_Market = df_result["p"]
    edge = P_Model - P_Market 

    df_final = df_result.with_columns(edge = edge ,p_model = P_Model)
    


    return df_final.drop_nulls()

def effective_edge(edge):
    
    #spread = edge["outcomePrices"].max() - edge["outcomePrices"].min()
    #Spread history Polymarket do not provide, so we need to go with som other source
    # Either let me collect , but thus there is little data much better to take from outside
    spread = 0.05
    effect_edge = edge.with_columns( ( pl.col("edge") - spread/2 - settings.FEE_RATE).alias("effective_edge"))
    
    effect_edge = effect_edge.with_columns(pl.when((pl.col("edge").abs() >= settings.MIN_EDGE) & (pl.col("effective_edge").abs() >= settings.MIN_EFFECTIVE_EDGE)).then(True).otherwise(False).alias("effective_edge_flag"))
    return effect_edge



