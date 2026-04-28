"""
Animated play visualizations showing CRP building frame-by-frame
during the ball-in-air phase of a passing play.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation
from typing import Optional

from .metric import _velocity_toward_target, CATCH_RADIUS_YDS
from .visualizations import (
    _draw_field, FIELD_GREEN, FIELD_STRIPE, LINE_WHITE,
    OFF_COLOR, DEF_COLOR, BALL_COLOR, PASSER_COLOR
)


def _interpolate_ball_path(
    qb_x: float, qb_y: float,
    ball_x: float, ball_y: float,
    n_frames: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Approximate ball trajectory as a parabolic arc from QB to landing spot.
    Returns x and y arrays indexed by frame (0 = release, n-1 = arrival).
    """
    t = np.linspace(0, 1, n_frames)
    bx = qb_x + (ball_x - qb_x) * t
    by = qb_y + (ball_y - qb_y) * t
    return bx, by


def _crp_at_frame(
    defenders_df: pd.DataFrame,
    ball_x: float, ball_y: float,
    radius: float = CATCH_RADIUS_YDS,
) -> float:
    """Compute instantaneous CRP at one frame using current defender state."""
    crp = 0.0
    for _, d in defenders_df.iterrows():
        dist = np.sqrt((d["x"] - ball_x) ** 2 + (d["y"] - ball_y) ** 2)
        if dist > radius:
            continue
        proximity = 1.0 - (dist / radius)
        v = _velocity_toward_target(d["x"], d["y"], d["s"], d["dir"], ball_x, ball_y)
        v = max(v, 0.0)
        crp += proximity * (1.0 + v)
    return crp


