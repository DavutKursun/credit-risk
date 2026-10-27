# Economics on train (306,462 loans, 2012-01..2014-12)

LGD on 40,596 charged-off loans: mean 0.314, median 0.290. Median gain if repaid $2,125, median loss if default $3,141, median break-even PD 40.1%; scheduled interest exceeds LGD × principal for 7.8% of loans. Realized P&L on train: $1,330 per loan, 10.7% per dollar lent.

| Grade | Loans | Default rate | LGD mean | LGD median | n defaults | Gain if repaid (median) | Loss if default (median) | Break-even PD (median) | Break-even PD, grade LGD | Interest > LGD × principal | Realized P&L / loan |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 63,143 | 5.5% | 0.323 | 0.291 | 3,458 | $1,503 | $3,793 | 28.1% | 27.6% | 0.0% | $1,127 |
| B | 110,578 | 10.7% | 0.310 | 0.283 | 11,790 | $2,042 | $3,314 | 37.7% | 38.0% | 0.0% | $1,361 |
| C | 78,637 | 16.6% | 0.311 | 0.289 | 13,090 | $2,379 | $3,141 | 43.2% | 43.5% | 0.0% | $1,408 |
| D | 40,103 | 21.4% | 0.318 | 0.297 | 8,582 | $2,762 | $3,000 | 48.6% | 48.3% | 25.8% | $1,400 |
| E | 11,092 | 25.6% | 0.319 | 0.301 | 2,837 | $2,954 | $2,638 | 52.9% | 52.5% | 97.2% | $1,377 |
| F | 2,691 | 28.5% | 0.334 | 0.313 | 766 | $2,676 | $2,018 | 56.9% | 55.3% | 100.0% | $1,238 |
| G | 218 | 33.5% | 0.332 | 0.348 | 73 | $5,633 | $3,954 | 58.7% | 57.4% | 99.5% | $2,019 |

| Interest rate band | Loans | Default rate | Gain if repaid (median) | Loss if default (median) | Break-even PD (median) | Interest > LGD × principal | Realized P&L / loan |
|---|---|---|---|---|---|---|---|
| 5–10% | 79,636 | 6.1% | $1,558 | $3,769 | 28.7% | 0.0% | $1,143 |
| 10–15% | 146,165 | 13.0% | $2,149 | $3,141 | 40.1% | 0.0% | $1,364 |
| 15–20% | 69,223 | 20.1% | $2,692 | $3,125 | 47.4% | 18.2% | $1,453 |
| 20–25% | 11,084 | 25.0% | $2,833 | $2,419 | 53.8% | 100.0% | $1,447 |
| 25–30% | 354 | 36.7% | $4,314 | $3,019 | 58.7% | 100.0% | $1,350 |

- All numbers from the train split (loans issued 2012-01..2014-12); dev and test never read.
- Gain if repaid = installment × 36 − funded_amnt is scheduled interest: an upper bound, prepayment lowers it.
- Loss if default = LGD × funded_amnt with the overall train LGD; breakeven_pd_median_grade_lgd uses the grade's own LGD.
- Realized P&L = total_pymnt + recoveries − collection_recovery_fee − funded_amnt, a post-origination quantity used here only as a population check.
