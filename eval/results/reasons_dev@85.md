# Reason codes on dev (lgbm-bureau-no-state, scorecard-bureau-no-state; thresholds lgbm-bureau-no-state 0.253, scorecard-bureau-no-state 0.248 = 85 approval rate)

## Sample: clear_approve
**lgbm-bureau-no-state**: PD 0.026, approve

1. Lending Club sub-grade: A3 (associated with fewer defaults) (−0.301)
2. FICO score 762 supports approval (better than 90% of approved borrowers) (−0.208)
3. Annual income $95,000 supports approval (better than 75% of approved borrowers) (−0.163)
4. Share of bankcards above 75% of their limit 0.0% supports approval (better than 90% of approved borrowers) (−0.151)
5. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.142)

**scorecard-bureau-no-state**: PD 0.006, approve

1. Lending Club sub-grade: A3 (associated with fewer defaults) (−0.680)
2. FICO score 762 supports approval (better than 90% of approved borrowers) (−0.222)
3. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.162)
4. Installment relative to income 0.03 supports approval (better than 90% of approved borrowers) (−0.124)
5. Annual income $95,000 supports approval (better than 75% of approved borrowers) (−0.116)

## Sample: borderline
**lgbm-bureau-no-state**: PD 0.253, review

1. Lending Club sub-grade: C5 (associated with more defaults) (+0.300)
2. Installment relative to income 0.12 is higher than 75% of approved borrowers (+0.106)
3. Home ownership: RENT (associated with more defaults) (+0.084)
4. Debt-to-income ratio 21.8% is higher than 75% of approved borrowers (+0.072)
5. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.069)

**scorecard-bureau-no-state**: PD 0.283, decline

1. Lending Club sub-grade: C5 (associated with more defaults) (+0.207)
2. Installment relative to income 0.12 is higher than 75% of approved borrowers (+0.133)
3. Home ownership: RENT (associated with more defaults) (+0.064)
4. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.061)
5. Credit inquiries in the last 6 months 2 is higher than 90% of approved borrowers (+0.058)

> Principal reasons for this decision: Lending Club sub-grade: C5 (associated with more defaults); Installment relative to income 0.12 is higher than 75% of approved borrowers; Home ownership: RENT (associated with more defaults); Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers.

## Sample: clear_decline
**lgbm-bureau-no-state**: PD 0.402, decline

1. Loan purpose: small_business (associated with more defaults) (+0.502)
2. Lending Club sub-grade: F2 (associated with more defaults) (+0.352)
3. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.318)
4. Installment relative to income 0.30 is higher than 95% of approved borrowers (+0.246)
5. Debt-to-income ratio 33.9% is higher than 95% of approved borrowers (+0.194)

> Principal reasons for this decision: Loan purpose: small_business (associated with more defaults); Lending Club sub-grade: F2 (associated with more defaults); Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers; Installment relative to income 0.30 is higher than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.392, decline

1. Lending Club sub-grade: F2 (associated with more defaults) (+0.409)
2. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.287)
3. Installment relative to income 0.30 is higher than 95% of approved borrowers (+0.249)
4. Debt-to-income ratio 33.9% is higher than 95% of approved borrowers (+0.139)
5. Loan purpose: small_business (associated with more defaults) (+0.121)

> Principal reasons for this decision: Lending Club sub-grade: F2 (associated with more defaults); Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers; Installment relative to income 0.30 is higher than 95% of approved borrowers; Debt-to-income ratio 33.9% is higher than 95% of approved borrowers.

## Dev loan 50526960 — grade D4, outcome: charged off
**lgbm-bureau-no-state**: PD 0.278, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.417)
2. Lending Club sub-grade: D4 (associated with more defaults) (+0.265)
3. Debt-to-income ratio 30.6% is higher than 95% of approved borrowers (+0.172)
4. Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers (+0.162)
5. Total bankcard credit limit $3,000 is lower than 95% of approved borrowers (+0.102)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Lending Club sub-grade: D4 (associated with more defaults); Debt-to-income ratio 30.6% is higher than 95% of approved borrowers; Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.283, decline

