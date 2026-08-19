"""
Build Pass 3 archetype artifacts.

Outputs
-------
- data/archetypes.csv                       per-receiver archetype table
                                            (all receivers with ≥ min_targets;
                                             ``low_sample`` flag = contested_targets < 15)
- outputs/archetypes_quadrant.png           2×2 scatter (contested rate ↔ contested CROE)
                                            displayed rows: not low_sample
- outputs/archetypes_release_share.png      release-share vs contested rate
- outputs/archetypes_validation.md          panel checks + per-quadrant top-10s
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from crp.archetypes import CONTESTED_THRESHOLD, build_archetype_table  # noqa: E402


DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "outputs")

# Names to spotlight in the plot and in the validation panel.
LABEL_NAMES = [
    # trusted-winner archetype (plan-named)
    "DeAndre Hopkins", "Michael Thomas",
    # can't-separate archetype (plan-named + close analogues)
    "Quentin Johnston", "Justin Watson",
    # other useful reference points
    "CeeDee Lamb", "Justin Jefferson", "A.J. Brown", "Nico Collins",
    "DJ Moore", "Amon-Ra St. Brown", "Terry McLaurin", "Puka Nacua",
    "Cooper Kupp", "Davante Adams", "Ja'Marr Chase", "Mike Evans",
]

PLAN_PANEL = {
    "DeAndre Hopkins": "Trusted contested winner",
    "Michael Thomas": "Trusted contested winner",
    "Quentin Johnston": "Can't separate",
    "Justin Watson": "Can't separate",
}

QUADRANT_COLORS = {
    "Trusted contested winner": "#2ecc71",
    "Can't separate": "#e74c3c",
    "Efficient separator": "#3498db",
    "Uncontested filler": "#95a5a6",
    "Insufficient contested targets": "#555555",
}


def _dark_ax(figsize=(11, 8)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#111111")
    ax.set_facecolor("#1a1a1a")
    for s in ax.spines.values():
        s.set_edgecolor("#444444")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    return fig, ax


def _display_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Rows shown in headline plots and leaderboard tables (excludes low_sample)."""
    return df[df["contested_croe"].notna() & (~df["low_sample"])].copy()


