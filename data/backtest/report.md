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

## 2. Test period: 2023-24, 2024-25, 2025-26, 2026-27 (23360 matches)

Overall (lower log loss / Brier is better):

| model | log loss | Brier | accuracy |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | 51.6% |
| Elo | 1.0087 | 0.6035 | 49.7% |
| Elo + Platt calibration | 1.0080 | 0.6032 | 49.8% |
| Dixon-Coles | 1.0111 | 0.6051 | 49.8% |
| Elo + Dixon-Coles blend **(production)** | 1.0073 | 0.6026 | 50.0% |
| Gradient boosting (no odds) | 1.0091 | 0.6037 | 49.7% |
| Gradient boosting (with odds) | 0.9906 | 0.5909 | 51.4% |

Log loss by league:

| league | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|
| ALL | nan | 1.0087 | 1.0080 | 1.0111 | 1.0073 | 1.0091 | 0.9906 |
| AUT | 1.0099 | 1.0293 | 1.0263 | 1.0293 | 1.0272 | 1.0258 | 1.0098 |
| B1 | 0.9852 | 1.0026 | 1.0003 | 1.0042 | 1.0010 | 1.0023 | 0.9895 |
| D1 | 0.9616 | 0.9862 | 0.9880 | 0.9901 | 0.9865 | 0.9890 | 0.9673 |
| D2 | 1.0392 | 1.0500 | 1.0502 | 1.0562 | 1.0511 | 1.0514 | 1.0398 |
| DNK | 0.9985 | 1.0200 | 1.0196 | 1.0240 | 1.0201 | 1.0224 | 1.0021 |
| E0 | 0.9640 | 0.9861 | 0.9852 | 0.9855 | 0.9837 | 0.9894 | 0.9674 |
| E1 | 1.0264 | 1.0469 | 1.0469 | 1.0479 | 1.0457 | 1.0512 | 1.0335 |
| F1 | 0.9792 | 0.9989 | 0.9982 | 1.0026 | 0.9988 | 1.0012 | 0.9819 |
| F2 | 1.0453 | 1.0693 | 1.0684 | 1.0709 | 1.0674 | 1.0698 | 1.0457 |
| G1 | 0.9258 | 0.9510 | 0.9492 | 0.9530 | 0.9486 | 0.9470 | 0.9260 |
| I1 | 0.9590 | 0.9787 | 0.9791 | 0.9807 | 0.9763 | 0.9803 | 0.9615 |
| I2 | 1.0380 | 1.0606 | 1.0618 | 1.0648 | 1.0598 | 1.0610 | 1.0351 |
| N1 | 0.9441 | 0.9635 | 0.9593 | 0.9661 | 0.9613 | 0.9588 | 0.9439 |
| NOR | 0.9563 | 0.9837 | 0.9869 | 0.9802 | 0.9798 | 0.9866 | 0.9630 |
| P1 | 0.9100 | 0.9297 | 0.9270 | 0.9364 | 0.9265 | 0.9274 | 0.9112 |
| POL | 1.0421 | 1.0523 | 1.0511 | 1.0537 | 1.0517 | 1.0534 | 1.0470 |
| ROU | 1.0167 | 1.0383 | 1.0365 | 1.0405 | 1.0372 | 1.0380 | 1.0202 |
| SC0 | 0.9580 | 0.9739 | 0.9701 | 0.9734 | 0.9711 | 0.9660 | 0.9542 |
| SP1 | 0.9496 | 0.9661 | 0.9670 | 0.9722 | 0.9667 | 0.9677 | 0.9505 |
| SP2 | nan | 1.0464 | 1.0455 | 1.0488 | 1.0456 | 1.0472 | 1.0290 |
| SWZ | 1.0206 | 1.0372 | 1.0375 | 1.0355 | 1.0340 | 1.0330 | 1.0209 |
| T1 | 0.9376 | 0.9706 | 0.9698 | 0.9765 | 0.9698 | 0.9721 | 0.9392 |

Log loss by season:

| season | n | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|---|
| 2023-24 | 7090 | 0.9822 | 1.0015 | 1.0019 | 1.0059 | 1.0013 | 1.0034 | 0.9836 |
| 2024-25 | 6960 | 0.9901 | 1.0121 | 1.0102 | 1.0128 | 1.0098 | 1.0121 | 0.9933 |
| 2025-26 | 6929 | 0.9987 | 1.0182 | 1.0172 | 1.0199 | 1.0166 | 1.0176 | 1.0008 |
| 2026-27 | 2381 | nan | 0.9922 | 0.9928 | 0.9960 | 0.9911 | 0.9924 | 0.9732 |

Gap to the bookmaker (model minus bookmaker log loss; negative = model better), 95% CI from a bootstrap over weeks:

- Elo: +nan  [+0.0180, +0.0228]
- Elo + Platt calibration: +nan  [+0.0174, +0.0221]
- Dixon-Coles: +nan  [+0.0206, +0.0252]
- Elo + Dixon-Coles blend: +nan  [+0.0169, +0.0212]
- Gradient boosting (no odds): +nan  [+0.0185, +0.0232]
- Gradient boosting (with odds): +nan  [+0.0011, +0.0030]

