# Backtest report

Out-of-sample predictions from 2020-21; test seasons 2023-24, 2024-25, 2025-26, 2026-27.
All choices below were made on seasons before 2023-24.

## 1. Choices made on pre-test data

Blend weight on Elo (tune seasons ['2021-22', '2022-23']): **0.5** (log loss 1.0082; Elo only 1.0108, Dixon-Coles only 1.0108)

Calibration choice: calibrators fitted on 2020-21..2022-23 (exclusive), scored on 2022-23 (7044 matches). Log loss:

| base | none | isotonic | platt |
|---|---|---|---|
| Elo | 1.0067 | 1.0088 | 1.0063 |
| Dixon-Coles | 1.0078 | 1.0103 | 1.0082 |
| Elo + Dixon-Coles blend | 1.0048 | 1.0062 | 1.0053 |

Gradient boosting (no odds), 2022-23: 1.0100
Bookmaker, 2022-23: 0.9874

Chosen calibration per base: {'elo': 'platt', 'dixon_coles': 'none', 'blend': 'none'}
**Pre-registered production model: Elo + Dixon-Coles blend (calibration: none)**

## 2. Test period: 2023-24, 2024-25, 2025-26, 2026-27 (23110 matches)

Overall (lower log loss / Brier is better):

| model | log loss | Brier | accuracy |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | 51.6% |
| Elo | 1.0092 | 0.6039 | 49.6% |
| Elo + Platt calibration | 1.0084 | 0.6035 | 49.7% |
| Dixon-Coles | 1.0115 | 0.6053 | 49.8% |
| Elo + Dixon-Coles blend **(production)** | 1.0078 | 0.6030 | 49.9% |
| Gradient boosting (no odds) | 1.0096 | 0.6041 | 49.7% |
| Gradient boosting (with odds) | 0.9933 | 0.5924 | 51.3% |

Log loss by league:

| league | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|
| ALL | nan | 1.0092 | 1.0084 | 1.0115 | 1.0078 | 1.0096 | 0.9933 |
| AUT | nan | 1.0308 | 1.0277 | 1.0308 | 1.0287 | 1.0272 | 1.0191 |
| B1 | nan | 1.0038 | 1.0014 | 1.0053 | 1.0021 | 1.0035 | 0.9947 |
| D1 | nan | 0.9897 | 0.9912 | 0.9933 | 0.9898 | 0.9920 | 0.9784 |
| D2 | nan | 1.0506 | 1.0507 | 1.0572 | 1.0519 | 1.0525 | 1.0444 |
| DNK | nan | 1.0218 | 1.0212 | 1.0254 | 1.0217 | 1.0236 | 1.0031 |
| E0 | nan | 0.9864 | 0.9855 | 0.9856 | 0.9839 | 0.9897 | 0.9692 |
| E1 | nan | 1.0460 | 1.0462 | 1.0471 | 1.0449 | 1.0506 | 1.0350 |
| F1 | nan | 0.9989 | 0.9981 | 1.0028 | 0.9989 | 1.0015 | 0.9830 |
| F2 | nan | 1.0698 | 1.0691 | 1.0714 | 1.0679 | 1.0704 | 1.0515 |
| G1 | nan | 0.9524 | 0.9502 | 0.9532 | 0.9494 | 0.9477 | 0.9306 |
| I1 | nan | 0.9785 | 0.9788 | 0.9799 | 0.9758 | 0.9801 | 0.9625 |
| I2 | nan | 1.0606 | 1.0616 | 1.0644 | 1.0597 | 1.0611 | 1.0376 |
| N1 | nan | 0.9623 | 0.9581 | 0.9654 | 0.9604 | 0.9580 | 0.9415 |
| NOR | nan | 0.9855 | 0.9887 | 0.9817 | 0.9815 | 0.9882 | 0.9683 |
| P1 | nan | 0.9318 | 0.9289 | 0.9380 | 0.9283 | 0.9288 | 0.9153 |
| POL | 1.0429 | 1.0532 | 1.0520 | 1.0547 | 1.0527 | 1.0542 | 1.0479 |
| ROU | 1.0156 | 1.0381 | 1.0364 | 1.0405 | 1.0371 | 1.0383 | 1.0194 |
| SC0 | nan | 0.9739 | 0.9699 | 0.9738 | 0.9712 | 0.9662 | 0.9536 |
| SP1 | nan | 0.9663 | 0.9671 | 0.9722 | 0.9669 | 0.9677 | 0.9536 |
| SP2 | nan | 1.0469 | 1.0459 | 1.0495 | 1.0461 | 1.0477 | 1.0271 |
| SWZ | 1.0189 | 1.0359 | 1.0362 | 1.0331 | 1.0321 | 1.0313 | 1.0198 |
| T1 | nan | 0.9728 | 0.9718 | 0.9777 | 0.9715 | 0.9737 | 0.9480 |

