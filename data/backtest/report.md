# Backtest report

Out-of-sample predictions from 2020-21; test seasons 2023-24, 2024-25, 2025-26, 2026-27.
All choices below were made on seasons before 2023-24.

## 1. Choices made on pre-test data

Blend weight on Elo (tune seasons ['2021-22', '2022-23']): **0.5** (log loss 1.0082; Elo only 1.0107, Dixon-Coles only 1.0110)

Calibration choice: calibrators fitted on 2020-21..2022-23 (exclusive), scored on 2022-23 (6802 matches). Log loss:

| base | none | isotonic | platt |
|---|---|---|---|
| Elo | 1.0071 | 1.0093 | 1.0066 |
| Dixon-Coles | 1.0084 | 1.0110 | 1.0087 |
| Elo + Dixon-Coles blend | 1.0053 | 1.0067 | 1.0057 |

Gradient boosting (no odds), 2022-23: 1.0089
Bookmaker, 2022-23: 0.9880

Chosen calibration per base: {'elo': 'platt', 'dixon_coles': 'none', 'blend': 'none'}
**Pre-registered production model: Elo + Dixon-Coles blend (calibration: none)**

## 2. Test period: 2023-24, 2024-25, 2025-26, 2026-27 (21481 matches)

Overall (lower log loss / Brier is better):

| model | log loss | Brier | accuracy |
|---|---|---|---|
| Bookmaker (closing, margin removed) | 0.9913 | 0.5920 | 51.2% |
| Elo | 1.0114 | 0.6055 | 49.3% |
| Elo + Platt calibration | 1.0104 | 0.6050 | 49.3% |
| Dixon-Coles | 1.0141 | 0.6072 | 49.4% |
| Elo + Dixon-Coles blend **(production)** | 1.0102 | 0.6047 | 49.5% |
| Gradient boosting (no odds) | 1.0117 | 0.6056 | 49.5% |
| Gradient boosting (with odds) | 0.9937 | 0.5935 | 51.2% |

Log loss by league:

| league | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|
| ALL | 0.9913 | 1.0114 | 1.0104 | 1.0141 | 1.0102 | 1.0117 | 0.9937 |
| AUT | 1.0169 | 1.0341 | 1.0310 | 1.0355 | 1.0327 | 1.0313 | 1.0176 |
| B1 | 0.9869 | 1.0054 | 1.0027 | 1.0073 | 1.0040 | 1.0037 | 0.9915 |
| D1 | 0.9607 | 0.9872 | 0.9890 | 0.9908 | 0.9874 | 0.9858 | 0.9627 |
| D2 | 1.0407 | 1.0518 | 1.0520 | 1.0586 | 1.0532 | 1.0539 | 1.0429 |
| DNK | 1.0002 | 1.0233 | 1.0229 | 1.0263 | 1.0229 | 1.0239 | 1.0034 |
| E0 | 0.9639 | 0.9851 | 0.9839 | 0.9842 | 0.9826 | 0.9897 | 0.9705 |
| E1 | 1.0269 | 1.0465 | 1.0462 | 1.0473 | 1.0453 | 1.0499 | 1.0339 |
| F1 | 0.9845 | 1.0032 | 1.0023 | 1.0073 | 1.0033 | 1.0045 | 0.9842 |
| F2 | 1.0484 | 1.0691 | 1.0687 | 1.0728 | 1.0683 | 1.0690 | 1.0492 |
| G1 | 0.9312 | 0.9557 | 0.9537 | 0.9548 | 0.9519 | 0.9543 | 0.9324 |
| I1 | 0.9624 | 0.9833 | 0.9836 | 0.9845 | 0.9804 | 0.9867 | 0.9674 |
| I2 | 1.0365 | 1.0605 | 1.0615 | 1.0633 | 1.0591 | 1.0614 | 1.0364 |
| N1 | 0.9382 | 0.9582 | 0.9544 | 0.9619 | 0.9567 | 0.9530 | 0.9364 |
| P1 | 0.9118 | 0.9327 | 0.9297 | 0.9402 | 0.9300 | 0.9311 | 0.9155 |
| POL | 1.0453 | 1.0563 | 1.0548 | 1.0582 | 1.0559 | 1.0558 | 1.0493 |
| ROU | 1.0195 | 1.0409 | 1.0388 | 1.0430 | 1.0398 | 1.0409 | 1.0254 |
| SC0 | 0.9561 | 0.9720 | 0.9685 | 0.9719 | 0.9693 | 0.9671 | 0.9563 |
| SP1 | 0.9527 | 0.9686 | 0.9690 | 0.9735 | 0.9686 | 0.9694 | 0.9530 |
| SP2 | 1.0279 | 1.0484 | 1.0472 | 1.0512 | 1.0478 | 1.0509 | 1.0281 |
| SWZ | 1.0224 | 1.0391 | 1.0391 | 1.0361 | 1.0352 | 1.0359 | 1.0234 |
| T1 | 0.9434 | 0.9761 | 0.9744 | 0.9821 | 0.9753 | 0.9757 | 0.9430 |