def animate_play(
    df_input_week: pd.DataFrame,
    df_output_week: pd.DataFrame,
    game_id: int,
    play_id: int,
    output_path: str,
    fps: int = 8,
    catch_radius: float = CATCH_RADIUS_YDS,
    title: str = "",
) -> str:
    """
    Build an animated GIF of a single play from ball release to catch.

    Each frame shows:
      - All player positions at that frame
      - The ball traveling along its arc
      - The catch radius circle (filling with color as CRP grows)
      - Live CRP score readout

    Parameters
    ----------
    df_input_week  : full input DataFrame for the week
    df_output_week : full output DataFrame for the week
    game_id, play_id
    output_path    : path to save .gif
    fps            : frames per second of the GIF
    catch_radius   : yards
    title          : custom title

    Returns
    -------
    output_path
    """
    # ── Slice to this play ───────────────────────────────────────────────
    play_in = df_input_week[
        (df_input_week["game_id"] == game_id)
        & (df_input_week["play_id"] == play_id)
    ].copy()
    play_out = df_output_week[
        (df_output_week["game_id"] == game_id)
        & (df_output_week["play_id"] == play_id)
    ].copy()

    if play_in.empty:
        raise ValueError(f"Play ({game_id}, {play_id}) not found in input.")

    meta = play_in.iloc[0]
    ball_land_x = meta["ball_land_x"]
    ball_land_y = meta["ball_land_y"]
    n_frames_out = int(meta["num_frames_output"])

    # ── Get player snapshot at ball release (last input frame) ───────────
    last_input_frame = play_in["frame_id"].max()
    snapshot = play_in[play_in["frame_id"] == last_input_frame].copy()

    # ── Build ball arc ───────────────────────────────────────────────────
    qb_row = snapshot[snapshot["player_role"] == "Passer"]
    if qb_row.empty:
        # Fallback: use min x as QB position
        qb_x = snapshot["x"].min()
        qb_y = ball_land_y
    else:
        qb_x = float(qb_row["x"].values[0])
        qb_y = float(qb_row["y"].values[0])
    ball_xs, ball_ys = _interpolate_ball_path(qb_x, qb_y, ball_land_x, ball_land_y, n_frames_out)

    # ── For each output frame, compute predicted player positions ────────
    # Predicted players (receivers + targeted defenders) come from output;
    # other players we'll project linearly from their last known velocity.
    predicted_ids = play_out["nfl_id"].unique() if not play_out.empty else []

    def get_player_state(nfl_id, frame):
        """Return (x, y, s, dir) for a player at output frame."""
        # Predicted players: use output positions
        if nfl_id in predicted_ids:
            row = play_out[(play_out["nfl_id"] == nfl_id)
                           & (play_out["frame_id"] == frame)]
            if not row.empty:
                base = snapshot[snapshot["nfl_id"] == nfl_id]
                if base.empty:
                    return None
                base = base.iloc[0]
                return (
                    float(row["x"].values[0]),
                    float(row["y"].values[0]),
                    float(base["s"]),
                    float(base["dir"]),
                )
        # Non-predicted players: linear projection from last input frame
        base = snapshot[snapshot["nfl_id"] == nfl_id]
        if base.empty:
            return None
        base = base.iloc[0]
        # Project forward at constant velocity
        dir_rad = np.radians(base["dir"])
        # Speed in yards/sec; 10 frames/sec → yards/frame
        dx = np.sin(dir_rad) * base["s"] / 10.0
        dy = np.cos(dir_rad) * base["s"] / 10.0
        return (
            base["x"] + dx * frame,
            base["y"] + dy * frame,
            float(base["s"]),
            float(base["dir"]),
        )

    # ── Set up figure ────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor("#111111")

    # CRP track for top overlay
    crp_history = []

    def update(frame_idx):
        ax.clear()
        _draw_field(ax)

        ball_x = ball_xs[frame_idx]
        ball_y = ball_ys[frame_idx]

        # ── Compute defender positions at this frame ──────────────────────
        defenders = []
        for _, d in snapshot[snapshot["player_role"] == "Defensive Coverage"].iterrows():
            state = get_player_state(d["nfl_id"], frame_idx + 1)  # output frames are 1-indexed
            if state is None:
                continue
            x, y, s, direction = state
            defenders.append({
                "nfl_id": d["nfl_id"],
                "player_name": d["player_name"],
                "x": x, "y": y, "s": s, "dir": direction,
            })
        def_df = pd.DataFrame(defenders)

        # ── CRP at this frame (only when ball nearly arrived) ─────────────
        # Show CRP based on actual ball position to make it dramatic
        crp_now = _crp_at_frame(def_df, ball_x, ball_y, radius=catch_radius)
        crp_history.append(crp_now)

        # ── Catch radius circle (color intensity scales with CRP) ─────────
        max_crp_for_color = 2.0
        intensity = min(crp_now / max_crp_for_color, 1.0)
        radius_color = plt.cm.YlOrRd(0.3 + intensity * 0.6)
        circle = plt.Circle(
            (ball_x, ball_y), catch_radius,
            fill=True, facecolor=radius_color, edgecolor="white",
            linewidth=1.5, alpha=0.35 + intensity * 0.35, zorder=2,
        )
        ax.add_patch(circle)

        # ── Ball ─────────────────────────────────────────────────────────
        ax.scatter(ball_x, ball_y, s=140, color=BALL_COLOR, marker="o",
                   edgecolors="white", linewidths=1.8, zorder=8)

        # Ball trail
        if frame_idx > 0:
            ax.plot(ball_xs[:frame_idx + 1], ball_ys[:frame_idx + 1],
                    color=BALL_COLOR, alpha=0.6, linewidth=2, linestyle=":", zorder=3)

        # ── Receivers ─────────────────────────────────────────────────────
        for _, p in snapshot[snapshot["player_role"].isin(
                ["Targeted Receiver", "Other Route Runner"])].iterrows():
            state = get_player_state(p["nfl_id"], frame_idx + 1)
            if state is None:
                continue
            x, y, _, _ = state
            is_target = p["player_role"] == "Targeted Receiver"
            ax.scatter(x, y,
                       s=180 if is_target else 90,
                       color=OFF_COLOR,
                       marker="*" if is_target else "o",
                       edgecolors="white", linewidths=1.2, zorder=6)
            if is_target:
                ax.text(x, y - 1.8, p["player_name"][:14],
                        color=OFF_COLOR, fontsize=8, ha="center", va="top",
                        fontweight="bold", zorder=7)

        # ── QB (static at release) ────────────────────────────────────────
        ax.scatter(qb_x, qb_y, s=100, color=PASSER_COLOR,
                   edgecolors="white", linewidths=1, alpha=0.5, zorder=5)

        # ── Defenders ─────────────────────────────────────────────────────
        for _, d in def_df.iterrows():
            dist = np.sqrt((d["x"] - ball_x) ** 2 + (d["y"] - ball_y) ** 2)
            in_radius = dist <= catch_radius
            color = "#ff1744" if in_radius else DEF_COLOR
            size = 130 if in_radius else 80
            ax.scatter(d["x"], d["y"], s=size, color=color,
                       edgecolors="white", linewidths=1, zorder=6)

        # ── HUD overlay ──────────────────────────────────────────────────
        progress = (frame_idx + 1) / len(ball_xs) * 100
        n_in_radius = int((def_df.apply(
            lambda r: np.sqrt((r["x"]-ball_x)**2 + (r["y"]-ball_y)**2) <= catch_radius,
            axis=1,
        ).sum()) if not def_df.empty else 0)

        ax.text(
            0.02, 0.97,
            f"Frame {frame_idx+1}/{len(ball_xs)}   |   Ball in air {progress:.0f}%   |   "
            f"CRP: {crp_now:.3f}   |   Defenders in radius: {n_in_radius}",
            transform=ax.transAxes,
            color="white", fontsize=11, fontweight="bold",
            va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#000000aa", edgecolor="none"),
            zorder=10,
        )

        if title:
            ax.set_title(title, color="white", fontsize=12, pad=6)

        return []

    # ── Build animation ──────────────────────────────────────────────────
    n_total = len(ball_xs)
    anim = animation.FuncAnimation(
        fig, update, frames=n_total, interval=1000 / fps, blit=False,
    )

    # Save as GIF
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    writer = animation.PillowWriter(fps=fps)
    anim.save(output_path, writer=writer)
    plt.close(fig)

    return output_path
