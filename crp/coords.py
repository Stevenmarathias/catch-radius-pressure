"""
Coordinate standardization
==========================
Big Data Bowl tracking data has ``playDirection`` in {"left", "right"} depending
on which way the offense is moving. Downstream analysis is simpler when every
play moves left-to-right (offense drives toward increasing x).

This module provides the one canonical transform used repo-wide.

Convention
----------
When ``playDirection == "left"``, apply:
    x'   = FIELD_LEN_X - x           (mirror through midfield)
    y'   = FIELD_LEN_Y - y           (mirror through the center of the field)
    dir' = (dir + 180) mod 360       (rotate movement vector 180°)
    o'   = (o   + 180) mod 360       (rotate orientation 180°)

CRP v1 invariance
-----------------
CRP = Σ (1 - d_i/R) (1 + v_i) with R = 3 yd. This transform is a rigid
reflection (isometry), so:
- Every pairwise distance ``d_i`` is preserved.
- Every player's movement unit vector (sin dir, cos dir) flips sign.
- The unit vector "toward ball" also flips sign.
- Their dot product — i.e. ``v_toward`` — is therefore preserved.
Hence CRP is invariant. See ``tests/test_coords.py`` for a numeric check.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FIELD_LEN_X = 120.0   # 100 yards + two 10-yard endzones
FIELD_LEN_Y = 53.3    # NFL field width (matches crp.metric.MAX_FIELD_Y)


def standardize_tracking(
    df: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    dir_col: str | None = "dir",
    o_col: str | None = "o",
    direction_col: str = "play_direction",
) -> pd.DataFrame:
    """
    Return a copy of ``df`` with coordinates flipped so every play runs L→R.

    Rows where ``direction_col == "left"`` are mirrored; other rows pass through.
    Missing angle columns are skipped without error.
    """
    if direction_col not in df.columns:
        raise KeyError(
            f"standardize_tracking: no '{direction_col}' column; cannot orient plays."
        )

    out = df.copy()
    mask = out[direction_col].astype(str).str.lower() == "left"
    if not mask.any():
        return out

    out.loc[mask, x_col] = FIELD_LEN_X - out.loc[mask, x_col]
    out.loc[mask, y_col] = FIELD_LEN_Y - out.loc[mask, y_col]
    for col in (dir_col, o_col):
        if col and col in out.columns:
            out.loc[mask, col] = np.mod(out.loc[mask, col] + 180.0, 360.0)
    return out


def standardize_point(
    x: float, y: float, play_direction: str
) -> tuple[float, float]:
    """Standardize a single (x, y) point given the play direction."""
    if str(play_direction).lower() == "left":
        return FIELD_LEN_X - x, FIELD_LEN_Y - y
    return x, y


def sideline_distance(y: float) -> float:
    """Distance (yards) from a y-coordinate to the nearest sideline."""
    return float(min(y, FIELD_LEN_Y - y))
