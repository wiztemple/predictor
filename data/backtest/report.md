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

## 2. Test period: 2023-24, 2024-25, 2025-26, 2026-27 (22903 matches)

Overall (lower log loss / Brier is better):

| model | log loss | Brier | accuracy |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | 51.5% |
| Elo | 1.0098 | 0.6043 | 49.6% |
| Elo + Platt calibration | 1.0090 | 0.6039 | 49.7% |
| Dixon-Coles | 1.0121 | 0.6057 | 49.7% |
| Elo + Dixon-Coles blend **(production)** | 1.0084 | 0.6034 | 49.8% |
| Gradient boosting (no odds) | 1.0102 | 0.6045 | 49.6% |
| Gradient boosting (with odds) | 0.9964 | 0.5940 | 51.3% |

Log loss by league:

| league | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|
| ALL | nan | 1.0098 | 1.0090 | 1.0121 | 1.0084 | 1.0102 | 0.9964 |
| AUT | nan | 1.0324 | 1.0291 | 1.0329 | 1.0306 | 1.0290 | 1.0192 |
| B1 | nan | 1.0041 | 1.0016 | 1.0061 | 1.0027 | 1.0042 | 0.9897 |
| D1 | nan | 0.9886 | 0.9902 | 0.9924 | 0.9888 | 0.9910 | 0.9757 |
| D2 | nan | 1.0513 | 1.0513 | 1.0580 | 1.0527 | 1.0530 | 1.0448 |
| DNK | nan | 1.0223 | 1.0218 | 1.0255 | 1.0221 | 1.0239 | 1.0084 |
| E0 | nan | 0.9858 | 0.9849 | 0.9853 | 0.9835 | 0.9895 | 0.9758 |
| E1 | nan | 1.0474 | 1.0474 | 1.0484 | 1.0462 | 1.0519 | 1.0384 |
| F1 | nan | 1.0009 | 1.0001 | 1.0050 | 1.0010 | 1.0037 | 0.9930 |
| F2 | nan | 1.0692 | 1.0685 | 1.0709 | 1.0673 | 1.0698 | 1.0525 |
| G1 | nan | 0.9534 | 0.9512 | 0.9540 | 0.9503 | 0.9489 | 0.9344 |
| I1 | nan | 0.9806 | 0.9809 | 0.9825 | 0.9781 | 0.9826 | 0.9709 |
| I2 | nan | 1.0617 | 1.0625 | 1.0645 | 1.0603 | 1.0619 | 1.0475 |
| N1 | nan | 0.9621 | 0.9580 | 0.9656 | 0.9604 | 0.9577 | 0.9558 |
| NOR | nan | 0.9849 | 0.9879 | 0.9813 | 0.9810 | 0.9874 | 0.9654 |
| P1 | nan | 0.9354 | 0.9323 | 0.9409 | 0.9315 | 0.9321 | 0.9241 |
| POL | 1.0439 | 1.0544 | 1.0532 | 1.0563 | 1.0541 | 1.0557 | 1.0489 |
| ROU | 1.0156 | 1.0387 | 1.0368 | 1.0405 | 1.0374 | 1.0385 | 1.0195 |
| SC0 | nan | 0.9699 | 0.9664 | 0.9703 | 0.9675 | 0.9626 | 0.9536 |
| SP1 | nan | 0.9673 | 0.9682 | 0.9733 | 0.9679 | 0.9690 | 0.9580 |
| SP2 | nan | 1.0464 | 1.0455 | 1.0486 | 1.0455 | 1.0471 | 1.0251 |
| SWZ | 1.0203 | 1.0375 | 1.0377 | 1.0344 | 1.0336 | 1.0329 | 1.0212 |
| T1 | nan | 0.9737 | 0.9725 | 0.9791 | 0.9726 | 0.9744 | 0.9483 |

Log loss by season:

| season | n | bookmaker | elo | elo+platt | dixon_coles | blend | gbm | gbm_odds |
|---|---|---|---|---|---|---|---|---|
| 2023-24 | 7090 | 0.9822 | 1.0015 | 1.0019 | 1.0059 | 1.0013 | 1.0034 | 0.9837 |
| 2024-25 | 6960 | 0.9901 | 1.0121 | 1.0102 | 1.0128 | 1.0098 | 1.0121 | 0.9933 |
| 2025-26 | 6929 | 0.9987 | 1.0182 | 1.0172 | 1.0199 | 1.0166 | 1.0176 | 1.0008 |
| 2026-27 | 1924 | nan | 1.0015 | 1.0012 | 1.0039 | 0.9995 | 1.0018 | 1.0385 |

Gap to the bookmaker (model minus bookmaker log loss; negative = model better), 95% CI from a bootstrap over weeks:

- Elo: +nan  [+0.0180, +0.0231]
- Elo + Platt calibration: +nan  [+0.0173, +0.0222]
- Dixon-Coles: +nan  [+0.0204, +0.0253]
- Elo + Dixon-Coles blend: +nan  [+0.0169, +0.0214]
- Gradient boosting (no odds): +nan  [+0.0185, +0.0233]
- Gradient boosting (with odds): +nan  [+0.0013, +0.0031]

