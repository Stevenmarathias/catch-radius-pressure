"""
Field standardization utility.

NFL tracking data has plays going in both directions (left→right and
right→left) depending on which end zone the offense is attacking. This
module flips all plays so the offense is always attacking from left to
right (toward increasing x). This is a standard preprocessing step for
tracking-data analysis — without it, field heatmaps and location-based
analyses are muddled because "20 yards from own end zone" and "20 yards
from opponent's end zone" end up in different absolute x positions
depending on the play direction.

The `play_direction` column in the input data is either 'left' or 'right'.
For plays with direction='left', we flip x and y coordinates, plus adjust
directional angles.
"""

import numpy as np
import pandas as pd


FIELD_LENGTH = 120.0   # yards, including both end zones
FIELD_WIDTH = 53.3     # yards


def standardize_field(
    df: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
    dir_col: str | None = "dir",
    orientation_col: str | None = "o",
    play_direction_col: str = "play_direction",
) -> pd.DataFrame:
    """
    Flip coordinates for all plays with play_direction == 'left' so every
    play attacks toward increasing x (left→right).

    Also flips angular fields (`dir` and `o`) by adding 180°.

    Parameters
    ----------
    df : DataFrame containing tracking rows with x, y, dir, o, and play_direction
    x_col, y_col, dir_col, orientation_col, play_direction_col : column names

    Returns
    -------
    New DataFrame with coordinates standardized.
    """
    df = df.copy()
    flip_mask = df[play_direction_col] == "left"

    df.loc[flip_mask, x_col] = FIELD_LENGTH - df.loc[flip_mask, x_col]
    df.loc[flip_mask, y_col] = FIELD_WIDTH - df.loc[flip_mask, y_col]

    if dir_col is not None and dir_col in df.columns:
        df.loc[flip_mask, dir_col] = (df.loc[flip_mask, dir_col] + 180) % 360

    if orientation_col is not None and orientation_col in df.columns:
        df.loc[flip_mask, orientation_col] = (df.loc[flip_mask, orientation_col] + 180) % 360

    return df


def standardize_ball_landing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize the ball_land_x and ball_land_y columns the same way.
    Applied at the play level (not per-frame like standardize_field).
    """
    df = df.copy()
    flip_mask = df["play_direction"] == "left"
    df.loc[flip_mask, "ball_land_x"] = FIELD_LENGTH - df.loc[flip_mask, "ball_land_x"]
    df.loc[flip_mask, "ball_land_y"] = FIELD_WIDTH - df.loc[flip_mask, "ball_land_y"]
    return df


def yards_from_own_endzone(x: float) -> float:
    """
    After standardization, x=10 is the offense's own goal line and x=110 is
    the opponent's. This returns yards from the offense's own end zone (0-100).
    """
    return x - 10.0


def yards_to_opponent_endzone(x: float) -> float:
    """Distance from an x-coordinate to the opponent's end zone (goal line at x=110)."""
    return 110.0 - x
