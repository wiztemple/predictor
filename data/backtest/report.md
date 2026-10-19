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

## 2. Test period: 2023-24, 2024-25, 2025-26, 2026-27 (22718 matches)

Overall (lower log loss / Brier is better):

| model | log loss | Brier | accuracy |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | 51.4% |
| Elo | 1.0097 | 0.6042 | 49.6% |
| Elo + Platt calibration | 1.0089 | 0.6039 | 49.7% |
| Dixon-Coles | 1.0121 | 0.6058 | 49.7% |
| Elo + Dixon-Coles blend **(production)** | 1.0083 | 0.6034 | 49.8% |
| Gradient boosting (no odds) | 1.0101 | 0.6044 | 49.6% |
| Gradient boosting (with odds) | 0.9965 | 0.5941 | 51.2% |

Log loss by league:

| league | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|
| ALL | nan | 1.0097 | 1.0089 | 1.0121 | 1.0083 | 1.0101 | 0.9965 |
| AUT | nan | 1.0322 | 1.0290 | 1.0332 | 1.0306 | 1.0294 | 1.0184 |
| B1 | 0.9867 | 1.0049 | 1.0026 | 1.0068 | 1.0035 | 1.0050 | 0.9912 |
| D1 | nan | 0.9875 | 0.9892 | 0.9919 | 0.9880 | 0.9898 | 0.9718 |
| D2 | nan | 1.0509 | 1.0511 | 1.0577 | 1.0524 | 1.0528 | 1.0419 |
| DNK | nan | 1.0238 | 1.0232 | 1.0276 | 1.0239 | 1.0256 | 1.0107 |
| E0 | nan | 0.9843 | 0.9835 | 0.9841 | 0.9821 | 0.9881 | 0.9749 |
| E1 | nan | 1.0468 | 1.0470 | 1.0478 | 1.0457 | 1.0511 | 1.0409 |
| F1 | nan | 1.0002 | 0.9995 | 1.0043 | 1.0003 | 1.0031 | 0.9968 |
| F2 | nan | 1.0694 | 1.0687 | 1.0718 | 1.0678 | 1.0698 | 1.0573 |
| G1 | nan | 0.9545 | 0.9524 | 0.9542 | 0.9510 | 0.9500 | 0.9375 |
| I1 | nan | 0.9825 | 0.9827 | 0.9840 | 0.9798 | 0.9841 | 0.9696 |
| I2 | nan | 1.0611 | 1.0619 | 1.0641 | 1.0598 | 1.0615 | 1.0436 |
| N1 | nan | 0.9617 | 0.9575 | 0.9649 | 0.9599 | 0.9570 | 0.9472 |
| NOR | nan | 0.9844 | 0.9874 | 0.9805 | 0.9803 | 0.9869 | 0.9735 |
| P1 | 0.9107 | 0.9311 | 0.9283 | 0.9387 | 0.9285 | 0.9285 | 0.9117 |
| POL | 1.0437 | 1.0547 | 1.0534 | 1.0566 | 1.0543 | 1.0561 | 1.0488 |
| ROU | 1.0169 | 1.0396 | 1.0377 | 1.0414 | 1.0383 | 1.0391 | 1.0205 |
| SC0 | nan | 0.9723 | 0.9685 | 0.9722 | 0.9696 | 0.9646 | 0.9569 |
| SP1 | nan | 0.9666 | 0.9674 | 0.9728 | 0.9673 | 0.9681 | 0.9600 |
| SP2 | nan | 1.0474 | 1.0464 | 1.0494 | 1.0463 | 1.0479 | 1.0324 |
| SWZ | 1.0203 | 1.0375 | 1.0377 | 1.0344 | 1.0336 | 1.0329 | 1.0212 |
| T1 | nan | 0.9734 | 0.9721 | 0.9791 | 0.9725 | 0.9741 | 0.9433 |

Log loss by season:

