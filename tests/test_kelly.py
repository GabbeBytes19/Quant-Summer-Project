import pytest

from risk.kelly import kelly_criterion
from config import settings


def test_kelly_positive_when_model_more_confident_than_market():
    f_star = kelly_criterion([0.8], [0.5])
    assert f_star[0] > 0


def test_kelly_negative_when_model_less_confident_than_market():
    f_star = kelly_criterion([0.2], [0.5])
    assert f_star[0] < 0


def test_kelly_zero_when_model_matches_market():
    f_star = kelly_criterion([0.5], [0.5])
    assert f_star[0] == pytest.approx(0.0)


def test_kelly_stays_bounded_for_extreme_inputs():
    f_star = kelly_criterion([0.999], [0.001])
    assert abs(f_star[0]) <= 1.0


def test_kelly_applies_fractional_scaling():
    p_model = [0.8]
    market_odds = [0.5]

    b = (1 - market_odds[0]) / market_odds[0]
    p = p_model[0]
    q = 1 - p
    raw_f_star = (b * p - q) / b

    result = kelly_criterion(p_model, market_odds)
    assert result[0] == pytest.approx(raw_f_star * settings.FRACTIONAL_KELLY)
