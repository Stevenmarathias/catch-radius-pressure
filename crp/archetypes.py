"""
Pass 3 — receiver archetypes (View B outcome cross).

CRP tells us how much defensive pressure a receiver *faced*. It does not tell
us why: some receivers face pressure because QBs trust them to win contested
balls (Hopkins, Michael Thomas archetype); others face it because they *can't
separate* and every target is contested (Johnston, Watson archetype).

The two-view read
-----------------
**View B — outcome cross**, per receiver:

- ``contested_target_rate`` = share of targets with ``crp >= CONTESTED_THRESHOLD``.
  Uses the existing "High Pressure" cutoff (0.5), matching crp_label semantics.
- ``contested_croe``        = mean of ``is_completed − catch_prob_v3`` over
  contested targets only. Uses CROE v2 (leverage-adjusted), so any credit here
  is real over-performance on tight windows, not checkdown volume.

**View A — temporal shares** (from :mod:`crp.metric`), per receiver:

- ``release_share`` = ``sum(crp_at_release) / sum(crp)`` over the receiver's
  contested targets. High → pressure was already implied at the throw ("tight
  at release" — the can't-separate pattern). Low → pressure accrued during
  flight (long-developing throws, late-arriving defenders).
- ``median_sep_at_throw`` over the receiver's targets.

Quadrant classification
-----------------------
Split ranked receivers at the *median* of contested_target_rate and
contested_croe. The four quadrants:

- **Trusted contested winner**  high rate + high CROE — QB targets them into
  tight windows and they win. Hopkins, Michael Thomas archetype.
- **Can't separate**            high rate + low CROE — targets are always
  contested and outcomes are below expected. Johnston, Watson archetype.
  Typically pairs with high ``release_share``.
- **Efficient separator**       low rate + high CROE — mostly wide open, and
  what few contested balls they see, they win.
- **Uncontested filler**        low rate + low CROE — small volume, mediocre
  outcomes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


CONTESTED_THRESHOLD: float = 0.5   # matches crp_label High/Extreme cutoff
QUADRANT_LABELS = {
    ("high", "high"): "Trusted contested winner",
    ("high", "low"): "Can't separate",
    ("low", "high"): "Efficient separator",
    ("low", "low"): "Uncontested filler",
}


LOW_SAMPLE_CONTESTED: int = 15   # display filter; below this we hide labels


def build_archetype_table(
    crp_merged: pd.DataFrame,
    play_targets: pd.DataFrame,
    catch_prob_v3: pd.DataFrame,
    min_targets: int = 40,
    min_contested_targets: int = 8,
    low_sample_contested: int = LOW_SAMPLE_CONTESTED,
) -> pd.DataFrame:
    """
    Build the per-receiver archetype table.

    Parameters
    ----------
    crp_merged     : data/crp_merged.csv (must have crp_at_release, sep_at_throw)
    play_targets   : data/play_targets.csv
    catch_prob_v3  : data/catch_prob_v3.csv (from scripts/build_croe_v3.py)
    min_targets    : min completions+incompletions to appear on the table
    min_contested_targets : min contested targets to receive a ``contested_croe``
        value (any less and the mean is too noisy to be a stable estimate).
    low_sample_contested : threshold for the ``low_sample`` display flag —
        rows with fewer contested targets than this are still in the CSV but
        should be hidden from headline displays (leaderboards, quadrant
        scatter labels). Higher than ``min_contested_targets`` so that a
        row can carry a ``contested_croe`` while still being flagged as
        noisy for display purposes.

    Returns
    -------
    DataFrame with per-receiver rows. Includes a ``low_sample`` boolean
    column (True when ``contested_targets < low_sample_contested``) so
    downstream renderers can filter without discarding data.
    """
    for col in ("crp_at_release", "sep_at_throw"):
        if col not in crp_merged.columns:
            raise KeyError(f"crp_merged is missing {col!r}; re-run scripts/compute_crp.py.")

    df = crp_merged.merge(
        play_targets[["game_id", "play_id", "nfl_id", "player_name", "player_position"]],
        on=["game_id", "play_id"],
        how="inner",
    )
    df = df[df["pass_result"].isin(["C", "I"])].copy()
    df["is_completed"] = (df["pass_result"] == "C").astype(int)
    df = df.merge(
        catch_prob_v3[["game_id", "play_id", "catch_prob_v3"]],
        on=["game_id", "play_id"],
        how="inner",
    )
    df["croe_v3_play"] = df["is_completed"] - df["catch_prob_v3"]
    df["is_contested"] = (df["crp"] >= CONTESTED_THRESHOLD).astype(int)
    df["crp_flight_delta"] = df["crp"] - df["crp_at_release"]

    def _agg(g: pd.DataFrame) -> pd.Series:
        n = len(g)
        contested = g[g["is_contested"] == 1]
        n_contested = len(contested)
        contested_rate = contested["is_contested"].sum() / n if n else np.nan
        contested_croe = contested["croe_v3_play"].mean() if n_contested >= min_contested_targets else np.nan

        crp_sum = g["crp"].sum()
        release_sum = g["crp_at_release"].sum()
        # release_share only meaningful when there's any CRP faced at all
        release_share = (release_sum / crp_sum) if crp_sum > 1e-9 else np.nan
        flight_share = 1.0 - release_share if release_share is not None else np.nan

        return pd.Series({
            "targets": n,
            "contested_targets": n_contested,
            "contested_target_rate": contested_rate,
            "contested_catch_rate": contested["is_completed"].mean() if n_contested else np.nan,
            "contested_croe": contested_croe,
            "overall_croe_v3": g["croe_v3_play"].mean(),
            "avg_crp": g["crp"].mean(),
            "avg_crp_at_release": g["crp_at_release"].mean(),
            "avg_crp_flight_delta": g["crp_flight_delta"].mean(),
            "release_share": release_share,
            "flight_share": flight_share,
            "median_sep_at_throw": g["sep_at_throw"].median(),
            "avg_air_yards": g["pass_length"].mean(),
        })

    agg = (
        df.groupby(["nfl_id", "player_name", "player_position"], observed=True)
        .apply(_agg, include_groups=False)
        .reset_index()
    )
    agg = agg[agg["targets"] >= min_targets].reset_index(drop=True)

    # Quadrant split at medians (over players eligible for contested_croe).
    ranked = agg[agg["contested_croe"].notna()].copy()
    rate_median = ranked["contested_target_rate"].median()
    croe_median = ranked["contested_croe"].median()

    def _quadrant(row: pd.Series) -> str:
        if pd.isna(row["contested_croe"]):
            return "Insufficient contested targets"
        rate_bin = "high" if row["contested_target_rate"] >= rate_median else "low"
        croe_bin = "high" if row["contested_croe"] >= croe_median else "low"
        return QUADRANT_LABELS[(rate_bin, croe_bin)]

    agg["quadrant"] = agg.apply(_quadrant, axis=1)
    agg["low_sample"] = agg["contested_targets"] < low_sample_contested
    agg.attrs["rate_median"] = float(rate_median)
    agg.attrs["croe_median"] = float(croe_median)
    agg.attrs["contested_threshold"] = CONTESTED_THRESHOLD
    agg.attrs["low_sample_contested"] = int(low_sample_contested)

    for c in ("contested_target_rate", "contested_catch_rate", "contested_croe",
              "overall_croe_v3", "avg_crp", "avg_crp_at_release",
              "avg_crp_flight_delta", "release_share", "flight_share",
              "median_sep_at_throw", "avg_air_yards"):
        agg[c] = agg[c].round(4)

    return agg
