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

## 2. Test period: 2023-24, 2024-25, 2025-26, 2026-27 (22527 matches)

Overall (lower log loss / Brier is better):

| model | log loss | Brier | accuracy |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | 51.4% |
| Elo | 1.0099 | 0.6044 | 49.5% |
| Elo + Platt calibration | 1.0091 | 0.6040 | 49.6% |
| Dixon-Coles | 1.0124 | 0.6060 | 49.6% |
| Elo + Dixon-Coles blend **(production)** | 1.0086 | 0.6036 | 49.8% |
| Gradient boosting (no odds) | 1.0104 | 0.6046 | 49.6% |
| Gradient boosting (with odds) | 0.9963 | 0.5943 | 51.2% |

Log loss by league:

| league | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|
| ALL | nan | 1.0099 | 1.0091 | 1.0124 | 1.0086 | 1.0104 | 0.9963 |
| AUT | nan | 1.0348 | 1.0315 | 1.0361 | 1.0334 | 1.0326 | 1.0266 |
| B1 | nan | 1.0049 | 1.0026 | 1.0068 | 1.0035 | 1.0049 | 1.0006 |
| D1 | nan | 0.9878 | 0.9895 | 0.9924 | 0.9884 | 0.9904 | 0.9727 |
| D2 | nan | 1.0516 | 1.0519 | 1.0587 | 1.0531 | 1.0535 | 1.0447 |
| DNK | nan | 1.0231 | 1.0226 | 1.0264 | 1.0229 | 1.0249 | 1.0109 |
| E0 | nan | 0.9856 | 0.9846 | 0.9845 | 0.9830 | 0.9888 | 0.9731 |
| E1 | nan | 1.0459 | 1.0459 | 1.0471 | 1.0448 | 1.0506 | 1.0383 |
| F1 | nan | 1.0012 | 1.0003 | 1.0054 | 1.0013 | 1.0042 | 0.9855 |
| F2 | nan | 1.0684 | 1.0677 | 1.0719 | 1.0675 | 1.0691 | 1.0523 |
| G1 | nan | 0.9543 | 0.9522 | 0.9535 | 0.9506 | 0.9502 | 0.9257 |
| I1 | nan | 0.9823 | 0.9828 | 0.9842 | 0.9798 | 0.9842 | 0.9689 |
| I2 | nan | 1.0606 | 1.0614 | 1.0632 | 1.0591 | 1.0607 | 1.0423 |
| N1 | nan | 0.9589 | 0.9552 | 0.9624 | 0.9573 | 0.9550 | 0.9482 |
| NOR | nan | 0.9848 | 0.9876 | 0.9817 | 0.9811 | 0.9878 | 0.9746 |
| P1 | nan | 0.9303 | 0.9274 | 0.9380 | 0.9277 | 0.9277 | 0.9186 |
| POL | 1.0453 | 1.0563 | 1.0548 | 1.0582 | 1.0559 | 1.0575 | 1.0502 |
| ROU | 1.0194 | 1.0411 | 1.0391 | 1.0433 | 1.0400 | 1.0408 | 1.0230 |
| SC0 | nan | 0.9710 | 0.9673 | 0.9708 | 0.9683 | 0.9634 | 0.9572 |
| SP1 | nan | 0.9671 | 0.9678 | 0.9728 | 0.9676 | 0.9683 | 0.9564 |
| SP2 | nan | 1.0478 | 1.0468 | 1.0501 | 1.0470 | 1.0487 | 1.0264 |
| SWZ | 1.0224 | 1.0391 | 1.0393 | 1.0361 | 1.0352 | 1.0344 | 1.0228 |
| T1 | nan | 0.9756 | 0.9741 | 0.9816 | 0.9748 | 0.9767 | 0.9548 |

Log loss by season:

