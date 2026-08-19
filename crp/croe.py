"""
CROE — Catch Rate Over Expected with difficulty covariates
==========================================================

This is the current CROE model. Feature-set history
(per ``CRP_FEEDBACK_ADAPTATION_PLAN.md``):

- **v1** (in :mod:`crp.rankings`): expected catch rate from CRP alone via a
  rolling window over sorted CRP. Undervalues difficulty; RB checkdown
  specialists top the leaderboard.
- **v2 (Pass 1)**: HGB + isotonic on air yards, pass location, receiver
  position, release + arrival separation, formation/route, CRP itself.
- **v2 + leverage (Pass 2)**: added ``leverage_margin`` and
  ``rec_closing_v``. Test AUC 0.79 → 0.86, log-loss −19%.
- **v3 (Pass 4 recommendation)**: added ``is_red_zone`` (binary,
  ``yardline_100 ≤ 20``). Marginal aggregate AUC lift is small (~+0.001)
  because red zone is ~12% of plays, but the residual coefficient is large
  (~−0.4 log-odds) and enables red-zone attribution downstream.

Model architecture (unchanged v2 → v3, only the feature set grows):

* :class:`sklearn.ensemble.HistGradientBoostingClassifier` with native
  categorical support.
* Training: weeks 1–16 (dev), 5-fold ``GroupKFold(game_id)`` to produce
  out-of-fold predictions for every dev play.
* Test: refit on all of weeks 1–16, predict on weeks 17–18.
* Calibration: an :class:`sklearn.isotonic.IsotonicRegression` fit on the
  pooled OOF (prediction, actual) pairs, applied to both OOF and test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import GroupKFold

from crp.coords import FIELD_LEN_Y
from crp.leverage import add_leverage_margin


# ---------------------------------------------------------------------------
# Feature schema
# ---------------------------------------------------------------------------
CATEGORICAL_FEATURES: list[str] = [
    "player_position",
    "offense_formation",
    "receiver_alignment",
    "route_of_targeted_receiver",
    "dropback_type",
    "pass_location_type",
]

NUMERIC_FEATURES: list[str] = [
    "crp",
    "pass_length",
    "sideline_dist",
    "yards_to_endzone",
    # Two separation snapshots, both informative:
    #   release: what the QB "saw" when throwing (drives catchability)
    #   arrival: the actual window the receiver had to catch through
    "nearest_def_dist_release",
    "min_def_dist_arrival",
    "nearest_def_closing_vel_release",
    "n_defenders_in_R_release",
    "rec_speed",
    # Pass-2 receiver-leverage covariates
    "leverage_margin",
    "rec_closing_v",
    "down",
    "yards_to_go",
    "defenders_in_the_box",
    "dropback_distance",
    "quarter",
    # Pass-4 red-zone covariate (CROE v3): binary yardline_100 ≤ 20. Small
    # aggregate AUC lift; enables red-zone attribution and picks up ~-0.4
    # log-odds of residual completion suppression at fixed depth+CRP+leverage.
    "is_red_zone",
]

FEATURES: list[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET: str = "is_completed"
GROUP: str = "game_id"


# ---------------------------------------------------------------------------
# Feature assembly
# ---------------------------------------------------------------------------

def _yards_to_endzone(df: pd.DataFrame) -> pd.Series:
    """Convert BDB yardline_side/yardline_number to distance-to-opponent-endzone."""
    same_side = df["yardline_side"] == df["possession_team"]
    return np.where(same_side, 100 - df["yardline_number"], df["yardline_number"]).astype(float)


def _sideline_dist(y: pd.Series) -> pd.Series:
    return np.minimum(y, FIELD_LEN_Y - y).astype(float)


def build_feature_frame(
    crp_merged: pd.DataFrame,
    play_targets: pd.DataFrame,
    at_release: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assemble the per-play feature table.

    Filters to plays with ``pass_result in {"C", "I"}`` (matching CROE v1) so
    v1↔v2 comparisons are apples-to-apples; interceptions are excluded because
    the underlying question is "did the target catch it," not "was it picked".
    """
    crp_merged = add_leverage_margin(crp_merged)
    df = crp_merged.merge(
        play_targets[["game_id", "play_id", "nfl_id", "player_name", "player_position"]],
        on=["game_id", "play_id"],
        how="inner",
    )
    df = df.merge(
        at_release[
            [
                "game_id",
                "play_id",
                "n_defenders_in_R_release",
                "nearest_def_dist_release",
                "nearest_def_closing_vel_release",
                "rec_speed",
            ]
        ],
        on=["game_id", "play_id"],
        how="left",
    )
    # ``min_def_dist_arrival`` comes from ``crp_merged`` (added in the re-run
    # pipeline). It's already in the frame from the initial merge above.

    df = df[df["pass_result"].isin(["C", "I"])].copy()
    df[TARGET] = (df["pass_result"] == "C").astype(int)

    df["sideline_dist"] = _sideline_dist(df["ball_land_y"])
    df["yards_to_endzone"] = _yards_to_endzone(df)
    df["is_red_zone"] = (df["yards_to_endzone"] <= 20).astype(int)

    # Derive week: crp_merged has week_x and week_y after the merge with
    # supplementary data; use week_x (from the CRP output).
    week_col = "week_x" if "week_x" in df.columns else "week"
    df["week"] = df[week_col].astype(int)

    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].astype("category")

    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    keep = (
        ["game_id", "play_id", "week", "nfl_id", "player_name", TARGET, "yards_gained"]
        + FEATURES
    )
    return df[keep].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def _new_model(random_state: int = 0) -> HistGradientBoostingClassifier:
    """One place to change hyperparameters. Kept modest — this is a small dataset."""
    return HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=0.05,
        max_leaf_nodes=15,
        max_iter=400,
        l2_regularization=1.0,
        min_samples_leaf=40,
        early_stopping=True,
        validation_fraction=0.1,
        random_state=random_state,
        categorical_features=CATEGORICAL_FEATURES,
    )


