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

## 2. Test period: 2023-24, 2024-25, 2025-26, 2026-27 (23323 matches)

Overall (lower log loss / Brier is better):

| model | log loss | Brier | accuracy |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | 51.6% |
| Elo | 1.0085 | 0.6034 | 49.7% |
| Elo + Platt calibration | 1.0078 | 0.6030 | 49.8% |
| Dixon-Coles | 1.0109 | 0.6049 | 49.9% |
| Elo + Dixon-Coles blend **(production)** | 1.0071 | 0.6025 | 50.0% |
| Gradient boosting (no odds) | 1.0089 | 0.6036 | 49.7% |
| Gradient boosting (with odds) | 0.9956 | 0.5935 | 51.3% |

Log loss by league:

| league | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|
| ALL | nan | 1.0085 | 1.0078 | 1.0109 | 1.0071 | 1.0089 | 0.9956 |
| AUT | nan | 1.0293 | 1.0263 | 1.0293 | 1.0272 | 1.0258 | 1.0169 |
| B1 | nan | 1.0026 | 1.0003 | 1.0042 | 1.0010 | 1.0023 | 0.9938 |
| D1 | nan | 0.9862 | 0.9880 | 0.9901 | 0.9865 | 0.9890 | 0.9718 |
| D2 | nan | 1.0500 | 1.0502 | 1.0562 | 1.0511 | 1.0514 | 1.0438 |
| DNK | nan | 1.0200 | 1.0196 | 1.0240 | 1.0201 | 1.0224 | 1.0083 |
| E0 | nan | 0.9861 | 0.9852 | 0.9855 | 0.9837 | 0.9894 | 0.9698 |
| E1 | nan | 1.0469 | 1.0469 | 1.0479 | 1.0457 | 1.0512 | 1.0330 |
| F1 | nan | 0.9989 | 0.9982 | 1.0026 | 0.9988 | 1.0012 | 0.9925 |
| F2 | nan | 1.0693 | 1.0684 | 1.0709 | 1.0674 | 1.0698 | 1.0446 |
| G1 | nan | 0.9510 | 0.9492 | 0.9530 | 0.9486 | 0.9471 | 0.9375 |
| I1 | nan | 0.9787 | 0.9791 | 0.9807 | 0.9763 | 0.9803 | 0.9689 |
| I2 | nan | 1.0606 | 1.0618 | 1.0648 | 1.0598 | 1.0611 | 1.0460 |
| N1 | nan | 0.9635 | 0.9593 | 0.9661 | 0.9613 | 0.9587 | 0.9526 |
| NOR | nan | 0.9837 | 0.9868 | 0.9801 | 0.9797 | 0.9864 | 0.9667 |
| P1 | nan | 0.9297 | 0.9270 | 0.9364 | 0.9265 | 0.9274 | 0.9211 |
| POL | 1.0424 | 1.0523 | 1.0511 | 1.0537 | 1.0517 | 1.0533 | 1.0474 |
| ROU | 1.0139 | 1.0362 | 1.0346 | 1.0385 | 1.0352 | 1.0362 | 1.0176 |
| SC0 | nan | 0.9739 | 0.9701 | 0.9734 | 0.9711 | 0.9660 | 0.9630 |
| SP1 | nan | 0.9661 | 0.9670 | 0.9722 | 0.9667 | 0.9676 | 0.9624 |
| SP2 | nan | 1.0464 | 1.0455 | 1.0489 | 1.0456 | 1.0472 | 1.0303 |
| SWZ | 1.0203 | 1.0365 | 1.0368 | 1.0342 | 1.0330 | 1.0322 | 1.0208 |
| T1 | nan | 0.9706 | 0.9698 | 0.9765 | 0.9698 | 0.9721 | 0.9475 |

Log loss by season:

