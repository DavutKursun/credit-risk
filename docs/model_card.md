# Model card — credit-risk (filled at Milestone 4)

- **Models:** scorecard (optbinning WoE + logistic regression) and LightGBM, each with and without Lending Club grade features
- **Intended use:** portfolio demonstration of PD modelling with out-of-time validation; not a production credit decision system
- **Training data:** Lending Club 36-month loans issued 2012–2014 (train); 2015H1 for calibration and threshold choice
- **Evaluation:** 2015H2, once; metrics in README
- **Known limitations:** matured cohorts only (survivorship of the 2015 vintage noted); US consumer loans 2012–2015 — no claim about other markets or years; no protected attributes in the data, fairness audited on proxies only
- **Ethical considerations:** decisions are explained; the audit shows approval-rate differences across proxy groups without establishing their cause