@dataclass
class FitResult:
    per_play: pd.DataFrame          # game_id, play_id, catch_prob_v3, is_completed, split
    calibrator: IsotonicRegression
    final_model: HistGradientBoostingClassifier
    dev_oof_raw: pd.Series          # raw HGB scores on dev, indexed by feat.index
    metrics: dict[str, float]


def fit_and_predict(
    feat: pd.DataFrame,
    n_splits: int = 5,
    random_state: int = 0,
) -> FitResult:
    """
    Fit HGB with GroupKFold(game_id) on weeks 1–16 to produce OOF predictions,
    then fit a final HGB on all of weeks 1–16 to predict weeks 17–18. Calibrate
    with isotonic regression fit on pooled OOF scores.
    """
    dev_mask = feat["week"] <= 16
    dev = feat[dev_mask].copy()
    test = feat[~dev_mask].copy()

    X_dev = dev[FEATURES]
    y_dev = dev[TARGET].to_numpy()
    groups = dev[GROUP].to_numpy()

    oof = np.full(len(dev), np.nan)
    gkf = GroupKFold(n_splits=n_splits)
    for fold, (tr, va) in enumerate(gkf.split(X_dev, y_dev, groups=groups)):
        model = _new_model(random_state=random_state + fold)
        model.fit(X_dev.iloc[tr], y_dev[tr])
        oof[va] = model.predict_proba(X_dev.iloc[va])[:, 1]

    assert not np.isnan(oof).any(), "GroupKFold left some dev plays unpredicted"

    # Isotonic calibration on pooled OOF (well-known "OOF stacking calibration")
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(oof, y_dev)
    dev_cal = calibrator.transform(oof)

    # Final model for test predictions
    final_model = _new_model(random_state=random_state + 99)
    final_model.fit(X_dev, y_dev)

    if len(test) > 0:
        test_raw = final_model.predict_proba(test[FEATURES])[:, 1]
        test_cal = calibrator.transform(test_raw)
    else:
        test_raw = np.array([])
        test_cal = np.array([])

    per_play = pd.concat(
        [
            pd.DataFrame(
                {
                    "game_id": dev["game_id"].to_numpy(),
                    "play_id": dev["play_id"].to_numpy(),
                    "week": dev["week"].to_numpy(),
                    "catch_prob_v3": dev_cal,
                    "catch_prob_v3_raw": oof,
                    TARGET: y_dev,
                    "split": "dev",
                }
            ),
            pd.DataFrame(
                {
                    "game_id": test["game_id"].to_numpy(),
                    "play_id": test["play_id"].to_numpy(),
                    "week": test["week"].to_numpy(),
                    "catch_prob_v3": test_cal,
                    "catch_prob_v3_raw": test_raw,
                    TARGET: test[TARGET].to_numpy(),
                    "split": "test",
                }
            ),
        ],
        ignore_index=True,
    )

    metrics = _score(oof, dev_cal, y_dev, test_raw, test_cal, test[TARGET].to_numpy())
    return FitResult(
        per_play=per_play,
        calibrator=calibrator,
        final_model=final_model,
        dev_oof_raw=pd.Series(oof, index=dev.index),
        metrics=metrics,
    )