| season | n | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|---|
| 2023-24 | 7090 | 0.9822 | 1.0015 | 1.0019 | 1.0059 | 1.0013 | 1.0034 | 0.9837 |
| 2024-25 | 6960 | 0.9901 | 1.0121 | 1.0102 | 1.0128 | 1.0098 | 1.0121 | 0.9933 |
| 2025-26 | 6929 | 0.9987 | 1.0182 | 1.0172 | 1.0199 | 1.0166 | 1.0176 | 1.0008 |
| 2026-27 | 2344 | nan | 0.9902 | 0.9909 | 0.9939 | 0.9890 | 0.9905 | 1.0225 |

Gap to the bookmaker (model minus bookmaker log loss; negative = model better), 95% CI from a bootstrap over weeks:

- Elo: +nan  [+0.0181, +0.0229]
- Elo + Platt calibration: +nan  [+0.0174, +0.0221]
- Dixon-Coles: +nan  [+0.0204, +0.0250]
- Elo + Dixon-Coles blend: +nan  [+0.0169, +0.0212]
- Gradient boosting (no odds): +nan  [+0.0185, +0.0233]
- Gradient boosting (with odds): +nan  [+0.0012, +0.0031]

By bookmaker odds source (the benchmark is weaker where Pinnacle closing odds are missing):

| odds source | n | bookmaker | Elo + Dixon-Coles blend | gap |
|---|---|---|---|---|
| avg_closing | 6199 | 0.9909 | 1.0102 | +0.0193 |
| pinnacle_closing | 16963 | 0.9878 | 1.0068 | +0.0190 |

Matches involving a newly promoted team:

| subset | n | bookmaker | Elo | Dixon-Coles | Elo + Dixon-Coles blend |
|---|---|---|---|---|---|
| others | 15468 | nan | 1.0051 | 1.0067 | 1.0040 |
| promoted team | 7855 | nan | 1.0152 | 1.0192 | 1.0134 |

## 3. Calibration on the test period

Expected calibration error (count-weighted |predicted - observed|, 10 bins):

| model | home | draw | away |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | nan |
| Dixon-Coles | 0.0069 | 0.0130 | 0.0116 |
| Elo | 0.0102 | 0.0035 | 0.0103 |
| Elo + Dixon-Coles blend | 0.0058 | 0.0047 | 0.0094 |

Reliability table, Elo + Dixon-Coles blend (bins with n >= 30):

| outcome | bin | n | mean predicted | observed |
|---|---|---|---|---|
| home | 0.0-0.1 | 236 | 0.081 | 0.097 |
| home | 0.1-0.2 | 1309 | 0.157 | 0.150 |
| home | 0.2-0.3 | 2807 | 0.257 | 0.264 |
| home | 0.3-0.4 | 5619 | 0.354 | 0.360 |
| home | 0.4-0.5 | 6260 | 0.448 | 0.448 |
| home | 0.5-0.6 | 3877 | 0.544 | 0.541 |
| home | 0.6-0.7 | 1887 | 0.642 | 0.659 |
| home | 0.7-0.8 | 890 | 0.747 | 0.775 |
| home | 0.8-0.9 | 410 | 0.839 | 0.844 |
| draw | 0.0-0.1 | 163 | 0.082 | 0.086 |
| draw | 0.1-0.2 | 2257 | 0.164 | 0.160 |
| draw | 0.2-0.3 | 17971 | 0.261 | 0.267 |
| draw | 0.3-0.4 | 2932 | 0.314 | 0.313 |
| away | 0.0-0.1 | 1029 | 0.070 | 0.051 |
| away | 0.1-0.2 | 3852 | 0.159 | 0.148 |
| away | 0.2-0.3 | 7516 | 0.252 | 0.251 |
| away | 0.3-0.4 | 5831 | 0.345 | 0.334 |
| away | 0.4-0.5 | 2767 | 0.443 | 0.428 |
| away | 0.5-0.6 | 1265 | 0.545 | 0.530 |
| away | 0.6-0.7 | 684 | 0.644 | 0.668 |
| away | 0.7-0.8 | 325 | 0.740 | 0.738 |
| away | 0.8-0.9 | 54 | 0.825 | 0.741 |

