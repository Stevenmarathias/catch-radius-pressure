"""
Validation report for CROE v3 (against the CROE v1 leaderboard).

Requires that scripts/build_croe_v3.py has already run (reads the v3 leaderboard
CSV) and that the CROE v1 leaderboard is present (data/receiver_rankings.csv).
Writes outputs/croe_v3_validation.md with:

  - Spearman + Kendall rank correlation, v1 ↔ v3 (players present in both).
  - Biggest fallers (checkdown specialists whose CROE should regress).
  - Biggest risers (contested-catch receivers whose CROE should grow).
  - Face-validity spot checks for a hand-picked panel.
"""

from __future__ import annotations

import os

import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FACE_VALIDITY_PANEL = {
    "should_fall": [
        "Samaje Perine", "Chuba Hubbard", "Kenneth Gainwell",
        "Taysom Hill", "James Cook", "Rachaad White",
    ],
    "should_hold_or_rise": [
        "DeAndre Hopkins", "Michael Thomas", "Deebo Samuel",
        "Ja'Marr Chase", "Cooper Kupp", "CeeDee Lamb",
        "Nico Collins", "DJ Moore", "Justin Jefferson",
        "A.J. Brown", "Amon-Ra St. Brown",
    ],
}


def _load_leaderboards(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    v1 = pd.read_csv(os.path.join(data_dir, "receiver_rankings.csv"))
    v3 = pd.read_csv(os.path.join(data_dir, "receiver_rankings_v3.csv"))
    return v1, v3


def _joined(v1: pd.DataFrame, v3: pd.DataFrame) -> pd.DataFrame:
    v1s = v1[["nfl_id", "player_name", "player_position", "targets",
              "catch_rate", "avg_crp", "croe", "rank"]].rename(
        columns={"croe": "croe_v1", "rank": "rank_v1"}
    )
    v3s = v3[["nfl_id", "croe_v3", "rank", "avg_air_yards"]].rename(
        columns={"rank": "rank_v3"}
    )
    j = v1s.merge(v3s, on="nfl_id", how="inner")
    j["rank_change"] = j["rank_v1"] - j["rank_v3"]  # positive = climbed
    j["croe_change"] = j["croe_v3"] - j["croe_v1"]
    return j


def _fmt(df: pd.DataFrame, cols: list[str], n: int = 15) -> str:
    return df[cols].head(n).to_markdown(index=False, floatfmt=".3f")


def _panel_table(joined: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    sub = joined[joined["player_name"].isin(names)].copy()
    sub = sub.sort_values("rank_v1")
    return sub[[
        "player_name", "player_position", "targets", "avg_crp",
        "avg_air_yards", "rank_v1", "rank_v3", "rank_change",
        "croe_v1", "croe_v3", "croe_change",
    ]]


def main() -> None:
    data_dir = os.path.join(ROOT, "data")
    out_dir = os.path.join(ROOT, "outputs")
    os.makedirs(out_dir, exist_ok=True)

    v1, v3 = _load_leaderboards(data_dir)
    joined = _joined(v1, v3)

    rho, rho_p = spearmanr(joined["croe_v1"], joined["croe_v3"])
    tau, tau_p = kendalltau(joined["croe_v1"], joined["croe_v3"])
    n_common = len(joined)
    n_v1, n_v3 = len(v1), len(v3)

    fallers = joined.sort_values("rank_change").head(15)
    risers = joined.sort_values("rank_change", ascending=False).head(15)

    should_fall = _panel_table(joined, FACE_VALIDITY_PANEL["should_fall"])
    should_rise = _panel_table(joined, FACE_VALIDITY_PANEL["should_hold_or_rise"])

    cols = [
        "player_name", "player_position", "targets", "avg_crp",
        "avg_air_yards", "rank_v1", "rank_v3", "rank_change",
        "croe_v1", "croe_v3",
    ]

    lines: list[str] = []
    lines.append("# CROE v3 validation report (vs v1)\n")
    lines.append(
        f"Compared **v1** ({n_v1} ranked players) with **v3** ({n_v3} ranked players); "
        f"{n_common} players appear on both leaderboards (min 30 targets in each). "
        f"v3 = v2 feature set + `is_red_zone` per Pass 4.\n"
    )
    lines.append("## Rank-order agreement\n")
    lines.append(
        f"- **Spearman rho** = {rho:.3f} (p = {rho_p:.2e})\n"
        f"- **Kendall tau** = {tau:.3f} (p = {tau_p:.2e})\n\n"
        "A moderate positive correlation is expected: v3 preserves the broad "
        "ordering of receiver skill (good hands stay good hands) but re-shuffles "
        "the volume-of-checkdowns tail that v1 over-credited.\n"
    )

    lines.append("## Biggest fallers (v1 → v3)\n")
    lines.append(
        "If v3 is doing its job, plays with low CRP *and* short air yards should no "
        "longer earn much CROE, so RB checkdown specialists should fall.\n"
    )
    lines.append(_fmt(fallers, cols) + "\n")

    lines.append("## Biggest risers (v1 → v3)\n")
    lines.append(
        "Receivers who worked with high CRP and/or high air yards should get more "
        "credit under v3.\n"
    )
    lines.append(_fmt(risers, cols) + "\n")

    lines.append("## Face-validity panel: should fall\n")
    lines.append(
        "Named in the plan — RB / gadget-QB checkdown profiles. Expected: middling "
        "CROE v3, large negative rank_change.\n"
    )
    lines.append(should_fall.to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## Face-validity panel: should hold or rise\n")
    lines.append(
        "Named in the plan and generally known contested-catch receivers. Expected: "
        "positive rank_change or unchanged near the top.\n"
    )
    lines.append(should_rise.to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## v1 top 10 → v3 rank\n")
    top10_v1 = joined.sort_values("rank_v1").head(10)
    lines.append(_fmt(top10_v1, cols, n=10) + "\n")

    lines.append("## v3 top 10 → v1 rank\n")
    top10_v3 = joined.sort_values("rank_v3").head(10)
    lines.append(_fmt(top10_v3, cols, n=10) + "\n")

    out_path = os.path.join(out_dir, "croe_v3_validation.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[validate_croe_v3] wrote {out_path}")
    print()
    print(f"Spearman rho = {rho:.3f}, Kendall tau = {tau:.3f}, n = {n_common}")
    print()
    print("v1 top 10 → v3 rank:")
    print(top10_v1[cols].to_string(index=False))


if __name__ == "__main__":
    main()
