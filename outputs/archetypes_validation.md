# Pass 3 archetype validation

Contested threshold: CRP ≥ **0.5**. Split medians (over 102 receivers with ≥ 8 contested targets): rate = 0.221, contested_croe = +0.0225. Low-sample display threshold: contested_targets ≥ **15** — 64 of 102 receivers pass and appear in headline panels; low-sample rows are kept in the CSV with `low_sample = True`.

## Named archetype panel

The plan calls four receivers as ground truth. This report is regenerated on every rebuild, so results reflect the current model:

- **DeAndre Hopkins** — contested_targets = 33, rate = 0.300, contested_croe = -0.051. Expected: Trusted contested winner. Landed: **Can't separate** ✗
- **Michael Thomas** — contested_targets = 20, rate = 0.357, contested_croe = +0.185. Expected: Trusted contested winner. Landed: **Trusted contested winner** ✓
- **Quentin Johnston** — contested_targets = 21, rate = 0.396, contested_croe = -0.157. Expected: Can't separate. Landed: **Can't separate** ✓
- **Justin Watson** *(low_sample)* — contested_targets = 11, rate = 0.244, contested_croe = +0.120. Expected: Can't separate. Landed: **Trusted contested winner** ✗

**2 / 4 named receivers landed where the plan expected.** Where they didn't: (a) Hopkins in 2023 was on Tennessee at age 31 — the "trusted contested winner" reputation attaches to his 2017–2020 peak, not the season we model; (b) Watson has a small contested sample and sits near the rate-median boundary — under the ≥ 15 low-sample threshold he now displays as *(low_sample)* rather than driving headline narratives. The two strongest exemplars (Thomas, Johnston) land cleanly.

| player_name      | player_position   |   targets |   contested_targets |   contested_target_rate |   contested_catch_rate |   contested_croe |   release_share |   median_sep_at_throw | quadrant                 |
|:-----------------|:------------------|----------:|--------------------:|------------------------:|-----------------------:|-----------------:|----------------:|----------------------:|:-------------------------|
| DeAndre Hopkins  | WR                |   110.000 |              33.000 |                   0.300 |                  0.424 |           -0.051 |           0.204 |                 2.444 | Can't separate           |
| Michael Thomas   | WR                |    56.000 |              20.000 |                   0.357 |                  0.600 |            0.185 |           0.204 |                 2.992 | Trusted contested winner |
| Justin Watson    | WR                |    45.000 |              11.000 |                   0.244 |                  0.545 |            0.120 |           0.148 |                 2.241 | Trusted contested winner |
| Quentin Johnston | WR                |    53.000 |              21.000 |                   0.396 |                  0.286 |           -0.157 |           0.238 |                 1.949 | Can't separate           |

## Extended reference panel

Other high-profile receivers whose profiles should match intuition.

| player_name       | player_position   |   targets |   contested_targets |   contested_target_rate |   contested_catch_rate |   contested_croe |   release_share |   median_sep_at_throw | quadrant                 |
|:------------------|:------------------|----------:|--------------------:|------------------------:|-----------------------:|-----------------:|----------------:|----------------------:|:-------------------------|
| Puka Nacua        | WR                |   128.000 |              29.000 |                   0.227 |                  0.690 |            0.167 |           0.143 |                 3.070 | Trusted contested winner |
| DJ Moore          | WR                |   104.000 |              32.000 |                   0.308 |                  0.656 |            0.161 |           0.174 |                 2.806 | Trusted contested winner |
| Amon-Ra St. Brown | WR                |   136.000 |              26.000 |                   0.191 |                  0.615 |            0.103 |           0.182 |                 2.863 | Efficient separator      |
| Mike Evans        | WR                |   118.000 |              24.000 |                   0.203 |                  0.500 |            0.092 |           0.088 |                 2.415 | Efficient separator      |
| Ja'Marr Chase     | WR                |   105.000 |              25.000 |                   0.238 |                  0.560 |            0.068 |           0.160 |                 3.411 | Trusted contested winner |
| Nico Collins      | WR                |    85.000 |              16.000 |                   0.188 |                  0.688 |            0.067 |           0.181 |                 2.329 | Efficient separator      |
| Justin Jefferson  | WR                |    85.000 |              27.000 |                   0.318 |                  0.481 |            0.026 |           0.113 |                 3.077 | Trusted contested winner |
| Terry McLaurin    | WR                |   109.000 |              37.000 |                   0.339 |                  0.460 |            0.022 |           0.182 |                 2.731 | Can't separate           |
| CeeDee Lamb       | WR                |   164.000 |              43.000 |                   0.262 |                  0.535 |            0.001 |           0.110 |                 2.552 | Can't separate           |
| Cooper Kupp       | WR                |    83.000 |              16.000 |                   0.193 |                  0.438 |           -0.018 |           0.124 |                 3.246 | Uncontested filler       |
| Davante Adams     | WR                |   150.000 |              23.000 |                   0.153 |                  0.478 |           -0.026 |           0.180 |                 2.663 | Uncontested filler       |
| A.J. Brown        | WR                |   136.000 |              28.000 |                   0.206 |                  0.429 |           -0.033 |           0.145 |                 2.908 | Uncontested filler       |

