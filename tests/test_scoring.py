import numpy as np
import pytest

from evaluation.scoring import brier_score, log_loss, brier_skill_score


def test_brier_score_perfect_prediction():
    prob_matrix = [[1.0, 0.0, 0.0]]
    correct_indices = [0]
    assert brier_score(prob_matrix, correct_indices) == pytest.approx(0.0)


def test_brier_score_worst_prediction():
    prob_matrix = [[0.0, 0.0, 1.0]]
    correct_indices = [0]
    assert brier_score(prob_matrix, correct_indices) == pytest.approx(2.0)


def test_brier_score_matches_manual_calculation():
    prob_matrix = [[0.1, 0.7, 0.2], [0.7, 0.1, 0.2]]
    correct_indices = [1, 1]
    day1 = 1 - 2 * 0.7 + (0.1**2 + 0.7**2 + 0.2**2)
    day2 = 1 - 2 * 0.1 + (0.7**2 + 0.1**2 + 0.2**2)
    expected = (day1 + day2) / 2
    assert brier_score(prob_matrix, correct_indices) == pytest.approx(expected)


def test_log_loss_matches_manual_calculation():
    prob_matrix = [[0.1, 0.7, 0.2]]
    correct_indices = [1]
    expected = -np.log(0.7)
    assert log_loss(prob_matrix, correct_indices) == pytest.approx(expected)


def test_log_loss_clips_zero_probability():
    prob_matrix = [[0.0, 1.0]]
    correct_indices = [0]
    result = log_loss(prob_matrix, correct_indices)
    assert np.isfinite(result)
    assert result == pytest.approx(-np.log(1e-15))


def test_brier_skill_score_positive_when_model_beats_baseline():
    assert brier_skill_score(0.5, 1.0) == pytest.approx(0.5)


def test_brier_skill_score_zero_when_equal_to_baseline():
    assert brier_skill_score(1.0, 1.0) == pytest.approx(0.0)