1. Lending Club sub-grade: D4 (associated with more defaults) (+0.314)
2. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.287)
3. Debt-to-income ratio 30.6% is higher than 95% of approved borrowers (+0.139)
4. Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers (+0.064)
5. Share of bankcards above 75% of their limit 0.0% supports approval (better than 90% of approved borrowers) (−0.062)

> Principal reasons for this decision: Lending Club sub-grade: D4 (associated with more defaults); Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Debt-to-income ratio 30.6% is higher than 95% of approved borrowers; Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers.

## Dev loan 48604527 — grade D3, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.287, decline

1. Lending Club sub-grade: D3 (associated with more defaults) (+0.248)
2. Annual income $24,669 is lower than 95% of approved borrowers (+0.157)
3. Installment relative to income 0.14 is higher than 90% of approved borrowers (+0.146)
4. Home ownership: RENT (associated with more defaults) (+0.112)
5. Interest rate 17.0% is higher than 95% of approved borrowers (+0.082)

> Principal reasons for this decision: Lending Club sub-grade: D3 (associated with more defaults); Annual income $24,669 is lower than 95% of approved borrowers; Installment relative to income 0.14 is higher than 90% of approved borrowers; Home ownership: RENT (associated with more defaults).

**scorecard-bureau-no-state**: PD 0.283, decline

1. Lending Club sub-grade: D3 (associated with more defaults) (+0.274)
2. Annual income $24,669 is lower than 95% of approved borrowers (+0.178)
3. Installment relative to income 0.14 is higher than 90% of approved borrowers (+0.170)
4. Home ownership: RENT (associated with more defaults) (+0.064)
5. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.061)

> Principal reasons for this decision: Lending Club sub-grade: D3 (associated with more defaults); Annual income $24,669 is lower than 95% of approved borrowers; Installment relative to income 0.14 is higher than 90% of approved borrowers; Home ownership: RENT (associated with more defaults).

## Dev loan 41348903 — grade C5, outcome: charged off
**lgbm-bureau-no-state**: PD 0.309, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.467)
2. Debt-to-income ratio 34.5% is higher than 95% of approved borrowers (+0.223)
3. Lending Club sub-grade: C5 (associated with more defaults) (+0.174)
4. Annual income $30,000 is lower than 95% of approved borrowers (+0.173)
5. Accounts opened in the last 12 months 7 is higher than 95% of approved borrowers (+0.128)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Debt-to-income ratio 34.5% is higher than 95% of approved borrowers; Lending Club sub-grade: C5 (associated with more defaults); Annual income $30,000 is lower than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.279, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.287)
2. Lending Club sub-grade: C5 (associated with more defaults) (+0.207)
3. Debt-to-income ratio 34.5% is higher than 95% of approved borrowers (+0.139)
4. Annual income $30,000 is lower than 95% of approved borrowers (+0.134)
5. Installment relative to income 0.05 supports approval (better than 75% of approved borrowers) (−0.088)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Lending Club sub-grade: C5 (associated with more defaults); Debt-to-income ratio 34.5% is higher than 95% of approved borrowers; Annual income $30,000 is lower than 95% of approved borrowers.

## Dev loan 48676667 — grade E1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.335, decline

1. Lending Club sub-grade: E1 (associated with more defaults) (+0.253)
2. Employment length: missing (associated with more defaults) (+0.212)
3. Annual income $24,000 is lower than 95% of approved borrowers (+0.155)
4. Total credit lines 5 is lower than 95% of approved borrowers (+0.144)
5. Months since the most recent credit inquiry 1.0 months is lower than 90% of approved borrowers (+0.115)

> Principal reasons for this decision: Lending Club sub-grade: E1 (associated with more defaults); Employment length: missing (associated with more defaults); Annual income $24,000 is lower than 95% of approved borrowers; Total credit lines 5 is lower than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.306, decline

1. Lending Club sub-grade: E1 (associated with more defaults) (+0.409)
2. Annual income $24,000 is lower than 95% of approved borrowers (+0.178)
3. Loan purpose: other (associated with more defaults) (+0.121)
4. Accounts opened in the last 24 months 3 supports approval (better than 50% of approved borrowers) (−0.065)
5. Home ownership: RENT (associated with more defaults) (+0.064)

