"""
Team-level defensive rankings based on Catch Radius Pressure (CRP).

Key metrics computed per defense:
  - Plays defended
  - Avg CRP generated      → how much pressure the defense creates per pass
  - Completion rate allowed → standard outcome stat for context
  - EPA allowed per play    → expected points added against (lower = better D)
  - High-Pressure Rate      → share of defended plays with CRP > 0.5
  - Pressure Efficiency     → completion rate allowed at CRP > 0 plays
                              (when they DO close on the ball, do they finish?)
  - DROE (Defensive Rate Over Expected)
                            → expected completion rate (given CRP exposure
                              they generate) minus actual completion rate
                              allowed. Positive = better than expected
                              given pressure level.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_team_defense_rankings(
    crp_merged: pd.DataFrame,
    min_plays: int = 100,
) -> pd.DataFrame:
    """
    Compute team-level defensive rankings from CRP-merged play data.

    Parameters
    ----------
    crp_merged : DataFrame containing CRP joined with supplementary data
                 (must have columns: defensive_team, crp, pass_result,
                 expected_points_added)
    min_plays  : minimum plays required to be ranked

    Returns
    -------
    DataFrame ranked by avg_crp (descending). Includes DROE column.
    """
    # Only keep plays with a clear C/I outcome
    df = crp_merged[crp_merged["pass_result"].isin(["C", "I"])].copy()
    df["completed"] = (df["pass_result"] == "C").astype(int)

    # League-wide expected completion rate as a function of CRP (rolling)
    df_sorted = df.sort_values("crp").copy()
    window = max(50, len(df_sorted) // 30)
    df_sorted["expected_rate"] = (
        df_sorted["completed"]
        .rolling(window=window, center=True, min_periods=10)
        .mean()
        .fillna(df_sorted["completed"].mean())
    )
    df = df.merge(
        df_sorted[["game_id", "play_id", "expected_rate"]],
        on=["game_id", "play_id"],
        how="left",
    )

    # ── Aggregate per defensive team ──────────────────────────────────────
    agg = (
        df.groupby("defensive_team")
        .agg(
            plays=("play_id", "count"),
            avg_crp=("crp", "mean"),
            high_pressure_rate=("crp", lambda x: (x > 0.5).mean()),
            extreme_pressure_rate=("crp", lambda x: (x > 1.0).mean()),
            completion_rate_allowed=("completed", "mean"),
            expected_completion_rate=("expected_rate", "mean"),
            epa_allowed=("expected_points_added", "mean"),
            yards_allowed=("yards_gained", "mean"),
        )
        .reset_index()
    )

    # DROE: lower (negative) = defense over-performed (allowed less than expected
    # given the pressure they generate). We invert sign so higher = better defense.
    agg["droe"] = agg["expected_completion_rate"] - agg["completion_rate_allowed"]

    # Pressure efficiency: completion rate allowed when defense IS in the radius
    pressured = df[df["crp"] > 0].copy()
    pressure_efficiency = (
        pressured.groupby("defensive_team")["completed"].mean().rename("pressure_efficiency")
    )
    agg = agg.merge(pressure_efficiency, on="defensive_team", how="left")

    # Filter and rank
    agg = agg[agg["plays"] >= min_plays].copy()
    agg = agg.sort_values("avg_crp", ascending=False).reset_index(drop=True)
    agg["crp_rank"] = np.arange(1, len(agg) + 1)

    # Round for readability
    for col in ["avg_crp", "high_pressure_rate", "extreme_pressure_rate",
                "completion_rate_allowed", "expected_completion_rate",
                "epa_allowed", "yards_allowed", "droe", "pressure_efficiency"]:
        agg[col] = agg[col].round(4)

    # Reorder columns
    agg = agg[[
        "crp_rank", "defensive_team", "plays",
        "avg_crp", "high_pressure_rate", "extreme_pressure_rate",
        "completion_rate_allowed", "expected_completion_rate", "droe",
        "pressure_efficiency", "epa_allowed", "yards_allowed",
    ]]

    return agg


def plot_team_crp_ranking(
    rankings: pd.DataFrame,
    n: int | None = None,
    ax: plt.Axes | None = None,
    title: str = "NFL Defenses Ranked by Catch Radius Pressure Generated",
) -> plt.Axes:
    """Horizontal bar chart of all 32 defenses by avg CRP generated."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 10))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    df = rankings.copy()
    if n is not None:
        df = df.head(n)
    df = df.iloc[::-1]  # reverse so #1 is at top

    colors = plt.cm.RdYlGn(np.linspace(0.15, 0.85, len(df)))

    ax.barh(df["defensive_team"], df["avg_crp"],
            color=colors, edgecolor="#222222")

    for i, (_, row) in enumerate(df.iterrows()):
        label = (
            f"  {row['avg_crp']:.3f}  "
            f"({row['completion_rate_allowed']:.0%} comp allowed, "
            f"EPA {row['epa_allowed']:+.2f})"
        )
        ax.text(row["avg_crp"], i, label,
                va="center", color="white", fontsize=8)

    ax.set_xlabel("Average CRP Generated per Pass Play", color="white")
    ax.set_title(title, color="white", fontsize=13, pad=10)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.set_xlim(0, df["avg_crp"].max() * 1.55)

    return ax