By bookmaker odds source (the benchmark is weaker where Pinnacle closing odds are missing):

| odds source | n | bookmaker | Elo + Dixon-Coles blend | gap |
|---|---|---|---|---|
| avg_closing | 5783 | 0.9934 | 1.0130 | +0.0196 |
| pinnacle_closing | 16963 | 0.9878 | 1.0068 | +0.0190 |

Matches involving a newly promoted team:

| subset | n | bookmaker | Elo | Dixon-Coles | Elo + Dixon-Coles blend |
|---|---|---|---|---|---|
| others | 15183 | nan | 1.0061 | 1.0077 | 1.0049 |
| promoted team | 7720 | nan | 1.0171 | 1.0207 | 1.0151 |

## 3. Calibration on the test period

Expected calibration error (count-weighted |predicted - observed|, 10 bins):

| model | home | draw | away |
|---|---|---|---|
| Bookmaker (closing, margin removed) | nan | nan | nan |
| Dixon-Coles | 0.0078 | 0.0140 | 0.0116 |
| Elo | 0.0098 | 0.0039 | 0.0110 |
| Elo + Dixon-Coles blend | 0.0061 | 0.0057 | 0.0092 |

Reliability table, Elo + Dixon-Coles blend (bins with n >= 30):

| outcome | bin | n | mean predicted | observed |
|---|---|---|---|---|
| home | 0.0-0.1 | 232 | 0.081 | 0.099 |
| home | 0.1-0.2 | 1288 | 0.157 | 0.150 |
| home | 0.2-0.3 | 2754 | 0.257 | 0.264 |
| home | 0.3-0.4 | 5506 | 0.354 | 0.359 |
| home | 0.4-0.5 | 6147 | 0.448 | 0.448 |
| home | 0.5-0.6 | 3815 | 0.544 | 0.538 |
| home | 0.6-0.7 | 1855 | 0.642 | 0.658 |
| home | 0.7-0.8 | 875 | 0.747 | 0.775 |
| home | 0.8-0.9 | 404 | 0.839 | 0.842 |
| draw | 0.0-0.1 | 162 | 0.082 | 0.086 |
| draw | 0.1-0.2 | 2215 | 0.164 | 0.162 |
| draw | 0.2-0.3 | 17638 | 0.261 | 0.268 |
| draw | 0.3-0.4 | 2888 | 0.314 | 0.313 |
| away | 0.0-0.1 | 1014 | 0.070 | 0.051 |
| away | 0.1-0.2 | 3785 | 0.159 | 0.148 |
| away | 0.2-0.3 | 7396 | 0.252 | 0.252 |
| away | 0.3-0.4 | 5713 | 0.345 | 0.334 |
| away | 0.4-0.5 | 2709 | 0.443 | 0.428 |
| away | 0.5-0.6 | 1242 | 0.545 | 0.528 |
| away | 0.6-0.7 | 672 | 0.644 | 0.664 |
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

Test period (22903 matches). Log loss (lower is better):

| market | baseline | model raw | model calibrated | bookmaker | calibration error raw -> calibrated |
|---|---|---|---|---|---|
| over_1_5 | 0.5442 | 0.5420 | 0.5396 | - | 0.0235 -> 0.0096 |
| over_2_5 | 0.6897 | 0.6852 | 0.6820 | 0.6713 | 0.0318 -> 0.0178 |
| over_3_5 | 0.6143 | 0.6097 | 0.6068 | - | 0.0237 -> 0.0142 |
| btts | 0.6893 | 0.6891 | 0.6858 | - | 0.0318 -> 0.0147 |

Over/under 2.5 vs bookmaker on 17748 matches: model 0.6820, bookmaker 0.6713, gap +0.0107 [+0.0089, +0.0125]

Calibrated: when the model gave at least X%, how often did it happen?

| market | side | min | n | avg predicted | happened |
|---|---|---|---|---|---|
| over_1_5 | over | 50% | 22903 | 75.5% | 76.4% |
| over_1_5 | over | 60% | 22879 | 75.5% | 76.4% |
| over_1_5 | over | 70% | 19578 | 76.8% | 77.5% |
| over_1_5 | over | 80% | 4342 | 82.6% | 83.7% |
| over_2_5 | over | 50% | 12573 | 56.3% | 58.2% |
| over_2_5 | over | 60% | 2494 | 63.8% | 66.2% |
| over_2_5 | over | 70% | 148 | 73.4% | 76.4% |
| over_2_5 | over | 80% | 7 | 80.8% | 85.7% |
| over_2_5 | under | 50% | 10330 | 55.2% | 53.4% |
| over_2_5 | under | 60% | 1229 | 62.5% | 58.0% |
| over_2_5 | under | 70% | 4 | 70.8% | 50.0% |
| over_3_5 | over | 50% | 121 | 53.7% | 48.8% |
| over_3_5 | over | 60% | 8 | 62.5% | 62.5% |
| over_3_5 | under | 50% | 22782 | 70.8% | 69.4% |
| over_3_5 | under | 60% | 21424 | 71.7% | 70.5% |
| over_3_5 | under | 70% | 13054 | 75.4% | 74.3% |
| over_3_5 | under | 80% | 1529 | 82.0% | 78.0% |
| btts | over | 50% | 17052 | 55.1% | 56.2% |
| btts | over | 60% | 1581 | 62.0% | 62.6% |
| btts | over | 70% | 7 | 72.3% | 42.9% |
| btts | under | 50% | 5851 | 52.7% | 50.2% |
| btts | under | 60% | 45 | 61.2% | 53.3% |