def _score(oof_raw, oof_cal, y_dev, test_raw, test_cal, y_test) -> dict[str, float]:
    from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

    def block(pref, p, y):
        if len(y) == 0:
            return {}
        return {
            f"{pref}_logloss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6))),
            f"{pref}_brier": float(brier_score_loss(y, p)),
            f"{pref}_auc": float(roc_auc_score(y, p)),
        }

    m: dict[str, float] = {}
    m.update(block("dev_oof_raw", oof_raw, y_dev))
    m.update(block("dev_oof_cal", oof_cal, y_dev))
    m.update(block("test_raw", test_raw, y_test))
    m.update(block("test_cal", test_cal, y_test))
    return m


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------

RECEIVER_POSITIONS = ("WR", "TE", "RB", "FB")


def _aggregate(
    df: pd.DataFrame, min_targets: int, group_cols: Sequence[str] = ("nfl_id", "player_name", "player_position")
) -> pd.DataFrame:
    agg = (
        df.groupby(list(group_cols), observed=True)
        .agg(
            targets=("play_id", "count"),
            catches=(TARGET, "sum"),
            catch_rate=(TARGET, "mean"),
            avg_crp=("crp", "mean"),
            high_pressure_pct=("crp", lambda x: (x > 0.5).mean()),
            avg_air_yards=("pass_length", "mean"),
            expected_catch_rate=("catch_prob_v3", "mean"),
            avg_yards=("yards_gained", "mean"),
        )
        .reset_index()
    )
    agg["croe_v3"] = agg["catch_rate"] - agg["expected_catch_rate"]
    agg = agg[agg["targets"] >= min_targets].copy()
    agg = agg.sort_values("croe_v3", ascending=False).reset_index(drop=True)
    agg["rank"] = np.arange(1, len(agg) + 1)
    for c in ["catch_rate", "avg_crp", "high_pressure_pct", "avg_air_yards",
              "expected_catch_rate", "avg_yards", "croe_v3"]:
        agg[c] = agg[c].round(4)
    return agg


def build_leaderboards(
    feat: pd.DataFrame,
    per_play: pd.DataFrame,
    min_targets_overall: int = 30,
    min_targets_position: int = 20,
    downfield_air_yards: float = 10.0,
    min_targets_downfield: int = 15,
) -> dict[str, pd.DataFrame]:
    """
    Attach catch_prob_v3 back onto the feature frame (which carries player id +
    position + air yards) and produce the three leaderboard views.
    """
    df = feat.merge(
        per_play[["game_id", "play_id", "catch_prob_v3"]],
        on=["game_id", "play_id"],
        how="inner",
    )

    overall = _aggregate(df, min_targets_overall)

    by_pos_frames: list[pd.DataFrame] = []
    for pos in RECEIVER_POSITIONS:
        sub = df[df["player_position"] == pos]
        if len(sub) == 0:
            continue
        pos_df = _aggregate(sub, min_targets_position)
        by_pos_frames.append(pos_df)
    by_position = pd.concat(by_pos_frames, ignore_index=True) if by_pos_frames else pd.DataFrame()

    downfield = _aggregate(
        df[df["pass_length"] >= downfield_air_yards], min_targets_downfield
    )

    return {"overall": overall, "by_position": by_position, "downfield": downfield}