## Top of each quadrant (displayed rows only)

Filtered to `contested_targets ≥ 15`. Rows with between 8 and 14 contested targets carry a contested_croe in the CSV but are hidden from these tables.

### Trusted contested winner  (n = 21)

| player_name      | player_position   |   targets |   contested_targets |   contested_target_rate |   contested_catch_rate |   contested_croe |   release_share |   median_sep_at_throw | quadrant                 |
|:-----------------|:------------------|----------:|--------------------:|------------------------:|-----------------------:|-----------------:|----------------:|----------------------:|:-------------------------|
| Michael Thomas   | WR                |    56.000 |              20.000 |                   0.357 |                  0.600 |            0.185 |           0.204 |                 2.992 | Trusted contested winner |
| Puka Nacua       | WR                |   128.000 |              29.000 |                   0.227 |                  0.690 |            0.167 |           0.143 |                 3.070 | Trusted contested winner |
| DJ Moore         | WR                |   104.000 |              32.000 |                   0.308 |                  0.656 |            0.161 |           0.174 |                 2.806 | Trusted contested winner |
| Michael Pittman  | WR                |   115.000 |              26.000 |                   0.226 |                  0.615 |            0.155 |           0.367 |                 2.634 | Trusted contested winner |
| Calvin Ridley    | WR                |   111.000 |              26.000 |                   0.234 |                  0.654 |            0.138 |           0.155 |                 2.127 | Trusted contested winner |
| Hunter Henry     | TE                |    56.000 |              16.000 |                   0.286 |                  0.562 |            0.134 |           0.234 |                 2.724 | Trusted contested winner |
| Brandin Cooks    | WR                |    67.000 |              24.000 |                   0.358 |                  0.708 |            0.127 |           0.129 |                 2.810 | Trusted contested winner |
| Courtland Sutton | WR                |    81.000 |              20.000 |                   0.247 |                  0.550 |            0.096 |           0.126 |                 3.059 | Trusted contested winner |
| Chris Godwin Jr. | WR                |   103.000 |              23.000 |                   0.223 |                  0.609 |            0.091 |           0.205 |                 3.033 | Trusted contested winner |
| Michael Gallup   | WR                |    49.000 |              16.000 |                   0.327 |                  0.562 |            0.086 |           0.207 |                 2.070 | Trusted contested winner |

### Can't separate  (n = 20)

| player_name      | player_position   |   targets |   contested_targets |   contested_target_rate |   contested_catch_rate |   contested_croe |   release_share |   median_sep_at_throw | quadrant       |
|:-----------------|:------------------|----------:|--------------------:|------------------------:|-----------------------:|-----------------:|----------------:|----------------------:|:---------------|
| Alec Pierce      | WR                |    60.000 |              27.000 |                   0.450 |                  0.444 |           -0.060 |           0.165 |                 2.258 | Can't separate |
| Quentin Johnston | WR                |    53.000 |              21.000 |                   0.396 |                  0.286 |           -0.157 |           0.238 |                 1.949 | Can't separate |
| Marquise Brown   | WR                |    80.000 |              31.000 |                   0.388 |                  0.290 |           -0.143 |           0.256 |                 2.583 | Can't separate |
| DeVante Parker   | WR                |    47.000 |              17.000 |                   0.362 |                  0.471 |           -0.022 |           0.379 |                 2.302 | Can't separate |
| Terry McLaurin   | WR                |   109.000 |              37.000 |                   0.339 |                  0.460 |            0.022 |           0.182 |                 2.731 | Can't separate |
| Jakobi Meyers    | WR                |    88.000 |              27.000 |                   0.307 |                  0.333 |           -0.113 |           0.142 |                 2.956 | Can't separate |
| DeAndre Hopkins  | WR                |   110.000 |              33.000 |                   0.300 |                  0.424 |           -0.051 |           0.204 |                 2.444 | Can't separate |
| Tee Higgins      | WR                |    67.000 |              19.000 |                   0.284 |                  0.316 |           -0.145 |           0.087 |                 2.620 | Can't separate |
| Romeo Doubs      | WR                |    82.000 |              23.000 |                   0.281 |                  0.478 |            0.001 |           0.118 |                 2.623 | Can't separate |
| Garrett Wilson   | WR                |   137.000 |              38.000 |                   0.277 |                  0.421 |            0.014 |           0.220 |                 2.810 | Can't separate |