## 4. Goals markets (Dixon-Coles)

Calibration choice: fitted on 2020-21..2022-23 (exclusive), scored on 2022-23. Log loss:

| market | none | platt | isotonic | chosen |
|---|---|---|---|---|
| over_1_5 | 0.5685 | 0.5660 | 0.5668 | **platt** |
| over_2_5 | 0.6839 | 0.6812 | 0.6815 | **platt** |
| over_3_5 | 0.5827 | 0.5798 | 0.5801 | **platt** |
| btts | 0.6922 | 0.6887 | 0.6891 | **platt** |

Test period (23323 matches). Log loss (lower is better):

| market | baseline | model raw | model calibrated | bookmaker | calibration error raw -> calibrated |
|---|---|---|---|---|---|
| over_1_5 | 0.5432 | 0.5411 | 0.5386 | - | 0.0239 -> 0.0102 |
| over_2_5 | 0.6897 | 0.6851 | 0.6819 | 0.6714 | 0.0321 -> 0.0182 |
| over_3_5 | 0.6147 | 0.6101 | 0.6073 | - | 0.0240 -> 0.0144 |
| btts | 0.6892 | 0.6890 | 0.6857 | - | 0.0315 -> 0.0147 |

Over/under 2.5 vs bookmaker on 18078 matches: model 0.6820, bookmaker 0.6714, gap +0.0106 [+0.0088, +0.0125]

Calibrated: when the model gave at least X%, how often did it happen?

| market | side | min | n | avg predicted | happened |
|---|---|---|---|---|---|
| over_1_5 | over | 50% | 23323 | 75.5% | 76.5% |
| over_1_5 | over | 60% | 23299 | 75.5% | 76.5% |
| over_1_5 | over | 70% | 19973 | 76.8% | 77.6% |
| over_1_5 | over | 80% | 4459 | 82.6% | 83.7% |
| over_2_5 | over | 50% | 12860 | 56.3% | 58.2% |
| over_2_5 | over | 60% | 2569 | 63.8% | 66.2% |
| over_2_5 | over | 70% | 155 | 73.3% | 76.8% |
| over_2_5 | over | 80% | 8 | 81.0% | 87.5% |
| over_2_5 | under | 50% | 10463 | 55.1% | 53.4% |
| over_2_5 | under | 60% | 1236 | 62.5% | 57.9% |
| over_2_5 | under | 70% | 4 | 70.8% | 50.0% |
| over_3_5 | over | 50% | 123 | 53.8% | 49.6% |
| over_3_5 | over | 60% | 9 | 62.7% | 66.7% |
| over_3_5 | under | 50% | 23200 | 70.8% | 69.4% |
| over_3_5 | under | 60% | 21798 | 71.7% | 70.4% |
| over_3_5 | under | 70% | 13235 | 75.3% | 74.3% |
| over_3_5 | under | 80% | 1538 | 82.0% | 78.1% |
| btts | over | 50% | 17422 | 55.1% | 56.2% |
| btts | over | 60% | 1636 | 62.0% | 62.6% |
| btts | over | 70% | 7 | 72.3% | 42.9% |
| btts | under | 50% | 5901 | 52.7% | 50.3% |
| btts | under | 60% | 45 | 61.2% | 53.3% |

Production calibrators ({'over_1_5': 'platt', 'over_2_5': 'platt', 'over_3_5': 'platt', 'btts': 'platt'}) fitted on 44558 out-of-sample matches -> data/models/goals_calibration.json

## 5. Asian handicap (main line), test period

23323 matches. Home side, stake-weighted: predicted win/push/lose 43.3% / 13.6% / 43.1%, actual 43.4% / 14.1% / 42.5%.
Average profit per unit at our own fair odds: -0.001 (0 = calibrated; negative = we were too optimistic).

