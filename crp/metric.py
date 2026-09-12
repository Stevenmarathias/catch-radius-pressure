"""
Catch Radius Pressure v2 (CRP)
================================
Measures defensive pressure at the catch point, ADJUSTED for the
receiver's own position and velocity relative to the ball.

v1 → v2 changes
---------------
- v1 measured ONLY defender proximity/velocity. Two plays with
  identical defender configurations were rated equally, even if in
  one the ball was heading right into the receiver's chest and in
  the other both receiver and defenders had to chase after it.
- v2 introduces a "receiver advantage" factor: how much closer to
  the ball the receiver is compared to the nearest defender, plus
  how well-aligned the receiver's own velocity is with the ball.

Formula
-------
    CRP_v2 = defender_pressure * (1 - receiver_advantage)

Where:
    defender_pressure = Σ (1 - d_i/R) * (1 + v_i)      [same as v1]

    receiver_advantage = clip(0, 1,
        0.5 * receiver_proximity_advantage
      + 0.5 * receiver_velocity_alignment)

    receiver_proximity_advantage = (d_nearest_defender - d_receiver) / R
        → 1.0 when receiver is at catch point and nearest defender is at radius edge
        → 0.0 when receiver and nearest defender are at equal distance
        → clipped negative to 0 when receiver is FURTHER than nearest defender

    receiver_velocity_alignment = max(0, velocity_toward_ball / max_speed)
        → 1.0 when receiver is running full-speed directly at the ball
        → 0.0 when receiver is stationary or moving away

Interpretation
--------------
    CRP_v2 = 0.0     → open catch, ball delivered to a well-positioned receiver
    CRP_v2 = 1.0     → moderately contested catch
    CRP_v2 = 2.0+    → extreme pressure, receiver disadvantaged
"""

import numpy as np
import pandas as pd
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CATCH_RADIUS_YDS = 3.0
FRAMES_PER_SECOND = 10
MAX_PLAYER_SPEED_YDS_PER_FRAME = 1.1   # ~11 yds/sec is elite sprint


