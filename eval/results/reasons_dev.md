# Reason codes on dev (lgbm-bureau-no-state, scorecard-bureau-no-state; thresholds lgbm-bureau-no-state 0.410, scorecard-bureau-no-state 0.400 = expected-value)

## Sample: clear_approve
**lgbm-bureau-no-state**: PD 0.026, approve

1. FICO score 762 supports approval (better than 90% of approved borrowers) (−0.208)
2. Annual income $95,000 supports approval (better than 75% of approved borrowers) (−0.163)
3. Share of bankcards above 75% of their limit 0.0% supports approval (better than 90% of approved borrowers) (−0.151)
4. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.142)
5. Debt-to-income ratio 9.5% supports approval (better than 90% of approved borrowers) (−0.116)

**scorecard-bureau-no-state**: PD 0.006, approve

1. FICO score 762 supports approval (better than 90% of approved borrowers) (−0.222)
2. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.162)
3. Annual income $95,000 supports approval (better than 75% of approved borrowers) (−0.116)
4. Debt-to-income ratio 9.5% supports approval (better than 90% of approved borrowers) (−0.088)
5. Loan purpose: credit_card (associated with fewer defaults) (−0.076)

## Sample: borderline
**lgbm-bureau-no-state**: PD 0.253, approve

1. Home ownership: RENT (associated with more defaults) (+0.084)
2. Debt-to-income ratio 21.8% is higher than 75% of approved borrowers (+0.072)
3. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.069)
4. Loan amount relative to income 0.29 is higher than 75% of approved borrowers (+0.049)
5. FICO score 682 is lower than 75% of approved borrowers (+0.048)

**scorecard-bureau-no-state**: PD 0.283, approve

1. Home ownership: RENT (associated with more defaults) (+0.064)
2. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.061)
3. Credit inquiries in the last 6 months 2 is higher than 90% of approved borrowers (+0.058)
4. Debt-to-income ratio 21.8% is higher than 75% of approved borrowers (+0.047)
5. Loan amount relative to income 0.29 is higher than 75% of approved borrowers (+0.041)

## Sample: clear_decline
**lgbm-bureau-no-state**: PD 0.402, review

1. Loan purpose: small_business (associated with more defaults) (+0.502)
2. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.318)
3. Debt-to-income ratio 33.9% is higher than 95% of approved borrowers (+0.194)
4. Credit inquiries in the last 6 months 5 is higher than 95% of approved borrowers (+0.168)
5. Loan amount relative to income 0.63 is higher than 95% of approved borrowers (+0.158)

**scorecard-bureau-no-state**: PD 0.392, review

1. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.287)
2. Debt-to-income ratio 33.9% is higher than 95% of approved borrowers (+0.139)
3. Loan purpose: small_business (associated with more defaults) (+0.121)
4. Loan amount relative to income 0.63 is higher than 95% of approved borrowers (+0.086)
5. FICO score 662 is lower than 95% of approved borrowers (+0.082)

## Dev loan 38141807 — grade E5, outcome: charged off
**lgbm-bureau-no-state**: PD 0.402, review

1. Employment length: missing (associated with more defaults) (+0.288)
2. Annual income $27,383 is lower than 95% of approved borrowers (+0.192)
3. Debt-to-income ratio 34.0% is higher than 95% of approved borrowers (+0.166)
4. Accounts opened in the last 24 months 6 is higher than 75% of approved borrowers (+0.142)
5. FICO score 662 is lower than 95% of approved borrowers (+0.119)

**scorecard-bureau-no-state**: PD 0.345, approve

1. Debt-to-income ratio 34.0% is higher than 95% of approved borrowers (+0.139)
2. Annual income $27,383 is lower than 95% of approved borrowers (+0.134)
3. Accounts opened in the last 24 months 6 is higher than 75% of approved borrowers (+0.126)
4. Loan amount relative to income 0.34 is higher than 90% of approved borrowers (+0.086)
5. FICO score 662 is lower than 95% of approved borrowers (+0.082)

## Dev loan 46756257 — grade D5, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.402, review

1. Total bankcard credit limit $1,800 is lower than 95% of approved borrowers (+0.206)
2. Delinquencies in the last 2 years 2 is higher than 95% of approved borrowers (+0.192)
3. Accounts opened in the last 24 months 6 is higher than 75% of approved borrowers (+0.167)
4. Debt-to-income ratio 27.7% is higher than 90% of approved borrowers (+0.166)
5. Months since the most recent credit inquiry 1.0 months is lower than 90% of approved borrowers (+0.120)

**scorecard-bureau-no-state**: PD 0.392, review

1. Accounts opened in the last 24 months 6 is higher than 75% of approved borrowers (+0.126)
2. Debt-to-income ratio 27.7% is higher than 90% of approved borrowers (+0.100)
3. Loan amount relative to income 0.35 is higher than 90% of approved borrowers (+0.086)
4. FICO score 662 is lower than 95% of approved borrowers (+0.082)
5. Home ownership: RENT (associated with more defaults) (+0.064)

## Dev loan 43225410 — grade E2, outcome: charged off
**lgbm-bureau-no-state**: PD 0.402, review

