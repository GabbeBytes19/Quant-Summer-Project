import polars as pl

def prob_market_v_model(p_model,df_result):
    P_Model = pl.Series(p_model)
    P_Market = df_result["p"]
    edge = P_Model - P_Market 

    df_final = df_result.with_columns(edge = edge )
    return df_final.drop_nulls()