def plot_team_quadrant(
    rankings: pd.DataFrame,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Scatter: x = avg CRP generated, y = completion rate allowed.
    Bottom-right quadrant = elite defense (high pressure, low completion allowed).
    Top-left = bad defense (no pressure, high completion).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 8))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    x = rankings["avg_crp"]
    y = rankings["completion_rate_allowed"] * 100

    ax.scatter(x, y, s=100, c=rankings["epa_allowed"],
               cmap="RdYlGn_r", edgecolors="white", linewidths=1.2, zorder=3)

    for _, row in rankings.iterrows():
        ax.annotate(
            row["defensive_team"],
            (row["avg_crp"], row["completion_rate_allowed"] * 100),
            xytext=(6, 4), textcoords="offset points",
            color="white", fontsize=9, fontweight="bold",
        )

    # Quadrant lines at the medians
    ax.axvline(x.median(), color="#888888", linestyle="--", alpha=0.4, linewidth=0.8)
    ax.axhline(y.median(), color="#888888", linestyle="--", alpha=0.4, linewidth=0.8)

    # Quadrant labels
    ax.text(x.max() * 0.98, y.min() * 1.005, "Elite\n(↑ Pressure, ↓ Completion)",
            ha="right", va="bottom", color="#7fff7f", fontsize=9, alpha=0.85, fontweight="bold")
    ax.text(x.min() * 1.05, y.max() * 0.99, "Struggling\n(↓ Pressure, ↑ Completion)",
            ha="left", va="top", color="#ff7f7f", fontsize=9, alpha=0.85, fontweight="bold")

    ax.set_xlabel("Avg CRP Generated", color="white")
    ax.set_ylabel("Completion Rate Allowed (%)", color="white")
    ax.set_title("Defensive Identity: Pressure vs. Completion Allowed",
                 color="white", fontsize=13, pad=10)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")

    return ax


def plot_team_droe(
    rankings: pd.DataFrame,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Defenses ranked by DROE (Defensive Rate Over Expected).
    Positive DROE = defense allows fewer completions than expected given
    the pressure level they generate. Negative = defense gets pressure
    but doesn't finish plays.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 10))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    df = rankings.sort_values("droe", ascending=False).copy()
    df = df.iloc[::-1]  # so best is at top
    colors = plt.cm.RdYlGn(np.linspace(0.15, 0.85, len(df)))

    ax.barh(df["defensive_team"], df["droe"],
            color=colors, edgecolor="#222222")

    for i, (_, row) in enumerate(df.iterrows()):
        ax.text(row["droe"], i, f"  {row['droe']:+.1%}",
                va="center", color="white", fontsize=8)

    ax.axvline(0, color="white", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Defensive Rate Over Expected (DROE)", color="white")
    ax.set_title("Defenses Ranked by DROE — How Much Better Than Expected\n"
                 "(Given the Pressure They Generate)",
                 color="white", fontsize=12, pad=10)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")

    return ax
