"""Tests for SM-2 scheduler."""

import pytest

from src.xianjue.learning.srs import calculate_next


class TestSM2:
    def test_first_correct(self):
        ef, interval, reps = calculate_next(2.5, 0, 0, 5)
        assert interval == 1
        assert reps == 1
        assert ef > 2.5

    def test_second_correct(self):
        ef, interval, reps = calculate_next(2.5, 1, 1, 4)
        assert interval == 3
        assert reps == 2

    def test_subsequent_correct(self):
        ef, interval, reps = calculate_next(2.5, 3, 2, 5)
        assert interval == round(3 * 2.5)  # 7 or 8
        assert reps == 3

    def test_wrong_resets(self):
        ef, interval, reps = calculate_next(2.5, 10, 3, 2)
        assert interval == 0
        assert reps == 0

    def test_ease_factor_decreases_on_medium(self):
        ef, interval, reps = calculate_next(2.5, 5, 2, 3)
        assert ef < 2.5

    def test_ease_factor_floor(self):
        ef, interval, reps = calculate_next(1.3, 10, 5, 0)
        assert ef >= 1.3

