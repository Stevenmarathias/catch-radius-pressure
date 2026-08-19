"""
Regression test: CRP v1 must be invariant under left→right standardization.

We construct a synthetic play, compute CRP, then apply
``crp.coords.standardize_tracking`` to the same defender snapshot and the ball
landing point with ``play_direction="left"``, and check that CRP is unchanged
to numerical precision.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crp.coords import FIELD_LEN_X, FIELD_LEN_Y, standardize_point, standardize_tracking
from crp.metric import compute_crp_for_play


def _synthetic_play() -> tuple[pd.DataFrame, float, float]:
    """Three defenders around a ball, mix of inside / edge / outside catch radius."""
    ball_x, ball_y = 45.0, 20.0
    defenders = pd.DataFrame(
        [
            # Right on top of the ball, closing fast from the north
            {"nfl_id": 1, "player_name": "A", "x": 45.0, "y": 22.5, "s": 6.5, "dir": 180.0},
            # Just inside the 3-yard radius, drifting away
            {"nfl_id": 2, "player_name": "B", "x": 47.5, "y": 19.0, "s": 4.0, "dir": 90.0},
            # Outside the radius — should not contribute
            {"nfl_id": 3, "player_name": "C", "x": 50.0, "y": 25.0, "s": 5.0, "dir": 45.0},
        ]
    )
    return defenders, ball_x, ball_y


def test_crp_invariant_under_standardization():
    defenders, ball_x, ball_y = _synthetic_play()
    original = compute_crp_for_play(defenders, ball_x, ball_y)

    # Attach play_direction = "left" so the transform actually applies
    df = defenders.assign(play_direction="left")
    flipped = standardize_tracking(df)
    flipped_ball_x, flipped_ball_y = standardize_point(ball_x, ball_y, "left")
    reflected = compute_crp_for_play(flipped, flipped_ball_x, flipped_ball_y)

    assert abs(original["crp"] - reflected["crp"]) < 1e-9, (
        f"CRP changed under L→R flip: {original['crp']} vs {reflected['crp']}"
    )
    assert original["n_defenders"] == reflected["n_defenders"]


def test_standardize_noop_when_direction_right():
    defenders, ball_x, ball_y = _synthetic_play()
    df = defenders.assign(play_direction="right")
    out = standardize_tracking(df)
    pd.testing.assert_frame_equal(
        out.drop(columns=["play_direction"]).reset_index(drop=True),
        defenders.reset_index(drop=True),
    )


def test_standardize_point_matches_field_mirror():
    x, y = 30.0, 10.0
    xr, yr = standardize_point(x, y, "left")
    assert xr == FIELD_LEN_X - x
    assert yr == FIELD_LEN_Y - y
    # Idempotent under a second flip
    assert standardize_point(xr, yr, "left") == (x, y)


def test_defender_distances_preserved():
    defenders, ball_x, ball_y = _synthetic_play()
    df = defenders.assign(play_direction="left")
    flipped = standardize_tracking(df)
    fx, fy = standardize_point(ball_x, ball_y, "left")

    original_d = np.sqrt(
        (defenders["x"] - ball_x) ** 2 + (defenders["y"] - ball_y) ** 2
    ).to_numpy()
    flipped_d = np.sqrt(
        (flipped["x"] - fx) ** 2 + (flipped["y"] - fy) ** 2
    ).to_numpy()
    np.testing.assert_allclose(original_d, flipped_d, atol=1e-12)


if __name__ == "__main__":
    test_crp_invariant_under_standardization()
    test_standardize_noop_when_direction_right()
    test_standardize_point_matches_field_mirror()
    test_defender_distances_preserved()
    print("OK: all coord standardization tests passed.")