| season | n | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|---|
| 2023-24 | 7090 | 0.9822 | 1.0015 | 1.0019 | 1.0059 | 1.0013 | 1.0034 | 0.9837 |
| 2024-25 | 6960 | 0.9901 | 1.0121 | 1.0102 | 1.0128 | 1.0098 | 1.0121 | 0.9933 |
| 2025-26 | 6929 | 0.9987 | 1.0182 | 1.0172 | 1.0199 | 1.0166 | 1.0176 | 1.0008 |
| 2026-27 | 1739 | nan | 0.9995 | 0.9995 | 1.0034 | 0.9983 | 0.9993 | 1.0444 |

Gap to the bookmaker (model minus bookmaker log loss; negative = model better), 95% CI from a bootstrap over weeks:

- Elo: +nan  [+0.0180, +0.0229]
- Elo + Platt calibration: +nan  [+0.0174, +0.0220]
- Dixon-Coles: +nan  [+0.0206, +0.0254]
- Elo + Dixon-Coles blend: +nan  [+0.0170, +0.0213]
- Gradient boosting (no odds): +nan  [+0.0187, +0.0232]
- Gradient boosting (with odds): +nan  [+0.0012, +0.0031]

By bookmaker odds source (the benchmark is weaker where Pinnacle closing odds are missing):

| odds source | n | bookmaker | Elo + Dixon-Coles blend | gap |
|---|---|---|---|---|
| avg_closing | 5614 | 0.9943 | 1.0138 | +0.0195 |
| pinnacle_closing | 16963 | 0.9878 | 1.0068 | +0.0190 |

Matches involving a newly promoted team:

| subset | n | bookmaker | Elo | Dixon-Coles | Elo + Dixon-Coles blend |
|---|---|---|---|---|---|
| others | 15062 | nan | 1.0062 | 1.0079 | 1.0051 |
| promoted team | 7656 | nan | 1.0166 | 1.0204 | 1.0148 |

## 3. Calibration on the test period

Expected calibration error (count-weighted |predicted - observed|, 10 bins):

| model | home | draw | away |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | nan |
| Dixon-Coles | 0.0078 | 0.0143 | 0.0115 |
| Elo | 0.0098 | 0.0039 | 0.0112 |
| Elo + Dixon-Coles blend | 0.0062 | 0.0059 | 0.0092 |

Reliability table, Elo + Dixon-Coles blend (bins with n >= 30):

| outcome | bin | n | mean predicted | observed |
|---|---|---|---|---|
| home | 0.0-0.1 | 232 | 0.081 | 0.099 |
| home | 0.1-0.2 | 1280 | 0.157 | 0.149 |
| home | 0.2-0.3 | 2737 | 0.257 | 0.264 |
| home | 0.3-0.4 | 5456 | 0.354 | 0.359 |
| home | 0.4-0.5 | 6095 | 0.448 | 0.447 |
| home | 0.5-0.6 | 3785 | 0.544 | 0.538 |
| home | 0.6-0.7 | 1836 | 0.642 | 0.658 |
| home | 0.7-0.8 | 867 | 0.747 | 0.774 |
| home | 0.8-0.9 | 403 | 0.839 | 0.844 |
| draw | 0.0-0.1 | 162 | 0.082 | 0.086 |
| draw | 0.1-0.2 | 2199 | 0.164 | 0.162 |
| draw | 0.2-0.3 | 17485 | 0.261 | 0.268 |
| draw | 0.3-0.4 | 2872 | 0.314 | 0.312 |
| away | 0.0-0.1 | 1006 | 0.070 | 0.050 |
| away | 0.1-0.2 | 3753 | 0.159 | 0.148 |
| away | 0.2-0.3 | 7334 | 0.252 | 0.252 |
| away | 0.3-0.4 | 5668 | 0.345 | 0.333 |
| away | 0.4-0.5 | 2683 | 0.443 | 0.429 |
| away | 0.5-0.6 | 1233 | 0.545 | 0.528 |
| away | 0.6-0.7 | 669 | 0.644 | 0.662 |
| away | 0.7-0.8 | 321 | 0.740 | 0.735 |
| away | 0.8-0.9 | 51 | 0.826 | 0.725 |

