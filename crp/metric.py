"""
Catch Radius Pressure (CRP) Metric
===================================
Measures defensive pressure at the catch point when the ball arrives.

Core formula:
    CRP = Σ [ (1 - d_i / R) * (1 + v_i) ] for all defenders i within radius R

Where:
    d_i = distance from defender i to ball landing spot (yards)
    R   = catch radius (default 3 yards)
    v_i = velocity component of defender i toward the ball (yards/frame)

A higher CRP indicates a more contested, difficult catch situation.
"""

import numpy as np
import pandas as pd
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CATCH_RADIUS_YDS = 3.0          # Realistic catch radius in yards
FRAMES_PER_SECOND = 10          # NFL tracking data: 10 frames/sec
MAX_FIELD_Y = 53.3              # NFL field width in yards


# ---------------------------------------------------------------------------
# Direction helpers
# ---------------------------------------------------------------------------

def _velocity_toward_target(
    player_x: float,
    player_y: float,
    player_speed: float,
    player_dir_deg: float,
    target_x: float,
    target_y: float,
) -> float:
    """
    Returns the velocity component (yards/frame) of a player moving toward
    a target point.  Positive = moving toward target; negative = moving away.
    """
    # Unit vector from player toward target
    dx = target_x - player_x
    dy = target_y - player_y
    dist = np.sqrt(dx**2 + dy**2)
    if dist == 0:
        return player_speed / FRAMES_PER_SECOND  # already at target

    toward_x = dx / dist
    toward_y = dy / dist

    # Convert player direction (degrees, 0=up, clockwise) to unit vector
    dir_rad = np.radians(player_dir_deg)
    move_x = np.sin(dir_rad)   # NFL tracking: 0° = up (+y), 90° = right (+x)
    move_y = np.cos(dir_rad)

    dot = move_x * toward_x + move_y * toward_y
    return (player_speed / FRAMES_PER_SECOND) * dot


# ---------------------------------------------------------------------------
# Single-play CRP
# ---------------------------------------------------------------------------

def compute_crp_for_play(
    defenders_at_arrival: pd.DataFrame,
    ball_land_x: float,
    ball_land_y: float,
    catch_radius: float = CATCH_RADIUS_YDS,
) -> dict:
    """
    Compute CRP for a single play given defender positions at ball arrival.

    Parameters
    ----------
    defenders_at_arrival : DataFrame with columns
        x, y, s (speed in yds/s), dir (direction in degrees)
        One row per defender active in coverage.
    ball_land_x, ball_land_y : float
        Ball landing coordinates.
    catch_radius : float
        Radius (yards) around landing spot to consider.

    Returns
    -------
    dict with keys:
        crp         – final Catch Radius Pressure score
        n_defenders – number of defenders within catch radius
        defender_contributions – list of per-defender dicts
    """
    if defenders_at_arrival.empty:
        return {"crp": 0.0, "n_defenders": 0, "defender_contributions": []}

    contributions = []

    for _, row in defenders_at_arrival.iterrows():
        dist = np.sqrt((row["x"] - ball_land_x) ** 2 + (row["y"] - ball_land_y) ** 2)

        if dist > catch_radius:
            continue

        # Proximity factor: 1 when at ball, 0 at edge of radius
        proximity = 1.0 - (dist / catch_radius)

        # Velocity toward ball (yards/frame); clamp negative values at 0
        v_toward = _velocity_toward_target(
            row["x"], row["y"], row["s"], row["dir"], ball_land_x, ball_land_y
        )
        v_toward = max(v_toward, 0.0)

        # Pressure contribution
        pressure = proximity * (1.0 + v_toward)

        contributions.append(
            {
                "nfl_id": row.get("nfl_id", np.nan),
                "player_name": row.get("player_name", "Unknown"),
                "dist_to_ball": round(dist, 3),
                "speed": round(row["s"], 3),
                "v_toward": round(v_toward, 4),
                "proximity": round(proximity, 4),
                "pressure": round(pressure, 4),
            }
        )

    crp = sum(c["pressure"] for c in contributions)

    return {
        "crp": round(crp, 4),
        "n_defenders": len(contributions),
        "defender_contributions": contributions,
    }


# ---------------------------------------------------------------------------
# Batch computation across all plays
# ---------------------------------------------------------------------------

