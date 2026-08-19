"""
Compare CROE v2 (leverage) vs CROE v3 (leverage + is_red_zone).

Reads the v2 snapshot from /tmp/croe_v2_snapshot/ (produced right before the
v3 refit) and the current v3 artifacts. Writes:

    outputs/croe_v3_vs_v2.md    metric shift + leaderboard movers
"""

from __future__ import annotations

import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "outputs")
SNAP = "/tmp/croe_v2_snapshot"


def _metrics(path: str) -> dict[str, float]:
    with open(path) as f:
        m = json.load(f)
    keep = [
        "dev_oof_cal_auc", "dev_oof_cal_logloss", "dev_oof_cal_brier",
        "test_cal_auc", "test_cal_logloss", "test_cal_brier",
    ]
    return {k: m[k] for k in keep if k in m}


def main() -> None:
    if not os.path.isdir(SNAP):
        raise FileNotFoundError(
            f"v2 snapshot not found at {SNAP}. Re-run the snapshot step before "
            "regenerating v3 artifacts."
        )
    v2_m = _metrics(os.path.join(SNAP, "croe_v2_metrics.json"))
    v3_m = _metrics(os.path.join(OUT, "croe_v3_metrics.json"))

    v2_lb = pd.read_csv(os.path.join(SNAP, "receiver_rankings_v2.csv"))
    v3_lb = pd.read_csv(os.path.join(DATA, "receiver_rankings_v3.csv"))

    v2s = v2_lb[["nfl_id", "player_name", "player_position", "targets",
                 "avg_crp", "avg_air_yards", "croe_v2", "rank"]].rename(
        columns={"croe_v2": "croe_v2", "rank": "rank_v2"}
    )
    v3s = v3_lb[["nfl_id", "croe_v3", "rank"]].rename(columns={"rank": "rank_v3"})
    j = v2s.merge(v3s, on="nfl_id", how="inner")
    j["rank_change"] = j["rank_v2"] - j["rank_v3"]     # positive = climbed under v3
    j["croe_change"] = j["croe_v3"] - j["croe_v2"]

    rho = j["croe_v2"].corr(j["croe_v3"], method="spearman")
    tau = j["croe_v2"].corr(j["croe_v3"], method="kendall")

    def fmt(m: dict[str, float]) -> str:
        return " | ".join(f"{v:.4f}" for v in m.values())

    lines: list[str] = []
    lines.append("# CROE v3 vs CROE v2 — model & leaderboard movers\n")
    lines.append(
        "v3 = v2 feature set + `is_red_zone` binary covariate "
        "(added per Pass 4's field-position study). Model architecture and "
        "training protocol are otherwise identical.\n"
    )

    lines.append("## Model metrics (calibrated)\n")
    lines.append("| variant | dev_auc | dev_logloss | dev_brier | test_auc | test_logloss | test_brier |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.append(f"| v2 (leverage) | {fmt(v2_m)} |")
    lines.append(f"| v3 (leverage + is_red_zone) | {fmt(v3_m)} |")
    lines.append("")
    lines.append(
        "Expectation from Pass 4: aggregate AUC lift is small (~+0.001) "
        "because red zone is only ~12% of plays; the model's residual "
        "coefficient on `is_red_zone` is meaningful (~−0.4 log-odds), but "
        "moves headline metrics only slightly.\n"
    )

    lines.append("## Rank-order agreement, v2 ↔ v3\n")
    lines.append(
        f"- Spearman ρ = {rho:.3f}\n"
        f"- Kendall τ = {tau:.3f}\n\n"
        "Very high correlation — as expected for a single-feature addition.\n"
    )

    lines.append("## Biggest CROE risers (v2 → v3)\n")
    lines.append(
        "Receivers who saw more red-zone contested balls than average should "
        "get lifted: the model now assigns those catches a lower baseline "
        "expectation, so completing them yields more CROE credit.\n"
    )
    top_up = j.sort_values("croe_change", ascending=False).head(12)
    lines.append(top_up[[
        "player_name", "player_position", "targets",
        "avg_crp", "avg_air_yards",
        "croe_v2", "croe_v3", "croe_change",
        "rank_v2", "rank_v3", "rank_change",
    ]].to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## Biggest CROE fallers (v2 → v3)\n")
    lines.append(
        "Symmetric: receivers whose completions on non-RZ plays previously "
        "carried a bit of red-zone confounding lose a small amount of credit.\n"
    )
    top_down = j.sort_values("croe_change").head(12)
    lines.append(top_down[[
        "player_name", "player_position", "targets",
        "avg_crp", "avg_air_yards",
        "croe_v2", "croe_v3", "croe_change",
        "rank_v2", "rank_v3", "rank_change",
    ]].to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## v2 top 10 → v3 rank\n")
    top10 = j.sort_values("rank_v2").head(10)
    lines.append(top10[[
        "player_name", "player_position", "targets",
        "croe_v2", "croe_v3", "croe_change",
        "rank_v2", "rank_v3", "rank_change",
    ]].to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## v3 top 10 → v2 rank\n")
    top10v3 = j.sort_values("rank_v3").head(10)
    lines.append(top10v3[[
        "player_name", "player_position", "targets",
        "croe_v2", "croe_v3", "croe_change",
        "rank_v2", "rank_v3", "rank_change",
    ]].to_markdown(index=False, floatfmt=".3f") + "\n")

    out_path = os.path.join(OUT, "croe_v3_vs_v2.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[compare] wrote {out_path}")


if __name__ == "__main__":
    main()