Production calibrators ({'over_1_5': 'platt', 'over_2_5': 'platt', 'over_3_5': 'platt', 'btts': 'platt'}) fitted on 44138 out-of-sample matches -> data/models/goals_calibration.json

## 5. Asian handicap (main line), test period

22903 matches. Home side, stake-weighted: predicted win/push/lose 43.3% / 13.6% / 43.1%, actual 43.3% / 14.1% / 42.6%.
Average profit per unit at our own fair odds: -0.001 (0 = calibrated; negative = we were too optimistic).

| our chance | bets | avg chance | won | push | lost | profit at fair odds |
|---|---|---|---|---|---|---|
| <45% | 102 | 44.7% | 27.5% | 29.4% | 43.1% | -0.091 |
| 45-50% | 22801 | 48.1% | 40.6% | 14.0% | 45.3% | -0.014 |
| 50-55% | 22801 | 51.9% | 45.3% | 14.0% | 40.6% | +0.013 |
| 55-60% | 102 | 55.3% | 43.1% | 29.4% | 27.5% | +0.073 |

Against bookmaker closing AH odds, at the bookmaker's own line (16556 matches, pushes excluded). Log loss, lower is better:

| odds source | n | ours | bookmaker | gap |
|---|---|---|---|---|
| avg_closing | 4050 | 0.7118 | 0.6925 | +0.0193 |
| b365_closing | 1 | 1.0260 | 0.6545 | +0.3715 |
| pinnacle_closing | 12505 | 0.7107 | 0.6922 | +0.0184 |
| ALL | 16556 | 0.7110 | 0.6923 | +0.0187 [+0.0159, +0.0214] |

Backing our side whenever our fair odds beat the closing price (any edge): 13736 bets, avg odds 1.95, profit -496.8 units, ROI -3.6%

Backing our side whenever our fair odds beat the closing price (edge 5%+): 9932 bets, avg odds 1.95, profit -432.2 units, ROI -4.4%

## 6. Half-time result (check of the early-result method), test period

First-half share of goals, fitted before the test period: 0.4448. 17743 matches with half-time scores.
Log loss: model 1.0446 vs league-average baseline 1.0802; accuracy 44.8% vs 40.7%.
Half-time draws: predicted 41.4%, happened 40.7%.

| predicted HT draw | n | avg predicted | happened |
|---|---|---|---|
| 0.2-0.3 | 363 | 27.2% | 27.3% |
| 0.3-0.4 | 6078 | 36.9% | 36.3% |
| 0.4-0.5 | 10826 | 43.9% | 43.1% |
| 0.5-0.6 | 471 | 51.6% | 51.2% |

## 7. Derived markets (one consistent scoreline grid), test period

Baseline = each league's outcome frequencies in earlier seasons. Log loss, lower is better.

| market | n | model | baseline | gap | calibration error |
|---|---|---|---|---|---|
| Result & both teams score | 22903 | 1.6656 | 1.7362 | -0.0706 | 0.3 pts |
| Result & over/under 2.5 | 22903 | 1.6487 | 1.7190 | -0.0703 | 0.4 pts |
| Home team over/under 0.5 | 22903 | 0.5075 | 0.5315 | -0.0240 | 1.5 pts |
| Home team over/under 1.5 | 22903 | 0.6535 | 0.6868 | -0.0333 | 0.9 pts |
| Away team over/under 0.5 | 22903 | 0.5900 | 0.6105 | -0.0206 | 0.9 pts |
| Away team over/under 1.5 | 22903 | 0.6201 | 0.6469 | -0.0268 | 1.1 pts |
| Exact total goals | 22903 | 1.7189 | 1.7295 | -0.0106 | 0.3 pts |
| Odd/even goals | 22903 | 0.6933 | 0.6933 | -0.0001 | 0.8 pts |
| Half-time result | 17743 | 1.0433 | 1.0802 | -0.0368 | 0.3 pts |
| Half-time/full-time | 17743 | 1.8938 | 1.9686 | -0.0748 | 0.4 pts |
| 1st half over/under 0.5 | 17743 | 0.5977 | 0.6010 | -0.0033 | 1.7 pts |
| 1st half over/under 1.5 | 17743 | 0.6418 | 0.6459 | -0.0041 | 1.8 pts |
| Highest-scoring half | 17743 | 1.0721 | 1.0728 | -0.0007 | 0.4 pts |
| Home win to nil | 22903 | 0.5148 | 0.5406 | -0.0258 | 0.5 pts |
| Away win to nil | 22903 | 0.4059 | 0.4315 | -0.0256 | 1.0 pts |