1. Loan purpose: small_business (associated with more defaults) (+0.604)
2. Debt-to-income ratio 30.5% is higher than 95% of approved borrowers (+0.152)
3. Annual income $45,000 is lower than 90% of approved borrowers (+0.096)
4. Open credit lines 25 is higher than 95% of approved borrowers (+0.090)
5. Total credit lines 46 supports approval (better than 90% of approved borrowers) (−0.087)

**scorecard-bureau-no-state**: PD 0.306, approve

1. Debt-to-income ratio 30.5% is higher than 95% of approved borrowers (+0.139)
2. Loan purpose: small_business (associated with more defaults) (+0.121)
3. Home ownership: MORTGAGE (associated with fewer defaults) (−0.072)
4. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.061)
5. Loan amount relative to income 0.32 is higher than 90% of approved borrowers (+0.058)

## Dev loan 51075913 — grade G1, outcome: charged off
**lgbm-bureau-no-state**: PD 0.402, review

1. Accounts opened in the last 24 months 14 is higher than 95% of approved borrowers (+0.483)
2. Accounts opened in the last 12 months 11 is higher than 95% of approved borrowers (+0.181)
3. Debt-to-income ratio 24.6% is higher than 75% of approved borrowers (+0.145)
4. Home ownership: RENT (associated with more defaults) (+0.084)
5. Months since the most recent account was opened 1.0 months is lower than 95% of approved borrowers (+0.077)

**scorecard-bureau-no-state**: PD 0.349, approve

1. Accounts opened in the last 24 months 14 is higher than 95% of approved borrowers (+0.287)
2. Home ownership: RENT (associated with more defaults) (+0.064)
3. Accounts opened in the last 12 months 11 is higher than 95% of approved borrowers (+0.064)
4. Debt-to-income ratio 24.6% is higher than 75% of approved borrowers (+0.063)
5. Credit inquiries in the last 6 months 2 is higher than 90% of approved borrowers (+0.058)

## Dev loan 42494412 — grade E2, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.402, review

1. Loan purpose: small_business (associated with more defaults) (+0.509)
2. Accounts opened in the last 24 months 8 is higher than 95% of approved borrowers (+0.264)
3. Debt-to-income ratio 28.4% is higher than 90% of approved borrowers (+0.170)
4. Loan amount relative to income 0.48 is higher than 95% of approved borrowers (+0.119)
5. FICO score 662 is lower than 95% of approved borrowers (+0.117)

**scorecard-bureau-no-state**: PD 0.392, review

1. Accounts opened in the last 24 months 8 is higher than 95% of approved borrowers (+0.287)
2. Loan purpose: small_business (associated with more defaults) (+0.121)
3. Debt-to-income ratio 28.4% is higher than 90% of approved borrowers (+0.100)
4. Loan amount relative to income 0.48 is higher than 95% of approved borrowers (+0.086)
5. FICO score 662 is lower than 95% of approved borrowers (+0.082)

## Dev loan 50839265 — grade A1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.010, approve

1. FICO score 777 supports approval (better than 95% of approved borrowers) (−0.331)
2. Total current balance of all accounts $441,808 supports approval (better than 90% of approved borrowers) (−0.245)
3. Annual income $140,000 supports approval (better than 90% of approved borrowers) (−0.211)
4. Debt-to-income ratio 7.5% supports approval (better than 90% of approved borrowers) (−0.171)
5. Share of bankcards above 75% of their limit 0.0% supports approval (better than 90% of approved borrowers) (−0.153)

**scorecard-bureau-no-state**: PD 0.006, approve

1. FICO score 777 supports approval (better than 95% of approved borrowers) (−0.222)
2. Annual income $140,000 supports approval (better than 90% of approved borrowers) (−0.167)
3. Total current balance of all accounts $441,808 supports approval (better than 90% of approved borrowers) (−0.119)
4. Total bankcard credit limit $151,000 supports approval (better than 95% of approved borrowers) (−0.104)
5. Bankcard open-to-buy $106,550 supports approval (better than 95% of approved borrowers) (−0.102)

## Dev loan 46847589 — grade C3, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.278, approve

1. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.327)
2. Debt-to-income ratio 32.5% is higher than 95% of approved borrowers (+0.152)
3. Home ownership: RENT (associated with more defaults) (+0.095)
4. Annual income $74,600 supports approval (better than 50% of approved borrowers) (−0.082)
5. FICO score 682 is lower than 75% of approved borrowers (+0.055)

**scorecard-bureau-no-state**: PD 0.275, approve

1. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.287)
2. Debt-to-income ratio 32.5% is higher than 95% of approved borrowers (+0.139)
3. Home ownership: RENT (associated with more defaults) (+0.064)
4. Annual income $74,600 supports approval (better than 50% of approved borrowers) (−0.050)
5. FICO score 682 is lower than 75% of approved borrowers (+0.037)

## Agreement and leading reasons

Top-3 reasons overlap in at least one feature for 98.7% of 2,000 sampled dev rows; the #1 reason is the same feature for 61.8%.


Text check: no raw column names or NaN in any reason text
