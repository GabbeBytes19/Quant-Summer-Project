import polars as pl

def prob_market_v_model(p_model,df_result):
    P_Model = pl.Series(p_model)
    P_Market = df_result["p"]
    edge = P_Model - P_Market 
    df_edge = pl.Series('edge',edge)
    df_final = df_result.insert_column(1,df_edge)

    return df_final.drop_nulls()