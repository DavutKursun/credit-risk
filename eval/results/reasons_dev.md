# Reason codes on dev (lgbm-bureau-no-state, scorecard-bureau-no-state)

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
**lgbm-bureau-no-state**: PD 0.253, approve

1. Lending Club sub-grade: C5 (associated with more defaults) (+0.300)
2. Installment relative to income 0.12 is higher than 75% of approved borrowers (+0.106)
3. Home ownership: RENT (associated with more defaults) (+0.084)
4. Debt-to-income ratio 21.8% is higher than 75% of approved borrowers (+0.072)
5. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.069)

**scorecard-bureau-no-state**: PD 0.283, approve

1. Lending Club sub-grade: C5 (associated with more defaults) (+0.207)
2. Installment relative to income 0.12 is higher than 75% of approved borrowers (+0.133)
3. Home ownership: RENT (associated with more defaults) (+0.064)
4. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.061)
5. Credit inquiries in the last 6 months 2 is higher than 90% of approved borrowers (+0.058)

## Sample: clear_decline
**lgbm-bureau-no-state**: PD 0.402, review

1. Loan purpose: small_business (associated with more defaults) (+0.502)
2. Lending Club sub-grade: F2 (associated with more defaults) (+0.352)
3. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.318)
4. Installment relative to income 0.30 is higher than 95% of approved borrowers (+0.246)
5. Debt-to-income ratio 33.9% is higher than 95% of approved borrowers (+0.194)

**scorecard-bureau-no-state**: PD 0.392, review

1. Lending Club sub-grade: F2 (associated with more defaults) (+0.409)
2. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.287)
3. Installment relative to income 0.30 is higher than 95% of approved borrowers (+0.249)
4. Debt-to-income ratio 33.9% is higher than 95% of approved borrowers (+0.139)
5. Loan purpose: small_business (associated with more defaults) (+0.121)

## Dev loan 38141807 — grade E5, outcome: charged off
**lgbm-bureau-no-state**: PD 0.402, review

1. Lending Club sub-grade: E5 (associated with more defaults) (+0.412)
2. Employment length: missing (associated with more defaults) (+0.288)
3. Installment relative to income 0.15 is higher than 95% of approved borrowers (+0.246)
4. Annual income $27,383 is lower than 95% of approved borrowers (+0.192)
5. Debt-to-income ratio 34.0% is higher than 95% of approved borrowers (+0.166)

**scorecard-bureau-no-state**: PD 0.345, approve

1. Lending Club sub-grade: E5 (associated with more defaults) (+0.409)
2. Installment relative to income 0.15 is higher than 95% of approved borrowers (+0.249)
3. Debt-to-income ratio 34.0% is higher than 95% of approved borrowers (+0.139)
4. Annual income $27,383 is lower than 95% of approved borrowers (+0.134)
5. Accounts opened in the last 24 months 6 is higher than 75% of approved borrowers (+0.126)

## Dev loan 46756257 — grade D5, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.402, review

1. Lending Club sub-grade: D5 (associated with more defaults) (+0.414)
2. Installment relative to income 0.15 is higher than 95% of approved borrowers (+0.217)
3. Total bankcard credit limit $1,800 is lower than 95% of approved borrowers (+0.206)
4. Delinquencies in the last 2 years 2 is higher than 95% of approved borrowers (+0.192)
5. Accounts opened in the last 24 months 6 is higher than 75% of approved borrowers (+0.167)

**scorecard-bureau-no-state**: PD 0.392, review

1. Lending Club sub-grade: D5 (associated with more defaults) (+0.409)
2. Installment relative to income 0.15 is higher than 95% of approved borrowers (+0.249)
3. Accounts opened in the last 24 months 6 is higher than 75% of approved borrowers (+0.126)
4. Debt-to-income ratio 27.7% is higher than 90% of approved borrowers (+0.100)
5. Loan amount relative to income 0.35 is higher than 90% of approved borrowers (+0.086)

## Dev loan 43225410 — grade E2, outcome: charged off
**lgbm-bureau-no-state**: PD 0.402, review

