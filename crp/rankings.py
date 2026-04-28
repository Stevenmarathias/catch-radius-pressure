"""
Player rankings based on Catch Radius Pressure (CRP).

Key metrics computed per player:
  - Targets:           number of plays where targeted
  - Catch Rate:        actual completion %
  - Avg CRP:           mean defensive pressure faced
  - High-Pressure %:   share of targets with CRP > 0.5
  - CROE:              Catch Rate Over Expected — actual catch rate minus
                       expected catch rate based on the player's CRP exposure
                       (how much better/worse than league average given
                       similar pressure levels)
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_play_targets(data_dir: str) -> pd.DataFrame:
    """Load the play→receiver lookup table."""
    path = os.path.join(data_dir, "play_targets.csv")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"play_targets.csv not found at {path}.")
    return pd.read_csv(path)


def build_expected_catch_rate(crp_merged: pd.DataFrame) -> pd.Series:
    """
    Estimate league-wide expected catch rate as a function of CRP.

    Uses smoothed binning: the expected catch rate at CRP = c is the
    completion rate of all league plays in a small CRP window around c.

    Returns
    -------
    Series indexed by play (matching crp_merged) with expected catch rate.
    """
    df = crp_merged[crp_merged["pass_result"].isin(["C", "I"])].copy()
    df["completed"] = (df["pass_result"] == "C").astype(int)

    # Sort by CRP and use a rolling window to compute expected rate
    df = df.sort_values("crp")
    window = max(50, len(df) // 30)
    df["expected_rate"] = (
        df["completed"]
        .rolling(window=window, center=True, min_periods=10)
        .mean()
    )
    df["expected_rate"] = df["expected_rate"].fillna(df["completed"].mean())

    # Return as series indexed by (game_id, play_id)
    return df.set_index(["game_id", "play_id"])["expected_rate"]


def compute_player_rankings(
    crp_merged: pd.DataFrame,
    play_targets: pd.DataFrame,
    min_targets: int = 30,
) -> pd.DataFrame:
    """
    Compute per-receiver rankings based on CRP.

    Parameters
    ----------
    crp_merged   : CRP results joined with supplementary data
    play_targets : play→receiver lookup
    min_targets  : minimum targets required to be ranked

    Returns
    -------
    DataFrame ranked by CROE (Catch Rate Over Expected)
    """
    # Build expected catch rate per play
    expected = build_expected_catch_rate(crp_merged)
    crp_merged = crp_merged.merge(
        expected.rename("expected_rate").reset_index(),
        on=["game_id", "play_id"],
        how="left",
    )

    # Join play data with targeted receiver
    df = crp_merged.merge(
        play_targets[["game_id", "play_id", "nfl_id", "player_name", "player_position"]],
        on=["game_id", "play_id"],
        how="inner",
    )
    df = df[df["pass_result"].isin(["C", "I"])].copy()
    df["completed"] = (df["pass_result"] == "C").astype(int)

    # Aggregate per receiver
    agg = (
        df.groupby(["nfl_id", "player_name", "player_position"])
        .agg(
            targets=("play_id", "count"),
            catches=("completed", "sum"),
            catch_rate=("completed", "mean"),
            avg_crp=("crp", "mean"),
            high_pressure_pct=("crp", lambda x: (x > 0.5).mean()),
            expected_catch_rate=("expected_rate", "mean"),
            avg_yards=("yards_gained", "mean"),
        )
        .reset_index()
    )

    agg["croe"] = agg["catch_rate"] - agg["expected_catch_rate"]
    agg = agg[agg["targets"] >= min_targets].copy()
    agg = agg.sort_values("croe", ascending=False).reset_index(drop=True)
    agg["rank"] = np.arange(1, len(agg) + 1)

    # Round for readability
    for col in ["catch_rate", "avg_crp", "high_pressure_pct",
                "expected_catch_rate", "avg_yards", "croe"]:
        agg[col] = agg[col].round(4)

    return agg


def plot_top_receivers(
    rankings: pd.DataFrame,
    metric: str = "croe",
    n: int = 15,
    title: str | None = None,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Horizontal bar chart of top-N receivers by a given metric."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    top = rankings.head(n).iloc[::-1]  # reverse for top-down display
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, n))

    bars = ax.barh(
        top["player_name"], top[metric],
        color=colors, edgecolor="#222222",
    )

    # Annotate with avg CRP and target count
    for i, (_, row) in enumerate(top.iterrows()):
        label = f"{row[metric]:+.1%}  ({row['targets']} targets, CRP {row['avg_crp']:.2f})"
        ax.text(
            row[metric], i,
            f"  {label}",
            va="center", color="white", fontsize=8,
        )

    ax.set_xlabel("Catch Rate Over Expected (CROE)", color="white")
    ax.set_title(title or f"Top {n} Receivers by CROE", color="white", fontsize=14, pad=10)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.axvline(0, color="white", linestyle="--", alpha=0.3, linewidth=0.8)
    ax.set_xlim(top[metric].min() - 0.02, top[metric].max() + 0.18)

    return ax


def plot_pressure_specialists(
    rankings: pd.DataFrame,
    n: int = 15,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Receivers who face the most pressure (highest avg CRP).
    Shows who QBs trust in tough spots.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    top = rankings.sort_values("avg_crp", ascending=False).head(n).iloc[::-1]
    colors = plt.cm.plasma(np.linspace(0.3, 0.9, n))

    bars = ax.barh(top["player_name"], top["avg_crp"], color=colors, edgecolor="#222222")
    for i, (_, row) in enumerate(top.iterrows()):
        label = f"  CRP {row['avg_crp']:.2f}  ({row['targets']} tgts, {row['catch_rate']:.0%} catch)"
        ax.text(row["avg_crp"], i, label, va="center", color="white", fontsize=8)

    ax.set_xlabel("Average CRP Faced", color="white")
    ax.set_title("Receivers Who Face the Toughest Coverage (Avg CRP)",
                 color="white", fontsize=14, pad=10)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.set_xlim(0, top["avg_crp"].max() * 1.45)

    return ax
