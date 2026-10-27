# Reason codes on test (lgbm-bureau-no-state, scorecard-bureau-no-state; thresholds lgbm-bureau-no-state 0.253, scorecard-bureau-no-state 0.248 = 85 approval rate)

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

## Dev loan 66402443 — grade C5, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.278, decline

1. Employment length: missing (associated with more defaults) (+0.311)
2. Debt-to-income ratio 29.9% is higher than 95% of approved borrowers (+0.158)
3. Credit inquiries in the last 6 months 4 is higher than 95% of approved borrowers (+0.142)
4. Accounts opened in the last 24 months 7 is higher than 90% of approved borrowers (+0.116)
5. Months since the most recent credit inquiry 0.0 months is lower than 95% of approved borrowers (+0.099)

> Principal reasons for this decision: Employment length: missing (associated with more defaults); Debt-to-income ratio 29.9% is higher than 95% of approved borrowers; Credit inquiries in the last 6 months 4 is higher than 95% of approved borrowers; Accounts opened in the last 24 months 7 is higher than 90% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.275, decline

1. Accounts opened in the last 24 months 7 is higher than 90% of approved borrowers (+0.149)
2. Debt-to-income ratio 29.9% is higher than 95% of approved borrowers (+0.139)
3. Credit inquiries in the last 6 months 4 is higher than 95% of approved borrowers (+0.079)
4. FICO score 672 is lower than 90% of approved borrowers (+0.061)
5. Months since the most recent credit inquiry 0.0 months is lower than 95% of approved borrowers (+0.060)

> Principal reasons for this decision: Accounts opened in the last 24 months 7 is higher than 90% of approved borrowers; Debt-to-income ratio 29.9% is higher than 95% of approved borrowers; Credit inquiries in the last 6 months 4 is higher than 95% of approved borrowers; FICO score 672 is lower than 90% of approved borrowers.

## Dev loan 65302450 — grade D1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.287, decline

1. Accounts opened in the last 24 months 10 is higher than 95% of approved borrowers (+0.312)
2. Annual income $15,000 is lower than 95% of approved borrowers (+0.172)
3. FICO score 662 is lower than 95% of approved borrowers (+0.134)
4. Loan amount relative to income 0.40 is higher than 95% of approved borrowers (+0.117)
5. Loan amount $6,000 supports approval (better than 90% of approved borrowers) (−0.077)

> Principal reasons for this decision: Accounts opened in the last 24 months 10 is higher than 95% of approved borrowers; Annual income $15,000 is lower than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers; Loan amount relative to income 0.40 is higher than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.334, decline

1. Accounts opened in the last 24 months 10 is higher than 95% of approved borrowers (+0.287)
2. Annual income $15,000 is lower than 95% of approved borrowers (+0.178)
3. Loan amount relative to income 0.40 is higher than 95% of approved borrowers (+0.086)
4. FICO score 662 is lower than 95% of approved borrowers (+0.082)
5. Loan purpose: credit_card (associated with fewer defaults) (−0.076)

> Principal reasons for this decision: Accounts opened in the last 24 months 10 is higher than 95% of approved borrowers; Annual income $15,000 is lower than 95% of approved borrowers; Loan amount relative to income 0.40 is higher than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers.

## Dev loan 59729293 — grade F1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.309, decline

1. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.207)
2. Debt-to-income ratio 39.2% is higher than 95% of approved borrowers (+0.207)
3. Annual income $22,000 is lower than 95% of approved borrowers (+0.200)
4. Revolving balance $164 is lower than 95% of approved borrowers (+0.158)
5. Total bankcard credit limit $300 is lower than 95% of approved borrowers (+0.146)

> Principal reasons for this decision: Debt-to-income ratio 39.2% is higher than 95% of approved borrowers; Annual income $22,000 is lower than 95% of approved borrowers; Revolving balance $164 is lower than 95% of approved borrowers; Total bankcard credit limit $300 is lower than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.294, decline

1. Annual income $22,000 is lower than 95% of approved borrowers (+0.178)
2. Accounts opened in the last 24 months 2 supports approval (better than 75% of approved borrowers) (−0.162)
3. Debt-to-income ratio 39.2% is higher than 95% of approved borrowers (+0.139)
4. FICO score 662 is lower than 95% of approved borrowers (+0.082)
5. Home ownership: RENT (associated with more defaults) (+0.064)

> Principal reasons for this decision: Annual income $22,000 is lower than 95% of approved borrowers; Debt-to-income ratio 39.2% is higher than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers; Home ownership: RENT (associated with more defaults).

## Dev loan 65605742 — grade C2, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.335, decline

1. Accounts opened in the last 24 months 11 is higher than 95% of approved borrowers (+0.321)
2. Annual income $28,000 is lower than 95% of approved borrowers (+0.207)
3. Debt-to-income ratio 25.7% is higher than 75% of approved borrowers (+0.155)
4. FICO score 672 is lower than 90% of approved borrowers (+0.092)
5. Accounts opened in the last 12 months 4 is higher than 95% of approved borrowers (+0.086)

> Principal reasons for this decision: Accounts opened in the last 24 months 11 is higher than 95% of approved borrowers; Annual income $28,000 is lower than 95% of approved borrowers; Debt-to-income ratio 25.7% is higher than 75% of approved borrowers; FICO score 672 is lower than 90% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.332, decline

