# Catch Radius Pressure (CRP)
### NFL Big Data Bowl 2026 — Analytics Track

> **Quantifying defensive pressure at the catch point across 14,108 passing plays from the 2023 NFL season.**

---

## The Problem

Traditional passing metrics — completion percentage, yards after catch, EPA — tell us *what happened*. They don't tell us *how hard it was*. A receiver making a catch while wide open is evaluated the same as one fighting through traffic with two defenders closing in.

**Catch Radius Pressure (CRP)** fills this gap.

---

## What is CRP?

CRP measures how much defensive pressure exists at the exact field location where the ball arrives. For every passing play, it answers: *how crowded and contested was the catch point when the ball got there?*

### Formula

$$\text{CRP} = \sum_{i \in D_R} \left(1 - \frac{d_i}{R}\right) \cdot (1 + v_i)$$

| Variable | Definition |
|----------|-----------|
| $D_R$ | Set of defenders within catch radius $R$ |
| $d_i$ | Distance (yards) from defender $i$ to ball landing spot |
| $v_i$ | Velocity of defender $i$ toward the ball (yards/frame), floored at 0 |
| $R$ | Catch radius — default **3.0 yards** |

**Intuition:** A defender right at the catch point, sprinting toward it, contributes maximum pressure. A defender drifting toward the edge of the radius contributes nearly nothing.

### CRP Labels

| Score | Label |
|-------|-------|
| 0 | Open |
| 0 – 0.5 | Low Pressure |
| 0.5 – 1.0 | Moderate Pressure |
| 1.0 – 1.5 | High Pressure |
| > 1.5 | Extreme Pressure |

---

## Key Findings

| Finding | Stat |
|---------|------|
| Completion rate, Open plays | **79.6%** |
| Completion rate, High Pressure | **45.6%** |
| Completion rate, Extreme Pressure | **37.5%** |
| Coverage with highest avg CRP | COVER_1_MAN (0.304) |
| Route with highest avg CRP | GO route (0.477) |
| Season max CRP | **2.56** |

Man coverage generates significantly more catch-point pressure than zone. GO routes face the most pressure; HITCH and OUT routes see the least — consistent with how offensive coordinators design quick-game and West Coast systems to attack soft zone.

---

## Project Structure

```
catch-radius-pressure/
├── crp/
│   ├── __init__.py          # Public API
│   ├── metric.py            # CRP formula & batch computation
│   ├── data_loader.py       # Data loading utilities
│   └── visualizations.py   # Field plots, heatmaps, distributions
├── notebooks/
│   └── crp_analysis.ipynb  # Full analysis walkthrough
├── scripts/
│   └── compute_crp.py      # CLI: regenerate CRP from raw data
├── data/
│   ├── crp_all_weeks.csv   # Pre-computed CRP, all 14,108 plays
│   ├── crp_merged.csv      # CRP + supplementary play metadata
│   └── crp_w01.csv … w18   # Per-week CRP files
├── outputs/
│   ├── 01_crp_distribution.png
│   ├── 02_crp_vs_completion.png
│   ├── 03_crp_heatmap.png
│   ├── 04_crp_by_coverage.png
│   ├── 05_example_play_high_crp.png
│   └── 06_example_play_low_crp.png
└── requirements.txt
```

---

## Getting Started

### Option A: Google Colab (zero setup)

1. Open [Google Colab](https://colab.research.google.com)
2. Upload `catch_radius_pressure_project.zip` to the Colab session
3. Run in a cell: `!unzip -q catch_radius_pressure_project.zip -d /content/`
4. Open `notebooks/crp_analysis_colab.ipynb` and run all cells

The Colab notebook handles path setup, dependencies, and data location automatically.

### Option B: Local Setup

#### 1. Install dependencies
```bash
pip install -r requirements.txt
```

#### 2. Set up data

Place the competition data folder inside `data/`:
```
data/114239_nfl_competition_files_published_analytics_final/
    supplementary_data.csv
    train/
        input_2023_w01.csv
        output_2023_w01.csv
        ...
```

Pre-computed CRP files (`crp_all_weeks.csv`, `crp_merged.csv`) are included — you can use these directly without reprocessing.

#### 3. Recompute CRP (optional)
```bash
python scripts/compute_crp.py
# or with explicit path:
python scripts/compute_crp.py --data_dir /path/to/competition/data
```

#### 4. Run the analysis notebook
```bash
cd notebooks
jupyter notebook crp_analysis.ipynb
```

---

## API Reference

```python
from crp import compute_crp_for_play, compute_crp_dataset, load_week

# Single play
result = compute_crp_for_play(defenders_df, ball_land_x, ball_land_y)
print(result['crp'])                   # float
print(result['n_defenders'])           # int
print(result['defender_contributions']) # list of dicts

# Full week batch
df_in, df_out = load_week(week=1)
df_crp = compute_crp_dataset(df_in, df_out)
# Returns DataFrame: game_id, play_id, crp, n_defenders_in_radius, ...
```

---

## Visualizations

All figures are in `outputs/`. Key charts:

**CRP Distribution** — Right-skewed; ~57% of plays are Open (no defender in radius)

**CRP vs Completion Rate** — Monotonic relationship: higher pressure = lower completion rate

**Field Heatmap** — Pressure concentrates at sidelines and in the red zone

**Coverage Analysis** — Man coverage generates more catch-point pressure than zone

---

## Future Work

- **Receiver grades**: Compare each receiver's actual catch rate vs expected given CRP exposure
- **QB bravery index**: Do quarterbacks throw into contested windows or take the safe option?
- **Temporal CRP**: Animate how pressure builds frame-by-frame during ball flight
- **Team-level coverage efficiency**: Which defenses generate the most CRP per play called?

---

## Data

Competition data provided by the NFL via the [Big Data Bowl 2026](https://www.kaggle.com/competitions/nfl-big-data-bowl-2026).  
2023 NFL season tracking data: Weeks 1–18.

---

*NFL Big Data Bowl 2026 | Analytics Track*
