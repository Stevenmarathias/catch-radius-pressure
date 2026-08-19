# Receiver leverage (Pass 2) — descriptive summary

Leverage margin = ``min_def_dist_arrival − rec_dist_to_ball`` (yards). Positive = ball is at the receiver, defender farther away; negative = defender is closer to the arrival point than the receiver is.

## Distribution overall

|       |   rec_dist_to_ball |   rec_closing_v |   leverage_margin |
|:------|-------------------:|----------------:|------------------:|
| count |          14108.000 |       14108.000 |         14107.000 |
| mean  |              1.593 |          -0.135 |             2.664 |
| std   |              1.648 |           0.399 |             3.422 |
| min   |              0.000 |          -0.990 |           -36.838 |
| 10%   |              0.379 |          -0.611 |            -0.342 |
| 25%   |              0.636 |          -0.443 |             0.584 |
| 50%   |              1.186 |          -0.195 |             1.830 |
| 75%   |              1.981 |           0.132 |             3.946 |
| 90%   |              3.080 |           0.476 |             7.179 |
| max   |             50.979 |           0.984 |            21.918 |

Share of plays with negative leverage_margin: **13.8%** (defender was closer to arrival than the receiver).

## By pass depth

| depth_bin   |        n |   median_leverage |   mean_leverage |   pct_negative |   catch_rate |
|:------------|---------:|------------------:|----------------:|---------------:|-------------:|
| <0          | 1088.000 |             7.830 |           7.946 |          0.014 |        0.877 |
| 0–4         | 4061.000 |             2.954 |           3.722 |          0.054 |        0.805 |
| 5–9         | 3911.000 |             1.618 |           2.018 |          0.107 |        0.726 |
| 10–14       | 1869.000 |             1.116 |           1.414 |          0.189 |        0.611 |
| 15–19       | 1355.000 |             1.134 |           1.488 |          0.232 |        0.599 |
| 20+         | 1822.000 |             0.549 |           0.698 |          0.343 |        0.398 |

## By receiver position (WR/TE/RB/FB)

| player_position   |        n |   median_leverage |   mean_leverage |   pct_negative |   catch_rate |
|:------------------|---------:|------------------:|----------------:|---------------:|-------------:|
| FB                |   77.000 |             4.459 |           4.831 |          0.013 |        0.844 |
| RB                | 2111.000 |             4.903 |           5.676 |          0.032 |        0.797 |
| TE                | 3249.000 |             2.068 |           2.933 |          0.114 |        0.737 |
| WR                | 8611.000 |             1.339 |           1.801 |          0.175 |        0.644 |

## Catch rate by leverage decile

|   decile |        n |   mean_leverage |   catch_rate |
|---------:|---------:|----------------:|-------------:|
|        0 | 1377.000 |          -1.467 |        0.255 |
|        1 | 1377.000 |           0.169 |        0.408 |
|        2 | 1377.000 |           0.646 |        0.574 |
|        3 | 1377.000 |           1.086 |        0.688 |
|        4 | 1377.000 |           1.605 |        0.748 |
|        5 | 1377.000 |           2.233 |        0.841 |
|        6 | 1377.000 |           3.001 |        0.857 |
|        7 | 1377.000 |           4.035 |        0.871 |
|        8 | 1377.000 |           5.839 |        0.911 |
|        9 | 1377.000 |          10.434 |        0.917 |
