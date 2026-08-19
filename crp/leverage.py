"""
Receiver leverage — the receiver-side companion to CRP.

Motivation
----------
CRP sums pressure over defenders only. A ball thrown directly to the receiver
differs from one both players chase, even at identical defender proximity.
This module quantifies the *receiver's* positional answer to that pressure.

Columns
-------
Three per-play numbers, all measured at the ball-arrival frame:

- ``rec_dist_to_ball``   receiver distance to arrival point (yards).
- ``rec_closing_v``      receiver velocity toward arrival point (yards/frame).
                         Positive = closing on the ball; negative = drifting.
- ``leverage_margin``    ``min_def_dist_arrival - rec_dist_to_ball``.
                         Large positive → ball is *at* the receiver; catch is
                         positional. Near zero or negative → the nearest
                         defender is as close (or closer) than the receiver —
                         a contested chase.

The three raw inputs (``rec_dist_to_ball``, ``rec_closing_v``,
``min_def_dist_arrival``) are produced by :func:`crp.metric.compute_crp_dataset`
and land in ``data/crp_merged.csv`` after the pipeline runs.
"""

from __future__ import annotations

import pandas as pd


LEVERAGE_COLUMNS = ("rec_dist_to_ball", "rec_closing_v", "leverage_margin")


def add_leverage_margin(df: pd.DataFrame) -> pd.DataFrame:
    """Return ``df`` with a ``leverage_margin`` column added (does not copy in place)."""
    missing = [c for c in ("min_def_dist_arrival", "rec_dist_to_ball") if c not in df.columns]
    if missing:
        raise KeyError(
            f"add_leverage_margin: missing required column(s) {missing}. "
            "Re-run scripts/compute_crp.py to refresh crp_merged.csv."
        )
    out = df.copy()
    out["leverage_margin"] = out["min_def_dist_arrival"] - out["rec_dist_to_ball"]
    return out


def leverage_frame(crp_merged: pd.DataFrame) -> pd.DataFrame:
    """Extract the standalone per-play leverage table (four keys + three metrics)."""
    df = add_leverage_margin(crp_merged)
    keep = ["game_id", "play_id", "rec_dist_to_ball", "rec_closing_v", "leverage_margin"]
    return df[keep].copy()