## 4. Goals markets (Dixon-Coles)

Calibration choice: fitted on 2020-21..2022-23 (exclusive), scored on 2022-23. Log loss:

| market | none | platt | isotonic | chosen |
|---|---|---|---|---|
| over_1_5 | 0.5685 | 0.5660 | 0.5668 | **platt** |
| over_2_5 | 0.6839 | 0.6812 | 0.6815 | **platt** |
| over_3_5 | 0.5827 | 0.5798 | 0.5801 | **platt** |
| btts | 0.6922 | 0.6887 | 0.6891 | **platt** |

Test period (22718 matches). Log loss (lower is better):

| market | baseline | model raw | model calibrated | bookmaker | calibration error raw -> calibrated |
|---|---|---|---|---|---|
| over_1_5 | 0.5444 | 0.5423 | 0.5399 | - | 0.0235 -> 0.0094 |
| over_2_5 | 0.6898 | 0.6852 | 0.6820 | 0.6714 | 0.0320 -> 0.0180 |
| over_3_5 | 0.6144 | 0.6096 | 0.6068 | - | 0.0235 -> 0.0143 |
| btts | 0.6894 | 0.6892 | 0.6859 | - | 0.0323 -> 0.0149 |

Over/under 2.5 vs bookmaker on 17616 matches: model 0.6821, bookmaker 0.6714, gap +0.0106 [+0.0088, +0.0124]

Calibrated: when the model gave at least X%, how often did it happen?

| market | side | min | n | avg predicted | happened |
|---|---|---|---|---|---|
| over_1_5 | over | 50% | 22718 | 75.4% | 76.4% |
| over_1_5 | over | 60% | 22694 | 75.5% | 76.4% |
| over_1_5 | over | 70% | 19408 | 76.8% | 77.5% |
| over_1_5 | over | 80% | 4291 | 82.6% | 83.7% |
| over_2_5 | over | 50% | 12452 | 56.3% | 58.2% |
| over_2_5 | over | 60% | 2457 | 63.8% | 66.1% |
| over_2_5 | over | 70% | 146 | 73.4% | 77.4% |
| over_2_5 | over | 80% | 7 | 80.8% | 85.7% |
| over_2_5 | under | 50% | 10266 | 55.2% | 53.5% |
| over_2_5 | under | 60% | 1222 | 62.5% | 58.0% |
| over_2_5 | under | 70% | 4 | 70.8% | 50.0% |
| over_3_5 | over | 50% | 120 | 53.7% | 49.2% |
| over_3_5 | over | 60% | 8 | 62.5% | 62.5% |
| over_3_5 | under | 50% | 22598 | 70.8% | 69.4% |
| over_3_5 | under | 60% | 21261 | 71.7% | 70.4% |
| over_3_5 | under | 70% | 12962 | 75.4% | 74.3% |
| over_3_5 | under | 80% | 1522 | 82.0% | 78.1% |
| btts | over | 50% | 16893 | 55.1% | 56.2% |
| btts | over | 60% | 1554 | 62.0% | 62.4% |
| btts | over | 70% | 7 | 72.3% | 42.9% |
| btts | under | 50% | 5825 | 52.7% | 50.2% |
| btts | under | 60% | 45 | 61.2% | 53.3% |

Production calibrators ({'over_1_5': 'platt', 'over_2_5': 'platt', 'over_3_5': 'platt', 'btts': 'platt'}) fitted on 43953 out-of-sample matches -> data/models/goals_calibration.json

## 5. Asian handicap (main line), test period

22718 matches. Home side, stake-weighted: predicted win/push/lose 43.3% / 13.6% / 43.1%, actual 43.3% / 14.1% / 42.6%.
Average profit per unit at our own fair odds: -0.001 (0 = calibrated; negative = we were too optimistic).

