import polars as pl

from config import settings
from pricing import fair_value
from evaluation import eval_loop


def test_get_bucket_polymarket_handles_open_ended_buckets():
    df_result = pl.DataFrame({
        "groupItemTitle": ["25°C", "20°C or below", "34°C or higher"],
    })
    buckets = fair_value.create_buckets(20, 36)

    result = fair_value.get_bucket_polymarket(df_result, buckets)
    predicted = result["predicted_indices"].to_list()

    assert predicted[0] == buckets.index((25, 26))
    assert predicted[1] is None  # "below" market has no fixed-bucket index
    assert predicted[2] is None  # "higher" market has no fixed-bucket index


def test_run_eval_loop_polymarket_matches_ground_truth_by_date_not_row_position(monkeypatch):
    # two row ground truth, so the forecast history requirement must be switched off for this test
    monkeypatch.setattr(settings, "MIN_FORECAST_HISTORY", 0)
    buckets = fair_value.create_buckets(20, 32)

    # df_pair (ground truth) rows deliberately in a different order than df_result,
    # to catch a regression back to matching by row position instead of by "date".
    df_pair = pl.DataFrame({
        "date": ["2024-01-02", "2024-01-01"],
        "actual_temp": [20.5, 30.5],  # -> correct buckets (20,21) and (30,31)
    })
    df_result = pl.DataFrame({
        "date": ["2024-01-01", "2024-01-02"],
        # both markets have the SAME own bucket, so only the ground-truth date match
        # can tell these two rows apart
        "groupItemTitle": ["30°C", "30°C"],
    })

    dummy_factory = lambda day: (lambda low, high: 0.5)
    result = eval_loop.run_eval_loop_polymarket(dummy_factory, buckets, df_pair, df_result)

    flag_by_date = dict(zip(result["date"].to_list(), result["win/loss flag"].to_list()))

    # 2024-01-01's real outcome was (30,31) -> matches this market's own (30,31) bucket -> win
    assert flag_by_date["2024-01-01"] == 1
    # 2024-01-02's real outcome was (20,21) -> does NOT match this market's (30,31) bucket -> loss
    assert flag_by_date["2024-01-02"] == 0