| season | n | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|---|
| 2023-24 | 7090 | 0.9822 | 1.0015 | 1.0019 | 1.0059 | 1.0013 | 1.0034 | 0.9837 |
| 2024-25 | 6960 | 0.9901 | 1.0121 | 1.0102 | 1.0128 | 1.0098 | 1.0121 | 0.9933 |
| 2025-26 | 6929 | 0.9987 | 1.0182 | 1.0172 | 1.0199 | 1.0166 | 1.0176 | 1.0008 |
| 2026-27 | 1548 | nan | 1.0005 | 1.0003 | 1.0065 | 1.0004 | 1.0022 | 1.0479 |

Gap to the bookmaker (model minus bookmaker log loss; negative = model better), 95% CI from a bootstrap over weeks:

- Elo: +nan  [+0.0180, +0.0232]
- Elo + Platt calibration: +nan  [+0.0173, +0.0223]
- Dixon-Coles: +nan  [+0.0206, +0.0252]
- Elo + Dixon-Coles blend: +nan  [+0.0170, +0.0214]
- Gradient boosting (no odds): +nan  [+0.0185, +0.0234]
- Gradient boosting (with odds): +nan  [+0.0012, +0.0031]

By bookmaker odds source (the benchmark is weaker where Pinnacle closing odds are missing):

| odds source | n | bookmaker | Elo + Dixon-Coles blend | gap |
|---|---|---|---|---|
| avg_closing | 5411 | 0.9965 | 1.0160 | +0.0195 |
| pinnacle_closing | 16963 | 0.9878 | 1.0068 | +0.0190 |

Matches involving a newly promoted team:

| subset | n | bookmaker | Elo | Dixon-Coles | Elo + Dixon-Coles blend |
|---|---|---|---|---|---|
| others | 14937 | nan | 1.0067 | 1.0084 | 1.0056 |
| promoted team | 7590 | nan | 1.0160 | 1.0202 | 1.0144 |

## 3. Calibration on the test period

Expected calibration error (count-weighted |predicted - observed|, 10 bins):

| model | home | draw | away |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | nan |
| Dixon-Coles | 0.0079 | 0.0146 | 0.0120 |
| Elo | 0.0098 | 0.0049 | 0.0112 |
| Elo + Dixon-Coles blend | 0.0064 | 0.0064 | 0.0096 |

Reliability table, Elo + Dixon-Coles blend (bins with n >= 30):

| outcome | bin | n | mean predicted | observed |
|---|---|---|---|---|
| home | 0.0-0.1 | 231 | 0.081 | 0.095 |
| home | 0.1-0.2 | 1267 | 0.157 | 0.150 |
| home | 0.2-0.3 | 2718 | 0.257 | 0.264 |
| home | 0.3-0.4 | 5410 | 0.354 | 0.359 |
| home | 0.4-0.5 | 6044 | 0.448 | 0.447 |
| home | 0.5-0.6 | 3743 | 0.544 | 0.537 |
| home | 0.6-0.7 | 1826 | 0.642 | 0.659 |
| home | 0.7-0.8 | 859 | 0.747 | 0.773 |
| home | 0.8-0.9 | 402 | 0.839 | 0.843 |
| draw | 0.0-0.1 | 161 | 0.082 | 0.087 |
| draw | 0.1-0.2 | 2184 | 0.164 | 0.163 |
| draw | 0.2-0.3 | 17326 | 0.261 | 0.269 |
| draw | 0.3-0.4 | 2856 | 0.314 | 0.313 |
| away | 0.0-0.1 | 1002 | 0.070 | 0.049 |
| away | 0.1-0.2 | 3721 | 0.159 | 0.149 |
| away | 0.2-0.3 | 7267 | 0.252 | 0.251 |
| away | 0.3-0.4 | 5623 | 0.345 | 0.333 |
| away | 0.4-0.5 | 2662 | 0.443 | 0.428 |
| away | 0.5-0.6 | 1222 | 0.545 | 0.526 |
| away | 0.6-0.7 | 660 | 0.644 | 0.661 |
| away | 0.7-0.8 | 320 | 0.740 | 0.738 |
| away | 0.8-0.9 | 50 | 0.825 | 0.740 |

