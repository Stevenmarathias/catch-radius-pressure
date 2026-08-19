# CROE v3 validation report (vs v1)

Compared **v1** (168 ranked players) with **v3** (168 ranked players); 168 players appear on both leaderboards (min 30 targets in each). v3 = v2 feature set + `is_red_zone` per Pass 4.

## Rank-order agreement

- **Spearman rho** = 0.699 (p = 5.75e-26)
- **Kendall tau** = 0.506 (p = 2.17e-22)

A moderate positive correlation is expected: v3 preserves the broad ordering of receiver skill (good hands stay good hands) but re-shuffles the volume-of-checkdowns tail that v1 over-credited.

## Biggest fallers (v1 → v3)

If v3 is doing its job, plays with low CRP *and* short air yards should no longer earn much CROE, so RB checkdown specialists should fall.

| player_name       | player_position   |   targets |   avg_crp |   avg_air_yards |   rank_v1 |   rank_v3 |   rank_change |   croe_v1 |   croe_v3 |
|:------------------|:------------------|----------:|----------:|----------------:|----------:|----------:|--------------:|----------:|----------:|
| Austin Hooper     | TE                |        30 |     0.100 |           4.367 |        38 |       130 |           -92 |     0.060 |    -0.034 |
| Ezekiel Elliott   | RB                |        34 |     0.148 |           1.735 |        59 |       144 |           -85 |     0.037 |    -0.053 |
| Joe Mixon         | RB                |        39 |     0.045 |          -1.077 |        75 |       157 |           -82 |     0.018 |    -0.086 |
| Zach Charbonnet   | RB                |        33 |     0.048 |          -0.151 |        46 |       126 |           -80 |     0.050 |    -0.032 |
| Isaiah Likely     | TE                |        35 |     0.153 |           7.571 |        48 |       123 |           -75 |     0.049 |    -0.027 |
| Breece Hall       | RB                |        58 |     0.057 |           1.172 |        43 |       117 |           -74 |     0.053 |    -0.018 |
| Jaylen Warren     | RB                |        42 |     0.103 |          -0.643 |        15 |        89 |           -74 |     0.106 |     0.002 |
| Wan'Dale Robinson | WR                |        62 |     0.090 |           5.823 |        52 |       125 |           -73 |     0.044 |    -0.031 |
| Javonte Williams  | RB                |        41 |     0.008 |          -0.366 |        66 |       133 |           -67 |     0.031 |    -0.038 |
| George Kittle     | TE                |        83 |     0.213 |           9.783 |        54 |       119 |           -65 |     0.043 |    -0.021 |
| Pat Freiermuth    | TE                |        39 |     0.202 |           7.487 |        70 |       135 |           -65 |     0.025 |    -0.041 |
| Chig Okonkwo      | TE                |        60 |     0.192 |           7.967 |        57 |       118 |           -61 |     0.042 |    -0.019 |
| Travis Etienne    | RB                |        40 |     0.064 |           1.850 |        17 |        74 |           -57 |     0.103 |     0.014 |
| Michael Mayer     | TE                |        36 |     0.160 |           6.167 |        64 |       120 |           -56 |     0.033 |    -0.022 |
| Josh Jacobs       | RB                |        37 |     0.059 |           1.540 |        95 |       147 |           -52 |    -0.008 |    -0.059 |

## Biggest risers (v1 → v3)

Receivers who worked with high CRP and/or high air yards should get more credit under v3.