1. Accounts opened in the last 24 months 11 is higher than 95% of approved borrowers (+0.287)
2. Annual income $28,000 is lower than 95% of approved borrowers (+0.134)
3. Loan purpose: other (associated with more defaults) (+0.121)
4. Debt-to-income ratio 25.7% is higher than 75% of approved borrowers (+0.100)
5. Home ownership: RENT (associated with more defaults) (+0.064)

> Principal reasons for this decision: Accounts opened in the last 24 months 11 is higher than 95% of approved borrowers; Annual income $28,000 is lower than 95% of approved borrowers; Loan purpose: other (associated with more defaults); Debt-to-income ratio 25.7% is higher than 75% of approved borrowers.

## Dev loan 66613420 — grade E1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.388, decline

1. Debt-to-income ratio 34.4% is higher than 95% of approved borrowers (+0.246)
2. FICO score 662 is lower than 95% of approved borrowers (+0.118)
3. Annual income $39,000 is lower than 90% of approved borrowers (+0.117)
4. Months since the most recent credit inquiry 0.0 months is lower than 95% of approved borrowers (+0.102)
5. Home ownership: RENT (associated with more defaults) (+0.093)

> Principal reasons for this decision: Debt-to-income ratio 34.4% is higher than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers; Annual income $39,000 is lower than 90% of approved borrowers; Months since the most recent credit inquiry 0.0 months is lower than 95% of approved borrowers.

**scorecard-bureau-no-state**: PD 0.332, decline

1. Debt-to-income ratio 34.4% is higher than 95% of approved borrowers (+0.139)
2. FICO score 662 is lower than 95% of approved borrowers (+0.082)
3. Annual income $39,000 is lower than 90% of approved borrowers (+0.081)
4. Home ownership: RENT (associated with more defaults) (+0.064)
5. Accounts opened in the last 24 months 5 is higher than 75% of approved borrowers (+0.061)

> Principal reasons for this decision: Debt-to-income ratio 34.4% is higher than 95% of approved borrowers; FICO score 662 is lower than 95% of approved borrowers; Annual income $39,000 is lower than 90% of approved borrowers; Home ownership: RENT (associated with more defaults).

## Dev loan 68587652 — grade A1, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.010, approve

1. FICO score 797 supports approval (better than 95% of approved borrowers) (−0.354)
2. Total current balance of all accounts $430,856 supports approval (better than 90% of approved borrowers) (−0.225)
3. Annual income $150,000 supports approval (better than 90% of approved borrowers) (−0.198)
4. Accounts opened in the last 24 months 1 supports approval (better than 90% of approved borrowers) (−0.195)
5. Share of bankcards above 75% of their limit 0.0% supports approval (better than 90% of approved borrowers) (−0.140)

**scorecard-bureau-no-state**: PD 0.006, approve

1. Accounts opened in the last 24 months 1 supports approval (better than 90% of approved borrowers) (−0.262)
2. FICO score 797 supports approval (better than 95% of approved borrowers) (−0.222)
3. Annual income $150,000 supports approval (better than 90% of approved borrowers) (−0.167)
4. Total current balance of all accounts $430,856 supports approval (better than 90% of approved borrowers) (−0.119)
5. Debt-to-income ratio 9.5% supports approval (better than 90% of approved borrowers) (−0.088)

## Dev loan 55988377 — grade C4, outcome: fully paid
**lgbm-bureau-no-state**: PD 0.200, approve

1. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.226)
2. Total credit lines 64 supports approval (better than 95% of approved borrowers) (−0.178)
3. Months since the most recent credit inquiry 1.0 months is lower than 90% of approved borrowers (+0.107)
4. FICO score 667 is lower than 90% of approved borrowers (+0.090)
5. Accounts opened in the last 12 months 6 is higher than 95% of approved borrowers (+0.079)

**scorecard-bureau-no-state**: PD 0.240, review

1. Accounts opened in the last 24 months 9 is higher than 95% of approved borrowers (+0.287)
2. Total bankcard credit limit $68,080 supports approval (better than 95% of approved borrowers) (−0.104)
3. Credit inquiries in the last 6 months 3 is higher than 95% of approved borrowers (+0.079)
4. Home ownership: MORTGAGE (associated with fewer defaults) (−0.072)
5. FICO score 667 is lower than 90% of approved borrowers (+0.067)

## Agreement and leading reasons

Top-3 reasons overlap in at least one feature for 98.3% of 2,000 sampled test rows; the #1 reason is the same feature for 59.1%.

**lgbm-bureau-no-state**: #1 reason over 15,775 declined rows: Accounts opened in the last 24 months 43.5%, Employment length 12.3%, Annual income 12.2%, Debt-to-income ratio 11.5%, Revolving balance 4.3%, Loan purpose 4.2%, Total bankcard credit limit 2.7%, Bankcard utilization 2.6%

**scorecard-bureau-no-state**: #1 reason over 14,499 declined rows: Accounts opened in the last 24 months 55.0%, Annual income 26.1%, Debt-to-income ratio 12.4%, Loan amount relative to income 3.2%, Loan purpose 2.3%, FICO score 0.6%, Home ownership 0.4%, Credit inquiries in the last 6 months 0.1%


Text check: no raw column names or NaN in any reason text
