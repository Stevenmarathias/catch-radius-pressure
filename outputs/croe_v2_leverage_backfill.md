# CROE v2 before/after Pass 2 leverage covariates

Added ``leverage_margin`` (= ``min_def_dist_arrival − rec_dist_to_ball``) and ``rec_closing_v`` to the CROE v2 feature set.

## Model metrics (calibrated)

| variant | dev_auc | dev_logloss | dev_brier | test_auc | test_logloss | test_brier |
|---|---|---|---|---|---|---|
| pre-leverage | 0.7834 | 0.4857 | 0.1583 | 0.7934 | 0.4791 | 0.1559 |
| with leverage | 0.8398 | 0.4160 | 0.1307 | 0.8551 | 0.3889 | 0.1207 |

Interpretation: leverage is a *very* strong single-feature lift. Log-loss drops ~19%, Brier ~23%, AUC jumps by ~6 points on the test weeks. This is not surprising — empirical catch rate rises monotonically from 25.5% (bottom leverage decile) to 91.7% (top decile), so encoding it as a covariate compresses the residual (= CROE) toward the true skill signal.

## Rank-order stability, pre-leverage ↔ with-leverage

- Spearman ρ = 0.899
- Kendall τ = 0.735

Ordering is largely preserved. Where it moves, it moves for a reason:

## Biggest CROE drops (leverage removed over-credit)

Receivers whose targets were wide-open on average lose CROE — the model now correctly assigns those catches higher baseline expectation.

| player_name       | player_position   |   targets |   croe_pre |   croe_now |   croe_change |   rank_pre |   rank_now |
|:------------------|:------------------|----------:|-----------:|-----------:|--------------:|-----------:|-----------:|
| Nelson Agholor    | WR                |        36 |      0.116 |      0.057 |        -0.059 |          4 |         25 |
| Khalil Shakir     | WR                |        39 |      0.112 |      0.061 |        -0.051 |          7 |         20 |
| Taysom Hill       | QB                |        35 |      0.086 |      0.036 |        -0.050 |         15 |         45 |
| Rondale Moore     | WR                |        44 |     -0.083 |     -0.130 |        -0.046 |        156 |        166 |
| K.J. Osborn       | WR                |        61 |     -0.002 |     -0.048 |        -0.045 |         91 |        139 |
| Demarcus Robinson | WR                |        33 |      0.119 |      0.074 |        -0.045 |          2 |         11 |
| Kenneth Gainwell  | RB                |        30 |      0.113 |      0.074 |        -0.038 |          6 |         12 |
| Pat Freiermuth    | TE                |        39 |     -0.002 |     -0.041 |        -0.038 |         92 |        135 |
| Jameson Williams  | WR                |        33 |     -0.066 |     -0.104 |        -0.038 |        146 |        161 |
| Dawson Knox       | TE                |        31 |     -0.112 |     -0.148 |        -0.037 |        162 |        168 |
| Jalin Hyatt       | WR                |        33 |      0.081 |      0.047 |        -0.034 |         18 |         32 |
| Brandon Aiyuk     | WR                |        96 |      0.097 |      0.062 |        -0.034 |         12 |         19 |

## Biggest CROE lifts (leverage added credit)

Receivers who worked with tight leverage windows (low or negative ``leverage_margin``) get more credit — those catches were genuinely harder than the pre-leverage model realized.

| player_name        | player_position   |   targets |   croe_pre |   croe_now |   croe_change |   rank_pre |   rank_now |
|:-------------------|:------------------|----------:|-----------:|-----------:|--------------:|-----------:|-----------:|
| Donald Parham      | TE                |        38 |     -0.050 |      0.033 |         0.082 |        138 |         48 |
| Noah Gray          | TE                |        38 |     -0.028 |      0.029 |         0.056 |        122 |         56 |
| Isiah Pacheco      | RB                |        32 |      0.012 |      0.067 |         0.055 |         70 |         16 |
| Jonnu Smith        | TE                |        54 |     -0.038 |      0.017 |         0.055 |        130 |         68 |
| Luke Musgrave      | TE                |        37 |     -0.082 |     -0.029 |         0.053 |        154 |        124 |
| Garrett Wilson     | WR                |       137 |     -0.048 |      0.004 |         0.052 |        135 |         86 |
| Brandon Powell     | WR                |        38 |     -0.010 |      0.035 |         0.045 |        101 |         46 |
| Van Jefferson      | WR                |        35 |     -0.084 |     -0.040 |         0.043 |        157 |        134 |
| DeMario Douglas    | WR                |        52 |     -0.125 |     -0.084 |         0.041 |        166 |        154 |
| Jaxon Smith-Njigba | WR                |        62 |     -0.037 |      0.004 |         0.041 |        127 |         85 |
| Kyle Pitts         | TE                |        79 |     -0.038 |      0.001 |         0.039 |        131 |         90 |
| Jayden Reed        | WR                |        69 |      0.001 |      0.040 |         0.039 |         86 |         44 |

## New top 10

|   rank | player_name         | player_position   |   targets |   avg_crp |   avg_air_yards |   expected_catch_rate |   catch_rate |   croe_v2 |
|-------:|:--------------------|:------------------|----------:|----------:|----------------:|----------------------:|-------------:|----------:|
|      1 | DJ Moore            | WR                |       104 |     0.317 |          13.086 |                 0.623 |        0.740 |     0.117 |
|      2 | Tanner Hudson       | TE                |        44 |     0.240 |           6.318 |                 0.716 |        0.818 |     0.102 |
|      3 | Nico Collins        | WR                |        85 |     0.249 |          12.612 |                 0.664 |        0.765 |     0.101 |
|      4 | Michael Wilson      | WR                |        49 |     0.290 |          11.551 |                 0.620 |        0.714 |     0.094 |
|      5 | Christian McCaffrey | RB                |        57 |     0.116 |           3.368 |                 0.785 |        0.877 |     0.092 |
|      6 | Rachaad White       | RB                |        52 |     0.042 |           0.885 |                 0.838 |        0.923 |     0.085 |
|      7 | Allen Robinson      | WR                |        39 |     0.167 |           6.282 |                 0.736 |        0.821 |     0.085 |
|      8 | Michael Pittman     | WR                |       115 |     0.244 |           8.487 |                 0.684 |        0.765 |     0.081 |
|      9 | Justin Jefferson    | WR                |        85 |     0.302 |          13.541 |                 0.638 |        0.718 |     0.080 |
|     10 | Samaje Perine       | RB                |        44 |     0.035 |           0.750 |                 0.878 |        0.955 |     0.077 |

## Ship decision

**Ship with leverage.** The plan called for adopting leverage if the model improves; the improvement is large and consistent across dev/test and across all three calibration-quality metrics. Note that some checkdown-heavy RBs re-enter the top 20 with modest (~7%) CROE — that is the correct behavior once the model can see they had huge leverage: their over-performance is small but real, not spuriously large as in v1.