| our chance | bets | avg chance | won | push | lost | profit at fair odds |
|---|---|---|---|---|---|---|
| <45% | 105 | 44.6% | 26.7% | 28.6% | 44.8% | -0.117 |
| 45-50% | 23218 | 48.1% | 40.6% | 14.0% | 45.3% | -0.014 |
| 50-55% | 23218 | 51.9% | 45.3% | 14.0% | 40.6% | +0.013 |
| 55-60% | 104 | 55.3% | 44.2% | 28.8% | 26.9% | +0.087 |
| 60%+ | 1 | 62.4% | 100.0% | 0.0% | 0.0% | +0.603 |

Against bookmaker closing AH odds, at the bookmaker's own line (16870 matches, pushes excluded). Log loss, lower is better:

| odds source | n | ours | bookmaker | gap |
|---|---|---|---|---|
| avg_closing | 4364 | 0.7123 | 0.6925 | +0.0198 |
| b365_closing | 1 | 1.0260 | 0.6545 | +0.3715 |
| pinnacle_closing | 12505 | 0.7107 | 0.6922 | +0.0184 |
| ALL | 16870 | 0.7111 | 0.6923 | +0.0188 [+0.0160, +0.0215] |

Backing our side whenever our fair odds beat the closing price (any edge): 13943 bets, avg odds 1.94, profit -519.9 units, ROI -3.7%

Backing our side whenever our fair odds beat the closing price (edge 5%+): 10071 bets, avg odds 1.95, profit -451.7 units, ROI -4.5%

## 6. Half-time result (check of the early-result method), test period

First-half share of goals, fitted before the test period: 0.4448. 18073 matches with half-time scores.
Log loss: model 1.0454 vs league-average baseline 1.0807; accuracy 44.6% vs 40.5%.
Half-time draws: predicted 41.4%, happened 40.5%.

| predicted HT draw | n | avg predicted | happened |
|---|---|---|---|
| 0.2-0.3 | 366 | 27.2% | 27.0% |
| 0.3-0.4 | 6215 | 36.9% | 36.3% |
| 0.4-0.5 | 11011 | 43.9% | 43.0% |
| 0.5-0.6 | 475 | 51.6% | 50.7% |

## 7. Derived markets (one consistent scoreline grid), test period

Baseline = each league's outcome frequencies in earlier seasons. Log loss, lower is better.

| market | n | model | baseline | gap | calibration error |
|---|---|---|---|---|---|
| Result & both teams score | 23323 | 1.6642 | 1.7355 | -0.0713 | 0.3 pts |
| Result & over/under 2.5 | 23323 | 1.6477 | 1.7187 | -0.0710 | 0.4 pts |
| Home team over/under 0.5 | 23323 | 0.5061 | 0.5303 | -0.0242 | 1.6 pts |
| Home team over/under 1.5 | 23323 | 0.6538 | 0.6871 | -0.0333 | 1.0 pts |
| Away team over/under 0.5 | 23323 | 0.5899 | 0.6106 | -0.0206 | 0.9 pts |
| Away team over/under 1.5 | 23323 | 0.6200 | 0.6474 | -0.0273 | 1.1 pts |
| Exact total goals | 23323 | 1.7181 | 1.7288 | -0.0107 | 0.3 pts |
| Odd/even goals | 23323 | 0.6932 | 0.6933 | -0.0001 | 0.7 pts |
| Half-time result | 18073 | 1.0441 | 1.0807 | -0.0366 | 0.3 pts |
| Half-time/full-time | 18073 | 1.8937 | 1.9684 | -0.0747 | 0.4 pts |
| 1st half over/under 0.5 | 18073 | 0.5973 | 0.6007 | -0.0033 | 1.7 pts |
| 1st half over/under 1.5 | 18073 | 0.6417 | 0.6461 | -0.0043 | 1.7 pts |
| Highest-scoring half | 18073 | 1.0719 | 1.0727 | -0.0008 | 0.4 pts |
| Home win to nil | 23323 | 0.5156 | 0.5414 | -0.0258 | 0.4 pts |
| Away win to nil | 23323 | 0.4050 | 0.4308 | -0.0258 | 1.0 pts |
