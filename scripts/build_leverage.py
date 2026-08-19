"""
Build the Pass 2 leverage artifacts.

Outputs
-------
- ``data/leverage.csv``           per-play (game_id, play_id, rec_dist_to_ball,
                                  rec_closing_v, leverage_margin)
- ``outputs/leverage_summary.md`` distribution / by-depth / by-position /
                                  vs-catch-rate summary tables
- ``outputs/leverage_by_depth.png``     leverage_margin vs air-yards bins
- ``outputs/leverage_vs_catch.png``     empirical catch rate vs leverage_margin
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from crp.leverage import add_leverage_margin, leverage_frame  # noqa: E402


DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "outputs")


def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    m = pd.read_csv(os.path.join(DATA, "crp_merged.csv"))
    t = pd.read_csv(os.path.join(DATA, "play_targets.csv"))
    return m, t


def _dark_ax(figsize: tuple[int, int] = (8, 6)) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#111111")
    ax.set_facecolor("#1a1a1a")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444444")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    return fig, ax


def _plot_by_depth(df: pd.DataFrame, path: str) -> None:
    bins = [-15, 0, 5, 10, 15, 20, 60]
    labels = ["<0", "0–4", "5–9", "10–14", "15–19", "20+"]
    df = df.assign(depth_bin=pd.cut(df["pass_length"], bins=bins, labels=labels, right=False))

    fig, ax = _dark_ax((9, 6))
    data = [df.loc[df["depth_bin"] == lb, "leverage_margin"].dropna() for lb in labels]
    bp = ax.boxplot(
        data, labels=labels, showfliers=False, patch_artist=True,
        medianprops={"color": "#ff9800", "linewidth": 2},
    )
    for patch in bp["boxes"]:
        patch.set_facecolor("#2ecc71")
        patch.set_edgecolor("#111111")
    ax.axhline(0, color="#f5f5f5", linestyle="--", alpha=0.4)
    ax.set_xlabel("Air yards")
    ax.set_ylabel("Leverage margin (min_def_dist_arrival − rec_dist_to_ball, yards)")
    ax.set_title("Receiver leverage by pass depth")
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _plot_vs_catch(df: pd.DataFrame, path: str) -> None:
    df = df[df["pass_result"].isin(["C", "I"])].copy()
    df["completed"] = (df["pass_result"] == "C").astype(int)

    edges = np.quantile(df["leverage_margin"], np.linspace(0, 1, 21))
    edges = np.unique(edges)
    df["bin"] = pd.cut(df["leverage_margin"], bins=edges, include_lowest=True)
    g = df.groupby("bin", observed=True).agg(
        mid=("leverage_margin", "mean"),
        catch_rate=("completed", "mean"),
        n=("completed", "size"),
    ).reset_index()

    fig, ax = _dark_ax((9, 6))
    ax.plot(g["mid"], g["catch_rate"], marker="o", color="#2ecc71", linewidth=2)
    for _, row in g.iterrows():
        ax.annotate(
            f"n={int(row['n'])}",
            (row["mid"], row["catch_rate"]),
            xytext=(0, 6), textcoords="offset points",
            fontsize=7, color="#aaaaaa", ha="center",
        )
    ax.axhline(df["completed"].mean(), color="#f39c12", linestyle="--", alpha=0.5,
               label=f"League avg {df['completed'].mean():.3f}")
    ax.set_xlabel("Leverage margin (yards)")
    ax.set_ylabel("Empirical catch rate")
    ax.set_title("Catch rate vs. receiver leverage")
    ax.set_ylim(0, 1)
    ax.legend(facecolor="#1a1a1a", edgecolor="#444444", labelcolor="white")
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)

    crp_merged, targets = _load()
    lev = leverage_frame(crp_merged)
    lev_path = os.path.join(DATA, "leverage.csv")
    lev.to_csv(lev_path, index=False)
    print(f"[leverage] wrote {lev_path}  ({len(lev):,} rows)")

    df = add_leverage_margin(crp_merged).merge(
        targets[["game_id", "play_id", "player_position"]],
        on=["game_id", "play_id"], how="left",
    )

    _plot_by_depth(df, os.path.join(OUT, "leverage_by_depth.png"))
    _plot_vs_catch(df, os.path.join(OUT, "leverage_vs_catch.png"))

    lines: list[str] = ["# Receiver leverage (Pass 2) — descriptive summary\n"]
    lines.append(
        "Leverage margin = ``min_def_dist_arrival − rec_dist_to_ball`` (yards). "
        "Positive = ball is at the receiver, defender farther away; negative = "
        "defender is closer to the arrival point than the receiver is.\n"
    )

    lines.append("## Distribution overall\n")
    desc = df[["rec_dist_to_ball", "rec_closing_v", "leverage_margin"]].describe(
        percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]
    ).round(3)
    lines.append(desc.to_markdown(floatfmt=".3f") + "\n")

    lines.append(
        f"Share of plays with negative leverage_margin: "
        f"**{(df['leverage_margin'] < 0).mean():.1%}** "
        f"(defender was closer to arrival than the receiver).\n"
    )

    lines.append("## By pass depth\n")
    bins = [-15, 0, 5, 10, 15, 20, 60]
    labels = ["<0", "0–4", "5–9", "10–14", "15–19", "20+"]
    df["depth_bin"] = pd.cut(df["pass_length"], bins=bins, labels=labels, right=False)
    by_depth = df.groupby("depth_bin", observed=True).agg(
        n=("play_id", "size"),
        median_leverage=("leverage_margin", "median"),
        mean_leverage=("leverage_margin", "mean"),
        pct_negative=("leverage_margin", lambda s: (s < 0).mean()),
        catch_rate=("pass_result", lambda s: (s == "C").mean()),
    ).round(3)
    lines.append(by_depth.to_markdown(floatfmt=".3f") + "\n")

    lines.append("## By receiver position (WR/TE/RB/FB)\n")
    pos_mask = df["player_position"].isin(["WR", "TE", "RB", "FB"])
    by_pos = df[pos_mask].groupby("player_position", observed=True).agg(
        n=("play_id", "size"),
        median_leverage=("leverage_margin", "median"),
        mean_leverage=("leverage_margin", "mean"),
        pct_negative=("leverage_margin", lambda s: (s < 0).mean()),
        catch_rate=("pass_result", lambda s: (s == "C").mean()),
    ).round(3)
    lines.append(by_pos.to_markdown(floatfmt=".3f") + "\n")

    lines.append("## Catch rate by leverage decile\n")
    catchable = df[df["pass_result"].isin(["C", "I"])].copy()
    catchable["completed"] = (catchable["pass_result"] == "C").astype(int)
    catchable["decile"] = pd.qcut(catchable["leverage_margin"], q=10, labels=False)
    dec = catchable.groupby("decile", observed=True).agg(
        n=("completed", "size"),
        mean_leverage=("leverage_margin", "mean"),
        catch_rate=("completed", "mean"),
    ).round(3)
    lines.append(dec.to_markdown(floatfmt=".3f") + "\n")

    summary_path = os.path.join(OUT, "leverage_summary.md")
    with open(summary_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[leverage] wrote {summary_path}")


if __name__ == "__main__":
    main()