By bookmaker odds source (the benchmark is weaker where Pinnacle closing odds are missing):

| odds source | n | bookmaker | Elo + Dixon-Coles blend | gap |
|---|---|---|---|---|
| avg_closing | 6387 | 0.9895 | 1.0087 | +0.0192 |
| pinnacle_closing | 16963 | 0.9878 | 1.0068 | +0.0190 |

Matches involving a newly promoted team:

| subset | n | bookmaker | Elo | Dixon-Coles | Elo + Dixon-Coles blend |
|---|---|---|---|---|---|
| others | 15492 | nan | 1.0054 | 1.0070 | 1.0043 |
| promoted team | 7868 | nan | 1.0151 | 1.0192 | 1.0134 |

## 3. Calibration on the test period

Expected calibration error (count-weighted |predicted - observed|, 10 bins):

| model | home | draw | away |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | nan |
| Dixon-Coles | 0.0069 | 0.0133 | 0.0117 |
| Elo | 0.0102 | 0.0033 | 0.0104 |
| Elo + Dixon-Coles blend | 0.0059 | 0.0050 | 0.0096 |

Reliability table, Elo + Dixon-Coles blend (bins with n >= 30):

| outcome | bin | n | mean predicted | observed |
|---|---|---|---|---|
| home | 0.0-0.1 | 236 | 0.081 | 0.097 |
| home | 0.1-0.2 | 1310 | 0.157 | 0.150 |
| home | 0.2-0.3 | 2810 | 0.257 | 0.264 |
| home | 0.3-0.4 | 5629 | 0.354 | 0.360 |
| home | 0.4-0.5 | 6271 | 0.448 | 0.448 |
| home | 0.5-0.6 | 3885 | 0.544 | 0.541 |
| home | 0.6-0.7 | 1891 | 0.642 | 0.658 |
| home | 0.7-0.8 | 890 | 0.747 | 0.775 |
| home | 0.8-0.9 | 410 | 0.839 | 0.844 |
| draw | 0.0-0.1 | 163 | 0.082 | 0.086 |
| draw | 0.1-0.2 | 2257 | 0.164 | 0.160 |
| draw | 0.2-0.3 | 18006 | 0.261 | 0.267 |
| draw | 0.3-0.4 | 2934 | 0.314 | 0.313 |
| away | 0.0-0.1 | 1029 | 0.070 | 0.051 |
| away | 0.1-0.2 | 3859 | 0.159 | 0.148 |
| away | 0.2-0.3 | 7530 | 0.252 | 0.251 |
| away | 0.3-0.4 | 5838 | 0.345 | 0.334 |
| away | 0.4-0.5 | 2775 | 0.443 | 0.428 |
| away | 0.5-0.6 | 1266 | 0.545 | 0.529 |
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

Test period (23360 matches). Log loss (lower is better):

| market | baseline | model raw | model calibrated | bookmaker | calibration error raw -> calibrated |
|---|---|---|---|---|---|
| over_1_5 | 0.5433 | 0.5412 | 0.5388 | - | 0.0241 -> 0.0101 |
| over_2_5 | 0.6897 | 0.6851 | 0.6819 | 0.6715 | 0.0321 -> 0.0181 |
| over_3_5 | 0.6146 | 0.6101 | 0.6072 | - | 0.0240 -> 0.0143 |
| btts | 0.6893 | 0.6890 | 0.6858 | - | 0.0315 -> 0.0146 |

Over/under 2.5 vs bookmaker on 18223 matches: model 0.6821, bookmaker 0.6715, gap +0.0106 [+0.0088, +0.0124]

Calibrated: when the model gave at least X%, how often did it happen?

| market | side | min | n | avg predicted | happened |
|---|---|---|---|---|---|
| over_1_5 | over | 50% | 23360 | 75.5% | 76.5% |
| over_1_5 | over | 60% | 23336 | 75.5% | 76.5% |
| over_1_5 | over | 70% | 20006 | 76.8% | 77.6% |
| over_1_5 | over | 80% | 4465 | 82.6% | 83.7% |
| over_2_5 | over | 50% | 12882 | 56.3% | 58.2% |
| over_2_5 | over | 60% | 2575 | 63.8% | 66.2% |
| over_2_5 | over | 70% | 156 | 73.3% | 76.9% |
| over_2_5 | over | 80% | 8 | 81.0% | 87.5% |
| over_2_5 | under | 50% | 10478 | 55.1% | 53.4% |
| over_2_5 | under | 60% | 1239 | 62.5% | 57.9% |
| over_2_5 | under | 70% | 4 | 70.8% | 50.0% |
| over_3_5 | over | 50% | 124 | 53.8% | 50.0% |
| over_3_5 | over | 60% | 9 | 62.7% | 66.7% |
| over_3_5 | under | 50% | 23236 | 70.8% | 69.4% |
| over_3_5 | under | 60% | 21833 | 71.7% | 70.4% |
| over_3_5 | under | 70% | 13258 | 75.3% | 74.3% |
| over_3_5 | under | 80% | 1541 | 82.0% | 78.1% |
| btts | over | 50% | 17452 | 55.1% | 56.2% |
| btts | over | 60% | 1640 | 62.0% | 62.6% |
| btts | over | 70% | 7 | 72.3% | 42.9% |
| btts | under | 50% | 5908 | 52.7% | 50.3% |
| btts | under | 60% | 45 | 61.2% | 53.3% |

