# Reason codes on dev (lgbm-bureau-no-state, scorecard-bureau-no-state; thresholds lgbm-bureau-no-state 0.253, scorecard-bureau-no-state 0.248 = 85 approval rate)

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
**lgbm-bureau-no-state**: PD 0.253, review

1. Home ownership: RENT (associated with more defaults) (+0.084)
2. Debt-to-income ratio 21.8% is higher than 75% of approved borrowers (+0.072)
3. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.069)
4. Loan amount relative to income 0.29 is higher than 75% of approved borrowers (+0.049)
5. FICO score 682 is lower than 75% of approved borrowers (+0.048)

**scorecard-bureau-no-state**: PD 0.283, decline

1. Home ownership: RENT (associated with more defaults) (+0.064)
2. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.061)
3. Credit inquiries in the last 6 months 2 is higher than 90% of approved borrowers (+0.058)
4. Debt-to-income ratio 21.8% is higher than 75% of approved borrowers (+0.047)
5. Loan amount relative to income 0.29 is higher than 75% of approved borrowers (+0.041)

> Principal reasons for this decision: Home ownership: RENT (associated with more defaults); Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers; Credit inquiries in the last 6 months 2 is higher than 90% of approved borrowers; Debt-to-income ratio 21.8% is higher than 75% of approved borrowers.

## Sample: clear_decline
**lgbm-bureau-no-state**: PD 0.402, decline

1. Loan purpose: small_business (associated with more defaults) (+0.502)
2. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.318)
3. Debt-to-income ratio 33.9% is higher than 95% of approved borrowers (+0.194)
4. Credit inquiries in the last 6 months 5 is higher than 95% of approved borrowers (+0.168)
5. Loan amount relative to income 0.63 is higher than 95% of approved borrowers (+0.158)

> Principal reasons for this decision: Loan purpose: small_business (associated with more defaults); Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers; Debt-to-income ratio 33.9% is higher than 95% of approved borrowers; Credit inquiries in the last 6 months 5 is higher than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.392, decline

1. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.287)
2. Debt-to-income ratio 33.9% is higher than 95% of approved borrowers (+0.139)
3. Loan purpose: small_business (associated with more defaults) (+0.121)
4. Loan amount relative to income 0.63 is higher than 95% of approved borrowers (+0.086)
5. FICO score 662 is lower than 95% of approved borrowers (+0.082)

> Principal reasons for this decision: Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers; Debt-to-income ratio 33.9% is higher than 95% of approved borrowers; Loan purpose: small_business (associated with more defaults); Loan amount relative to income 0.63 is higher than 95% of approved borrowers.

## Dev loan 50526960 — grade D4, outcome: charged off
**lgbm-bureau-no-state**: PD 0.278, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.417)
2. Debt-to-income ratio 30.6% is higher than 95% of approved borrowers (+0.172)
3. Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers (+0.162)
4. Total bankcard credit limit $3,000 is lower than 95% of approved borrowers (+0.102)
5. Share of bankcards above 75% of their limit 0.0% supports approval (better than 90% of approved borrowers) (−0.085)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Debt-to-income ratio 30.6% is higher than 95% of approved borrowers; Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers; Total bankcard credit limit $3,000 is lower than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.283, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.287)
2. Debt-to-income ratio 30.6% is higher than 95% of approved borrowers (+0.139)
3. Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers (+0.064)
4. Share of bankcards above 75% of their limit 0.0% supports approval (better than 90% of approved borrowers) (−0.062)
5. Total bankcard credit limit $3,000 is lower than 95% of approved borrowers (+0.038)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Debt-to-income ratio 30.6% is higher than 95% of approved borrowers; Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers; Total bankcard credit limit $3,000 is lower than 95% of approved borrowers.

## Dev loan 48604527 — grade D3, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.287, decline

1. Annual income $24,669 is lower than 95% of approved borrowers (+0.157)
2. Home ownership: RENT (associated with more defaults) (+0.112)
3. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.076)
4. FICO score 672 is lower than 90% of approved borrowers (+0.073)
5. Accounts opened in the last 12 months 4 is higher than 95% of approved borrowers (+0.066)

> Principal reasons for this decision: Annual income $24,669 is lower than 95% of approved borrowers; Home ownership: RENT (associated with more defaults); Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers; FICO score 672 is lower than 90% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.283, decline

1. Annual income $24,669 is lower than 95% of approved borrowers (+0.178)
2. Home ownership: RENT (associated with more defaults) (+0.064)
3. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.061)
4. FICO score 672 is lower than 90% of approved borrowers (+0.061)
5. Loan amount relative to income 0.32 is higher than 90% of approved borrowers (+0.058)

> Principal reasons for this decision: Annual income $24,669 is lower than 95% of approved borrowers; Home ownership: RENT (associated with more defaults); Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers; FICO score 672 is lower than 90% of approved borrowers.

