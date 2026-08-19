"""
Generator for notebooks/red_zone_pressure.ipynb.

We build the notebook cell-by-cell in nbformat so the source stays diffable and
version-controllable. Run this, then execute the notebook with:

    python3 -m jupyter nbconvert --to notebook --execute \
        --inplace notebooks/red_zone_pressure.ipynb
"""

from __future__ import annotations

import os
import nbformat as nbf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_PATH = os.path.join(ROOT, "notebooks", "red_zone_pressure.ipynb")


def md(src: str) -> dict:
    return nbf.v4.new_markdown_cell(src)


def code(src: str) -> dict:
    return nbf.v4.new_code_cell(src)


cells: list = []

# ── 1. Title & framing ─────────────────────────────────────────────────────
cells.append(md("""\
# Pass 4 — Red-zone pressure & field-position study

**Question (from CRP_FEEDBACK_ADAPTATION_PLAN.md).** Once plays are
standardised, does pressure concentrate in the red zone, where the field is
compressed, versus being diluted by deep-in-own-territory plays? And more
sharply: does field position add *incremental* signal to a catch-probability
model that already knows air yards?

**Setup.** Coarse bins (red zone ≤ 20 / midfield 21–79 / deep-own 80–99),
then a finer 10-yard binning, then the confounder check: red-zone throws are
short by construction. So a naive comparison would just re-discover "short
throws are pressured differently than long ones". The load-bearing analysis
is *within* depth bands.

**Decision output.** Whether to add `yardline_100` (or a red-zone indicator)
as a CROE v3 covariate.
"""))

# ── 2. Setup ───────────────────────────────────────────────────────────────
cells.append(code("""\
import os, sys, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.insert(0, ROOT)

from crp.leverage import add_leverage_margin

DARK_BG = "#111111"
PANEL_BG = "#1a1a1a"

def dark_ax(figsize=(9, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)
    for s in ax.spines.values(): s.set_edgecolor("#444444")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white"); ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    return fig, ax

plt.rcParams["figure.facecolor"] = DARK_BG
plt.rcParams["axes.facecolor"] = PANEL_BG
plt.rcParams["text.color"] = "white"
plt.rcParams["axes.labelcolor"] = "white"
plt.rcParams["xtick.color"] = "white"
plt.rcParams["ytick.color"] = "white"

crp_merged = pd.read_csv(os.path.join(ROOT, "data", "crp_merged.csv"))
play_targets = pd.read_csv(os.path.join(ROOT, "data", "play_targets.csv"))
catch_prob = pd.read_csv(os.path.join(ROOT, "data", "catch_prob_v3.csv"))
crp_merged = add_leverage_margin(crp_merged)
print("crp_merged:", crp_merged.shape)
print("play_targets:", play_targets.shape)
print("catch_prob_v3:", catch_prob.shape)
"""))

cells.append(code("""\
# yards_to_endzone = the offense's distance to the goal line they're driving toward
# (BDB uses yardline_side + yardline_number; convert into yardline_100 semantics)
same_side = crp_merged["yardline_side"] == crp_merged["possession_team"]
crp_merged["yardline_100"] = np.where(
    same_side,
    100 - crp_merged["yardline_number"],
    crp_merged["yardline_number"],
).astype(float)

# Filter to catchable pass attempts (matches CROE v2 convention)
plays = crp_merged[crp_merged["pass_result"].isin(["C", "I"])].copy()
plays["is_completed"] = (plays["pass_result"] == "C").astype(int)
plays["is_contested"] = (plays["crp"] >= 0.5).astype(int)

# Depth bands (matches Pass 2)
depth_bins = [-15, 0, 5, 10, 15, 20, 60]
depth_labels = ["<0", "0-4", "5-9", "10-14", "15-19", "20+"]
plays["depth_bin"] = pd.cut(plays["pass_length"], bins=depth_bins,
                            labels=depth_labels, right=False)

# Coarse field position: red zone / midfield / deep-own
def _fp_coarse(y):
    if y <= 20: return "red zone (≤20)"
    if y <= 79: return "midfield (21-79)"
    return "deep own (80-99)"

plays["fp_coarse"] = plays["yardline_100"].apply(_fp_coarse)

# 10-yard bands (offense POV: 1-9 = goal-line, 90-99 = backed up)
fine_bins = list(range(0, 101, 10))
fine_labels = [f"{a+1}-{a+10}" for a in fine_bins[:-1]]
plays["fp_fine"] = pd.cut(plays["yardline_100"], bins=fine_bins,
                          labels=fine_labels, include_lowest=True, right=True)

# Attach catch_prob_v3 for CROE
plays = plays.merge(
    catch_prob[["game_id", "play_id", "catch_prob_v3"]],
    on=["game_id", "play_id"], how="inner",
)
plays["croe_v3_play"] = plays["is_completed"] - plays["catch_prob_v3"]

print(f"analysis frame: {len(plays):,} plays (pass_result in C, I)")
print()
print("yardline_100 distribution:")
print(plays["yardline_100"].describe().round(1))
"""))