| player_name      | player_position   |   targets |   avg_crp |   avg_air_yards |   rank_v1 |   rank_v3 |   rank_change |   croe_v1 |   croe_v3 |
|:-----------------|:------------------|----------:|----------:|----------------:|----------:|----------:|--------------:|----------:|----------:|
| Jalen Tolbert    | WR                |        30 |     0.262 |          14.233 |       119 |        17 |           102 |    -0.039 |     0.064 |
| Odell Beckham    | WR                |        55 |     0.230 |          13.491 |       137 |        49 |            88 |    -0.059 |     0.033 |
| Mike Evans       | WR                |       118 |     0.271 |          14.432 |       115 |        33 |            82 |    -0.028 |     0.047 |
| Drake London     | WR                |        96 |     0.265 |          12.135 |        97 |        23 |            74 |    -0.009 |     0.059 |
| Jayden Reed      | WR                |        69 |     0.206 |          13.217 |       118 |        44 |            74 |    -0.038 |     0.040 |
| Gabe Davis       | WR                |        65 |     0.260 |          14.662 |       120 |        54 |            66 |    -0.039 |     0.029 |
| Kendrick Bourne  | WR                |        45 |     0.195 |          11.933 |        77 |        14 |            63 |     0.018 |     0.069 |
| Jalin Hyatt      | WR                |        33 |     0.396 |          19.576 |        93 |        32 |            61 |    -0.006 |     0.047 |
| Chris Godwin Jr. | WR                |       103 |     0.240 |          10.408 |        90 |        31 |            59 |    -0.003 |     0.047 |
| Amari Cooper     | WR                |       107 |     0.339 |          13.561 |        79 |        21 |            58 |     0.015 |     0.060 |
| George Pickens   | WR                |        88 |     0.289 |          12.954 |        92 |        34 |            58 |    -0.004 |     0.046 |
| Brandon Powell   | WR                |        38 |     0.239 |           9.026 |       104 |        46 |            58 |    -0.017 |     0.035 |
| Josh Palmer      | WR                |        49 |     0.318 |          12.286 |       107 |        50 |            57 |    -0.022 |     0.031 |
| Isaiah Hodgins   | WR                |        32 |     0.275 |           8.375 |       106 |        52 |            54 |    -0.021 |     0.030 |
| Calvin Ridley    | WR                |       111 |     0.269 |          13.802 |       147 |        93 |            54 |    -0.092 |    -0.000 |

## Face-validity panel: should fall

Named in the plan — RB / gadget-QB checkdown profiles. Expected: middling CROE v3, large negative rank_change.

| player_name      | player_position   |   targets |   avg_crp |   avg_air_yards |   rank_v1 |   rank_v3 |   rank_change |   croe_v1 |   croe_v3 |   croe_change |
|:-----------------|:------------------|----------:|----------:|----------------:|----------:|----------:|--------------:|----------:|----------:|--------------:|
| Taysom Hill      | QB                |        35 |     0.243 |           5.743 |         1 |        45 |           -44 |     0.180 |     0.036 |        -0.144 |
| Samaje Perine    | RB                |        44 |     0.035 |           0.750 |         2 |        10 |            -8 |     0.179 |     0.077 |        -0.102 |
| Chuba Hubbard    | RB                |        38 |     0.025 |          -0.579 |         3 |        22 |           -19 |     0.162 |     0.059 |        -0.103 |
| Kenneth Gainwell | RB                |        30 |     0.041 |           1.500 |         4 |        12 |            -8 |     0.159 |     0.074 |        -0.084 |
| Rachaad White    | RB                |        52 |     0.042 |           0.885 |         6 |         6 |             0 |     0.145 |     0.085 |        -0.060 |
| James Cook       | RB                |        42 |     0.125 |           4.048 |        29 |        73 |           -44 |     0.075 |     0.014 |        -0.061 |

## Face-validity panel: should hold or rise

Named in the plan and generally known contested-catch receivers. Expected: positive rank_change or unchanged near the top.

| player_name       | player_position   |   targets |   avg_crp |   avg_air_yards |   rank_v1 |   rank_v3 |   rank_change |   croe_v1 |   croe_v3 |   croe_change |
|:------------------|:------------------|----------:|----------:|----------------:|----------:|----------:|--------------:|----------:|----------:|--------------:|
| CeeDee Lamb       | WR                |       164 |     0.262 |          10.268 |        24 |        13 |            11 |     0.078 |     0.072 |        -0.006 |
| Nico Collins      | WR                |        85 |     0.249 |          12.612 |        26 |         3 |            23 |     0.076 |     0.101 |         0.024 |
| DJ Moore          | WR                |       104 |     0.317 |          13.086 |        30 |         1 |            29 |     0.069 |     0.117 |         0.048 |
| A.J. Brown        | WR                |       136 |     0.257 |          11.750 |        49 |        30 |            19 |     0.048 |     0.048 |         0.000 |
| Amon-Ra St. Brown | WR                |       136 |     0.230 |           9.441 |        50 |        55 |            -5 |     0.048 |     0.029 |        -0.019 |
| Justin Jefferson  | WR                |        85 |     0.302 |          13.541 |        55 |         9 |            46 |     0.042 |     0.080 |         0.038 |
| Michael Thomas    | WR                |        56 |     0.365 |           9.875 |        58 |        42 |            16 |     0.040 |     0.041 |         0.001 |
| Ja'Marr Chase     | WR                |       105 |     0.274 |          11.067 |        99 |       102 |            -3 |    -0.013 |    -0.006 |         0.007 |
| Cooper Kupp       | WR                |        83 |     0.209 |           9.048 |       130 |       111 |            19 |    -0.049 |    -0.013 |         0.036 |
| DeAndre Hopkins   | WR                |       110 |     0.325 |          14.700 |       134 |       122 |            12 |    -0.053 |    -0.024 |         0.029 |