## Dev loan 41348903 — grade C5, outcome: charged off
**lgbm-bureau-no-state**: PD 0.309, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.467)
2. Debt-to-income ratio 34.5% is higher than 95% of approved borrowers (+0.223)
3. Annual income $30,000 is lower than 95% of approved borrowers (+0.173)
4. Accounts opened in the last 12 months 7 is higher than 95% of approved borrowers (+0.128)
5. Months since the most recent credit inquiry 1.0 months is lower than 90% of approved borrowers (+0.112)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Debt-to-income ratio 34.5% is higher than 95% of approved borrowers; Annual income $30,000 is lower than 95% of approved borrowers; Accounts opened in the last 12 months 7 is higher than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.279, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.287)
2. Debt-to-income ratio 34.5% is higher than 95% of approved borrowers (+0.139)
3. Annual income $30,000 is lower than 95% of approved borrowers (+0.134)
4. Credit inquiries in the last 6 months 3 is higher than 95% of approved borrowers (+0.079)
5. Loan purpose: credit_card (associated with fewer defaults) (−0.076)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Debt-to-income ratio 34.5% is higher than 95% of approved borrowers; Annual income $30,000 is lower than 95% of approved borrowers; Credit inquiries in the last 6 months 3 is higher than 95% of approved borrowers.

## Dev loan 48676667 — grade E1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.335, decline

1. Employment length: missing (associated with more defaults) (+0.212)
2. Annual income $24,000 is lower than 95% of approved borrowers (+0.155)
3. Total credit lines 5 is lower than 95% of approved borrowers (+0.144)
4. Months since the most recent credit inquiry 1.0 months is lower than 90% of approved borrowers (+0.115)
5. Home ownership: RENT (associated with more defaults) (+0.097)

> Principal reasons for this decision: Employment length: missing (associated with more defaults); Annual income $24,000 is lower than 95% of approved borrowers; Total credit lines 5 is lower than 95% of approved borrowers; Months since the most recent credit inquiry 1.0 months is lower than 90% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.306, decline

1. Annual income $24,000 is lower than 95% of approved borrowers (+0.178)
2. Loan purpose: other (associated with more defaults) (+0.121)
3. Accounts opened in the last 24 months 3 supports approval (better than 50% of approved borrowers) (−0.065)
4. Home ownership: RENT (associated with more defaults) (+0.064)
5. FICO score 672 is lower than 90% of approved borrowers (+0.061)

> Principal reasons for this decision: Annual income $24,000 is lower than 95% of approved borrowers; Loan purpose: other (associated with more defaults); Home ownership: RENT (associated with more defaults); FICO score 672 is lower than 90% of approved borrowers.

## Dev loan 46426382 — grade D2, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.387, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.507)
2. Delinquencies in the last 2 years 4 is higher than 95% of approved borrowers (+0.178)
3. FICO score 662 is lower than 95% of approved borrowers (+0.156)
4. Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers (+0.150)
5. Annual income $89,000 supports approval (better than 50% of approved borrowers) (−0.109)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; Delinquencies in the last 2 years 4 is higher than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers; Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.283, decline

1. Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers (+0.287)
2. Annual income $89,000 supports approval (better than 50% of approved borrowers) (−0.116)
3. FICO score 662 is lower than 95% of approved borrowers (+0.082)
4. Home ownership: RENT (associated with more defaults) (+0.064)
5. Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers (+0.064)

> Principal reasons for this decision: Accounts opened in the last 24 months 12 is higher than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers; Home ownership: RENT (associated with more defaults); Accounts opened in the last 12 months 8 is higher than 95% of approved borrowers.

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

## Dev loan 27651914 — grade D3, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.203, approve

1. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.179)
2. Revolving balance $51,517 is higher than 95% of approved borrowers (+0.154)
3. Debt-to-income ratio 32.4% is higher than 95% of approved borrowers (+0.149)
4. FICO score 662 is lower than 95% of approved borrowers (+0.110)
5. Annual income $46,000 is lower than 90% of approved borrowers (+0.093)

**scorecard-bureau-no-state**: PD 0.174, approve

1. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.162)
2. Debt-to-income ratio 32.4% is higher than 95% of approved borrowers (+0.139)
3. Loan purpose: other (associated with more defaults) (+0.121)
4. FICO score 662 is lower than 95% of approved borrowers (+0.082)
5. Total current balance of all accounts $186,298 supports approval (better than 50% of approved borrowers) (−0.041)

## Agreement and leading reasons

Top-3 reasons overlap in at least one feature for 98.7% of 2,000 sampled dev rows; the #1 reason is the same feature for 61.8%.

**lgbm-bureau-no-state**: #1 reason over 13,981 declined rows: Accounts opened in the last 24 months 42.0%, Annual income 13.6%, Debt-to-income ratio 13.4%, Employment length 11.0%, Loan purpose 4.1%, Revolving balance 3.0%, Total bankcard credit limit 2.8%, Bankcard utilization 2.4%

**scorecard-bureau-no-state**: #1 reason over 13,351 declined rows: Accounts opened in the last 24 months 52.6%, Annual income 26.1%, Debt-to-income ratio 13.9%, Loan amount relative to income 3.6%, Loan purpose 2.4%, FICO score 0.7%, Home ownership 0.5%, Credit inquiries in the last 6 months 0.1%


Text check: no raw column names or NaN in any reason text