# ── 3. Coarse binning ──────────────────────────────────────────────────────
cells.append(md("""\
## 1. Coarse binning — the naive view

Does the red zone jump out on raw metrics, before we control for anything?
"""))

cells.append(code("""\
coarse = plays.groupby("fp_coarse", observed=True).agg(
    n=("play_id", "size"),
    avg_air_yards=("pass_length", "mean"),
    mean_crp=("crp", "mean"),
    contested_rate=("is_contested", "mean"),
    mean_leverage=("leverage_margin", "mean"),
    catch_rate=("is_completed", "mean"),
).round(3)
coarse = coarse.reindex(["deep own (80-99)", "midfield (21-79)", "red zone (≤20)"])
coarse
"""))

cells.append(md("""\
**Read.** Red-zone plays have (a) shorter passes on average, (b) higher
contested rate, (c) lower catch rate, (d) higher mean CRP. But (a) is a
confounder: shorter passes always have different pressure characteristics.
Need to control.
"""))

# ── 4. Fine binning ────────────────────────────────────────────────────────
cells.append(md("## 2. Fine 10-yard bands — where does the effect live?"))

cells.append(code("""\
fine = plays.groupby("fp_fine", observed=True).agg(
    n=("play_id", "size"),
    avg_air_yards=("pass_length", "mean"),
    mean_crp=("crp", "mean"),
    contested_rate=("is_contested", "mean"),
    mean_leverage=("leverage_margin", "mean"),
    catch_rate=("is_completed", "mean"),
).round(3)
fine
"""))

cells.append(code("""\
fig, axes = plt.subplots(1, 3, figsize=(18, 5), facecolor=DARK_BG)
for ax, (col, ylab, color) in zip(axes, [
    ("mean_crp", "Mean CRP", "#f39c12"),
    ("contested_rate", "Contested-target rate (CRP ≥ 0.5)", "#e74c3c"),
    ("mean_leverage", "Mean leverage_margin (yd)", "#2ecc71"),
]):
    ax.set_facecolor(PANEL_BG)
    for s in ax.spines.values(): s.set_edgecolor("#444444")
    ax.tick_params(colors="white")
    ax.plot(range(len(fine)), fine[col], marker="o", color=color, linewidth=2)
    ax.set_xticks(range(len(fine)))
    ax.set_xticklabels(fine.index, rotation=45, ha="right", color="white")
    ax.set_ylabel(ylab, color="white")
    ax.set_xlabel("Offense's distance to opponent endzone (yardline_100)",
                  color="white")
    ax.axvline(1.5, linestyle="--", alpha=0.4, color="white")  # RZ boundary
    ax.axvspan(-0.5, 1.5, alpha=0.08, color="red")
fig.suptitle("Pressure signals by field position (unconditioned on depth)",
             color="white", fontsize=13)
plt.tight_layout()
plt.show()
"""))

# ── 5. Confounder check ────────────────────────────────────────────────────
cells.append(md("""\
## 3. Confounder — depth of pass by field position

The 20+ air-yard band is essentially impossible in the red zone. Anything we
saw above is at least partially a depth-mix effect.
"""))