Log loss by season:

| season | n | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|---|
| 2023-24 | 7090 | 0.9822 | 1.0015 | 1.0019 | 1.0059 | 1.0013 | 1.0034 | 0.9837 |
| 2024-25 | 6960 | 0.9901 | 1.0121 | 1.0102 | 1.0128 | 1.0098 | 1.0121 | 0.9933 |
| 2025-26 | 6929 | 0.9987 | 1.0182 | 1.0172 | 1.0199 | 1.0166 | 1.0176 | 1.0008 |
| 2026-27 | 2131 | nan | 0.9960 | 0.9960 | 0.9981 | 0.9939 | 0.9957 | 1.0004 |

Gap to the bookmaker (model minus bookmaker log loss; negative = model better), 95% CI from a bootstrap over weeks:

- Elo: +nan  [+0.0182, +0.0229]
- Elo + Platt calibration: +nan  [+0.0173, +0.0221]
- Dixon-Coles: +nan  [+0.0204, +0.0252]
- Elo + Dixon-Coles blend: +nan  [+0.0168, +0.0213]
- Gradient boosting (no odds): +nan  [+0.0185, +0.0234]
- Gradient boosting (with odds): +nan  [+0.0013, +0.0032]

By bookmaker odds source (the benchmark is weaker where Pinnacle closing odds are missing):

| odds source | n | bookmaker | Elo + Dixon-Coles blend | gap |
|---|---|---|---|---|
| avg_closing | 5999 | 0.9926 | 1.0122 | +0.0196 |
| pinnacle_closing | 16963 | 0.9878 | 1.0068 | +0.0190 |

Matches involving a newly promoted team:

| subset | n | bookmaker | Elo | Dixon-Coles | Elo + Dixon-Coles blend |
|---|---|---|---|---|---|
| others | 15326 | nan | 1.0057 | 1.0072 | 1.0045 |
| promoted team | 7784 | nan | 1.0162 | 1.0198 | 1.0142 |

## 3. Calibration on the test period

Expected calibration error (count-weighted |predicted - observed|, 10 bins):

| model | home | draw | away |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | nan |
| Dixon-Coles | 0.0069 | 0.0135 | 0.0118 |
| Elo | 0.0106 | 0.0032 | 0.0106 |
| Elo + Dixon-Coles blend | 0.0062 | 0.0052 | 0.0095 |

Reliability table, Elo + Dixon-Coles blend (bins with n >= 30):

| outcome | bin | n | mean predicted | observed |
|---|---|---|---|---|
| home | 0.0-0.1 | 235 | 0.081 | 0.098 |
| home | 0.1-0.2 | 1298 | 0.157 | 0.150 |
| home | 0.2-0.3 | 2778 | 0.257 | 0.264 |
| home | 0.3-0.4 | 5564 | 0.354 | 0.360 |
| home | 0.4-0.5 | 6199 | 0.448 | 0.449 |
| home | 0.5-0.6 | 3850 | 0.544 | 0.539 |
| home | 0.6-0.7 | 1869 | 0.642 | 0.658 |
| home | 0.7-0.8 | 883 | 0.747 | 0.775 |
| home | 0.8-0.9 | 406 | 0.839 | 0.842 |
| draw | 0.0-0.1 | 163 | 0.082 | 0.086 |
| draw | 0.1-0.2 | 2235 | 0.164 | 0.161 |
| draw | 0.2-0.3 | 17797 | 0.261 | 0.267 |
| draw | 0.3-0.4 | 2915 | 0.314 | 0.313 |
| away | 0.0-0.1 | 1022 | 0.070 | 0.051 |
| away | 0.1-0.2 | 3818 | 0.159 | 0.148 |
| away | 0.2-0.3 | 7460 | 0.252 | 0.251 |
| away | 0.3-0.4 | 5769 | 0.345 | 0.334 |
| away | 0.4-0.5 | 2737 | 0.443 | 0.428 |
| away | 0.5-0.6 | 1248 | 0.545 | 0.529 |
| away | 0.6-0.7 | 679 | 0.644 | 0.666 |
| away | 0.7-0.8 | 324 | 0.740 | 0.738 |
| away | 0.8-0.9 | 53 | 0.825 | 0.736 |

