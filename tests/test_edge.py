import polars as pl
import pytest

from pricing import edge
from config import settings


def test_prob_market_v_model_does_not_mutate_input():
    df_result = pl.DataFrame({"p": [0.3, 0.5, 0.7]})
    p_model = [0.4, 0.5, 0.6]

    edge_1 = edge.prob_market_v_model(p_model, df_result)
    # If prob_market_v_model mutated df_result in place (e.g. via insert_column),
    # this second call would raise a DuplicateError on the second "edge" insert.
    edge_2 = edge.prob_market_v_model(p_model, df_result)

    assert "edge" not in df_result.columns
    assert "edge" in edge_1.columns
    assert "edge" in edge_2.columns
    assert edge_1["edge"].to_list() == pytest.approx([0.1, 0.0, -0.1])


def test_effective_edge_flag_requires_both_thresholds():
    # row 0: raw edge passes MIN_EDGE, effective edge fails MIN_EFFECTIVE_EDGE -> False
    # row 1: raw edge fails MIN_EDGE, effective edge alone would pass -> still False
    # row 2: both pass -> True
    df = pl.DataFrame({"edge": [0.05, -0.04, 0.1]})
    result = edge.effective_edge(df)

    assert result["effective_edge_flag"].to_list() == [False, False, True]


def test_effective_edge_reads_spread_from_settings(monkeypatch):
    df = pl.DataFrame({"edge": [0.10]})

    monkeypatch.setattr(settings, "ASSUMED_SPREAD", 0.0)
    no_spread = edge.effective_edge(df)["effective_edge"][0]

    monkeypatch.setattr(settings, "ASSUMED_SPREAD", 0.04)
    with_spread = edge.effective_edge(df)["effective_edge"][0]

    assert no_spread - with_spread == pytest.approx(0.02)


def test_effective_edge_preserves_raw_edge_column():
    df = pl.DataFrame({"edge": [0.1, -0.2]})
    result = edge.effective_edge(df)

    assert result["edge"].to_list() == pytest.approx([0.1, -0.2])
    assert "effective_edge" in result.columns
    # effective_edge must differ from raw edge (spread + fee actually subtracted)
    assert result["effective_edge"].to_list() != result["edge"].to_list()