1. Loan purpose: small_business (associated with more defaults) (+0.604)
2. Lending Club sub-grade: E2 (associated with more defaults) (+0.466)
3. Installment relative to income 0.14 is higher than 90% of approved borrowers (+0.176)
4. Debt-to-income ratio 30.5% is higher than 95% of approved borrowers (+0.152)
5. Lending Club grade: E (associated with more defaults) (+0.125)

**scorecard-bureau-no-state**: PD 0.306, approve

1. Lending Club sub-grade: E2 (associated with more defaults) (+0.409)
2. Installment relative to income 0.14 is higher than 90% of approved borrowers (+0.170)
3. Debt-to-income ratio 30.5% is higher than 95% of approved borrowers (+0.139)
4. Loan purpose: small_business (associated with more defaults) (+0.121)
5. Home ownership: MORTGAGE (associated with fewer defaults) (−0.072)

## Dev loan 43225410 — grade E2, outcome: charged off
**lgbm-bureau-no-state**: PD 0.402, review

1. Loan purpose: small_business (associated with more defaults) (+0.604)
2. Lending Club sub-grade: E2 (associated with more defaults) (+0.466)
3. Installment relative to income 0.14 is higher than 90% of approved borrowers (+0.176)
4. Debt-to-income ratio 30.5% is higher than 95% of approved borrowers (+0.152)
5. Lending Club grade: E (associated with more defaults) (+0.125)

**scorecard-bureau-no-state**: PD 0.306, approve

1. Lending Club sub-grade: E2 (associated with more defaults) (+0.409)
2. Installment relative to income 0.14 is higher than 90% of approved borrowers (+0.170)
3. Debt-to-income ratio 30.5% is higher than 95% of approved borrowers (+0.139)
4. Loan purpose: small_business (associated with more defaults) (+0.121)
5. Home ownership: MORTGAGE (associated with fewer defaults) (−0.072)

## Dev loan 51075913 — grade G1, outcome: charged off
**lgbm-bureau-no-state**: PD 0.402, review

1. Lending Club sub-grade: G1 (associated with more defaults) (+0.617)
2. Accounts opened in the last 24 months 14 is higher than 95% of approved borrowers (+0.483)
3. Interest rate 26.8% is higher than 95% of approved borrowers (+0.185)
4. Accounts opened in the last 12 months 11 is higher than 95% of approved borrowers (+0.181)
5. Installment relative to income 0.12 is higher than 75% of approved borrowers (+0.159)

**scorecard-bureau-no-state**: PD 0.349, approve

1. Lending Club sub-grade: G1 (associated with more defaults) (+0.409)
2. Accounts opened in the last 24 months 14 is higher than 95% of approved borrowers (+0.287)
3. Installment relative to income 0.12 is higher than 90% of approved borrowers (+0.133)
4. Home ownership: RENT (associated with more defaults) (+0.064)
5. Accounts opened in the last 12 months 11 is higher than 95% of approved borrowers (+0.064)

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

## Dev loan 48051748 — grade E1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.278, approve

1. Lending Club sub-grade: E1 (associated with more defaults) (+0.376)
2. Debt-to-income ratio 36.4% is higher than 95% of approved borrowers (+0.271)
3. Installment relative to income 0.22 is higher than 95% of approved borrowers (+0.221)
4. Accounts opened in the last 24 months 8 is higher than 95% of approved borrowers (+0.195)
5. Loan amount relative to income 0.50 is higher than 95% of approved borrowers (+0.133)

**scorecard-bureau-no-state**: PD 0.283, approve

1. Lending Club sub-grade: E1 (associated with more defaults) (+0.409)
2. Accounts opened in the last 24 months 8 is higher than 95% of approved borrowers (+0.287)
3. Installment relative to income 0.22 is higher than 95% of approved borrowers (+0.249)
4. Debt-to-income ratio 36.4% is higher than 95% of approved borrowers (+0.139)
5. Total bankcard credit limit $68,800 supports approval (better than 95% of approved borrowers) (−0.104)

## Agreement and leading reasons

Top-3 reasons overlap in at least one feature for 99.7% of 2,000 sampled dev rows; the #1 reason is the same feature for 64.8%.


Text check: no raw column names or NaN in any reason text
