import polars as pl
from pricing.fair_value import (
    find_correct_bucket,
    build_probability_vector,
    create_buckets,

)

from models.baseline import (
    gaussian_probability,
)

from models.bayesian_model import (
    posterior_probability,
    bayesian_interference,
     
)
from models.kde_model import (
    kde_estimate
)

def run_eval(prob_fn_factory, buckets, df_pair):

    prob_matrix = []
    correct_indices = []
    for row in df_pair.iter_rows(named = True):
        try:
            correct_idx = find_correct_bucket(row["actual_temp"], buckets)
        except ValueError:
            continue
        prob_fn = prob_fn_factory(row["date"])
        prob_vector = build_probability_vector(prob_fn, buckets)
        prob_matrix.append(prob_vector)
        correct_indices.append(correct_idx)

    return prob_matrix,correct_indices                                  


def run_eval_loop_polymarket(prob_fn_factory,buckets,df_pair,df_result):
    #df_pair is the groundtruth
    #df_result is the polymarket
    prob_matrix = []
    correct_indices = []
    dates = []
    for row in df_pair.iter_rows(named = True):
        try:
            correct_idx = find_correct_bucket(row["actual_temp"], buckets)
        except ValueError:
            continue
        prob_fn = prob_fn_factory(row["date"])
        prob_vector = build_probability_vector(prob_fn, buckets)
        prob_matrix.append(prob_vector)
        correct_indices.append(correct_idx)
        dates.append(row["date"])
    df_correct= pl.DataFrame({"date": dates, "correct_indices": correct_indices})

    df_res = df_result.join(df_correct, on = "date", how = "left")
    df_res = df_res.with_columns(pl.when(pl.col("correct_indices") == pl.col("will be coming later beaucse we dont have data yet")).then(1).otherwise(0).alias("win/loss flag"))
    return df_res
                        