# CROE v2: arrival-separation backfill vs release-frame proxy

## What changed

The initial Pass 1 shipment used `nearest_def_dist_release` (release-frame nearest defender distance) as a proxy for the plan's specified "receiver separation at arrival" because raw tracking wasn't on disk. After copying the competition data into place, `crp.metric` now also emits `min_def_dist_arrival` and the CROE v2 feature set uses **both** release-frame *and* arrival-frame separation.

Why both, not just arrival: substituting arrival for release alone *degraded* AUC (0.7852 vs 0.7916 test-cal). Interpretation — release-frame separation captures what the QB "saw" when throwing, which drives whether a ball is catchable at all; arrival-frame separation is largely correlated with CRP (both are arrival-frame quantities) and adds less marginal signal for pure catch-probability, but *does* help enough that the combination beats either alone.

## Model metrics (test = weeks 17–18, calibrated)

| variant | dev_auc | dev_logloss | dev_brier | test_auc | test_logloss | test_brier |
|---|---|---|---|---|---|---|
| release-only (proxy) | 0.7786 | 0.4887 | 0.1594 | 0.7916 | 0.4795 | 0.1565 |
| release + arrival (current) | 0.7834 | 0.4857 | 0.1583 | 0.7934 | 0.4791 | 0.1559 |

## Rank-order stability, proxy ↔ current

- Spearman ρ = 0.993
- Kendall τ = 0.934

Very high correlation — arrival-frame doesn't shake the CROE leaderboard, it just re-weights a small number of edge cases.

## Biggest CROE lifts (arrival separation adds credit)

| player_name       | player_position   |   targets |   croe_v2_proxy |   croe_v2_now |   croe_change |   rank_proxy |   rank_now |
|:------------------|:------------------|----------:|----------------:|--------------:|--------------:|-------------:|-----------:|
| Jameson Williams  | WR                |        33 |          -0.093 |        -0.066 |         0.027 |          157 |        146 |
| Greg Dortch       | WR                |        34 |          -0.052 |        -0.038 |         0.014 |          139 |        128 |
| Mike Gesicki      | TE                |        38 |           0.018 |         0.032 |         0.014 |           65 |         55 |
| Jahmyr Gibbs      | RB                |        51 |          -0.023 |        -0.011 |         0.012 |          117 |        103 |
| Jerome Ford       | RB                |        44 |          -0.042 |        -0.030 |         0.012 |          132 |        124 |
| Robert Woods      | WR                |        59 |          -0.089 |        -0.077 |         0.012 |          156 |        153 |
| Zach Ertz         | TE                |        34 |           0.024 |         0.035 |         0.012 |           62 |         50 |
| Demarcus Robinson | WR                |        33 |           0.107 |         0.119 |         0.012 |            9 |          2 |
| Michael Wilson    | WR                |        49 |           0.104 |         0.115 |         0.011 |           10 |          5 |
| Jalen Tolbert     | WR                |        30 |           0.046 |         0.057 |         0.011 |           40 |         29 |

## Biggest CROE drops (arrival separation removes credit)

| player_name   | player_position   |   targets |   croe_v2_proxy |   croe_v2_now |   croe_change |   rank_proxy |   rank_now |
|:--------------|:------------------|----------:|----------------:|--------------:|--------------:|-------------:|-----------:|
| Michael Mayer | TE                |        36 |          -0.022 |        -0.038 |        -0.015 |          115 |        129 |
| Mark Andrews  | TE                |        54 |           0.022 |         0.008 |        -0.014 |           63 |         78 |
| Logan Thomas  | TE                |        68 |           0.043 |         0.029 |        -0.014 |           43 |         57 |
| Noah Fant     | TE                |        40 |           0.001 |        -0.012 |        -0.013 |           86 |        105 |
| Kalif Raymond | WR                |        33 |           0.058 |         0.047 |        -0.012 |           31 |         37 |
| Tyler Lockett | WR                |        97 |           0.058 |         0.047 |        -0.011 |           30 |         36 |
| Taysom Hill   | QB                |        35 |           0.097 |         0.086 |        -0.011 |           12 |         15 |
| Durham Smythe | TE                |        42 |           0.037 |         0.026 |        -0.011 |           50 |         60 |
| Austin Ekeler | RB                |        49 |          -0.123 |        -0.133 |        -0.010 |          165 |        167 |
| Chuba Hubbard | RB                |        38 |           0.079 |         0.069 |        -0.010 |           21 |         22 |