Log loss by season:

| season | n | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|---|
| 2023-24 | 6848 | 0.9829 | 1.0022 | 1.0023 | 1.0069 | 1.0022 | 1.0038 | 0.9853 |
| 2024-25 | 6718 | 0.9893 | 1.0111 | 1.0092 | 1.0119 | 1.0088 | 1.0115 | 0.9919 |
| 2025-26 | 6689 | 1.0018 | 1.0210 | 1.0196 | 1.0224 | 1.0192 | 1.0196 | 1.0042 |
| 2026-27 | 1226 | 0.9916 | 1.0133 | 1.0126 | 1.0199 | 1.0135 | 1.0136 | 0.9928 |

Gap to the bookmaker (model minus bookmaker log loss; negative = model better), 95% CI from a bootstrap over weeks:

- Elo: +0.0201  [+0.0177, +0.0227]
- Elo + Platt calibration: +0.0191  [+0.0167, +0.0215]
- Dixon-Coles: +0.0228  [+0.0203, +0.0251]
- Elo + Dixon-Coles blend: +0.0189  [+0.0167, +0.0210]
- Gradient boosting (no odds): +0.0204  [+0.0179, +0.0227]
- Gradient boosting (with odds): +0.0024  [+0.0013, +0.0034]

By bookmaker odds source (the benchmark is weaker where Pinnacle closing odds are missing):

| odds source | n | bookmaker | Elo + Dixon-Coles blend | gap |
|---|---|---|---|---|
| avg_closing | 5208 | 0.9999 | 1.0189 | +0.0190 |
| pinnacle_closing | 16273 | 0.9885 | 1.0074 | +0.0189 |

Matches involving a newly promoted team:

| subset | n | bookmaker | Elo | Dixon-Coles | Elo + Dixon-Coles blend |
|---|---|---|---|---|---|
| others | 14178 | 0.9895 | 1.0090 | 1.0107 | 1.0079 |
| promoted team | 7303 | 0.9948 | 1.0162 | 1.0206 | 1.0147 |

## 3. Calibration on the test period

Expected calibration error (count-weighted |predicted - observed|, 10 bins):

| model | home | draw | away |
|---|---|---|---|
| Bookmaker (closing, margin removed) | 0.0111 | 0.0083 | 0.0123 |
| Dixon-Coles | 0.0090 | 0.0161 | 0.0128 |
| Elo | 0.0097 | 0.0062 | 0.0118 |
| Elo + Dixon-Coles blend | 0.0073 | 0.0076 | 0.0102 |

Reliability table, Elo + Dixon-Coles blend (bins with n >= 30):

| outcome | bin | n | mean predicted | observed |
|---|---|---|---|---|
| home | 0.0-0.1 | 230 | 0.081 | 0.096 |
| home | 0.1-0.2 | 1216 | 0.157 | 0.150 |
| home | 0.2-0.3 | 2595 | 0.257 | 0.264 |
| home | 0.3-0.4 | 5192 | 0.354 | 0.360 |
| home | 0.4-0.5 | 5794 | 0.448 | 0.444 |
| home | 0.5-0.6 | 3537 | 0.544 | 0.536 |
| home | 0.6-0.7 | 1713 | 0.642 | 0.660 |
| home | 0.7-0.8 | 793 | 0.747 | 0.770 |
| home | 0.8-0.9 | 386 | 0.839 | 0.839 |
| draw | 0.0-0.1 | 153 | 0.082 | 0.092 |
| draw | 0.1-0.2 | 2002 | 0.163 | 0.166 |
| draw | 0.2-0.3 | 16487 | 0.262 | 0.271 |
| draw | 0.3-0.4 | 2839 | 0.314 | 0.313 |
| away | 0.0-0.1 | 959 | 0.070 | 0.049 |
| away | 0.1-0.2 | 3534 | 0.159 | 0.149 |
| away | 0.2-0.3 | 6954 | 0.252 | 0.251 |
| away | 0.3-0.4 | 5378 | 0.345 | 0.331 |
| away | 0.4-0.5 | 2520 | 0.443 | 0.426 |
| away | 0.5-0.6 | 1143 | 0.545 | 0.526 |
| away | 0.6-0.7 | 633 | 0.643 | 0.659 |
| away | 0.7-0.8 | 310 | 0.741 | 0.742 |
| away | 0.8-0.9 | 50 | 0.825 | 0.740 |

## 4. Goals markets (Dixon-Coles)

Calibration choice: fitted on 2020-21..2022-23 (exclusive), scored on 2022-23. Log loss:

| market | none | platt | isotonic | chosen |
|---|---|---|---|---|
| over_1_5 | 0.5720 | 0.5696 | 0.5702 | **platt** |
| over_2_5 | 0.6847 | 0.6816 | 0.6820 | **platt** |
| over_3_5 | 0.5790 | 0.5757 | 0.5764 | **platt** |
| btts | 0.6930 | 0.6894 | 0.6899 | **platt** |

Test period (21481 matches). Log loss (lower is better):

| market | baseline | model raw | model calibrated | bookmaker | calibration error raw -> calibrated |
|---|---|---|---|---|---|
| over_1_5 | 0.5471 | 0.5449 | 0.5425 | - | 0.0228 -> 0.0079 |
| over_2_5 | 0.6904 | 0.6858 | 0.6826 | 0.6715 | 0.0314 -> 0.0162 |
| over_3_5 | 0.6112 | 0.6063 | 0.6035 | - | 0.0229 -> 0.0120 |
| btts | 0.6894 | 0.6894 | 0.6860 | - | 0.0330 -> 0.0145 |

Over/under 2.5 vs bookmaker on 17457 matches: model 0.6821, bookmaker 0.6715, gap +0.0106 [+0.0087, +0.0125]

Calibrated: when the model gave at least X%, how often did it happen?

| market | side | min | n | avg predicted | happened |
|---|---|---|---|---|---|
| over_1_5 | over | 50% | 21481 | 75.4% | 76.1% |
| over_1_5 | over | 60% | 21459 | 75.4% | 76.1% |
| over_1_5 | over | 70% | 18283 | 76.8% | 77.3% |
| over_1_5 | over | 80% | 3955 | 82.6% | 83.6% |
| over_2_5 | over | 50% | 11519 | 56.1% | 57.8% |
| over_2_5 | over | 60% | 2107 | 63.7% | 66.2% |
| over_2_5 | over | 70% | 126 | 73.1% | 80.2% |
| over_2_5 | over | 80% | 5 | 80.8% | 100.0% |
| over_2_5 | under | 50% | 9962 | 55.1% | 53.6% |
| over_2_5 | under | 60% | 1159 | 62.4% | 58.1% |
| over_2_5 | under | 70% | 2 | 71.2% | 100.0% |
| over_3_5 | over | 50% | 100 | 53.4% | 52.0% |
| over_3_5 | over | 60% | 7 | 62.2% | 71.4% |
| over_3_5 | under | 50% | 21381 | 71.0% | 69.8% |
| over_3_5 | under | 60% | 20270 | 71.8% | 70.7% |
| over_3_5 | under | 70% | 12524 | 75.3% | 74.6% |
| over_3_5 | under | 80% | 1419 | 82.0% | 78.6% |
| btts | over | 50% | 15994 | 54.9% | 56.1% |
| btts | over | 60% | 1324 | 61.9% | 62.7% |
| btts | over | 70% | 7 | 72.1% | 42.9% |
| btts | under | 50% | 5487 | 52.6% | 50.4% |
| btts | under | 60% | 31 | 61.4% | 61.3% |

Production calibrators ({'over_1_5': 'platt', 'over_2_5': 'platt', 'over_3_5': 'platt', 'btts': 'platt'}) fitted on 41993 out-of-sample matches -> data/models/goals_calibration.json

## 5. Asian handicap (main line), test period

21481 matches. Home side, stake-weighted: predicted win/push/lose 43.2% / 13.7% / 43.1%, actual 43.2% / 14.3% / 42.5%.
Average profit per unit at our own fair odds: -0.001 (0 = calibrated; negative = we were too optimistic).

| our chance | bets | avg chance | won | push | lost | profit at fair odds |
|---|---|---|---|---|---|---|
| <45% | 99 | 44.7% | 28.3% | 29.8% | 41.9% | -0.069 |
| 45-50% | 21382 | 48.1% | 40.6% | 14.2% | 45.2% | -0.013 |
| 50-55% | 21382 | 51.9% | 45.2% | 14.2% | 40.6% | +0.011 |
| 55-60% | 99 | 55.3% | 41.9% | 29.8% | 28.3% | +0.055 |

Against bookmaker closing AH odds, at the bookmaker's own line (16283 matches, pushes excluded). Log loss, lower is better:

| odds source | n | ours | bookmaker | gap |
|---|---|---|---|---|
| avg_closing | 3777 | 0.7105 | 0.6923 | +0.0182 |
| b365_closing | 1 | 1.0260 | 0.6545 | +0.3715 |
| pinnacle_closing | 12505 | 0.7107 | 0.6922 | +0.0184 |
| ALL | 16283 | 0.7107 | 0.6922 | +0.0184 [+0.0157, +0.0212] |

Backing our side whenever our fair odds beat the closing price (any edge): 13548 bets, avg odds 1.95, profit -480.3 units, ROI -3.5%

Backing our side whenever our fair odds beat the closing price (edge 5%+): 9798 bets, avg odds 1.95, profit -407.0 units, ROI -4.2%