> Principal reasons for this decision: Lending Club sub-grade: E1 (associated with more defaults); Annual income $24,000 is lower than 95% of approved borrowers; Loan purpose: other (associated with more defaults); Home ownership: RENT (associated with more defaults).

## Dev loan 46426382 — grade D2, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.387, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.507)
2. Lending Club sub-grade: D2 (associated with more defaults) (+0.461)
3. Delinquencies in the last 2 years 4 is higher than 95% of approved borrowers (+0.178)
4. FICO score 662 is lower than 95% of approved borrowers (+0.156)
5. Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers (+0.150)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Lending Club sub-grade: D2 (associated with more defaults); Delinquencies in the last 2 years 4 is higher than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.283, decline

1. Lending Club sub-grade: D2 (associated with more defaults) (+0.314)
2. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.287)
3. Annual income $89,000 supports approval (better than 50% of approved borrowers) (−0.116)
4. Installment relative to income 0.04 supports approval (better than 75% of approved borrowers) (−0.108)
5. FICO score 662 is lower than 95% of approved borrowers (+0.082)

> Principal reasons for this decision: Lending Club sub-grade: D2 (associated with more defaults); Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers.

## Dev loan 50839265 — grade A1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.010, approve

1. Lending Club sub-grade: A1 (associated with fewer defaults) (−0.457)
2. Interest rate 5.3% supports approval (better than 95% of approved borrowers) (−0.424)
3. FICO score 777 supports approval (better than 95% of approved borrowers) (−0.331)
4. Total current balance of all accounts $441,808 supports approval (better than 90% of approved borrowers) (−0.245)
5. Annual income $140,000 supports approval (better than 90% of approved borrowers) (−0.211)

**scorecard-bureau-no-state**: PD 0.006, approve

1. Lending Club sub-grade: A1 (associated with fewer defaults) (−0.680)
2. FICO score 777 supports approval (better than 95% of approved borrowers) (−0.222)
3. Installment relative to income 0.02 supports approval (better than 95% of approved borrowers) (−0.181)
4. Annual income $140,000 supports approval (better than 90% of approved borrowers) (−0.167)
5. Total current balance of all accounts $441,808 supports approval (better than 90% of approved borrowers) (−0.119)

## Dev loan 27651914 — grade D3, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.203, approve

1. Lending Club sub-grade: D3 (associated with more defaults) (+0.220)
2. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.179)
3. Revolving balance $51,517 is higher than 95% of approved borrowers (+0.154)
4. Debt-to-income ratio 32.4% is higher than 95% of approved borrowers (+0.149)
5. FICO score 662 is lower than 95% of approved borrowers (+0.110)

**scorecard-bureau-no-state**: PD 0.174, approve

1. Lending Club sub-grade: D3 (associated with more defaults) (+0.274)
2. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.162)
3. Debt-to-income ratio 32.4% is higher than 95% of approved borrowers (+0.139)
4. Loan purpose: other (associated with more defaults) (+0.121)
5. Installment relative to income 0.05 supports approval (better than 75% of approved borrowers) (−0.108)

## Agreement and leading reasons

Top-3 reasons overlap in at least one feature for 99.7% of 2,000 sampled dev rows; the #1 reason is the same feature for 64.8%.

**lgbm-bureau-no-state**: #1 reason over 13,981 declined rows: Lending Club sub-grade 59.8%, Accounts opened in the last 24 months 23.4%, Employment length 7.9%, Loan purpose 2.4%, Debt-to-income ratio 1.7%, Annual income 1.6%, Installment relative to income 1.4%, Revolving balance 0.9%

**scorecard-bureau-no-state**: #1 reason over 13,351 declined rows: Lending Club sub-grade 71.5%, Accounts opened in the last 24 months 19.8%, Installment relative to income 7.4%, Annual income 1.1%, Debt-to-income ratio 0.2%, Loan purpose 0.0%


Text check: no raw column names or NaN in any reason text
