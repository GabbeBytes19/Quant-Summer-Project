import polars as pl
import pytest

from backtest.engine import engine


def _four_row_df_result():
    # row 0: edge=+0.1 -> side Yes, price_paid=0.5 (kept)
    # row 1: edge=+0.6 -> side Yes, price_paid=0.0 (must be dropped)
    # row 2: edge=-0.4 -> side No,  price_paid=1-1.0=0.0 (must be dropped)
    # row 3: edge=-0.2 -> side No,  price_paid=0.7 (kept)
    df_result = pl.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "p": [0.5, 0.0, 1.0, 0.3],
        "win/loss flag": [1, 1, 0, 0],
    })
    p_model = [0.6, 0.6, 0.6, 0.1]
    return p_model, df_result


def test_engine_excludes_zero_and_one_price_paid():
    p_model, df_result = _four_row_df_result()
    result = engine(p_model, df_result)

    assert result.height == 2
    assert 0.0 not in result["price_paid"].to_list()
    assert 1.0 not in result["price_paid"].to_list()


def test_engine_profit_and_cumulative_profit_match_expected():
    p_model, df_result = _four_row_df_result()
    result = engine(p_model, df_result)
    
    profits = result["profit"].to_list()
    assert profits == pytest.approx([0.049, 0.07], abs=1e-6)

    # cumulative_profit must be a true running total in date order
    running = 0.0
    expected_cum = []
    for p in profits:
        running += p
        expected_cum.append(running)
    assert result["cumulative_profit"].to_list() == pytest.approx(expected_cum, abs=1e-9)


def test_engine_no_side_wins_when_outcome_did_not_happen():
    df_result = pl.DataFrame({
        "date": ["2024-01-01"],
        "p": [0.9],
        "win/loss flag": [0],  # outcome did NOT happen -> betting No was correct
    })
    p_model = [0.3]  # edge = 0.3 - 0.9 = -0.6 -> side "No"

    result = engine(p_model, df_result)

    assert result["side"].to_list() == ["No"]
    assert result["profit"][0] > 0


def test_engine_no_side_loses_when_outcome_happened():
    df_result = pl.DataFrame({
        "date": ["2024-01-01"],
        "p": [0.9],
        "win/loss flag": [1],  # outcome DID happen -> betting No was wrong
    })
    p_model = [0.3]  # same edge, same side "No"

    result = engine(p_model, df_result)

    assert result["side"].to_list() == ["No"]
    assert result["profit"][0] == pytest.approx(-0.166,abs=1e-2)
