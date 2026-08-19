# Pass 4 — Red-zone pressure & field-position study

**Source**: `notebooks/red_zone_pressure.ipynb` (executed inline).

## Findings

### 1. The naive comparison confirms red-zone plays look different

| field position (yardline_100) | n | avg air yd | mean CRP | contested rate | leverage margin | catch rate |
|---|---|---|---|---|---|---|
| deep own (80–99) | 1,373 | 9.2 | 0.172 | 15.8% | 3.06 | 73.0% |
| midfield (21–79) | 10,785 | 9.5 | 0.206 | 18.9% | 2.83 | 71.5% |
| **red zone (≤20)** | **1,612** | **5.7** | **0.277** | **25.7%** | **2.01** | **63.3%** |

Red-zone throws have +34% CRP, +36% contested rate, −29% leverage vs midfield.
But red-zone passes are also 40% shorter on average, so most of that looks
like a depth-mix effect.

### 2. Depth composition confirms the confounder

Red-zone targets are 78% at 0–9 air yards; 20+ balls are essentially
non-existent in the red zone (1.1% of RZ plays vs 14% of midfield).

### 3. The load-bearing result — controlled for depth, red zone still bites

**Mean CRP within depth band** — RZ column is systematically ~1.5–2× the
midfield column:

| air yards | deep own | midfield | red zone | RZ / mid ratio |
|---|---|---|---|---|
| 0–4  | 0.093 | 0.113 | **0.216** | 1.91× |
| 5–9  | 0.156 | 0.198 | **0.306** | 1.55× |
| 10–14 | 0.169 | 0.252 | **0.395** | 1.57× |
| 15–19 | 0.255 | 0.252 | **0.479** | 1.90× |
| 20+  | 0.423 | 0.431 | 0.670 | 1.55× (n=17, noisy) |

**Contested-target rate within depth band** — same shape:

| air yards | deep own | midfield | red zone |
|---|---|---|---|
| 0–4  | 7.6% | 9.9% | **19.2%** |
| 5–9  | 14.0% | 17.3% | **27.8%** |
| 10–14 | 13.7% | 23.8% | **38.1%** |
| 15–19 | 26.5% | 24.3% | **46.9%** |

**Leverage margin within depth band** — red zone compresses the space by 35–45%:

| air yards | midfield | red zone | drop |
|---|---|---|---|
| 0–4  | 4.00 yd | 2.41 yd | −40% |
| 5–9  | 2.15 yd | 1.36 yd | −37% |
| 10–14 | 1.57 yd | 0.87 yd | −45% |

The compressed-field effect is **real, large, and directionally consistent**
across all depth bands: same air yards → more CRP, more contested targets,
less leverage.

### 4. But does field position add signal beyond depth + CRP + leverage?

5-fold GroupKFold(game_id) logistic regression on `is_completed`:

| model | AUC | log-loss | ΔAUC | Δlog-loss |
|---|---|---|---|---|
| base (pass_length + crp + leverage_margin) | 0.7874 | 0.5060 | — | — |
| + yardline_100 (continuous) | 0.7883 | 0.5049 | +0.0009 | −0.0012 |
| + is_red_zone (binary)      | 0.7887 | 0.5045 | +0.0013 | −0.0015 |

Fitted coefficient for `is_red_zone` (with the other three in the model):
**−0.4053 log-odds**, i.e. red-zone context alone reduces completion odds by
~33% at the same air yards + CRP + leverage. Statistically credible; the
tiny AUC lift is because red zone is only ~12% of plays, so a real effect on
a small slice moves aggregate metrics only a little.

### 5. Interpretation

Two things are simultaneously true:

- **The compressed-field mechanism is real** — RZ heatmaps are unambiguous.
- **Most of that mechanism is already captured** by CRP and `leverage_margin`,
  because both are arrival-frame measurements taken *after* the field
  compression has already produced tighter windows. That's Pass 2 doing its
  job: the pressure/leverage covariates already encode "the field is tight."

The −0.4 log-odds residual on `is_red_zone` suggests a *further* red-zone
effect the arrival-frame covariates don't capture — plausibly from defender
scheme choices that don't show up as arrival-position variance (jam coverage,
undercutting, cross-face help) or from QB decision-making priors (throw
harder, throw sooner, target back-shoulder).

## Recommendation

**Weak add** — include `is_red_zone` (binary, yardline_100 ≤ 20) as a CROE v3
covariate when we next re-fit the model. Reasons:

- The residual coefficient is large enough to matter for red-zone attribution
  (−0.4 log-odds ≈ 33% completion-odds discount holding CRP/leverage fixed).
- Cost is negligible (one binary column, HGB handles it natively).
- It gives downstream analysis (dashboard slicing, player-vs-league RZ
  splits) a natural handle for red-zone-specific views.
- Aggregate AUC lift is small (~+0.001), but that's expected for a 12%
  slice; the improvement on RZ-restricted evaluation would be larger.

**Do not** promote red zone to a headline story. The finding is a
validation of Pass 2 — leverage margin plus CRP already carry most of the
compressed-field signal — not a new signal that eclipses them.

**If Pass 5+ builds a CROE v3**, sanity check by:

1. Fitting with and without `is_red_zone`.
2. Evaluating on the RZ subset specifically (AUC / logloss on `yardline_100 ≤ 20`
   only) — that's where the covariate should help most.
3. Verifying no receiver in the RZ top of the leaderboard is a red-zone
   volume artifact.