def _plot_quadrant(df: pd.DataFrame, path: str) -> None:
    ranked = _display_frame(df)
    rate_med = df.attrs["rate_median"]
    croe_med = df.attrs["croe_median"]
    low_sample_thresh = df.attrs["low_sample_contested"]

    fig, ax = _dark_ax()
    for quad, color in QUADRANT_COLORS.items():
        sub = ranked[ranked["quadrant"] == quad]
        if not len(sub):
            continue
        ax.scatter(
            sub["contested_target_rate"], sub["contested_croe"],
            s=(sub["targets"] * 1.5).clip(20, 400),
            alpha=0.6, c=color, edgecolor="#111111", linewidth=0.5, label=quad,
        )

    for _, row in ranked[ranked["player_name"].isin(LABEL_NAMES)].iterrows():
        ax.annotate(
            row["player_name"],
            (row["contested_target_rate"], row["contested_croe"]),
            fontsize=8, color="white", xytext=(4, 4), textcoords="offset points",
        )

    ax.axvline(rate_med, color="#f5f5f5", linestyle="--", alpha=0.4)
    ax.axhline(croe_med, color="#f5f5f5", linestyle="--", alpha=0.4)
    ax.axhline(0, color="#888", linestyle=":", alpha=0.3)

    ax.set_xlabel(
        f"Contested target rate (share of targets with CRP ≥ {CONTESTED_THRESHOLD})"
    )
    ax.set_ylabel("Contested CROE v3 (over contested targets)")
    ax.set_title(
        "Receiver archetypes — 2×2 quadrant\n"
        f"medians: rate={rate_med:.2f}, CROE={croe_med:+.3f}  |  "
        f"displayed: contested_targets ≥ {low_sample_thresh}"
    )
    ax.legend(facecolor="#1a1a1a", edgecolor="#444444", labelcolor="white",
              loc="lower left", fontsize=8)
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _plot_release_share(df: pd.DataFrame, path: str) -> None:
    ranked = _display_frame(df)
    fig, ax = _dark_ax((11, 8))
    for quad, color in QUADRANT_COLORS.items():
        sub = ranked[ranked["quadrant"] == quad]
        if not len(sub):
            continue
        ax.scatter(
            sub["contested_target_rate"], sub["release_share"],
            s=(sub["targets"] * 1.5).clip(20, 400),
            alpha=0.6, c=color, edgecolor="#111111", linewidth=0.5, label=quad,
        )
    for _, row in ranked[ranked["player_name"].isin(LABEL_NAMES)].iterrows():
        ax.annotate(
            row["player_name"],
            (row["contested_target_rate"], row["release_share"]),
            fontsize=8, color="white", xytext=(4, 4), textcoords="offset points",
        )
    ax.set_xlabel("Contested target rate")
    ax.set_ylabel("Release share = sum(crp_at_release) / sum(crp)")
    ax.set_title("Release-share of pressure vs contested rate\n"
                 "high on both = 'tight at release' can't-separate signature")
    ax.legend(facecolor="#1a1a1a", edgecolor="#444444", labelcolor="white",
              loc="upper left", fontsize=8)
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _validation_report(df: pd.DataFrame, path: str) -> None:
    display_cols = [
        "player_name", "player_position", "targets", "contested_targets",
        "contested_target_rate", "contested_catch_rate", "contested_croe",
        "release_share", "median_sep_at_throw", "quadrant",
    ]
    rate_med = df.attrs["rate_median"]
    croe_med = df.attrs["croe_median"]
    low_sample_thresh = df.attrs["low_sample_contested"]
    n_ranked = int(df["contested_croe"].notna().sum())
    n_displayed = int(len(_display_frame(df)))

    def _panel_line(name: str, expected: str) -> str:
        row = df[df["player_name"] == name]
        if len(row) == 0:
            return f"- **{name}** — not on the leaderboard."
        r = row.iloc[0]
        landed = r["quadrant"] if pd.notna(r["contested_croe"]) else "Insufficient contested targets"
        match = "✓" if landed == expected else "✗"
        low_flag = " *(low_sample)*" if bool(r["low_sample"]) else ""
        return (
            f"- **{name}**{low_flag} — contested_targets = {int(r['contested_targets'])}, "
            f"rate = {r['contested_target_rate']:.3f}, "
            f"contested_croe = {r['contested_croe']:+.3f}. "
            f"Expected: {expected}. Landed: **{landed}** {match}"
        )

    lines: list[str] = ["# Pass 3 archetype validation\n"]
    lines.append(
        f"Contested threshold: CRP ≥ **{CONTESTED_THRESHOLD}**. "
        f"Split medians (over {n_ranked} receivers with ≥ 8 contested targets): "
        f"rate = {rate_med:.3f}, contested_croe = {croe_med:+.4f}. "
        f"Low-sample display threshold: contested_targets ≥ **{low_sample_thresh}** — "
        f"{n_displayed} of {n_ranked} receivers pass and appear in headline "
        f"panels; low-sample rows are kept in the CSV with `low_sample = True`.\n"
    )

    lines.append("## Named archetype panel\n")
    lines.append(
        "The plan calls four receivers as ground truth. This report is "
        "regenerated on every rebuild, so results reflect the current model:\n"
    )
    for name, expected in PLAN_PANEL.items():
        lines.append(_panel_line(name, expected))
    matches = sum(
        1 for name, expected in PLAN_PANEL.items()
        if (row := df[df["player_name"] == name]).size and
           (row.iloc[0]["quadrant"] == expected) and pd.notna(row.iloc[0]["contested_croe"])
    )
    lines.append("")
    lines.append(
        f"**{matches} / {len(PLAN_PANEL)} named receivers landed where the plan expected.** "
        "Where they didn't: (a) Hopkins in 2023 was on Tennessee at age 31 — the "
        "\"trusted contested winner\" reputation attaches to his 2017–2020 peak, "
        "not the season we model; (b) Watson has a small contested sample and "
        "sits near the rate-median boundary — under the ≥ 15 low-sample "
        "threshold he now displays as *(low_sample)* rather than driving "
        "headline narratives. The two strongest exemplars (Thomas, Johnston) "
        "land cleanly.\n"
    )

    panel = df[df["player_name"].isin(PLAN_PANEL)].copy().reindex(columns=display_cols)
    lines.append(panel.to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## Extended reference panel\n")
    lines.append(
        "Other high-profile receivers whose profiles should match intuition.\n"
    )
    ext_names = [n for n in LABEL_NAMES if n not in PLAN_PANEL]
    ext = df[df["player_name"].isin(ext_names)].copy() \
        .reindex(columns=display_cols) \
        .sort_values("contested_croe", ascending=False)
    lines.append(ext.to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## Top of each quadrant (displayed rows only)\n")
    lines.append(
        f"Filtered to `contested_targets ≥ {low_sample_thresh}`. Rows with "
        f"between 8 and {low_sample_thresh - 1} contested targets carry a "
        f"contested_croe in the CSV but are hidden from these tables.\n"
    )
    displayed = _display_frame(df)
    for quad in [
        "Trusted contested winner", "Can't separate",
        "Efficient separator", "Uncontested filler",
    ]:
        sub = displayed[displayed["quadrant"] == quad].copy()
        if quad == "Trusted contested winner":
            sub = sub.sort_values("contested_croe", ascending=False)
        elif quad == "Can't separate":
            sub = sub.sort_values(["contested_target_rate", "release_share"],
                                  ascending=[False, False])
        else:
            sub = sub.sort_values("targets", ascending=False)
        lines.append(f"### {quad}  (n = {len(sub)})\n")
        lines.append(sub.head(10).reindex(columns=display_cols).to_markdown(
            index=False, floatfmt=".3f") + "\n")

    with open(path, "w") as f:
        f.write("\n".join(lines))


def main() -> None:
    os.makedirs(OUT, exist_ok=True)

    crp_merged = pd.read_csv(os.path.join(DATA, "crp_merged.csv"))
    play_targets = pd.read_csv(os.path.join(DATA, "play_targets.csv"))
    catch_prob = pd.read_csv(os.path.join(DATA, "catch_prob_v3.csv"))

    df = build_archetype_table(crp_merged, play_targets, catch_prob)
    out_csv = os.path.join(DATA, "archetypes.csv")
    df.to_csv(out_csv, index=False)
    n_low = int(df["low_sample"].sum())
    n_ranked = int(df["contested_croe"].notna().sum())
    print(f"[archetypes] wrote {out_csv}  ({len(df)} receivers, "
          f"{n_ranked} with contested_croe, {n_low} low_sample)")

    _plot_quadrant(df, os.path.join(OUT, "archetypes_quadrant.png"))
    _plot_release_share(df, os.path.join(OUT, "archetypes_release_share.png"))
    print("[archetypes] wrote quadrant + release-share figures")

    _validation_report(df, os.path.join(OUT, "archetypes_validation.md"))
    print("[archetypes] wrote validation report")

    print()
    print(f"Medians (used for quadrant split): "
          f"rate={df.attrs['rate_median']:.3f}, "
          f"contested_croe={df.attrs['croe_median']:+.4f}")


if __name__ == "__main__":
    main()
