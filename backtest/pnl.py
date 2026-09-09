
from evaluation.eval_loop import run_eval_loop_polymarket
from risk.metrics import  value_at_risk,expected_shortfall,rolling_max_dd,sharpe_ratio
from backtest.engine import engine
import polars as pl
def run_all_models(df_result,models):

    #run_eval_loop_polymarket(prob_fn_factory,buckets,df_pair,df_result)
    result= {}
    for key,value in models.items():
       engine_res = engine(value,df_result)
       result[key] = engine_res
    return result

def get_pnl(results):
    for key,value in results.items():
        print( "=== Scores === ")
        print(f" Model {key} has profit {value.select(pl.last("cumulative_profit")).item()}")
        print(f" Model {key} has value at risk {value_at_risk(value)}")
        print(f" Model {key} has expected_shortfall {expected_shortfall(value, value_at_risk(value))}")
        print(f" Model {key} has sharpe ratio {sharpe_ratio(value)}")
        df = rolling_max_dd(value)
        smallest_val = df["rolling_max"].max()
        print(f" Model {key} has rolling max {smallest_val}")
        print(f" Model {key} had trade count {value.select(pl.len()).item()}")