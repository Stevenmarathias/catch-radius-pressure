# CRP v2 — Methodology Upgrade

Following expert feedback on the v1 methodology, CRP has been substantially revised. This document explains what changed and why.

---

## Reviewer's feedback (summarized)

The v1 metric had four legitimate methodological gaps:

1. **CRP only measured defender information.** A play where the ball is thrown right at the receiver's chest was rated identically to a play where both receiver and defenders had to chase after it.
2. **Field coordinates were not standardized.** Plays going left→right and right→left were mixed together, making the heatmap ambiguous and making it impossible to see zone-specific patterns (like red zone vs. backed-up-in-own-territory).
3. **CROE (Catch Rate Over Expected) was picking up easy plays.** Running backs catching flat-route dumps ranked as elite "receivers" because their expected completion rate was low relative to their actual results — but they weren't doing anything hard.
4. **Pressure specialists were ambiguous.** A high average CRP faced could mean either "the QB trusts them in contested spots" or "they can't get open, so every throw to them looks contested." The metric didn't distinguish these.

---

## What changed in v2

### 1. Receiver context is now part of the metric

CRP v2 introduces a **receiver advantage factor** that captures whether the receiver has a positional or velocity edge at the catch point:

$$\text{CRP}_{v2} = \underbrace{\sum_{i \in D_R}\left(1 - \frac{d_i}{R}\right)(1 + v_i)}_{\text{defender pressure (v1)}} \cdot \underbrace{(1 - A_r)}_{\text{receiver advantage discount}}$$

Where the receiver advantage $A_r \in [0, 1]$ is:

$$A_r = 0.5 \cdot \max\left(0, \frac{d_{\text{nearest defender}} - d_{\text{receiver}}}{R}\right) + 0.5 \cdot \max\left(0, \frac{v_{\text{receiver toward ball}}}{v_{\text{max}}}\right)$$

**Interpretation:** A ball delivered right into a stationary defender's zone (receiver stuck yards away) now scores much higher than a ball delivered where the receiver has a clear route to it. Same defender configuration, different play difficulty — which is what actually matters.

### 2. Field coordinates are standardized

All plays are now flipped so the offense always attacks from left to right (x increasing toward the opponent's end zone). This is standard practice for tracking-data analysis but was missing in v1.

**Result:** The red zone (x = 90–110 after standardization) is now clearly the highest-pressure area, with **2× the average CRP of plays in one's own territory** — a signal that was previously washed out.

| Field Zone | Avg CRP v2 | Open % | High-Pressure % |
|------------|-----------|--------|-----------------|
| Own 20 (backed up) | 0.039 | 88.5% | 3.3% |
| Midfield | 0.076 | 81.3% | 6.3% |
| Opp Territory | 0.097 | 78.0% | 8.1% |
| Red Zone | **0.158** | **69.4%** | **14.6%** |

### 3. CROE is now position- and depth-adjusted

Expected catch rate now conditions on **both** CRP v2 **and** air yards (depth of target). Rankings are computed **within position groups** (WR / TE / RB) rather than league-wide.

**Result:** The top-15 WR list is now full of actual elite WRs — Justin Jefferson, DJ Moore, CeeDee Lamb, DeVonta Smith, Nico Collins. Samaje Perine still ranks as an elite pass-catching RB but no longer appears in the receiver leaderboard.

**Top 5 WRs by adjusted CROE:**

| Rank | Player | Targets | Avg Air Yards | Catch Rate | Expected | CROE |
|------|--------|---------|---------------|-----------|----------|------|
| 1 | Khalil Shakir | 39 | 17.1 | 84.6% | 68.4% | +16.2% |
| 2 | Brandon Aiyuk | 96 | 20.5 | 77.1% | 63.9% | +13.2% |
| 3 | Nico Collins | 85 | 19.7 | 76.5% | 64.8% | +11.7% |
| 4 | DeVonta Smith | 91 | 21.1 | 74.7% | 63.7% | +11.1% |
| 5 | DJ Moore | 104 | 20.6 | 74.0% | 63.5% | +10.6% |

### 4. Pressure specialists are decomposed

The single "avg CRP faced" ranking has been split into two categories based on whether the receiver **produces above expected** under that pressure:

- **Trusted under pressure** — top 30% CRP faced *and* positive CROE. These are receivers QBs trust in contested spots and who deliver.
- **Struggling separator** — top 30% CRP faced *and* negative CROE. These are receivers whose high CRP comes from an inability to separate, not from being trusted.

**Trusted under pressure (top 5):** Michael Thomas, DeVonta Smith, Jaylen Waddle, Puka Nacua, Jakobi Meyers  
**Struggling separators (top 5):** Michael Gallup, Alec Pierce, Trey Palmer, Marquise Brown, Quentin Johnston

The reviewer specifically flagged Quentin Johnston as a suspected struggling separator — the metric now confirms that classification.

---

## Distributional impact

| Metric | v1 (all plays) | v2 (all plays) |
|--------|---------------|----------------|
| Mean | 0.222 | 0.098 |
| Median | 0.000 | 0.000 |
| Max | 2.564 | 1.994 |
| % Open | 57.2% | 78.4% |
| % Extreme | 0.5% | 0.7% |

CRP v2 marks more plays as "Open" — because it now correctly identifies plays where a defender was in the radius but the receiver had a clear positional/velocity advantage. Extreme-pressure plays remain rare and continue to have the strongest link to completion outcomes.

---

## Files

- Metric: `crp/metric.py` — v2 implementation
- Field standardization: `crp/field.py`
- Rankings: `crp/rankings.py` — position-aware, depth-adjusted CROE + pressure specialist classification
- Data: `data/crp_v2_all_weeks.csv`, `data/crp_v2_merged.csv`, `data/receiver_rankings_v2.csv`
- Charts: `outputs/v2_*.png`
