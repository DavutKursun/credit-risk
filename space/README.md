---
title: credit-risk
emoji: 🏦
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
license: mit
pinned: false
short_description: Loan default PD, decision by policy, five reasons — tested out of time
---

# credit-risk — probability of default, decision and reasons, validated the way a bank would

Scores a loan application with two models side by side, LightGBM and a points scorecard, both calibrated on 2015H1 Lending Club
loans and tested once on 2015H2 (AUC 0.705 / 0.697 against 0.681 for the lender's own grade; ECE 0.007 / 0.009). The decision
applies the 85% operating-point thresholds chosen on dev with a ±2 point review band, and every decision carries five reasons in
adverse-action wording that never name the grade itself. Historical public data; not a credit decision system; nothing you type
is stored. Open **/ui** for the review screen, **/docs** for the API; repository: https://github.com/DavutKursun/credit-risk
