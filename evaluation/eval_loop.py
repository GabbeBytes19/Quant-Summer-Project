import polars as pl
from config import settings
from pricing.fair_value import (
    find_correct_bucket,
    build_probability_vector,
    create_buckets,
    get_bucket_polymarket,
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
    # df_pair is sorted by date, so the first MIN_FORECAST_HISTORY rows lack enough earlier days to estimate forecast error
    for i, row in enumerate(df_pair.iter_rows(named = True)):
        if i < settings.MIN_FORECAST_HISTORY:
            continue
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
    for i, row in enumerate(df_pair.iter_rows(named = True)):
        if i < settings.MIN_FORECAST_HISTORY:
            continue
        try:
            correct_idx = find_correct_bucket(row["actual_temp"], buckets)
        except ValueError:
            continue
        prob_fn = prob_fn_factory(row["date"])
        prob_vector = build_probability_vector(prob_fn, buckets)
        prob_matrix.append(prob_vector)
        correct_indices.append(correct_idx)
        dates.append(row["date"])
    df_correct = pl.DataFrame(
        {"date": dates, "correct_indices": correct_indices},
        schema={"date": pl.String, "correct_indices": pl.Int64},
    )
    df_result = get_bucket_polymarket(df_result, buckets)

    df_res = df_result.join(df_correct, on = "date", how = "left")
    # an open ended market or a day without ground truth has no knowable outcome, keep it null instead of calling it a loss
    df_res = df_res.with_columns(
        pl.when(pl.col("correct_indices").is_null() | pl.col("predicted_indices").is_null())
        .then(None)
        .when(pl.col("correct_indices") == pl.col("predicted_indices"))
        .then(1)
        .otherwise(0)
        .alias("win/loss flag")
    )
    return df_res


def make_static_factory(prob_fn):
    def factory(day):
        return prob_fn
    return factory

def bayes_static_factory(bayesian_prob_fn):
    def layer(day):
        def inner_func(low,high):
            return bayesian_prob_fn(day,low,high)
        return inner_func
    return layer