## 4. Goals markets (Dixon-Coles)

Calibration choice: fitted on 2020-21..2022-23 (exclusive), scored on 2022-23. Log loss:

| market | none | platt | isotonic | chosen |
|---|---|---|---|---|
| over_1_5 | 0.5685 | 0.5660 | 0.5668 | **platt** |
| over_2_5 | 0.6839 | 0.6812 | 0.6815 | **platt** |
| over_3_5 | 0.5827 | 0.5798 | 0.5801 | **platt** |
| btts | 0.6922 | 0.6887 | 0.6891 | **platt** |

Test period (23110 matches). Log loss (lower is better):

| market | baseline | model raw | model calibrated | bookmaker | calibration error raw -> calibrated |
|---|---|---|---|---|---|
| over_1_5 | 0.5434 | 0.5411 | 0.5387 | - | 0.0235 -> 0.0101 |
| over_2_5 | 0.6897 | 0.6851 | 0.6819 | 0.6713 | 0.0318 -> 0.0180 |
| over_3_5 | 0.6148 | 0.6102 | 0.6073 | - | 0.0239 -> 0.0146 |
| btts | 0.6893 | 0.6891 | 0.6858 | - | 0.0318 -> 0.0147 |

Over/under 2.5 vs bookmaker on 17921 matches: model 0.6820, bookmaker 0.6713, gap +0.0107 [+0.0089, +0.0125]

Calibrated: when the model gave at least X%, how often did it happen?

| market | side | min | n | avg predicted | happened |
|---|---|---|---|---|---|
| over_1_5 | over | 50% | 23110 | 75.5% | 76.5% |
| over_1_5 | over | 60% | 23086 | 75.5% | 76.5% |
| over_1_5 | over | 70% | 19770 | 76.8% | 77.6% |
| over_1_5 | over | 80% | 4398 | 82.6% | 83.8% |
| over_2_5 | over | 50% | 12718 | 56.3% | 58.2% |
| over_2_5 | over | 60% | 2532 | 63.8% | 66.2% |
| over_2_5 | over | 70% | 152 | 73.4% | 76.3% |
| over_2_5 | over | 80% | 8 | 81.0% | 87.5% |
| over_2_5 | under | 50% | 10392 | 55.1% | 53.4% |
| over_2_5 | under | 60% | 1233 | 62.5% | 57.9% |
| over_2_5 | under | 70% | 4 | 70.8% | 50.0% |
| over_3_5 | over | 50% | 122 | 53.8% | 49.2% |
| over_3_5 | over | 60% | 9 | 62.7% | 66.7% |
| over_3_5 | under | 50% | 22988 | 70.8% | 69.4% |
| over_3_5 | under | 60% | 21607 | 71.7% | 70.4% |
| over_3_5 | under | 70% | 13141 | 75.4% | 74.3% |
| over_3_5 | under | 80% | 1534 | 82.0% | 78.0% |
| btts | over | 50% | 17234 | 55.1% | 56.2% |
| btts | over | 60% | 1607 | 62.0% | 62.4% |
| btts | over | 70% | 7 | 72.3% | 42.9% |
| btts | under | 50% | 5876 | 52.7% | 50.2% |
| btts | under | 60% | 45 | 61.2% | 53.3% |

Production calibrators ({'over_1_5': 'platt', 'over_2_5': 'platt', 'over_3_5': 'platt', 'btts': 'platt'}) fitted on 44345 out-of-sample matches -> data/models/goals_calibration.json

## 5. Asian handicap (main line), test period

23110 matches. Home side, stake-weighted: predicted win/push/lose 43.3% / 13.6% / 43.1%, actual 43.4% / 14.1% / 42.5%.
Average profit per unit at our own fair odds: -0.001 (0 = calibrated; negative = we were too optimistic).

