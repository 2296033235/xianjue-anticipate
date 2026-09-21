"""SM-2 spaced repetition scheduler (pure functions for testability)."""

from __future__ import annotations


def calculate_next(
    ease_factor: float,
    interval_days: int,
    repetitions: int,
    quality: int,
) -> tuple[float, int, int]:
    """SM-2 algorithm.

    Args:
        ease_factor: current EF (>= 1.3).
        interval_days: current interval in days.
        repetitions: number of consecutive correct responses.
        quality: 0-5 user rating.

    Returns (new_ease_factor, new_interval_days, new_repetitions).
    """
    if quality < 3:
        return max(ease_factor, 1.3), 0, 0

    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 3
    else:
        new_interval = round(interval_days * ease_factor)

    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)

    return new_ef, new_interval, repetitions + 1