# ---------------------------------------------------------------------------
# Direction helpers (unchanged from v1)
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
    Returns velocity component (yards/frame) of player moving toward target.
    Positive = moving toward; negative = moving away.
    """
    dx = target_x - player_x
    dy = target_y - player_y
    dist = np.sqrt(dx**2 + dy**2)
    if dist == 0:
        return player_speed / FRAMES_PER_SECOND

    toward_x = dx / dist
    toward_y = dy / dist

    dir_rad = np.radians(player_dir_deg)
    move_x = np.sin(dir_rad)
    move_y = np.cos(dir_rad)

    dot = move_x * toward_x + move_y * toward_y
    return (player_speed / FRAMES_PER_SECOND) * dot


# ---------------------------------------------------------------------------
# Receiver advantage
# ---------------------------------------------------------------------------

def compute_receiver_advantage(
    receiver_row: pd.Series,
    nearest_defender_dist: float,
    ball_x: float,
    ball_y: float,
    catch_radius: float = CATCH_RADIUS_YDS,
) -> dict:
    """
    Quantify how favorable the receiver's position + velocity is at ball arrival.

    Returns
    -------
    dict with:
        receiver_dist          – receiver's distance to ball landing
        proximity_advantage    – (d_nearest_def - d_receiver) / R, clipped [0, 1]
        velocity_alignment     – receiver's velocity component toward ball,
                                 normalized by max sprint speed [0, 1]
        advantage              – combined advantage score [0, 1]
    """
    rx, ry = receiver_row["x"], receiver_row["y"]
    r_speed = receiver_row["s"]
    r_dir = receiver_row["dir"]

    r_dist = np.sqrt((rx - ball_x) ** 2 + (ry - ball_y) ** 2)

    # Proximity advantage
    if np.isnan(nearest_defender_dist):
        prox_adv = 1.0   # no defenders anywhere → maximum advantage
    else:
        raw_prox_adv = (nearest_defender_dist - r_dist) / catch_radius
        prox_adv = float(np.clip(raw_prox_adv, 0.0, 1.0))

    # Velocity alignment
    v_toward = _velocity_toward_target(rx, ry, r_speed, r_dir, ball_x, ball_y)
    vel_align = float(np.clip(v_toward / MAX_PLAYER_SPEED_YDS_PER_FRAME, 0.0, 1.0))

    advantage = 0.5 * prox_adv + 0.5 * vel_align

    return {
        "receiver_dist": round(r_dist, 3),
        "proximity_advantage": round(prox_adv, 4),
        "velocity_alignment": round(vel_align, 4),
        "advantage": round(advantage, 4),
    }


# ---------------------------------------------------------------------------
# CRP v2 per play
# ---------------------------------------------------------------------------

def compute_crp_v2_for_play(
    defenders_df: pd.DataFrame,
    receiver_row: Optional[pd.Series],
    ball_land_x: float,
    ball_land_y: float,
    catch_radius: float = CATCH_RADIUS_YDS,
) -> dict:
    """
    v2 CRP for a single play.

    Parameters
    ----------
    defenders_df : DataFrame of defenders at ball arrival (x, y, s, dir)
    receiver_row : Series for the targeted receiver at ball arrival
                   (x, y, s, dir); pass None to fall back to v1 behavior
    ball_land_x, ball_land_y : ball landing coordinates
    catch_radius : yards
    """
    # ── Raw defender pressure (v1 style) ─────────────────────────────────
    contributions = []
    all_def_dists = []

    for _, d in defenders_df.iterrows():
        dist = np.sqrt((d["x"] - ball_land_x) ** 2 + (d["y"] - ball_land_y) ** 2)
        all_def_dists.append(dist)
        if dist > catch_radius:
            continue
        proximity = 1.0 - (dist / catch_radius)
        v_toward = max(0.0, _velocity_toward_target(
            d["x"], d["y"], d["s"], d["dir"], ball_land_x, ball_land_y
        ))
        pressure_i = proximity * (1.0 + v_toward)
        contributions.append({
            "nfl_id": d.get("nfl_id"),
            "player_name": d.get("player_name", ""),
            "dist": round(dist, 3),
            "v_toward": round(v_toward, 4),
            "pressure": round(pressure_i, 4),
        })

    defender_pressure = sum(c["pressure"] for c in contributions)
    nearest_def_dist = min(all_def_dists) if all_def_dists else float("nan")

    # ── Receiver advantage ───────────────────────────────────────────────
    if receiver_row is None or (isinstance(receiver_row, pd.Series) and receiver_row.empty):
        receiver_info = {
            "receiver_dist": None,
            "proximity_advantage": None,
            "velocity_alignment": None,
            "advantage": 0.0,
        }
    else:
        receiver_info = compute_receiver_advantage(
            receiver_row, nearest_def_dist, ball_land_x, ball_land_y, catch_radius
        )

    # ── Combined CRP v2 ──────────────────────────────────────────────────
    crp_v2 = defender_pressure * (1.0 - receiver_info["advantage"])

    return {
        "crp_v2": round(crp_v2, 4),
        "defender_pressure": round(defender_pressure, 4),
        "receiver_advantage": receiver_info["advantage"],
        "receiver_dist": receiver_info["receiver_dist"],
        "nearest_defender_dist": round(nearest_def_dist, 3) if not np.isnan(nearest_def_dist) else None,
        "n_defenders_in_radius": len(contributions),
        "contributions": contributions,
    }


# ---------------------------------------------------------------------------
# Batch CRP v2 across a season
# ---------------------------------------------------------------------------

def compute_crp_v2_dataset(
    df_input: pd.DataFrame,
    df_output: pd.DataFrame,
    catch_radius: float = CATCH_RADIUS_YDS,
) -> pd.DataFrame:
    """
    Batch-compute CRP v2 for every play in a week's tracking data.

    Requires df_input and df_output to already be field-standardized
    (see crp.field.standardize_field / standardize_ball_landing).

    Returns
    -------
    DataFrame with one row per play:
        game_id, play_id, crp_v2, defender_pressure, receiver_advantage,
        receiver_dist, nearest_defender_dist, n_defenders_in_radius,
        ball_land_x, ball_land_y, num_frames_output
    """
    records = []

    for (game_id, play_id), play_df in df_input.groupby(["game_id", "play_id"]):
        meta = play_df.iloc[0]
        ball_x = meta["ball_land_x"]
        ball_y = meta["ball_land_y"]
        n_frames = int(meta["num_frames_output"])

        play_out = df_output[
            (df_output["game_id"] == game_id) & (df_output["play_id"] == play_id)
        ]

        # ── Snapshot at ball release for pos/vel initialization ─────────
        last_input_frame = play_df["frame_id"].max()
        snap = play_df[play_df["frame_id"] == last_input_frame]

        def_input = snap[snap["player_role"] == "Defensive Coverage"][
            ["nfl_id", "player_name", "x", "y", "s", "dir"]
        ].copy()
        rec_input = snap[snap["player_role"] == "Targeted Receiver"][
            ["nfl_id", "player_name", "x", "y", "s", "dir"]
        ].copy()

        # ── Use predicted positions at arrival if available ─────────────
        if not play_out.empty:
            arrival_frame = n_frames
            out_at_arrival = play_out[play_out["frame_id"] == arrival_frame][
                ["nfl_id", "x", "y"]
            ].rename(columns={"x": "x_pred", "y": "y_pred"})

            def _apply_pred(df_snap):
                merged = df_snap.merge(out_at_arrival, on="nfl_id", how="left")
                merged["x"] = merged["x_pred"].combine_first(merged["x"])
                merged["y"] = merged["y_pred"].combine_first(merged["y"])
                return merged[["nfl_id", "player_name", "x", "y", "s", "dir"]]

            def_input = _apply_pred(def_input)
            rec_input = _apply_pred(rec_input)

        # ── Receiver row ────────────────────────────────────────────────
        receiver_row = rec_input.iloc[0] if not rec_input.empty else None

        result = compute_crp_v2_for_play(
            def_input, receiver_row, ball_x, ball_y, catch_radius=catch_radius
        )

        records.append({
            "game_id": game_id,
            "play_id": play_id,
            "crp_v2": result["crp_v2"],
            "defender_pressure": result["defender_pressure"],
            "receiver_advantage": result["receiver_advantage"],
            "receiver_dist": result["receiver_dist"],
            "nearest_defender_dist": result["nearest_defender_dist"],
            "n_defenders_in_radius": result["n_defenders_in_radius"],
            "ball_land_x": ball_x,
            "ball_land_y": ball_y,
            "num_frames_output": n_frames,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

def crp_v2_label(crp: float) -> str:
    """Human-readable pressure tier for a CRP v2 score."""
    if crp == 0:
        return "Open"
    elif crp < 0.3:
        return "Low Pressure"
    elif crp < 0.7:
        return "Moderate Pressure"
    elif crp < 1.2:
        return "High Pressure"
    else:
        return "Extreme Pressure"


def add_crp_v2_labels(df: pd.DataFrame, crp_col: str = "crp_v2") -> pd.DataFrame:
    df = df.copy()
    df["crp_v2_label"] = df[crp_col].apply(crp_v2_label)
    return df
