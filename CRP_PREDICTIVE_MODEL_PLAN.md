# CRP Predictive Model — Plan & Decisions

Working notes for predicting Catch Radius Pressure (CRP) from play context.
Target source: `data/crp_merged.csv` (14,108 unique plays, 2023 season weeks 1–18).

---

## Pass 1 — Audit (complete)

- **Rows**: 14,108. `(game_id, play_id)` is the unique key (0 duplicates).
- **`week`**: not present as a single column. Merge produced `week_x` and `week_y`; they agree on every row (range 1–18). Decision: **collapse to a single `week` column** at the top of Pass 2.
- **CRP target distribution**:
  - Mean 0.222, median 0.000, max 2.563, no NaN, no negatives.
  - **57.21% of plays are crp == 0** (8,071 / 14,108).
  - Non-zero mass is long-tailed and roughly exponential.

---

## Modeling target — two-stage hurdle

Single continuous regression on CRP fights the 57% point mass. Adopt a **hurdle** decomposition:

- **Stage A — Binary**: `is_contested = (crp > 0)`. Classifier predicting whether *any* defender will be inside the catch radius at ball arrival.
- **Stage B — Regression**: model `crp` on the **positive subset only** (6,037 plays). Predicts severity given a contested arrival.

Composite prediction at inference: `E[crp | x] = P_A(x) * E_B[crp | x, crp > 0]`.

Pass 2+ must produce metrics and feature importances for **both stages**.

---

## Feature sets — two prediction time-points

Build two parallel feature sets from the same merged table. Every model run reports both.

### Pre-snap feature set (`features_pre_snap`)
What is knowable before the ball is snapped.

**Allowed (final for pre-snap, 19 columns):**
- Game/clock: `quarter`, `game_clock` (parsed `MM:SS` → seconds), `game_time_eastern`
- Down & distance: `down`, `yards_to_go`
- Field position: `yardline_side` (NaN → `MIDFIELD`), `yardline_number`
- Score state: `pre_snap_home_score`, `pre_snap_visitor_score`
- Win prob / EP: `pre_snap_home_team_win_probability`, `pre_snap_visitor_team_win_probability`, `expected_points`
- Teams: `possession_team`, `defensive_team`, `home_team_abbr`, `visitor_team_abbr`
- Formation: `offense_formation`, `receiver_alignment`
- Defense pre-snap look: `defenders_in_the_box`

**Dropped from pre-snap during Pass 3:**
- `game_date` — removed from feature set (only 56 unique values across one season; team identity already encodes the per-season effects we want)
- `play_action` — moved to the at-throw holding list (whether play-action is run is decided post-snap; same risk class as `dropback_type`)

**Excluded for pre-snap (any of: CRP-derived, post-snap-revealed, identity-of-target):**
- All CRP-derived: `crp`, `crp_label`, `n_defenders_in_radius`, `ball_land_x`, `ball_land_y`, `num_frames_output`
- All post-snap / outcome: `pass_result`, `pass_length`, `yards_gained`, `pre_penalty_yards_gained`, `penalty_yards`, `play_nullified_by_penalty`, `expected_points_added`, `home_team_win_probability_added`, `visitor_team_win_probility_added`, `play_description`, `dropback_type`, `dropback_distance`, `pass_location_type`
- **Realized coverage (leaks)**: `team_coverage_man_zone`, `team_coverage_type` — see "Coverage timing" below
- **Target identity (leaks intent)**: `route_of_targeted_receiver`

### At-throw feature set (`features_at_throw`)
What is knowable at/after the snap up to ball release. Strictly a superset of pre-snap.

**Additional allowed (over pre-snap), supplementary-derived:**
- `route_of_targeted_receiver` (route + targeted receiver identity)
- `team_coverage_man_zone`, `team_coverage_type` (realized coverage)
- `dropback_type`, `dropback_distance`, `pass_location_type` (QB action — knowable at release)
- `play_action` (only revealed at/after snap)
- `pass_length` — **reclassified at Pass 4 from "outcome" to at-throw legal**. The throw's air yards are determined by ball trajectory at release; same risk class as `dropback_distance`. Not derived from the catch frame.

