"""
Player Rankings v2
==================
Enhanced rankings that address feedback from reviewer:

  1. Position-adjusted CROE
       Compare each player to receivers of the SAME position type
       (WR / TE / RB) instead of the whole league. Solves the "Perine
       looks like a top-5 receiver because he catches easy dumps to
       the flat" problem.

  2. Air-yards-adjusted CROE
       Expected catch rate now conditions on BOTH pressure (CRP v2)
       AND depth of target (air yards). A wide-open 25-yard bomb is
       still harder than a wide-open 3-yard flip, and the metric
       should know that.

  3. Pressure Specialists decomposition
       Split "high avg CRP faced" into TWO camps:
         - Trusted targets    → high CRP faced + high CROE (QBs go to
                                them in contested spots and they deliver)
         - Struggling separators → high CRP faced + low CROE (they get
                                targeted because they can't separate,
                                not because they're trusted)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def build_expected_catch_rate_2d(
    df: pd.DataFrame,
    crp_col: str = "crp_v2",
    depth_col: str = "air_yards_approx",
) -> pd.Series:
    """
    Estimate expected completion rate as a function of BOTH pressure and
    target depth (air yards).

    Method: bin plays into a 2-D grid of (CRP tier, depth tier) and
    compute completion rate in each bin. Assign each play its bin's
    expected rate.

    Returns
    -------
    Series indexed by (game_id, play_id) with expected catch rate.
    """
    df = df[df["pass_result"].isin(["C", "I"])].copy()
    df["completed"] = (df["pass_result"] == "C").astype(int)

    # 2-D bins
    df["crp_bin"] = pd.cut(
        df[crp_col],
        bins=[-0.001, 0.0, 0.3, 0.7, 1.2, 100],
        labels=["Open", "Low", "Mod", "High", "Extreme"],
    )
    df["depth_bin"] = pd.cut(
        df[depth_col].fillna(df[depth_col].mean()),
        bins=[-0.001, 5, 10, 15, 25, 100],
        labels=["Screen", "Short", "Medium", "Deep", "Bomb"],
    )

    # Bin-level expected rates
    bin_rates = df.groupby(["crp_bin", "depth_bin"], observed=True)["completed"].mean()
    global_rate = df["completed"].mean()

    # Assign each play its bin's expected rate
    def _lookup(row):
        try:
            return bin_rates.loc[(row["crp_bin"], row["depth_bin"])]
        except KeyError:
            return global_rate

    expected = df.apply(_lookup, axis=1)
    expected.index = pd.MultiIndex.from_frame(df[["game_id", "play_id"]])
    return expected.rename("expected_rate")


def compute_player_rankings_v2(
    crp_merged: pd.DataFrame,
    play_targets: pd.DataFrame,
    min_targets: int = 30,
    crp_col: str = "crp_v2",
) -> pd.DataFrame:
    """
    Position-aware, depth-aware receiver rankings.

    Parameters
    ----------
    crp_merged   : CRP v2 results joined with supplementary play data
    play_targets : play→receiver lookup with player_position and air_yards_approx
    min_targets  : minimum targets required to be ranked
    crp_col      : CRP column to use (defaults to crp_v2)

    Returns
    -------
    DataFrame ranked by CROE_adj (depth+position-adjusted CROE).
    """
    # Merge target info
    df = crp_merged.merge(
        play_targets[["game_id", "play_id", "nfl_id", "player_name",
                      "player_position", "air_yards_approx"]],
        on=["game_id", "play_id"],
        how="inner",
    )
    df = df[df["pass_result"].isin(["C", "I"])].copy()
    df["completed"] = (df["pass_result"] == "C").astype(int)

    # ── Depth-and-pressure-based expected catch rate ──────────────────────
    expected = build_expected_catch_rate_2d(df, crp_col=crp_col)
    df = df.merge(
        expected.reset_index(),
        on=["game_id", "play_id"],
        how="left",
    )
    df["expected_rate"] = df["expected_rate"].fillna(df["completed"].mean())

    # ── Group receivers into position categories ──────────────────────────
    def _pos_group(pos: str) -> str:
        if pos == "WR":
            return "WR"
        elif pos == "TE":
            return "TE"
        elif pos in ("RB", "FB"):
            return "RB"
        else:
            return "Other"

    df["pos_group"] = df["player_position"].apply(_pos_group)

    # ── Aggregate per receiver ────────────────────────────────────────────
    agg = (
        df.groupby(["nfl_id", "player_name", "player_position", "pos_group"])
        .agg(
            targets=("play_id", "count"),
            catches=("completed", "sum"),
            catch_rate=("completed", "mean"),
            avg_crp=(crp_col, "mean"),
            high_pressure_pct=(crp_col, lambda x: (x > 0.5).mean()),
            expected_catch_rate=("expected_rate", "mean"),
            avg_air_yards=("air_yards_approx", "mean"),
            avg_yards=("yards_gained", "mean"),
        )
        .reset_index()
    )
    agg["croe"] = agg["catch_rate"] - agg["expected_catch_rate"]
    agg = agg[agg["targets"] >= min_targets].copy()

    # ── Position rank (within-position ranking is the fair one) ───────────
    agg["pos_rank"] = (
        agg.groupby("pos_group")["croe"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    agg = agg.sort_values("croe", ascending=False).reset_index(drop=True)
    agg["overall_rank"] = np.arange(1, len(agg) + 1)

    # Round
    for col in ["catch_rate", "avg_crp", "high_pressure_pct",
                "expected_catch_rate", "croe", "avg_air_yards", "avg_yards"]:
        agg[col] = agg[col].round(4)

    return agg


# ---------------------------------------------------------------------------
# Pressure specialists — decomposed
# ---------------------------------------------------------------------------

def classify_pressure_specialists(
    rankings: pd.DataFrame,
    crp_col: str = "avg_crp",
    croe_col: str = "croe",
    crp_threshold_pct: float = 0.70,
    croe_split: float = 0.0,
) -> pd.DataFrame:
    """
    Split high-pressure targets into "trusted" vs "struggling separators".

    A "high-pressure target" is a receiver in the top 30% of avg_crp faced.
    Within that group:
      - Trusted target     → CROE > 0    (QBs throw to them under pressure
                                           and they convert above expected)
      - Struggling         → CROE ≤ 0    (QBs throw to them under pressure
                                           BUT they don't convert well —
                                           the pressure exists because they
                                           can't separate)

    Returns rankings DataFrame with a new 'pressure_specialist_type' column.
    """
    df = rankings.copy()
    threshold = df[crp_col].quantile(crp_threshold_pct)

    def classify(row):
        if row[crp_col] < threshold:
            return "Normal target"
        elif row[croe_col] > croe_split:
            return "Trusted under pressure"
        else:
            return "Struggling separator"

    df["pressure_specialist_type"] = df.apply(classify, axis=1)
    return df


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_top_receivers_by_position(
    rankings: pd.DataFrame,
    position: str,
    n: int = 12,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Horizontal bar chart of top N receivers within one position group."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 7))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    df = rankings[rankings["pos_group"] == position].head(n).iloc[::-1]
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(df)))
    ax.barh(df["player_name"], df["croe"], color=colors, edgecolor="#222222")

    for i, (_, row) in enumerate(df.iterrows()):
        label = (f"  {row['croe']:+.1%}  "
                 f"({row['targets']} tgts, {row['avg_air_yards']:.1f} yds air, "
                 f"CRP {row['avg_crp']:.2f})")
        ax.text(row["croe"], i, label, va="center", color="white", fontsize=8)

    title_map = {"WR": "Wide Receivers", "TE": "Tight Ends", "RB": "Running Backs"}
    ax.set_title(
        f"Top {n} {title_map.get(position, position)} — Position-Adjusted CROE (2023)",
        color="white", fontsize=13, pad=10,
    )
    ax.set_xlabel("Catch Rate Over Expected (depth + pressure adjusted)", color="white")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.axvline(0, color="white", linestyle="--", alpha=0.3, linewidth=0.8)
    ax.set_xlim(df["croe"].min() - 0.02, df["croe"].max() + 0.20)

    return ax


def plot_pressure_specialist_decomposition(
    rankings: pd.DataFrame,
    n_per_group: int = 10,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """
    Scatter plot: x = avg CRP faced, y = CROE. Colors distinguish
    "trusted under pressure" from "struggling separators".
    Only WRs shown for clarity.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor("#111111")
        ax.set_facecolor("#1a1a1a")

    df = rankings[rankings["pos_group"] == "WR"].copy()
    df = classify_pressure_specialists(df)

    color_map = {
        "Trusted under pressure": "#7fff7f",
        "Struggling separator": "#ff5252",
        "Normal target": "#666666",
    }

    for label, color in color_map.items():
        sub = df[df["pressure_specialist_type"] == label]
        ax.scatter(sub["avg_crp"], sub["croe"] * 100,
                   c=color, s=60, alpha=0.75, edgecolors="white",
                   linewidths=0.8, label=label, zorder=3)

    # Annotate the extremes
    trusted = df[df["pressure_specialist_type"] == "Trusted under pressure"].nlargest(n_per_group, "avg_crp")
    struggling = df[df["pressure_specialist_type"] == "Struggling separator"].nlargest(n_per_group, "avg_crp")

    for _, r in pd.concat([trusted, struggling]).iterrows():
        ax.annotate(
            r["player_name"],
            (r["avg_crp"], r["croe"] * 100),
            xytext=(5, 3), textcoords="offset points",
            color="white", fontsize=8, alpha=0.9,
        )

    ax.axhline(0, color="white", linestyle="--", linewidth=0.6, alpha=0.4)
    ax.set_xlabel("Average CRP v2 Faced", color="white")
    ax.set_ylabel("CROE (Catch Rate Over Expected, %)", color="white")
    ax.set_title(
        "Pressure Specialists — Trusted vs. Struggling to Separate\n"
        "(WRs only, min 30 targets)",
        color="white", fontsize=13, pad=10,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.legend(facecolor="#222222", edgecolor="none", labelcolor="white", fontsize=9, loc="best")

    return ax