cells.append(code("""\
depth_by_fp = pd.crosstab(plays["fp_coarse"], plays["depth_bin"], normalize="index").round(3)
depth_by_fp = depth_by_fp.reindex(["deep own (80-99)", "midfield (21-79)", "red zone (≤20)"])
depth_by_fp = depth_by_fp[depth_labels]
depth_by_fp
"""))

cells.append(code("""\
fig, ax = dark_ax((10, 5))
bottom = np.zeros(len(depth_by_fp))
colors = plt.cm.viridis(np.linspace(0.15, 0.9, len(depth_labels)))
for lbl, c in zip(depth_labels, colors):
    ax.bar(depth_by_fp.index, depth_by_fp[lbl], bottom=bottom, label=lbl,
           color=c, edgecolor="#111111")
    bottom += depth_by_fp[lbl].to_numpy()
ax.set_ylabel("Share of targets", color="white")
ax.set_title("Depth composition of targets by field position", color="white")
ax.legend(title="Air yards", facecolor=PANEL_BG, edgecolor="#444444",
          labelcolor="white", title_fontsize=9, fontsize=8, loc="lower left")
plt.tight_layout()
plt.show()
"""))

cells.append(md("""\
Confirmed: red-zone targets are almost entirely ≤14 air yards; 20+ balls are
essentially non-existent. Any comparison against midfield / deep-own that
doesn't condition on depth is contaminated by this mixture.
"""))

# ── 6. Within-depth-band ───────────────────────────────────────────────────
cells.append(md("""\
## 4. The load-bearing analysis — within-depth-band comparisons

Now controlling for depth: within each air-yards band, does field position
still move CRP / contested rate / leverage?
"""))

cells.append(code("""\
def _cross(metric: str, agg="mean"):
    piv = plays.pivot_table(
        index="depth_bin", columns="fp_coarse", values=metric,
        aggfunc=agg, observed=True,
    )
    piv = piv.reindex(index=depth_labels,
                      columns=["deep own (80-99)", "midfield (21-79)", "red zone (≤20)"])
    return piv.round(3)

print("mean CRP by depth × field position:")
crp_cross = _cross("crp")
display(crp_cross)
print("contested rate (CRP ≥ 0.5) by depth × field position:")
cr_cross = _cross("is_contested")
display(cr_cross)
print("mean leverage_margin by depth × field position:")
lev_cross = _cross("leverage_margin")
display(lev_cross)
"""))

cells.append(code("""\
# Heatmap helper
def heatmap(piv, title, cmap="viridis"):
    fig, ax = dark_ax((8, 5))
    im = ax.imshow(piv.values, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns, color="white")
    ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index, color="white")
    ax.set_xlabel("Field position", color="white")
    ax.set_ylabel("Air yards", color="white")
    ax.set_title(title, color="white")
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.iloc[i, j]
            if pd.notna(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        color="white", fontsize=9)
    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.yaxis.set_tick_params(color="white")
    for lb in cbar.ax.get_yticklabels(): lb.set_color("white")
    plt.tight_layout(); plt.show()

heatmap(crp_cross, "Mean CRP by depth × field position", "YlOrRd")
heatmap(cr_cross, "Contested rate by depth × field position", "YlOrRd")
heatmap(lev_cross, "Mean leverage_margin by depth × field position", "YlGn")
"""))

cells.append(md("""\
**Sample-size check.** Some cells are thin (deep balls in the red zone don't
exist). Report the counts so we don't over-interpret sparse cells.
"""))

cells.append(code("""\
count_cross = plays.pivot_table(
    index="depth_bin", columns="fp_coarse", values="play_id",
    aggfunc="size", observed=True,
)
count_cross = count_cross.reindex(index=depth_labels,
                                  columns=["deep own (80-99)", "midfield (21-79)", "red zone (≤20)"])
count_cross.astype("Int64")
"""))

