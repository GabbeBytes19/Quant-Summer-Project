import polars as pl
import pytest

from risk import metrics
from config import settings


def test_rolling_max_dd_never_negative():
    df = pl.DataFrame({"cumulative_profit": [0.1, 0.05, 0.2, -0.1, 0.3, 0.25]})
    result = metrics.rolling_max_dd(df)

    assert (result["rolling_max"] >= 0).all()


def test_rolling_max_dd_resets_to_zero_at_new_peak():
    df = pl.DataFrame({"cumulative_profit": [0.1, -0.05, 0.3]})
    result = metrics.rolling_max_dd(df)

    dd = result["rolling_max"].to_list()
    assert dd[0] == pytest.approx(0.0)   # first point is its own peak
    assert dd[1] == pytest.approx(0.15)  # 0.1 - (-0.05)
    assert dd[2] == pytest.approx(0.0)   # new peak -> drawdown resets


def test_value_at_risk_raises_on_empty_profit():
    df = pl.DataFrame({"profit": []}, schema={"profit": pl.Float64})
    with pytest.raises(ValueError):
        metrics.value_at_risk(df)


def test_value_at_risk_matches_manual_quantile():
    df = pl.DataFrame({"profit": [-0.5, -0.3, -0.1, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]})
    var = metrics.value_at_risk(df)
    expected = -df.select(pl.col("profit").quantile(settings.ALPHA)).item()
    assert var == pytest.approx(expected)


def test_expected_shortfall_averages_tail_beyond_var():
    df = pl.DataFrame({"profit": [-0.5, -0.4, -0.3, -0.2, -0.1, 0.1, 0.2]})
    var = metrics.value_at_risk(df)
    es = metrics.expected_shortfall(df, var)

    tail_mean = df.filter(pl.col("profit") <= -var).select(pl.col("profit").mean()).item()
    assert es == pytest.approx(-tail_mean)