| our chance | bets | avg chance | won | push | lost | profit at fair odds |
|---|---|---|---|---|---|---|
| <45% | 105 | 44.6% | 26.7% | 28.6% | 44.8% | -0.117 |
| 45-50% | 23005 | 48.1% | 40.7% | 14.0% | 45.3% | -0.014 |
| 50-55% | 23005 | 51.9% | 45.3% | 14.0% | 40.7% | +0.013 |
| 55-60% | 104 | 55.3% | 44.2% | 28.8% | 26.9% | +0.087 |
| 60%+ | 1 | 62.4% | 100.0% | 0.0% | 0.0% | +0.603 |

Against bookmaker closing AH odds, at the bookmaker's own line (16718 matches, pushes excluded). Log loss, lower is better:

| odds source | n | ours | bookmaker | gap |
|---|---|---|---|---|
| avg_closing | 4212 | 0.7122 | 0.6925 | +0.0196 |
| b365_closing | 1 | 1.0260 | 0.6545 | +0.3715 |
| pinnacle_closing | 12505 | 0.7107 | 0.6922 | +0.0184 |
| ALL | 16718 | 0.7111 | 0.6923 | +0.0188 [+0.0160, +0.0217] |

Backing our side whenever our fair odds beat the closing price (any edge): 13841 bets, avg odds 1.94, profit -504.8 units, ROI -3.6%

Backing our side whenever our fair odds beat the closing price (edge 5%+): 10006 bets, avg odds 1.95, profit -442.1 units, ROI -4.4%

## 6. Half-time result (check of the early-result method), test period

First-half share of goals, fitted before the test period: 0.4448. 17916 matches with half-time scores.
Log loss: model 1.0452 vs league-average baseline 1.0804; accuracy 44.7% vs 40.6%.
Half-time draws: predicted 41.4%, happened 40.6%.

| predicted HT draw | n | avg predicted | happened |
|---|---|---|---|
| 0.2-0.3 | 363 | 27.2% | 27.3% |
| 0.3-0.4 | 6149 | 36.9% | 36.3% |
| 0.4-0.5 | 10925 | 43.9% | 43.1% |
| 0.5-0.6 | 474 | 51.6% | 50.8% |

## 7. Derived markets (one consistent scoreline grid), test period

Baseline = each league's outcome frequencies in earlier seasons. Log loss, lower is better.

| market | n | model | baseline | gap | calibration error |
|---|---|---|---|---|---|
| Result & both teams score | 23110 | 1.6649 | 1.7357 | -0.0708 | 0.3 pts |
| Result & over/under 2.5 | 23110 | 1.6482 | 1.7188 | -0.0706 | 0.4 pts |
| Home team over/under 0.5 | 23110 | 0.5067 | 0.5308 | -0.0241 | 1.6 pts |
| Home team over/under 1.5 | 23110 | 0.6537 | 0.6871 | -0.0334 | 0.9 pts |
| Away team over/under 0.5 | 23110 | 0.5902 | 0.6106 | -0.0204 | 0.9 pts |
| Away team over/under 1.5 | 23110 | 0.6200 | 0.6470 | -0.0270 | 1.1 pts |
| Exact total goals | 23110 | 1.7184 | 1.7291 | -0.0107 | 0.3 pts |
| Odd/even goals | 23110 | 0.6932 | 0.6933 | -0.0000 | 0.8 pts |
| Half-time result | 17916 | 1.0439 | 1.0804 | -0.0365 | 0.3 pts |
| Half-time/full-time | 17916 | 1.8943 | 1.9689 | -0.0746 | 0.4 pts |
| 1st half over/under 0.5 | 17916 | 0.5978 | 0.6011 | -0.0033 | 1.7 pts |
| 1st half over/under 1.5 | 17916 | 0.6417 | 0.6459 | -0.0042 | 1.8 pts |
| Highest-scoring half | 17916 | 1.0717 | 1.0726 | -0.0008 | 0.5 pts |
| Home win to nil | 23110 | 0.5155 | 0.5411 | -0.0255 | 0.4 pts |
| Away win to nil | 23110 | 0.4054 | 0.4311 | -0.0257 | 1.0 pts |