| our chance | bets | avg chance | won | push | lost | profit at fair odds |
|---|---|---|---|---|---|---|
| <45% | 101 | 44.7% | 27.7% | 29.2% | 43.1% | -0.087 |
| 45-50% | 22617 | 48.1% | 40.6% | 14.0% | 45.3% | -0.015 |
| 50-55% | 22617 | 51.9% | 45.3% | 14.0% | 40.6% | +0.013 |
| 55-60% | 101 | 55.3% | 43.1% | 29.2% | 27.7% | +0.070 |

Against bookmaker closing AH odds, at the bookmaker's own line (16431 matches, pushes excluded). Log loss, lower is better:

| odds source | n | ours | bookmaker | gap |
|---|---|---|---|---|
| avg_closing | 3925 | 0.7110 | 0.6923 | +0.0187 |
| b365_closing | 1 | 1.0260 | 0.6545 | +0.3715 |
| pinnacle_closing | 12505 | 0.7107 | 0.6922 | +0.0184 |
| ALL | 16431 | 0.7108 | 0.6923 | +0.0185 [+0.0158, +0.0211] |

Backing our side whenever our fair odds beat the closing price (any edge): 13645 bets, avg odds 1.95, profit -493.8 units, ROI -3.6%

Backing our side whenever our fair odds beat the closing price (edge 5%+): 9869 bets, avg odds 1.95, profit -421.1 units, ROI -4.3%

## 6. Half-time result (check of the early-result method), test period

First-half share of goals, fitted before the test period: 0.4448. 17611 matches with half-time scores.
Log loss: model 1.0446 vs league-average baseline 1.0800; accuracy 44.8% vs 40.7%.
Half-time draws: predicted 41.4%, happened 40.7%.

| predicted HT draw | n | avg predicted | happened |
|---|---|---|---|
| 0.2-0.3 | 359 | 27.2% | 27.6% |
| 0.3-0.4 | 6019 | 36.9% | 36.3% |
| 0.4-0.5 | 10761 | 43.9% | 43.2% |
| 0.5-0.6 | 467 | 51.6% | 51.2% |

## 7. Derived markets (one consistent scoreline grid), test period

Baseline = each league's outcome frequencies in earlier seasons. Log loss, lower is better.

| market | n | model | baseline | gap | calibration error |
|---|---|---|---|---|---|
| Result & both teams score | 22718 | 1.6657 | 1.7364 | -0.0707 | 0.3 pts |
| Result & over/under 2.5 | 22718 | 1.6488 | 1.7193 | -0.0705 | 0.4 pts |
| Home team over/under 0.5 | 22718 | 0.5078 | 0.5318 | -0.0240 | 1.5 pts |
| Home team over/under 1.5 | 22718 | 0.6536 | 0.6869 | -0.0333 | 0.9 pts |
| Away team over/under 0.5 | 22718 | 0.5898 | 0.6105 | -0.0207 | 1.0 pts |
| Away team over/under 1.5 | 22718 | 0.6200 | 0.6470 | -0.0271 | 1.1 pts |
| Exact total goals | 22718 | 1.7191 | 1.7297 | -0.0106 | 0.3 pts |
| Odd/even goals | 22718 | 0.6933 | 0.6933 | -0.0000 | 0.8 pts |
| Half-time result | 17611 | 1.0432 | 1.0800 | -0.0368 | 0.2 pts |
| Half-time/full-time | 17611 | 1.8939 | 1.9687 | -0.0748 | 0.4 pts |
| 1st half over/under 0.5 | 17611 | 0.5979 | 0.6013 | -0.0034 | 1.7 pts |
| 1st half over/under 1.5 | 17611 | 0.6415 | 0.6455 | -0.0040 | 1.7 pts |
| Highest-scoring half | 17611 | 1.0722 | 1.0729 | -0.0007 | 0.4 pts |
| Home win to nil | 22718 | 0.5144 | 0.5403 | -0.0259 | 0.5 pts |
| Away win to nil | 22718 | 0.4059 | 0.4316 | -0.0256 | 1.0 pts |
