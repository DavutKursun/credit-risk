"""The review UI (Gradio, mounted at /ui): Application · Policy · Monitoring · About.

Application: a form prefilled from the three sample applications, both deployed models side by side, and what-if sliders for
income, debt-to-income, revolving utilization and FICO that re-score live. Policy and Monitoring show the committed dev results.
"""

from __future__ import annotations

import json

import gradio as gr
import pandas as pd
from PIL import Image
from pydantic import ValidationError

from .config import RESULTS
from .features import FEATURE_LABELS
from .schema import SAMPLE_APPLICATIONS, Application
from .serving import DEPLOYED, Scorer

SAMPLES = list(SAMPLE_APPLICATIONS)
FIELDS = ["loan_amnt", "int_rate", "installment", "annual_inc", "dti", "fico_range_low", "delinq_2yrs", "inq_last_6mths", "open_acc", "pub_rec", "revol_bal", "revol_util",
          "total_acc", "mort_acc", "pub_rec_bankruptcies", "earliest_cr_line", "emp_length", "grade", "sub_grade", "home_ownership", "verification_status", "purpose",
          "addr_state", "initial_list_status", "application_type"]
BUREAU = ["acc_open_past_24mths", "bc_open_to_buy", "total_bc_limit", "bc_util", "tot_cur_bal", "num_tl_op_past_12m", "mo_sin_rcnt_tl", "mths_since_recent_inq", "percent_bc_gt_75"]
INTS = {"fico_range_low", "delinq_2yrs", "inq_last_6mths", "open_acc", "pub_rec", "total_acc", "mort_acc", "pub_rec_bankruptcies", "acc_open_past_24mths", "num_tl_op_past_12m",
        "mo_sin_rcnt_tl", "mths_since_recent_inq"}
ABOUT = """
## About this demo
**Data.** Lending Club loans 2007–2018Q4 (public, Kaggle). The models use 36-month loans issued 2012–2015 whose outcome is known:
train 2012–2014 (306,462 loans), dev 2015H1 (120,790) for calibration and thresholds, test 2015H2 (162,236) used once.

**Protocol.** Out-of-time: everything in dev and test was issued after everything in train. Every feature is known at
application (leakage audit in the repository). PDs are calibrated on dev; the decision uses a threshold chosen on dev and a ±2 point
review band. Test AUC 0.705 (LightGBM) and 0.697 (scorecard) against 0.681 for Lending Club's grade alone; ECE 0.007 / 0.009.

**Limits.** Historical, public data from one lender, 2012–2015. No bureau pull, no income verification, no pricing, no regulatory
sign-off. The grade and rate are Lending Club's own risk outputs: they enter the models but are never given as a reason.
Fairness is audited on proxies only (see the repository). **This is not a credit decision system.**

**Privacy.** Nothing you type is stored or logged: the server logs the method, path, status and latency of each call, never a field.

Repository: https://github.com/DavutKursun/credit-risk · design notes `docs/DESIGN.md` · model card `docs/model_card.md`
"""


def _img(name: str):
    p = RESULTS / name
    return Image.open(p) if p.exists() else None


def _policy_table() -> pd.DataFrame:
    p = json.loads((RESULTS / "policy_dev.json").read_text(encoding="utf-8"))
    rows = []
    for r in p["policies"]:
        rows.append({"policy": r["policy"], "threshold": r.get("threshold"), "approve": r["approve"], "review": r["review"], "decline": r["decline"],
                     "default rate among approved": r["default_rate_approved"], "realized P&L per approved loan": r["realized_pnl_per_approved"],
                     "per $ lent": r.get("realized_pnl_per_dollar_lent"), "defaults avoided / 1,000 vs sub-grade cut": r.get("defaults_avoided_per_1000_vs_subgrade_cut"),
                     "vs approve-all": r.get("defaults_avoided_per_1000_vs_approve_all")})
    return pd.DataFrame(rows)


def _monitoring_table(scorer: Scorer) -> pd.DataFrame:
    m = scorer.monitoring()
    rows = [{"feature": f["feature"], **{q: f["psi"][q] for q in m["quarters"]}, "driven by": f["driven_by"], "status": f["status"]} for f in m["features"]]
    return pd.DataFrame(rows)


def _reasons_md(r) -> str:
    head = f"### PD **{r.pd:.1%}** → **{r.decision.upper()}**"
    if r.score_points is not None:
        head += f" · {r.score_points} points"
    head += f"\n\n`{r.model}` · policy `{r.policy}`: approve below {r.threshold - r.review_band:.3f}, review within ±{r.review_band:.2f} of {r.threshold:.3f}, decline above"
    items = "\n".join(f"{i + 1}. {x.text}  *({'+' if x.direction == 'raises' else '−'}{abs(x.contribution):.2f})*" for i, x in enumerate(r.reasons))
    notice = f"\n\n> {r.adverse_action}" if r.adverse_action else ""
    return f"{head}\n\n{items}{notice}"