# ── 7. Statistical test ────────────────────────────────────────────────────
cells.append(md("""\
## 5. Does field position add signal beyond depth (and CRP)?

Fit a simple logistic regression `is_completed ~ pass_length + crp + leverage_margin`
and compare AUC / log-loss with vs without a `yardline_100` term. If adding
`yardline_100` doesn't move the metrics, red zone is fully explained by the
covariates the model already has (depth + pressure).
"""))

cells.append(code("""\
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss
from sklearn.model_selection import GroupKFold

feat = plays[[
    "game_id", "pass_length", "crp", "leverage_margin", "yardline_100",
    "is_completed",
]].dropna().copy()

Xbase = feat[["pass_length", "crp", "leverage_margin"]].to_numpy()
Xrz   = feat[["pass_length", "crp", "leverage_margin", "yardline_100"]].to_numpy()
y     = feat["is_completed"].to_numpy()
groups = feat["game_id"].to_numpy()

def cv_scores(X):
    aucs, lls = [], []
    for tr, va in GroupKFold(5).split(X, y, groups=groups):
        m = LogisticRegression(max_iter=500)
        m.fit(X[tr], y[tr])
        p = m.predict_proba(X[va])[:, 1]
        aucs.append(roc_auc_score(y[va], p))
        lls.append(log_loss(y[va], np.clip(p, 1e-6, 1-1e-6)))
    return float(np.mean(aucs)), float(np.mean(lls))

auc_base, ll_base = cv_scores(Xbase)
auc_rz,   ll_rz   = cv_scores(Xrz)
print(f"base   (depth + crp + leverage):        AUC {auc_base:.4f}  logloss {ll_base:.4f}")
print(f"+ yardline_100:                          AUC {auc_rz:.4f}  logloss {ll_rz:.4f}")
print(f"delta:                                   AUC {auc_rz-auc_base:+.4f}  logloss {ll_rz-ll_base:+.4f}")
"""))

cells.append(md("""\
Also try a red-zone *indicator* (binary) instead of the continuous
`yardline_100`, to see whether the effect is threshold-like.
"""))

cells.append(code("""\
feat["is_red_zone"] = (feat["yardline_100"] <= 20).astype(int)
Xrz_ind = feat[["pass_length", "crp", "leverage_margin", "is_red_zone"]].to_numpy()
auc_ind, ll_ind = cv_scores(Xrz_ind)
print(f"+ red-zone indicator:                    AUC {auc_ind:.4f}  logloss {ll_ind:.4f}")
print(f"delta vs base:                           AUC {auc_ind-auc_base:+.4f}  logloss {ll_ind-ll_base:+.4f}")

# What sign does the RZ indicator take once we control for depth + pressure?
m_all = LogisticRegression(max_iter=500).fit(Xrz_ind, y)
coef_names = ["pass_length", "crp", "leverage_margin", "is_red_zone"]
print()
print("Fitted coefficients (log-odds of completion):")
for n, c in zip(coef_names, m_all.coef_[0]):
    print(f"  {n:20s} {c:+.4f}")
print(f"  intercept            {m_all.intercept_[0]:+.4f}")
"""))

# ── 8. Recommendation ──────────────────────────────────────────────────────
cells.append(md("""\
## 6. Recommendation — CROE v3 covariate?

**Decision rule (from the plan).** "If the compressed-field effect is real
and large: propose field-position-adjusted expectation as a CROE v3 covariate."

**Read the numbers above.** Look at:

1. **Within-depth-band CRP heatmap** — does red zone increase mean CRP inside
   the same air-yards band, or is it flat once depth is fixed?
2. **Within-depth-band contested rate** — same question.
3. **AUC lift from adding `yardline_100` / `is_red_zone`** to a base model
   that already has depth + CRP + leverage. If the lift is < 0.005 AUC or
   log-loss doesn't move by more than the noise floor (~0.002), the effect
   is fully absorbed by the existing covariates.

The recommendation text is written up in
**`outputs/red_zone_summary.md`** after the notebook has run and the numbers
have been read.
"""))

# ── Save notebook ──────────────────────────────────────────────────────────
nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "version": "3"},
}

os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)
with open(NB_PATH, "w") as f:
    nbf.write(nb, f)
print(f"wrote {NB_PATH} ({len(cells)} cells)")
