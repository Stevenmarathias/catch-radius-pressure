"""
Build CROE v3 artifacts.

Reads data/{crp_merged, play_targets, at_release_tracking_features}.csv,
fits the CROE model (see crp.croe), and writes:

    data/catch_prob_v3.csv                    per-play calibrated catch probability
    data/receiver_rankings_v3.csv             overall leaderboard
    data/receiver_rankings_v3_by_position.csv WR/TE/RB/FB splits
    data/receiver_rankings_v3_downfield.csv   air-yards ≥ 10 restriction
    outputs/croe_v3_reliability.png           reliability curve (raw vs calibrated)
    outputs/croe_v3_metrics.json              logloss / AUC / Brier per split
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from crp.croe import build_feature_frame, build_leaderboards, fit_and_predict


def _load(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    crp_merged = pd.read_csv(os.path.join(data_dir, "crp_merged.csv"))
    play_targets = pd.read_csv(os.path.join(data_dir, "play_targets.csv"))
    at_release = pd.read_csv(os.path.join(data_dir, "at_release_tracking_features.csv"))
    return crp_merged, play_targets, at_release


def _reliability_plot(per_play: pd.DataFrame, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor("#111111")
    ax.set_facecolor("#1a1a1a")

    for label, col, color in [
        ("Raw HGB (OOF)", "catch_prob_v3_raw", "#f39c12"),
        ("Isotonic-calibrated", "catch_prob_v3", "#2ecc71"),
    ]:
        dev = per_play[per_play["split"] == "dev"]
        prob_true, prob_pred = calibration_curve(
            dev["is_completed"], dev[col], n_bins=12, strategy="quantile"
        )
        ax.plot(prob_pred, prob_true, marker="o", color=color, label=label, linewidth=2)

    ax.plot([0, 1], [0, 1], linestyle="--", color="#888888", label="Perfect calibration")
    ax.set_xlabel("Predicted catch probability", color="white")
    ax.set_ylabel("Empirical catch rate", color="white")
    ax.set_title("CROE v3 reliability curve (weeks 1–16, OOF)", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444444")
    ax.legend(facecolor="#1a1a1a", edgecolor="#444444", labelcolor="white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=os.path.join(ROOT, "data"))
    parser.add_argument("--out-dir", default=os.path.join(ROOT, "outputs"))
    parser.add_argument("--min-targets-overall", type=int, default=30)
    parser.add_argument("--min-targets-position", type=int, default=20)
    parser.add_argument("--min-targets-downfield", type=int, default=15)
    parser.add_argument("--downfield-air-yards", type=float, default=10.0)
    args = parser.parse_args()

    print("[croe_v3] loading inputs …")
    crp_merged, play_targets, at_release = _load(args.data_dir)

    print("[croe_v3] assembling features …")
    feat = build_feature_frame(crp_merged, play_targets, at_release)
    print(f"          {len(feat):,} plays after filtering to pass_result ∈ {{C, I}}")

    print("[croe_v3] fitting HGB + isotonic calibration …")
    result = fit_and_predict(feat)

    per_play_path = os.path.join(args.data_dir, "catch_prob_v3.csv")
    result.per_play.to_csv(per_play_path, index=False)
    print(f"[croe_v3] wrote {per_play_path}")

    metrics_path = os.path.join(args.out_dir, "croe_v3_metrics.json")
    os.makedirs(args.out_dir, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(result.metrics, f, indent=2)
    print(f"[croe_v3] wrote {metrics_path}")
    for k, v in result.metrics.items():
        print(f"          {k:24s} {v:.4f}")

    reliability_path = os.path.join(args.out_dir, "croe_v3_reliability.png")
    _reliability_plot(result.per_play, reliability_path)
    print(f"[croe_v3] wrote {reliability_path}")

    print("[croe_v3] building leaderboards …")
    boards = build_leaderboards(
        feat,
        result.per_play,
        min_targets_overall=args.min_targets_overall,
        min_targets_position=args.min_targets_position,
        min_targets_downfield=args.min_targets_downfield,
        downfield_air_yards=args.downfield_air_yards,
    )
    for name, path in [
        ("overall", os.path.join(args.data_dir, "receiver_rankings_v3.csv")),
        ("by_position", os.path.join(args.data_dir, "receiver_rankings_v3_by_position.csv")),
        ("downfield", os.path.join(args.data_dir, "receiver_rankings_v3_downfield.csv")),
    ]:
        boards[name].to_csv(path, index=False)
        print(f"[croe_v3] wrote {path}  ({len(boards[name])} rows)")

    print("\n[croe_v3] top 10 overall (min "
          f"{args.min_targets_overall} targets):")
    print(boards["overall"].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