## 4. Goals markets (Dixon-Coles)

Calibration choice: fitted on 2020-21..2022-23 (exclusive), scored on 2022-23. Log loss:

| market | none | platt | isotonic | chosen |
|---|---|---|---|---|
| over_1_5 | 0.5685 | 0.5660 | 0.5668 | **platt** |
| over_2_5 | 0.6839 | 0.6812 | 0.6815 | **platt** |
| over_3_5 | 0.5827 | 0.5798 | 0.5801 | **platt** |
| btts | 0.6922 | 0.6887 | 0.6891 | **platt** |

Test period (22527 matches). Log loss (lower is better):

| market | baseline | model raw | model calibrated | bookmaker | calibration error raw -> calibrated |
|---|---|---|---|---|---|
| over_1_5 | 0.5450 | 0.5428 | 0.5405 | - | 0.0231 -> 0.0090 |
| over_2_5 | 0.6898 | 0.6853 | 0.6821 | 0.6715 | 0.0314 -> 0.0171 |
| over_3_5 | 0.6133 | 0.6087 | 0.6059 | - | 0.0235 -> 0.0135 |
| btts | 0.6893 | 0.6892 | 0.6859 | - | 0.0320 -> 0.0147 |

Over/under 2.5 vs bookmaker on 17457 matches: model 0.6821, bookmaker 0.6715, gap +0.0106 [+0.0087, +0.0125]

Calibrated: when the model gave at least X%, how often did it happen?

| market | side | min | n | avg predicted | happened |
|---|---|---|---|---|---|
| over_1_5 | over | 50% | 22527 | 75.4% | 76.3% |
| over_1_5 | over | 60% | 22504 | 75.4% | 76.3% |
| over_1_5 | over | 70% | 19235 | 76.8% | 77.5% |
| over_1_5 | over | 80% | 4233 | 82.6% | 83.7% |
| over_2_5 | over | 50% | 12321 | 56.3% | 58.1% |
| over_2_5 | over | 60% | 2418 | 63.8% | 66.0% |
| over_2_5 | over | 70% | 143 | 73.4% | 76.9% |
| over_2_5 | over | 80% | 7 | 80.8% | 85.7% |
| over_2_5 | under | 50% | 10206 | 55.2% | 53.5% |
| over_2_5 | under | 60% | 1217 | 62.5% | 57.8% |
| over_2_5 | under | 70% | 4 | 70.8% | 50.0% |
| over_3_5 | over | 50% | 117 | 53.7% | 48.7% |
| over_3_5 | over | 60% | 8 | 62.5% | 62.5% |
| over_3_5 | under | 50% | 22410 | 70.8% | 69.5% |
| over_3_5 | under | 60% | 21092 | 71.7% | 70.6% |
| over_3_5 | under | 70% | 12876 | 75.4% | 74.4% |
| over_3_5 | under | 80% | 1513 | 82.0% | 78.0% |
| btts | over | 50% | 16728 | 55.1% | 56.2% |
| btts | over | 60% | 1523 | 62.0% | 62.4% |
| btts | over | 70% | 7 | 72.3% | 42.9% |
| btts | under | 50% | 5799 | 52.7% | 50.2% |
| btts | under | 60% | 45 | 61.2% | 53.3% |

Production calibrators ({'over_1_5': 'platt', 'over_2_5': 'platt', 'over_3_5': 'platt', 'btts': 'platt'}) fitted on 43762 out-of-sample matches -> data/models/goals_calibration.json

## 5. Asian handicap (main line), test period

22527 matches. Home side, stake-weighted: predicted win/push/lose 43.3% / 13.6% / 43.1%, actual 43.3% / 14.1% / 42.6%.
Average profit per unit at our own fair odds: -0.001 (0 = calibrated; negative = we were too optimistic).