def build(scorer: Scorer) -> gr.Blocks:
    def to_application(*values) -> Application:
        d = dict(zip(FIELDS + BUREAU, values, strict=True))
        d["fico_range_high"] = int(d["fico_range_low"]) + 4 if d.get("fico_range_low") is not None else None
        clean = {}
        for k, v in d.items():
            if v is None or v == "":
                continue
            clean[k] = round(float(v)) if k in INTS or k == "fico_range_high" else v
        return Application(**clean)

    def score_both(*values):
        try:
            app = to_application(*values)
        except (ValidationError, ValueError, TypeError) as e:
            msg = f"**Invalid application:** {str(e).splitlines()[0][:300]}"
            return msg, msg
        return _reasons_md(scorer.score("lgbm", app)), _reasons_md(scorer.score("scorecard", app))

    def fill(sample: str):
        s = SAMPLE_APPLICATIONS[sample]
        return [s.get(k) for k in FIELDS + BUREAU]

    with gr.Blocks(title="credit-risk") as demo:
        gr.Markdown("# credit-risk — probability of default, decision and reasons\nTwo models side by side: LightGBM and a scorecard, both calibrated on 2015H1 and tested once on 2015H2. "
                    f"Policy in force: **{scorer.policy}** (LightGBM threshold {scorer.threshold('lgbm'):.3f}, scorecard {scorer.threshold('scorecard'):.3f}, review band ±{scorer.band:.2f}). Version {scorer.version}.")
        with gr.Tabs():
            with gr.Tab("Application"):
                sample = gr.Dropdown(choices=SAMPLES, value="borderline", label="Prefill from a sample application")
                s0 = SAMPLE_APPLICATIONS["borderline"]
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("**What-if sliders** (re-score live)")
                        annual_inc = gr.Slider(10_000, 300_000, value=s0["annual_inc"], step=1_000, label=FEATURE_LABELS["annual_inc"] + " ($)")
                        dti = gr.Slider(0, 45, value=s0["dti"], step=0.5, label=FEATURE_LABELS["dti"] + " (%)")
                        revol_util = gr.Slider(0, 120, value=s0["revol_util"], step=1, label=FEATURE_LABELS["revol_util"] + " (%)")
                        fico = gr.Slider(660, 845, value=s0["fico_range_low"], step=5, label="FICO (range low; high = low + 4)")
                        gr.Markdown("**Loan and borrower**")
                        loan_amnt = gr.Number(value=s0["loan_amnt"], label="Loan amount ($)")
                        int_rate = gr.Number(value=s0["int_rate"], label="Interest rate (%)")
                        installment = gr.Number(value=s0["installment"], label="Monthly installment ($)")
                        grade = gr.Dropdown(choices=list("ABCDEFG"), value=s0["grade"], label="Lending Club grade")
                        sub_grade = gr.Dropdown(choices=[f"{g}{i}" for g in "ABCDEFG" for i in range(1, 6)], value=s0["sub_grade"], label="Sub-grade")
                        emp_length = gr.Dropdown(choices=["< 1 year", "1 year", "2 years", "3 years", "4 years", "5 years", "6 years", "7 years", "8 years", "9 years", "10+ years", "n/a"],
                                                 value=s0["emp_length"], label="Employment length")
                        home_ownership = gr.Dropdown(choices=["RENT", "OWN", "MORTGAGE", "ANY", "OTHER", "NONE"], value=s0["home_ownership"], label="Home ownership")
                        verification_status = gr.Dropdown(choices=["Not Verified", "Source Verified", "Verified"], value=s0["verification_status"], label="Income verification")
                        purpose = gr.Dropdown(choices=["debt_consolidation", "credit_card", "home_improvement", "other", "major_purchase", "medical", "small_business", "car", "moving",
                                                       "vacation", "house", "wedding", "renewable_energy", "educational"], value=s0["purpose"], label="Purpose")
                        addr_state = gr.Textbox(value=s0["addr_state"], label="State (2 letters; not a model input)")
                        initial_list_status = gr.Dropdown(choices=["w", "f"], value="w", label="Listing status")
                        application_type = gr.Dropdown(choices=["Individual", "Joint App"], value="Individual", label="Application type")
                    with gr.Column(scale=1):
                        gr.Markdown("**Credit file**")
                        delinq_2yrs = gr.Number(value=s0["delinq_2yrs"], label="Delinquencies in the last 2 years", precision=0)
                        inq_last_6mths = gr.Number(value=s0["inq_last_6mths"], label="Inquiries in the last 6 months", precision=0)
                        open_acc = gr.Number(value=s0["open_acc"], label="Open credit lines", precision=0)
                        total_acc = gr.Number(value=s0["total_acc"], label="Total credit lines", precision=0)
                        pub_rec = gr.Number(value=s0["pub_rec"], label="Public records", precision=0)
                        pub_rec_bankruptcies = gr.Number(value=s0["pub_rec_bankruptcies"], label="Bankruptcies", precision=0)
                        revol_bal = gr.Number(value=s0["revol_bal"], label="Revolving balance ($)")
                        mort_acc = gr.Number(value=s0["mort_acc"], label="Mortgage accounts", precision=0)
                        earliest_cr_line = gr.Textbox(value=s0["earliest_cr_line"], label="Earliest credit line (Mon-YYYY)")
                        gr.Markdown("**Bureau attributes** (optional; blank = not on file)")
                        acc_open_past_24mths = gr.Number(value=s0.get("acc_open_past_24mths"), label="Accounts opened in the last 24 months", precision=0)
                        num_tl_op_past_12m = gr.Number(value=s0.get("num_tl_op_past_12m"), label="Accounts opened in the last 12 months", precision=0)
                        mo_sin_rcnt_tl = gr.Number(value=s0.get("mo_sin_rcnt_tl"), label="Months since the most recent account", precision=0)
                        mths_since_recent_inq = gr.Number(value=s0.get("mths_since_recent_inq"), label="Months since the most recent inquiry (blank = none on file)", precision=0)
                        bc_open_to_buy = gr.Number(value=s0.get("bc_open_to_buy"), label="Bankcard open-to-buy ($)")
                        total_bc_limit = gr.Number(value=s0.get("total_bc_limit"), label="Total bankcard limit ($)")
                        bc_util = gr.Number(value=s0.get("bc_util"), label="Bankcard utilization (%)")
                        percent_bc_gt_75 = gr.Number(value=s0.get("percent_bc_gt_75"), label="Share of bankcards above 75% of limit (%)")
                        tot_cur_bal = gr.Number(value=s0.get("tot_cur_bal"), label="Total current balance of all accounts ($)")
                score_btn = gr.Button("Score with both models", variant="primary")
                with gr.Row():
                    out_lgbm = gr.Markdown("*LightGBM: press Score*")
                    out_card = gr.Markdown("*Scorecard: press Score*")
                inputs = [loan_amnt, int_rate, installment, annual_inc, dti, fico, delinq_2yrs, inq_last_6mths, open_acc, pub_rec, revol_bal, revol_util, total_acc, mort_acc,
                          pub_rec_bankruptcies, earliest_cr_line, emp_length, grade, sub_grade, home_ownership, verification_status, purpose, addr_state, initial_list_status,
                          application_type, acc_open_past_24mths, bc_open_to_buy, total_bc_limit, bc_util, tot_cur_bal, num_tl_op_past_12m, mo_sin_rcnt_tl, mths_since_recent_inq,
                          percent_bc_gt_75]
                score_btn.click(score_both, inputs=inputs, outputs=[out_lgbm, out_card])
                for s in (annual_inc, dti, revol_util, fico):
                    s.change(score_both, inputs=inputs, outputs=[out_lgbm, out_card])  # live re-score while the slider moves
                sample.change(fill, inputs=[sample], outputs=inputs).then(score_both, inputs=inputs, outputs=[out_lgbm, out_card])
            with gr.Tab("Policy"):
                gr.Markdown("## Which threshold makes money\nProfit curves on dev (2015H1): expected profit and realized P&L of the approved set against the PD threshold. "
                            "The expected-value threshold (0.41 LightGBM / 0.40 scorecard) approves 99.5% of applications: with a loss given default of 0.31 and 36 months of interest, "
                            "every grade is profitable on average, the break-even PD runs from 28% (grade A) to 59% (G), above almost every applicant's PD. The model's value is in "
                            "ranking applicants at the approval rate a lender chooses: at 85% approval LightGBM admits 12.3% defaulters against 12.8% for Lending Club's sub-grade cut "
                            "and earns $1,063 per approved loan against $1,015 (dev; test: 11.8% vs 12.3%, $1,022 vs $976). The policy in force here is the 85% operating point.")
                with gr.Row():
                    gr.Image(value=_img(f"profit_curve_dev_{DEPLOYED['lgbm']}.png"), label="LightGBM profit curve (dev)", interactive=False)
                    gr.Image(value=_img(f"profit_curve_dev_{DEPLOYED['scorecard']}.png"), label="Scorecard profit curve (dev)", interactive=False)
                gr.Dataframe(value=_policy_table(), label="Policies on dev: approve-all, grades A–C, sub-grade cuts, expected value and fixed approval rates", interactive=False, wrap=True)
            with gr.Tab("Monitoring"):
                gr.Markdown("## Population stability by quarter\nPSI of every feature and of the deployed scores, train (2012–2014) against each quarter of 2015. "
                            "**Rule of thumb: below 0.10 stable, 0.10–0.25 watch, above 0.25 act (retrain or investigate).** Value drift and missingness are measured apart; "
                            "a status driven by missingness (the bureau columns, missing for early-2012 listings only) is documented, not actionable. "
                            "Interest rate (repricing) and listing status (a channel change) move first; the scores stay below 0.02.")
                gr.Image(value=_img("psi_by_quarter.png"), label="PSI heat map", interactive=False)
                gr.Dataframe(value=_monitoring_table(scorer), label="PSI by quarter (max of value and missingness PSI)", interactive=False)
            with gr.Tab("About"):
                gr.Markdown(ABOUT)
    return demo
