"""
Visualization utilities for Catch Radius Pressure (CRP).

Includes:
  - Static field snapshots with CRP overlay
  - Animated play GIFs (ball-in-air phase)
  - Summary charts: CRP vs completion rate, field heatmaps, distributions
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.animation as animation
from typing import Optional, List, Tuple

from .metric import compute_crp_for_play, CATCH_RADIUS_YDS


# ── Color palette ────────────────────────────────────────────────────────────
FIELD_GREEN   = "#2d5a1b"
FIELD_STRIPE  = "#325f1e"
LINE_WHITE    = "#ffffff"
OFF_COLOR     = "#4fc3f7"   # offense: light blue
DEF_COLOR     = "#ef5350"   # defense: red
BALL_COLOR    = "#ff8f00"   # ball/catch point: amber
PASSER_COLOR  = "#fff176"   # QB: yellow


# ── Field drawing ────────────────────────────────────────────────────────────

def _draw_field(ax: plt.Axes, x_min: float = 0, x_max: float = 120) -> None:
    """Draw an NFL field background on ax."""
    ax.set_facecolor(FIELD_GREEN)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(0, 53.3)

    # Alternating yard stripes
    for yard in range(10, 110, 10):
        if (yard // 10) % 2 == 0:
            ax.axvspan(yard, yard + 10, color=FIELD_STRIPE, alpha=0.5, zorder=0)

    # Yard lines every 5 yards
    for yard in range(10, 111, 5):
        ax.axvline(yard, color=LINE_WHITE, linewidth=0.4, alpha=0.4, zorder=1)

    # End zones
    ax.axvspan(0, 10, color="#1a3a0e", zorder=0)
    ax.axvspan(110, 120, color="#1a3a0e", zorder=0)

    # Hash marks (rough approximation)
    for yard in range(11, 110):
        for hash_y in [22.91, 30.39]:
            ax.plot([yard, yard], [hash_y - 0.3, hash_y + 0.3],
                    color=LINE_WHITE, linewidth=0.6, alpha=0.5, zorder=1)

    ax.set_aspect("equal")
    ax.axis("off")


# ── Static play snapshot ─────────────────────────────────────────────────────

def plot_play_snapshot(
    play_df: pd.DataFrame,
    ball_land_x: float,
    ball_land_y: float,
    catch_radius: float = CATCH_RADIUS_YDS,
    title: str = "",
    ax: Optional[plt.Axes] = None,
    show_crp: bool = True,
) -> plt.Axes:
    """
    Draw a static field snapshot at ball release with CRP overlay.

    Parameters
    ----------
    play_df : DataFrame with one row per player at the snapshot frame
              (columns: x, y, s, dir, player_role, player_name, player_side)
    ball_land_x, ball_land_y : ball landing coords
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 6))
        fig.patch.set_facecolor("#111111")

    _draw_field(ax)

    # ── Catch radius circle ───────────────────────────────────────────────
    circle = plt.Circle(
        (ball_land_x, ball_land_y),
        catch_radius,
        fill=True,
        facecolor=BALL_COLOR,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.25,
        zorder=3,
    )
    ax.add_patch(circle)

    # Ball landing spot
    ax.scatter(
        ball_land_x, ball_land_y,
        s=120, color=BALL_COLOR, zorder=5,
        marker="o", edgecolors="white", linewidths=1.5,
    )
    ax.text(
        ball_land_x, ball_land_y + 1.2,
        "⬥ Ball", color=BALL_COLOR, fontsize=7,
        ha="center", va="bottom", fontweight="bold", zorder=6,
    )

    # ── Players ───────────────────────────────────────────────────────────
    defenders = play_df[play_df["player_role"] == "Defensive Coverage"]
    offenders = play_df[play_df["player_role"].isin(["Targeted Receiver", "Other Route Runner"])]
    passer    = play_df[play_df["player_role"] == "Passer"]

    for _, p in passer.iterrows():
        ax.scatter(p["x"], p["y"], s=120, color=PASSER_COLOR, zorder=4,
                   edgecolors="white", linewidths=1)

    for _, p in offenders.iterrows():
        marker = "*" if p["player_role"] == "Targeted Receiver" else "o"
        size   = 150 if p["player_role"] == "Targeted Receiver" else 80
        ax.scatter(p["x"], p["y"], s=size, color=OFF_COLOR, marker=marker,
                   zorder=4, edgecolors="white", linewidths=1)
        ax.text(p["x"], p["y"] - 1.5, p.get("player_name", "")[:12],
                color=OFF_COLOR, fontsize=6, ha="center", va="top", zorder=5)

    for _, d in defenders.iterrows():
        dist = np.sqrt((d["x"] - ball_land_x)**2 + (d["y"] - ball_land_y)**2)
        in_radius = dist <= catch_radius
        color  = "#ff1744" if in_radius else DEF_COLOR
        size   = 130 if in_radius else 80
        alpha  = 1.0 if in_radius else 0.6
        ax.scatter(d["x"], d["y"], s=size, color=color, zorder=4,
                   edgecolors="white", linewidths=1, alpha=alpha)
        ax.text(d["x"], d["y"] - 1.5, d.get("player_name", "")[:12],
                color=color, fontsize=6, ha="center", va="top", zorder=5, alpha=alpha)

        # Arrow showing movement direction
        if d["s"] > 0.5:
            dir_rad = np.radians(d["dir"])
            dx_arr = np.sin(dir_rad) * d["s"] * 0.4
            dy_arr = np.cos(dir_rad) * d["s"] * 0.4
            ax.annotate(
                "", xy=(d["x"] + dx_arr, d["y"] + dy_arr),
                xytext=(d["x"], d["y"]),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
                zorder=5,
            )

    # ── CRP score overlay ─────────────────────────────────────────────────
    if show_crp:
        crp_result = compute_crp_for_play(defenders, ball_land_x, ball_land_y, catch_radius)
        crp = crp_result["crp"]
        n_def = crp_result["n_defenders"]
        ax.text(
            0.02, 0.97,
            f"CRP: {crp:.3f}   |   Defenders in radius: {n_def}",
            transform=ax.transAxes,
            color="white", fontsize=11, fontweight="bold",
            va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#00000088", edgecolor="none"),
            zorder=10,
        )

    if title:
        ax.set_title(title, color="white", fontsize=12, pad=8)

    # Legend
    legend_elements = [
        mpatches.Patch(color=PASSER_COLOR, label="QB"),
        mpatches.Patch(color=OFF_COLOR, label="Receiver"),
        mpatches.Patch(color=DEF_COLOR, label="Defender"),
        mpatches.Patch(color="#ff1744", label="Defender in Radius"),
        mpatches.Patch(color=BALL_COLOR, label="Catch Point"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower right",
        fontsize=7,
        framealpha=0.4,
        facecolor="#111111",
        edgecolor="none",
        labelcolor="white",
    )

    return ax


# ── CRP distribution plot ─────────────────────────────────────────────────────

def plot_crp_distribution(
    df_crp: pd.DataFrame,
    crp_col: str = "crp",
    title: str = "Catch Radius Pressure Distribution",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """Histogram of CRP values across all plays."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    crp_vals = df_crp[crp_col].dropna()
    ax.hist(crp_vals, bins=40, color=BALL_COLOR, edgecolor="#111111", alpha=0.85)
    ax.axvline(crp_vals.mean(), color="white", linestyle="--", linewidth=1.5,
               label=f"Mean = {crp_vals.mean():.3f}")
    ax.axvline(crp_vals.median(), color="#90caf9", linestyle=":", linewidth=1.5,
               label=f"Median = {crp_vals.median():.3f}")

    ax.set_xlabel("CRP Score", color="white")
    ax.set_ylabel("Play Count", color="white")
    ax.set_title(title, color="white", fontsize=13)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.legend(facecolor="#222222", edgecolor="none", labelcolor="white", fontsize=9)

    return ax


# ── CRP vs completion rate ────────────────────────────────────────────────────

def plot_crp_vs_completion(
    df: pd.DataFrame,
    crp_col: str = "crp",
    result_col: str = "pass_result",
    n_bins: int = 8,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Bar chart: completion rate (%) binned by CRP score.
    Requires df to have both crp and pass_result columns.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    df = df[df[result_col].isin(["C", "I"])].copy()
    df["completed"] = (df[result_col] == "C").astype(int)
    df["crp_bin"] = pd.cut(df[crp_col], bins=n_bins)

    grouped = df.groupby("crp_bin", observed=True)["completed"].agg(["mean", "count"]).reset_index()
    grouped["pct"] = grouped["mean"] * 100
    grouped["label"] = grouped["crp_bin"].astype(str)

    colors = plt.cm.RdYlGn_r(np.linspace(0.1, 0.9, len(grouped)))
    bars = ax.bar(range(len(grouped)), grouped["pct"], color=colors, edgecolor="#111111")

    # Count annotations
    for bar, cnt in zip(bars, grouped["count"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"n={cnt:,}",
            ha="center", va="bottom", color="white", fontsize=7,
        )

    ax.set_xticks(range(len(grouped)))
    ax.set_xticklabels(grouped["label"], rotation=35, ha="right", color="white", fontsize=8)
    ax.set_xlabel("CRP Score Bin", color="white")
    ax.set_ylabel("Completion Rate (%)", color="white")
    ax.set_title("Completion Rate by Catch Radius Pressure", color="white", fontsize=13)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.set_ylim(0, 105)

    return ax


# ── Field heatmap ─────────────────────────────────────────────────────────────

def plot_crp_heatmap(
    df: pd.DataFrame,
    crp_col: str = "crp",
    x_col: str = "ball_land_x",
    y_col: str = "ball_land_y",
    title: str = "Average CRP by Field Location",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    2-D heatmap of average CRP across the field.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 6))
        fig.patch.set_facecolor("#111111")

    _draw_field(ax)

    # Bin and average
    df = df.dropna(subset=[x_col, y_col, crp_col])
    x_bins = np.linspace(10, 110, 31)
    y_bins = np.linspace(0, 53.3, 16)

    heatmap, xedges, yedges = np.histogram2d(
        df[x_col], df[y_col],
        bins=[x_bins, y_bins],
        weights=df[crp_col],
    )
    counts, _, _ = np.histogram2d(df[x_col], df[y_col], bins=[x_bins, y_bins])
    avg_crp = np.where(counts > 0, heatmap / counts, np.nan)

    im = ax.imshow(
        avg_crp.T,
        extent=[x_bins[0], x_bins[-1], y_bins[0], y_bins[-1]],
        origin="lower",
        aspect="auto",
        cmap="YlOrRd",
        alpha=0.65,
        zorder=2,
    )

    plt.colorbar(im, ax=ax, label="Avg CRP", fraction=0.02, pad=0.01)
    ax.set_title(title, color="white", fontsize=13, pad=8)

    return ax


# ── CRP by coverage type ──────────────────────────────────────────────────────

def plot_crp_by_coverage(
    df: pd.DataFrame,
    crp_col: str = "crp",
    coverage_col: str = "team_coverage_type",
    top_n: int = 8,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """Box plot of CRP distributions by coverage scheme."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 5))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    df = df.dropna(subset=[coverage_col, crp_col])
    top_cov = df[coverage_col].value_counts().head(top_n).index
    df = df[df[coverage_col].isin(top_cov)]

    order = df.groupby(coverage_col)[crp_col].median().sort_values(ascending=False).index.tolist()
    data_to_plot = [df[df[coverage_col] == cov][crp_col].values for cov in order]

    bp = ax.boxplot(
        data_to_plot,
        patch_artist=True,
        notch=False,
        vert=True,
        medianprops=dict(color="white", linewidth=2),
        whiskerprops=dict(color="#aaaaaa"),
        capprops=dict(color="#aaaaaa"),
        flierprops=dict(marker=".", color="#555555", markersize=2),
    )

    colors = plt.cm.plasma(np.linspace(0.2, 0.85, len(order)))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)

    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels(order, rotation=30, ha="right", color="white", fontsize=8)
    ax.set_ylabel("CRP Score", color="white")
    ax.set_title("CRP Distribution by Coverage Scheme", color="white", fontsize=13)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")

    return ax