def compute_crp_dataset(
    df_input: pd.DataFrame,
    df_output: pd.DataFrame,
    catch_radius: float = CATCH_RADIUS_YDS,
) -> pd.DataFrame:
    """
    Compute CRP for every play in the provided weekly data.

    Strategy
    --------
    1. For each play, find the Targeted Receiver's *last output frame*
       (ball arrival moment) to determine the arrival frame index.
    2. At that same frame, get all Defensive Coverage players' predicted
       positions from df_output (if available) or fall back to their last
       known input position projected forward.
    3. Compute CRP using ball_land_x / ball_land_y from df_input.

    Parameters
    ----------
    df_input  : combined input DataFrame (all weeks or one week)
    df_output : combined output DataFrame matching df_input
    catch_radius : float

    Returns
    -------
    DataFrame with one row per play:
        game_id, play_id, crp, n_defenders_in_radius,
        ball_land_x, ball_land_y, num_frames_output
    """
    records = []

    play_groups = df_input.groupby(["game_id", "play_id"])

    for (game_id, play_id), play_df in play_groups:

        # ── Ball landing coords & arrival duration ─────────────────────────
        meta_row = play_df.iloc[0]
        ball_x = meta_row["ball_land_x"]
        ball_y = meta_row["ball_land_y"]
        n_frames = int(meta_row["num_frames_output"])

        # ── Identify the arrival frame in output data ─────────────────────
        # Output frame_ids start at 1 and go up to num_frames_output
        arrival_frame = n_frames  # last frame = ball arrival

        play_out = df_output[
            (df_output["game_id"] == game_id) & (df_output["play_id"] == play_id)
        ]

        # ── Get defensive players ──────────────────────────────────────────
        def_input = play_df[play_df["player_role"] == "Defensive Coverage"]

        if play_out.empty:
            # No output data: use last known input positions as proxy
            last_input_frame = play_df["frame_id"].max()
            def_snapshot = (
                def_input[def_input["frame_id"] == last_input_frame]
                [["nfl_id", "player_name", "x", "y", "s", "dir"]]
                .copy()
            )
        else:
            # Use predicted positions at arrival frame from output
            # Output only tracks player_to_predict; defenders may not be in output
            # → merge: prefer output position for defenders that ARE tracked,
            #   fall back to last input frame for others
            out_at_arrival = play_out[play_out["frame_id"] == arrival_frame][
                ["nfl_id", "x", "y"]
            ]

            last_input_frame = play_df["frame_id"].max()
            def_last = (
                def_input[def_input["frame_id"] == last_input_frame]
                [["nfl_id", "player_name", "x", "y", "s", "dir"]]
                .copy()
            )

            # Merge: override x/y from output if available
            def_snapshot = def_last.merge(
                out_at_arrival.rename(columns={"x": "x_pred", "y": "y_pred"}),
                on="nfl_id",
                how="left",
            )
            def_snapshot["x"] = def_snapshot["x_pred"].combine_first(def_snapshot["x"])
            def_snapshot["y"] = def_snapshot["y_pred"].combine_first(def_snapshot["y"])
            def_snapshot = def_snapshot[["nfl_id", "player_name", "x", "y", "s", "dir"]]

        # ── Compute CRP ───────────────────────────────────────────────────
        result = compute_crp_for_play(
            def_snapshot, ball_x, ball_y, catch_radius=catch_radius
        )

        records.append(
            {
                "game_id": game_id,
                "play_id": play_id,
                "crp": result["crp"],
                "n_defenders_in_radius": result["n_defenders"],
                "ball_land_x": ball_x,
                "ball_land_y": ball_y,
                "num_frames_output": n_frames,
            }
        )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# CRP bucket labels (for readability)
# ---------------------------------------------------------------------------

def crp_label(crp: float) -> str:
    """Return a human-readable pressure label for a CRP value."""
    if crp == 0:
        return "Open"
    elif crp < 0.5:
        return "Low Pressure"
    elif crp < 1.0:
        return "Moderate Pressure"
    elif crp < 1.5:
        return "High Pressure"
    else:
        return "Extreme Pressure"


def add_crp_labels(df: pd.DataFrame, crp_col: str = "crp") -> pd.DataFrame:
    """Add a CRP label column to a DataFrame that has a CRP column."""
    df = df.copy()
    df["crp_label"] = df[crp_col].apply(crp_label)
    return df