| our chance | bets | avg chance | won | push | lost | profit at fair odds |
|---|---|---|---|---|---|---|
| <45% | 100 | 44.7% | 28.0% | 29.5% | 42.5% | -0.078 |
| 45-50% | 22427 | 48.1% | 40.6% | 14.1% | 45.3% | -0.015 |
| 50-55% | 22427 | 51.9% | 45.3% | 14.1% | 40.6% | +0.013 |
| 55-60% | 100 | 55.3% | 42.5% | 29.5% | 28.0% | +0.062 |

Against bookmaker closing AH odds, at the bookmaker's own line (16283 matches, pushes excluded). Log loss, lower is better:

| odds source | n | ours | bookmaker | gap |
|---|---|---|---|---|
| avg_closing | 3777 | 0.7105 | 0.6923 | +0.0182 |
| b365_closing | 1 | 1.0260 | 0.6545 | +0.3715 |
| pinnacle_closing | 12505 | 0.7107 | 0.6922 | +0.0184 |
| ALL | 16283 | 0.7107 | 0.6922 | +0.0184 [+0.0158, +0.0212] |

Backing our side whenever our fair odds beat the closing price (any edge): 13549 bets, avg odds 1.95, profit -479.5 units, ROI -3.5%

Backing our side whenever our fair odds beat the closing price (edge 5%+): 9798 bets, avg odds 1.95, profit -407.0 units, ROI -4.2%

## 6. Half-time result (check of the early-result method), test period

First-half share of goals, fitted before the test period: 0.4448. 17452 matches with half-time scores.
Log loss: model 1.0446 vs league-average baseline 1.0800; accuracy 44.8% vs 40.7%.
Half-time draws: predicted 41.4%, happened 40.7%.

| predicted HT draw | n | avg predicted | happened |
|---|---|---|---|
| 0.2-0.3 | 357 | 27.2% | 27.7% |
| 0.3-0.4 | 5952 | 36.9% | 36.2% |
| 0.4-0.5 | 10675 | 43.9% | 43.2% |
| 0.5-0.6 | 463 | 51.6% | 51.6% |

## 7. Derived markets (one consistent scoreline grid), test period

Baseline = each league's outcome frequencies in earlier seasons. Log loss, lower is better.

| market | n | model | baseline | gap | calibration error |
|---|---|---|---|---|---|
| Result & both teams score | 22527 | 1.6658 | 1.7364 | -0.0706 | 0.3 pts |
| Result & over/under 2.5 | 22527 | 1.6491 | 1.7196 | -0.0704 | 0.4 pts |
| Home team over/under 0.5 | 22527 | 0.5079 | 0.5319 | -0.0239 | 1.5 pts |
| Home team over/under 1.5 | 22527 | 0.6534 | 0.6866 | -0.0332 | 1.0 pts |
| Away team over/under 0.5 | 22527 | 0.5902 | 0.6109 | -0.0207 | 0.9 pts |
| Away team over/under 1.5 | 22527 | 0.6194 | 0.6465 | -0.0271 | 1.1 pts |
| Exact total goals | 22527 | 1.7189 | 1.7294 | -0.0105 | 0.3 pts |
| Odd/even goals | 22527 | 0.6932 | 0.6933 | -0.0001 | 0.8 pts |
| Half-time result | 17452 | 1.0433 | 1.0800 | -0.0367 | 0.2 pts |
| Half-time/full-time | 17452 | 1.8946 | 1.9692 | -0.0746 | 0.4 pts |
| 1st half over/under 0.5 | 17452 | 0.5982 | 0.6016 | -0.0034 | 1.7 pts |
| 1st half over/under 1.5 | 17452 | 0.6411 | 0.6452 | -0.0041 | 1.7 pts |
| Highest-scoring half | 17452 | 1.0723 | 1.0730 | -0.0007 | 0.4 pts |
| Home win to nil | 22527 | 0.5146 | 0.5406 | -0.0260 | 0.5 pts |
| Away win to nil | 22527 | 0.4057 | 0.4313 | -0.0255 | 1.0 pts |