**Additional allowed (over pre-snap), tracking-derived at the release frame** (last `frame_id` of `input_2023_w*.csv` per `crp/data_loader.py`):
- `rec_speed`, `rec_dir_sin`, `rec_dir_cos` — targeted receiver's velocity at release (direction encoded sin/cos to handle angular wrap)
- `nearest_def_dist_release` — distance from targeted receiver to closest defender at release (= receiver separation)
- `nearest_def_closing_vel_release` — that defender's velocity component toward the receiver
- `n_defenders_in_R_release` — count of defenders within R = 3 yd of the receiver at release (distinct from the catch-frame CRP count, which is excluded)

All at-throw additions are evaluated strictly at or before ball release. No catch-frame or post-throw quantities. The targeted receiver identity comes from `data/play_targets.csv`. One play (out of 14,108) has no targeted-receiver row at the release frame and is dropped from the at-throw set.

**Still excluded for at-throw:**
- All CRP-derived columns (circular).
- Pure outcome: `pass_result`, `pass_length`, `yards_gained`, `pre_penalty_yards_gained`, `penalty_yards`, `play_nullified_by_penalty`, `expected_points_added`, `home_team_win_probability_added`, `visitor_team_win_probility_added`, `play_description`.

### Keys / split columns (not features)
`game_id`, `play_id`, `week`.

---

## Coverage timing — finding

`team_coverage_man_zone` and `team_coverage_type` are **post-snap realized coverage labels**.

- Taxonomy is the standard NGS post-snap classification (`COVER_0_MAN`, `COVER_1_MAN`, `COVER_2_MAN`, `COVER_2_ZONE`, `COVER_3_ZONE`, `COVER_4_ZONE`, `COVER_6_ZONE`, `PREVENT`). Pre-snap shells use a different vocabulary (single-high / two-high / etc.).
- Near-complete fill: only 3/14,108 NaN. Pre-snap shells are ambiguous on disguised plays and would be missing more often; near-100% fill is consistent with a post-snap classifier.
- Source: `supplementary_data.csv` via `crp/data_loader.load_supplementary` — the standard channel for derived NGS labels.

Decision: **exclude both from the pre-snap set, allow in the at-throw set**. The competition data dictionary isn't materialized in this checkout; if the data is restored, re-confirm against the official field description before publishing results.

---

## Splitting strategy

The Stage B positive subset is only ~6,037 plays, so a single small validation slice is fragile. Use cross-validation on the development weeks and keep the last two weeks fully untouched for headline metrics.

- **Development pool**: weeks 1–16. **5-fold `GroupKFold` grouped by `game_id`** — prevents same-game leakage and uses all of dev for both training and validation across folds. Fold assignment is made once on the full dev set (Stage A scope) and reused for Stage B by filtering to positives within each fold. This guarantees a game appears in exactly one validation fold across both stages.
- **Held-out test**: weeks 17–18. Never touched during model selection or tuning. Final composite (`P_A × E_B`) is evaluated on this set end-to-end on the same plays for both stages.
- Same fold/test split is used for the pre-snap and at-throw feature sets, so the two feature regimes are directly comparable on identical plays.

---

## Pass 2+ outline (not yet started — held at Pass 1 gate)

- **Pass 2** — Build `features_pre_snap` and `features_at_throw` tables from `crp_merged.csv`. Materialize Stage A target `is_contested` and Stage B target `crp` on the positive subset. Verify no excluded column appears in either feature table. Verify both targets join cleanly on `(game_id, play_id)`.
- **Pass 3** — Baselines for both stages, both feature sets: Stage A logistic regression / Stage B linear regression on a small encoded feature set. Report ROC-AUC / log-loss / Brier (A) and MAE / RMSE / R² on positives (B), plus composite metrics.
- **Pass 4** — Gradient-boosted models (e.g. LightGBM) for both stages, both feature sets. Calibrate Stage A. Inspect feature importance / SHAP and confirm no leakage signature.
- **Pass 5** — Final eval on the held-out test weeks. Compare pre-snap vs at-throw lift to quantify the value of post-snap information.