### Efficient separator  (n = 13)

| player_name       | player_position   |   targets |   contested_targets |   contested_target_rate |   contested_catch_rate |   contested_croe |   release_share |   median_sep_at_throw | quadrant            |
|:------------------|:------------------|----------:|--------------------:|------------------------:|-----------------------:|-----------------:|----------------:|----------------------:|:--------------------|
| Amon-Ra St. Brown | WR                |   136.000 |              26.000 |                   0.191 |                  0.615 |            0.103 |           0.182 |                 2.863 | Efficient separator |
| Keenan Allen      | WR                |   128.000 |              21.000 |                   0.164 |                  0.571 |            0.072 |           0.266 |                 3.046 | Efficient separator |
| Adam Thielen      | WR                |   122.000 |              25.000 |                   0.205 |                  0.640 |            0.114 |           0.213 |                 2.793 | Efficient separator |
| Chris Olave       | WR                |   121.000 |              23.000 |                   0.190 |                  0.478 |            0.065 |           0.121 |                 2.938 | Efficient separator |
| Mike Evans        | WR                |   118.000 |              24.000 |                   0.203 |                  0.500 |            0.092 |           0.088 |                 2.415 | Efficient separator |
| Evan Engram       | TE                |   112.000 |              16.000 |                   0.143 |                  0.688 |            0.099 |           0.184 |                 3.553 | Efficient separator |
| Sam LaPorta       | TE                |   112.000 |              19.000 |                   0.170 |                  0.579 |            0.099 |           0.259 |                 3.264 | Efficient separator |
| Tyler Lockett     | WR                |    97.000 |              21.000 |                   0.216 |                  0.619 |            0.087 |           0.110 |                 3.891 | Efficient separator |
| Brandon Aiyuk     | WR                |    96.000 |              20.000 |                   0.208 |                  0.550 |            0.072 |           0.107 |                 3.090 | Efficient separator |
| DeVonta Smith     | WR                |    91.000 |              19.000 |                   0.209 |                  0.526 |            0.133 |           0.133 |                 3.080 | Efficient separator |

### Uncontested filler  (n = 10)

| player_name    | player_position   |   targets |   contested_targets |   contested_target_rate |   contested_catch_rate |   contested_croe |   release_share |   median_sep_at_throw | quadrant           |
|:---------------|:------------------|----------:|--------------------:|------------------------:|-----------------------:|-----------------:|----------------:|----------------------:|:-------------------|
| Davante Adams  | WR                |   150.000 |              23.000 |                   0.153 |                  0.478 |           -0.026 |           0.180 |                 2.663 | Uncontested filler |
| A.J. Brown     | WR                |   136.000 |              28.000 |                   0.206 |                  0.429 |           -0.033 |           0.145 |                 2.908 | Uncontested filler |
| Tyreek Hill    | WR                |   128.000 |              28.000 |                   0.219 |                  0.500 |            0.002 |           0.119 |                 2.798 | Uncontested filler |
| T.J. Hockenson | TE                |   117.000 |              25.000 |                   0.214 |                  0.440 |           -0.149 |           0.147 |                 3.650 | Uncontested filler |
| Travis Kelce   | TE                |    96.000 |              16.000 |                   0.167 |                  0.438 |           -0.040 |           0.218 |                 3.500 | Uncontested filler |
| Jake Ferguson  | TE                |    87.000 |              18.000 |                   0.207 |                  0.500 |            0.001 |           0.177 |                 3.397 | Uncontested filler |
| Cooper Kupp    | WR                |    83.000 |              16.000 |                   0.193 |                  0.438 |           -0.018 |           0.124 |                 3.246 | Uncontested filler |
| George Kittle  | TE                |    83.000 |              16.000 |                   0.193 |                  0.625 |            0.014 |           0.160 |                 4.220 | Uncontested filler |
| Josh Downs     | WR                |    80.000 |              16.000 |                   0.200 |                  0.500 |           -0.021 |           0.185 |                 3.204 | Uncontested filler |
| Tyler Conklin  | TE                |    74.000 |              15.000 |                   0.203 |                  0.533 |           -0.090 |           0.404 |                 3.378 | Uncontested filler |