Production calibrators ({'over_1_5': 'platt', 'over_2_5': 'platt', 'over_3_5': 'platt', 'btts': 'platt'}) fitted on 44595 out-of-sample matches -> data/models/goals_calibration.json

## 5. Asian handicap (main line), test period

23360 matches. Home side, stake-weighted: predicted win/push/lose 43.3% / 13.6% / 43.1%, actual 43.4% / 14.1% / 42.5%.
Average profit per unit at our own fair odds: -0.001 (0 = calibrated; negative = we were too optimistic).

| our chance | bets | avg chance | won | push | lost | profit at fair odds |
|---|---|---|---|---|---|---|
| <45% | 105 | 44.6% | 26.7% | 28.6% | 44.8% | -0.117 |
| 45-50% | 23255 | 48.1% | 40.6% | 14.0% | 45.3% | -0.015 |
| 50-55% | 23255 | 51.9% | 45.3% | 14.0% | 40.6% | +0.013 |
| 55-60% | 104 | 55.3% | 44.2% | 28.8% | 26.9% | +0.087 |
| 60%+ | 1 | 62.4% | 100.0% | 0.0% | 0.0% | +0.603 |

Against bookmaker closing AH odds, at the bookmaker's own line (17005 matches, pushes excluded). Log loss, lower is better:

| odds source | n | ours | bookmaker | gap |
|---|---|---|---|---|
| avg_closing | 4499 | 0.7122 | 0.6925 | +0.0196 |
| b365_closing | 1 | 1.0260 | 0.6545 | +0.3715 |
| pinnacle_closing | 12505 | 0.7107 | 0.6922 | +0.0184 |
| ALL | 17005 | 0.7111 | 0.6923 | +0.0188 [+0.0160, +0.0215] |

Backing our side whenever our fair odds beat the closing price (any edge): 14041 bets, avg odds 1.94, profit -518.7 units, ROI -3.7%

Backing our side whenever our fair odds beat the closing price (edge 5%+): 10142 bets, avg odds 1.95, profit -455.8 units, ROI -4.5%

## 6. Half-time result (check of the early-result method), test period

First-half share of goals, fitted before the test period: 0.4448. 18218 matches with half-time scores.
Log loss: model 1.0453 vs league-average baseline 1.0806; accuracy 44.7% vs 40.6%.
Half-time draws: predicted 41.4%, happened 40.6%.

| predicted HT draw | n | avg predicted | happened |
|---|---|---|---|
| 0.2-0.3 | 370 | 27.2% | 26.8% |
| 0.3-0.4 | 6276 | 36.9% | 36.3% |
| 0.4-0.5 | 11089 | 43.9% | 43.0% |
| 0.5-0.6 | 477 | 51.6% | 50.5% |

## 7. Derived markets (one consistent scoreline grid), test period

Baseline = each league's outcome frequencies in earlier seasons. Log loss, lower is better.

| market | n | model | baseline | gap | calibration error |
|---|---|---|---|---|---|
| Result & both teams score | 23360 | 1.6644 | 1.7355 | -0.0711 | 0.3 pts |
| Result & over/under 2.5 | 23360 | 1.6480 | 1.7188 | -0.0708 | 0.4 pts |
| Home team over/under 0.5 | 23360 | 0.5063 | 0.5304 | -0.0241 | 1.6 pts |
| Home team over/under 1.5 | 23360 | 0.6539 | 0.6871 | -0.0332 | 1.0 pts |
| Away team over/under 0.5 | 23360 | 0.5901 | 0.6107 | -0.0205 | 0.9 pts |
| Away team over/under 1.5 | 23360 | 0.6200 | 0.6473 | -0.0273 | 1.1 pts |
| Exact total goals | 23360 | 1.7182 | 1.7289 | -0.0106 | 0.3 pts |
| Odd/even goals | 23360 | 0.6932 | 0.6933 | -0.0001 | 0.7 pts |
| Half-time result | 18218 | 1.0439 | 1.0806 | -0.0367 | 0.3 pts |
| Half-time/full-time | 18218 | 1.8934 | 1.9684 | -0.0751 | 0.4 pts |
| 1st half over/under 0.5 | 18218 | 0.5974 | 0.6007 | -0.0033 | 1.7 pts |
| 1st half over/under 1.5 | 18218 | 0.6418 | 0.6461 | -0.0043 | 1.7 pts |
| Highest-scoring half | 18218 | 1.0716 | 1.0724 | -0.0009 | 0.5 pts |
| Home win to nil | 23360 | 0.5156 | 0.5413 | -0.0257 | 0.4 pts |
| Away win to nil | 23360 | 0.4050 | 0.4307 | -0.0257 | 1.0 pts |
