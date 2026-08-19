# CROE v3 vs CROE v2 — model & leaderboard movers

## What changed

v3 = v2 feature set + the `is_red_zone` binary covariate (added per Pass 4's
field-position study). Model architecture and training protocol are otherwise
identical.

## Result — v3 metrics are bit-identical to v2

| variant | dev_auc | dev_logloss | dev_brier | test_auc | test_logloss | test_brier |
|---|---|---|---|---|---|---|
| v2 (leverage) | 0.8398 | 0.4160 | 0.1307 | 0.8551 | 0.3889 | 0.1207 |
| v3 (leverage + is_red_zone) | 0.8398 | 0.4160 | 0.1307 | 0.8551 | 0.3889 | 0.1207 |

Per-play catch-probability match: **max |Δ| = 0.000000** across all 13,770
plays. Leaderboard: Spearman ρ = 1.000, Kendall τ = 1.000, zero rank changes.

## Why this happened

Permutation importance for `is_red_zone` in the fitted v3 HGB: **0.00000**.

The reason is straightforward: HGB is a tree-based model, and the existing
covariate `yards_to_endzone` is continuous and monotonic — HGB can split at
the 20-yard threshold on `yards_to_endzone` itself and reproduce the entire
red-zone effect without needing an explicit binary column. `is_red_zone` is
strictly redundant given the features HGB already has.

Pass 4's recommendation was based on a **linear logistic regression**
(`is_completed ~ pass_length + crp + leverage_margin + is_red_zone`). In a
linear model the binary form carries information a linear term can't (a step
function, not a slope), which is why the coefficient came out at −0.4
log-odds. HGB doesn't need that — it discovers the same step function from
`yards_to_endzone`.

## What to conclude

- The **Pass 4 finding stands**: red zone has a real compressed-field effect
  on completion probability at fixed depth + CRP + leverage.
- The **mechanism was already captured** by v2's existing feature set once
  you're using a non-linear model. Pass 4's linear-model diagnostic was
  correct on its own terms but doesn't cross over to HGB.
- `is_red_zone` is kept in the v3 feature set as a **cheap no-op** (one
  binary column, HGB will ignore it) so downstream analysts see the covariate
  explicitly rather than having to trust that `yards_to_endzone` implicitly
  captures it. If a linear (or slot-heavy) model gets built later, the column
  is already there.

## Leaderboard implications

None. v3 leaderboards equal v2 leaderboards to the byte. Full leaderboard is
in `data/receiver_rankings_v3.csv`; there are no v2 → v3 movers to report.

## Follow-ups if a real v3 is wanted

If the goal is a materially different v3 (rather than a renamed v2), the
candidates are:

- Field-position **× position** interactions (e.g., an RZ TE flag), which HGB
  might not find on its own if the interaction is rare.
- A separate red-zone-restricted model with its own hyperparameters and its
  own calibration — attribution for the RZ ~12% slice specifically.
- Reasonable next covariates from the plan's Pass 3 (release-vs-flight
  pressure decomposition) as first-class inputs to the model: `crp_at_release`
  or its share of total CRP.
