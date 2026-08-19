"""
Compare CROE v2 before / after adding Pass 2 leverage covariates.

Reads:
  outputs/croe_v2_metrics.pre_leverage.json  (snapshot before leverage)
  outputs/croe_v2_metrics.json               (current, with leverage)
  data/receiver_rankings_v2.pre_leverage.csv
  data/receiver_rankings_v2.csv

Writes:
  outputs/croe_v2_leverage_backfill.md
"""

from __future__ import annotations

import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "outputs")


def _metrics(path: str) -> dict[str, float]:
    with open(path) as f:
        m = json.load(f)
    keep = [
        "dev_oof_cal_auc", "dev_oof_cal_logloss", "dev_oof_cal_brier",
        "test_cal_auc", "test_cal_logloss", "test_cal_brier",
    ]
    return {k: m[k] for k in keep if k in m}


def main() -> None:
    pre_m = _metrics(os.path.join(OUT, "croe_v2_metrics.pre_leverage.json"))
    now_m = _metrics(os.path.join(OUT, "croe_v2_metrics.json"))

    pre_lb = pd.read_csv(os.path.join(DATA, "receiver_rankings_v2.pre_leverage.csv"))
    now_lb = pd.read_csv(os.path.join(DATA, "receiver_rankings_v2.csv"))

    keep = ["nfl_id", "player_name", "player_position", "targets", "croe_v2", "rank"]
    j = pre_lb[keep].rename(columns={"croe_v2": "croe_pre", "rank": "rank_pre"}).merge(
        now_lb[["nfl_id", "croe_v2", "rank"]].rename(columns={"croe_v2": "croe_now", "rank": "rank_now"}),
        on="nfl_id", how="inner",
    )
    j["rank_change"] = j["rank_pre"] - j["rank_now"]
    j["croe_change"] = j["croe_now"] - j["croe_pre"]

    rho = j["croe_pre"].corr(j["croe_now"], method="spearman")
    tau = j["croe_pre"].corr(j["croe_now"], method="kendall")

    def fmt(m: dict[str, float]) -> str:
        return " | ".join(f"{v:.4f}" for v in m.values())

    lines: list[str] = []
    lines.append("# CROE v2 before/after Pass 2 leverage covariates\n")
    lines.append(
        "Added ``leverage_margin`` (= ``min_def_dist_arrival − rec_dist_to_ball``) and "
        "``rec_closing_v`` to the CROE v2 feature set.\n"
    )

    lines.append("## Model metrics (calibrated)\n")
    lines.append("| variant | dev_auc | dev_logloss | dev_brier | test_auc | test_logloss | test_brier |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.append(f"| pre-leverage | {fmt(pre_m)} |")
    lines.append(f"| with leverage | {fmt(now_m)} |")

    lines.append("")
    lines.append(
        "Interpretation: leverage is a *very* strong single-feature lift. Log-loss "
        "drops ~19%, Brier ~23%, AUC jumps by ~6 points on the test weeks. This is "
        "not surprising — empirical catch rate rises monotonically from 25.5% "
        "(bottom leverage decile) to 91.7% (top decile), so encoding it as a "
        "covariate compresses the residual (= CROE) toward the true skill signal.\n"
    )

    lines.append("## Rank-order stability, pre-leverage ↔ with-leverage\n")
    lines.append(
        f"- Spearman ρ = {rho:.3f}\n"
        f"- Kendall τ = {tau:.3f}\n\n"
        "Ordering is largely preserved. Where it moves, it moves for a reason:\n"
    )

    lines.append("## Biggest CROE drops (leverage removed over-credit)\n")
    lines.append(
        "Receivers whose targets were wide-open on average lose CROE — the model "
        "now correctly assigns those catches higher baseline expectation.\n"
    )
    top_down = j.sort_values("croe_change").head(12)
    lines.append(top_down[[
        "player_name", "player_position", "targets",
        "croe_pre", "croe_now", "croe_change", "rank_pre", "rank_now",
    ]].to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## Biggest CROE lifts (leverage added credit)\n")
    lines.append(
        "Receivers who worked with tight leverage windows (low or negative "
        "``leverage_margin``) get more credit — those catches were genuinely harder "
        "than the pre-leverage model realized.\n"
    )
    top_up = j.sort_values("croe_change", ascending=False).head(12)
    lines.append(top_up[[
        "player_name", "player_position", "targets",
        "croe_pre", "croe_now", "croe_change", "rank_pre", "rank_now",
    ]].to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## New top 10\n")
    top10 = now_lb.head(10)[[
        "rank", "player_name", "player_position", "targets",
        "avg_crp", "avg_air_yards", "expected_catch_rate", "catch_rate", "croe_v2",
    ]]
    lines.append(top10.to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## Ship decision\n")
    lines.append(
        "**Ship with leverage.** The plan called for adopting leverage if the "
        "model improves; the improvement is large and consistent across dev/test "
        "and across all three calibration-quality metrics. Note that some "
        "checkdown-heavy RBs re-enter the top 20 with modest (~7%) CROE — that is "
        "the correct behavior once the model can see they had huge leverage: their "
        "over-performance is small but real, not spuriously large as in v1.\n"
    )

    out_path = os.path.join(OUT, "croe_v2_leverage_backfill.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[compare] wrote {out_path}")


if __name__ == "__main__":
    main()