Each pass ends at an explicit verify gate before the next begins.

---

## Pass 5–6 — final reported models (held-out test, weeks 17-18, 1,559 plays)

**Pre-snap Stage A** — **calibrated LR** (no-team, C=0.01, 15 features): test logloss 0.6596 / Brier 0.234 / AUC 0.608 / ECE 0.032.
**At-throw Stage A** — **uncalibrated HGB** (no coverage, lr=0.05, max_leaf=15, l2=0, 31 features): test logloss 0.5122 / Brier 0.173 / AUC 0.811 / ECE 0.018.
**Pre-snap Stage B** — tuned Ridge (α=100, full pre-snap 19 features): test RMSE 0.363 / R² +0.004 (≈ mean baseline; CV R² is actually −0.008 — no real signal).
**At-throw Stage B** — tuned Ridge (α=100, 31 features): test RMSE 0.344 / R² **+0.107**.
**Composite at-throw** (P_A × E_B, full 1,559 plays): RMSE **0.295** / R² **+0.253**.

Sensitivity check: `team_coverage_man_zone` / `team_coverage_type` moved CV log loss by 0.001 and CV RMSE by 0.0005 — **dropped from final at-throw set** (cleaner story, no measurable cost). Final at-throw feature count = 31 (was 33).

### Calibration decision

CalibratedClassifierCV (isotonic, GroupKFold-aware via PredefinedSplit) was tested on both Stage A models.
- **Pre-snap LR**: uncalibrated ECE 0.030 → calibrated 0.032; logloss tied. LR was already well-calibrated → kept calibrated for the paper (the step is a no-op; the wrapper makes the pipeline uniform).
- **At-throw HGB**: uncalibrated ECE 0.018 → calibrated 0.028; logloss 0.5122 → 0.5110 (tiny shift). Reliability diagram (`outputs/13_stage_a_reliability.png`) shows the uncalibrated curve tracks y=x essentially perfectly; isotonic introduces a visible wobble around p ∈ [0.5, 0.7]. **Report uncalibrated.** Calibration was tested and found unnecessary.

### Artifacts
- `data/test_predictions.csv` — 1,559 rows: `p_A_pre_snap_cal`, `p_A_at_throw_uncal` (REPORTED), `p_A_at_throw_cal` (record), `E_B_*`, `composite_pre_snap`, `composite_at_throw` (uses uncal P_A — REPORTED), `composite_at_throw_cal` (record).
- `outputs/12_hero_presnap_vs_at_throw.png` — regenerated with uncalibrated at-throw numbers.
- `outputs/13_stage_a_reliability.png` — calibration decision evidence.
- `outputs/14_at_throw_perm_importance.png`, `outputs/15_at_throw_stageB_pred_vs_actual.png`, `outputs/16_crp_distribution_hurdle.png`.

---

## Deferred to a final polish pass

After at-throw modeling is done, do **one** polish pass that handles:

- **Hyperparameter tuning** with GroupKFold-CV grid: `LogisticRegression.C`, `Ridge.alpha`, plus HGB `learning_rate` / `max_depth` / `min_samples_leaf` / `l2_regularization`. Tune Stage A and Stage B separately.
- **Stage A probability calibration**: add `CalibratedClassifierCV` (isotonic or sigmoid) on the winning Stage A model — HGB at 100 iterations on a binary target can be miscalibrated, which matters for the composite `P_A × E_B`.

Do not retune during Pass 4; report Pass 4 with the same defaults used in Pass 3.