## v1 top 10 → v3 rank

| player_name         | player_position   |   targets |   avg_crp |   avg_air_yards |   rank_v1 |   rank_v3 |   rank_change |   croe_v1 |   croe_v3 |
|:--------------------|:------------------|----------:|----------:|----------------:|----------:|----------:|--------------:|----------:|----------:|
| Taysom Hill         | QB                |        35 |     0.243 |           5.743 |         1 |        45 |           -44 |     0.180 |     0.036 |
| Samaje Perine       | RB                |        44 |     0.035 |           0.750 |         2 |        10 |            -8 |     0.179 |     0.077 |
| Chuba Hubbard       | RB                |        38 |     0.025 |          -0.579 |         3 |        22 |           -19 |     0.162 |     0.059 |
| Kenneth Gainwell    | RB                |        30 |     0.041 |           1.500 |         4 |        12 |            -8 |     0.159 |     0.074 |
| Najee Harris        | RB                |        30 |     0.111 |           0.733 |         5 |        28 |           -23 |     0.150 |     0.053 |
| Rachaad White       | RB                |        52 |     0.042 |           0.885 |         6 |         6 |             0 |     0.145 |     0.085 |
| Khalil Shakir       | WR                |        39 |     0.200 |          10.282 |         7 |        20 |           -13 |     0.138 |     0.061 |
| Christian McCaffrey | RB                |        57 |     0.116 |           3.368 |         8 |         5 |             3 |     0.137 |     0.092 |
| Antonio Gibson      | RB                |        41 |     0.070 |           1.732 |         9 |        15 |            -6 |     0.129 |     0.068 |
| Cole Kmet           | TE                |        76 |     0.177 |           6.947 |        10 |        18 |            -8 |     0.123 |     0.063 |

## v3 top 10 → v1 rank

| player_name         | player_position   |   targets |   avg_crp |   avg_air_yards |   rank_v1 |   rank_v3 |   rank_change |   croe_v1 |   croe_v3 |
|:--------------------|:------------------|----------:|----------:|----------------:|----------:|----------:|--------------:|----------:|----------:|
| DJ Moore            | WR                |       104 |     0.317 |          13.086 |        30 |         1 |            29 |     0.069 |     0.117 |
| Tanner Hudson       | TE                |        44 |     0.240 |           6.318 |        12 |         2 |            10 |     0.118 |     0.102 |
| Nico Collins        | WR                |        85 |     0.249 |          12.612 |        26 |         3 |            23 |     0.076 |     0.101 |
| Michael Wilson      | WR                |        49 |     0.290 |          11.551 |        44 |         4 |            40 |     0.053 |     0.094 |
| Christian McCaffrey | RB                |        57 |     0.116 |           3.368 |         8 |         5 |             3 |     0.137 |     0.092 |
| Rachaad White       | RB                |        52 |     0.042 |           0.885 |         6 |         6 |             0 |     0.145 |     0.085 |
| Allen Robinson      | WR                |        39 |     0.167 |           6.282 |        18 |         7 |            11 |     0.100 |     0.085 |
| Michael Pittman     | WR                |       115 |     0.244 |           8.487 |        28 |         8 |            20 |     0.075 |     0.081 |
| Justin Jefferson    | WR                |        85 |     0.302 |          13.541 |        55 |         9 |            46 |     0.042 |     0.080 |
| Samaje Perine       | RB                |        44 |     0.035 |           0.750 |         2 |        10 |            -8 |     0.179 |     0.077 |
