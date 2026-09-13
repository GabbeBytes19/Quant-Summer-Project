import polars as pl
import pytest

from config import settings
from data import fetcher, cleaner
from evaluation import eval_loop
from models.bayesian_model import bayesian_interference
from pricing import edge, fair_value
import run_experiment


# --- pricing/edge.py: cost filter must treat Yes and No sides the same ---

def test_effective_edge_flag_is_symmetric_in_sign():
    # +0.06 and -0.06 carry the same gross edge, so costs must shrink both by the same amount
    df = pl.DataFrame({"edge": [0.06, -0.06, 0.10, -0.10]})
    result = edge.effective_edge(df)

    flags = result["effective_edge_flag"].to_list()
    assert flags[0] == flags[1]
    assert flags[2] == flags[3]

    # 0.06 - 0.025 - 0.02 = 0.015 < MIN_EFFECTIVE_EDGE, so neither side may pass
    assert flags[0] is False
    assert flags[1] is False


def test_effective_edge_magnitude_is_symmetric_in_sign():
    df = pl.DataFrame({"edge": [0.08, -0.08]})
    result = edge.effective_edge(df)

    eff = result["effective_edge"].abs().to_list()
    assert eff[0] == pytest.approx(eff[1])


# --- models/bayesian_model.py: likelihood parameters may only use days strictly before the scored day ---

def _df_pair_with_outlier_on_last_day():
    # 19 days with alternating +/-0.1 forecast error, then one day with a +10 error
    dates = [f"2024-06-{d:02d}" for d in range(1, 21)]
    actual = [30.0] * 20
    predicted = [30.1 if d % 2 == 1 else 29.9 for d in range(1, 20)] + [40.0]
    return pl.DataFrame({
        "date": dates,
        "actual_temp": actual,
        "daily_max_predicted": predicted,
    })


def _df_summer():
    return [28.0, 29.0, 30.0, 31.0, 32.0] * 10


def test_bayesian_likelihood_excludes_the_scored_day():
    df_pair = _df_pair_with_outlier_on_last_day()
    day = "2024-06-20"
    forecast_value = fetcher.get_specific_day(day, df_pair)

    _, _, _, _, _, likelihood_mean = bayesian_interference(_df_summer(), day, df_pair)

    # bias estimated from the 19 prior days is ~0, so the likelihood mean must sit on the forecast
    # if the scored day's own +10 error leaks in, the bias becomes 0.5 and this fails
    assert abs(likelihood_mean - forecast_value) < 0.05


def test_bayesian_likelihood_excludes_future_days():
    df_pair = _df_pair_with_outlier_on_last_day()
    day = "2024-06-10"
    forecast_value = fetcher.get_specific_day(day, df_pair)

    _, _, _, _, _, likelihood_mean = bayesian_interference(_df_summer(), day, df_pair)

    # only 2024-06-01 to 2024-06-09 may inform the bias, the +10 outlier on 06-20 is in the future
    assert abs(likelihood_mean - forecast_value) < 0.05


# --- data/fetcher.py: the forecast fetch must honour the date range it is given ---

class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_previous_forecast_data_sends_requested_date_range(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured.update(params)
        hourly = {"time": ["2024-06-01T00:00"]}
        for lead in range(1, 6):
            hourly[f"temperature_2m_previous_day{lead}"] = [30.0]
        return _FakeResponse({"hourly": hourly})

    monkeypatch.setattr(fetcher.requests, "get", fake_get)

    fetcher.fetch_previous_forecast_data("2024-06-01", "2024-06-10")

    assert captured.get("start_date") == "2024-06-01"
    assert captured.get("end_date") == "2024-06-10"
    assert "past_days" not in captured


def test_fetch_previous_forecast_data_sends_configured_timezone(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured.update(params)
        hourly = {"time": ["2024-06-01T00:00"]}
        for lead in range(1, 6):
            hourly[f"temperature_2m_previous_day{lead}"] = [30.0]
        return _FakeResponse({"hourly": hourly})

    monkeypatch.setattr(fetcher.requests, "get", fake_get)

    fetcher.fetch_previous_forecast_data("2024-06-01", "2024-06-10")

    # actuals are fetched in settings.TIMEZONE, the forecast must be too or daily maxima land on the wrong day
    assert captured.get("timezone") == settings.TIMEZONE


# --- run_experiment.py: the weather pipeline must be fetched exactly once per run ---

def test_run_experiment_does_not_fetch_outside_run_system(monkeypatch):
    calls = {"n": 0}

    def counting_fetch():
        calls["n"] += 1
        return [], pl.DataFrame()

    monkeypatch.setattr(run_experiment, "fetch_all_data", counting_fetch)
    monkeypatch.setattr(run_experiment, "run_system", lambda: None)

    run_experiment.run_experiment()

    # run_system owns the fetch, run_experiment itself must not trigger a second one
    assert calls["n"] == 0


# --- evaluation/eval_loop.py: unknown outcomes must stay unknown, not become No wins ---

def test_win_loss_flag_is_null_when_outcome_is_unknown(monkeypatch):
    monkeypatch.setattr(settings, "MIN_FORECAST_HISTORY", 0)
    buckets = fair_value.create_buckets(25, 36)

    df_pair = pl.DataFrame({
        "date": ["2024-01-01", "2024-01-02"],
        "actual_temp": [30.5, 45.0],  # 45.0 is outside every bucket, so no ground truth for 01-02
    })
    df_result = pl.DataFrame({
        "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
        "groupItemTitle": ["30°C", "25°C or below", "30°C"],
    })

    factory = eval_loop.make_static_factory(lambda low, high: 0.5)
    result = eval_loop.run_eval_loop_polymarket(factory, buckets, df_pair, df_result)

    flags = result["win/loss flag"].to_list()
    titles = result["groupItemTitle"].to_list()
    dates = result["date"].to_list()

    by_key = dict(zip(zip(dates, titles), flags))

    # control row, real outcome (30,31) matches the market's own bucket
    assert by_key[("2024-01-01", "30°C")] == 1
    # open ended market has no fixed bucket index, outcome is not knowable from the index match
    assert by_key[("2024-01-01", "25°C or below")] is None
    # no ground truth row for this date, so the flag must not default to a loss
    assert by_key[("2024-01-02", "30°C")] is None


# --- data/cleaner.py: the gap rule must count consecutive nulls, not rows dropped after interpolation ---

def _df_with_null_run(n_rows, null_start, null_len):
    temps = [30.0 + (i % 3) for i in range(n_rows)]
    for i in range(null_start, null_start + null_len):
        temps[i] = None
    return pl.DataFrame({
        "time": [f"2024-06-{(i % 28) + 1:02d}" for i in range(n_rows)],
        "temperature_2m_max": temps,
        "temperature_2m_min": [25.0] * n_rows,
        "precipitation_sum": [0.0] * n_rows,
    })


def test_clean_data_rejects_interior_null_run_longer_than_max_gap():
    df = _df_with_null_run(n_rows=40, null_start=10, null_len=settings.MAX_NULL_GAP + 15)

    assert cleaner.clean_data(df) is None


def test_clean_data_fills_interior_null_run_within_max_gap():
    df = _df_with_null_run(n_rows=40, null_start=10, null_len=settings.MAX_NULL_GAP - 2)

    result = cleaner.clean_data(df)

    assert result is not None
    assert len(result) == 40
    assert result["temperature_2m_max"].null_count() == 0
