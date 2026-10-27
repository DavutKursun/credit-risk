"""Pydantic models for the API: what a client sends and what it gets back.

`Application` carries only fields known when the loan is applied for (see leakage.py). Ranges are
validated so the model never sees nonsense; unknown fields are rejected.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Grade = Literal["A", "B", "C", "D", "E", "F", "G"]
HomeOwnership = Literal["RENT", "OWN", "MORTGAGE", "ANY", "OTHER", "NONE"]
Verification = Literal["Not Verified", "Source Verified", "Verified"]
Purpose = Literal[
    "debt_consolidation", "credit_card", "home_improvement", "other", "major_purchase", "medical", "small_business",
    "car", "moving", "vacation", "house", "wedding", "renewable_energy", "educational",
]
EmpLength = Literal["< 1 year", "1 year", "2 years", "3 years", "4 years", "5 years", "6 years", "7 years", "8 years", "9 years", "10+ years", "n/a"]


class Application(BaseModel):
    """A loan application as the lender sees it at origination."""

    model_config = ConfigDict(extra="forbid")

    loan_amnt: float = Field(ge=500, le=40_000)
    int_rate: float = Field(ge=1, le=35, description="annual rate in percent, e.g. 13.5")
    installment: float = Field(gt=0, le=2_000)
    annual_inc: float = Field(ge=0, le=10_000_000)
    dti: float = Field(ge=0, le=100, description="debt-to-income in percent, excluding this loan")
    fico_range_low: int = Field(ge=300, le=850)
    fico_range_high: int = Field(ge=300, le=850)
    delinq_2yrs: int = Field(ge=0, le=50)
    inq_last_6mths: int = Field(ge=0, le=50)
    open_acc: int = Field(ge=0, le=100)
    pub_rec: int = Field(ge=0, le=50)
    revol_bal: float = Field(ge=0, le=3_000_000)
    revol_util: float | None = Field(default=None, ge=0, le=200, description="percent; None when no revolving accounts")
    total_acc: int = Field(ge=0, le=200)
    mort_acc: int | None = Field(default=None, ge=0, le=60)
    pub_rec_bankruptcies: int | None = Field(default=None, ge=0, le=20)
    earliest_cr_line: str = Field(pattern=r"^[A-Z][a-z]{2}-\d{4}$", description="e.g. 'Aug-2001'")
    issue_d: str = Field(default="Dec-2015", pattern=r"^[A-Z][a-z]{2}-\d{4}$", description="application month; credit age is measured from it")
    emp_length: EmpLength = "n/a"
    grade: Grade | None = Field(default=None, description="Lending Club grade; omit for the no-LC-grade model")
    sub_grade: str | None = Field(default=None, pattern=r"^[A-G][1-5]$")
    home_ownership: HomeOwnership = "RENT"
    verification_status: Verification = "Not Verified"
    purpose: Purpose = "debt_consolidation"
    addr_state: str = Field(default="CA", pattern=r"^[A-Z]{2}$")
    initial_list_status: Literal["w", "f"] = "w"
    application_type: Literal["Individual", "Joint App"] = "Individual"
    # Opt-in bureau attributes (features.BUREAU_FEATURES), read only by the bureau model variants. None = not on file.
    acc_open_past_24mths: int | None = Field(default=None, ge=0, le=100, description="accounts opened in the last 24 months; None = not on file")
    bc_open_to_buy: float | None = Field(default=None, ge=0, le=2_000_000, description="bankcard open-to-buy in $; None = not on file")
    total_bc_limit: float | None = Field(default=None, ge=0, le=2_000_000, description="total bankcard credit limit in $; None = not on file")
    bc_util: float | None = Field(default=None, ge=0, le=200, description="bankcard utilization in percent; None = not on file")
    tot_cur_bal: float | None = Field(default=None, ge=0, le=10_000_000, description="total current balance of all accounts in $; None = not on file")
    num_tl_op_past_12m: int | None = Field(default=None, ge=0, le=50, description="accounts opened in the last 12 months; None = not on file")
    mo_sin_rcnt_tl: int | None = Field(default=None, ge=0, le=600, description="months since the most recent account was opened; None = not on file")
    mths_since_recent_inq: int | None = Field(default=None, ge=0, le=600, description="months since the most recent inquiry; None = no inquiry on file")
    percent_bc_gt_75: float | None = Field(default=None, ge=0, le=100, description="share of bankcards above 75% of their limit, in percent; None = not on file")


class Reason(BaseModel):
    feature: str
    value: str
    direction: Literal["raises", "lowers"]
    text: str
    contribution: float


class ScoreResponse(BaseModel):
    pd: float = Field(ge=0, le=1)
    decision: Literal["approve", "review", "decline"]
    reasons: list[Reason]
    score_points: int | None = None
    model: str
    version: str
    latency_ms: float


SAMPLE_APPLICATIONS: dict[str, dict] = {
    "clear_approve": dict(loan_amnt=8000, int_rate=7.9, installment=250.4, annual_inc=95000, dti=9.5, fico_range_low=760, fico_range_high=764,
                          delinq_2yrs=0, inq_last_6mths=0, open_acc=9, pub_rec=0, revol_bal=4200, revol_util=18.0, total_acc=24, mort_acc=2,
                          pub_rec_bankruptcies=0, earliest_cr_line="Jun-1998", emp_length="10+ years", grade="A", sub_grade="A3",
                          home_ownership="MORTGAGE", verification_status="Source Verified", purpose="credit_card", addr_state="TX",
                          acc_open_past_24mths=2, bc_open_to_buy=18600, total_bc_limit=22000, bc_util=15.5, tot_cur_bal=186000, num_tl_op_past_12m=1,
                          mo_sin_rcnt_tl=9, mths_since_recent_inq=14, percent_bc_gt_75=0.0),
    "borderline": dict(loan_amnt=15000, int_rate=15.6, installment=524.3, annual_inc=52000, dti=21.8, fico_range_low=680, fico_range_high=684,
                       delinq_2yrs=0, inq_last_6mths=2, open_acc=11, pub_rec=0, revol_bal=12800, revol_util=71.0, total_acc=28, mort_acc=0,
                       pub_rec_bankruptcies=0, earliest_cr_line="Mar-2006", emp_length="4 years", grade="C", sub_grade="C5",
                       home_ownership="RENT", verification_status="Verified", purpose="debt_consolidation", addr_state="FL",
                       acc_open_past_24mths=5, bc_open_to_buy=4300, total_bc_limit=15000, bc_util=71.3, tot_cur_bal=31500, num_tl_op_past_12m=2,
                       mo_sin_rcnt_tl=4, mths_since_recent_inq=2, percent_bc_gt_75=50.0),
    "clear_decline": dict(loan_amnt=24000, int_rate=24.5, installment=951.2, annual_inc=38000, dti=33.9, fico_range_low=660, fico_range_high=664,
                          delinq_2yrs=2, inq_last_6mths=5, open_acc=14, pub_rec=1, revol_bal=21000, revol_util=96.0, total_acc=31, mort_acc=0,
                          pub_rec_bankruptcies=1, earliest_cr_line="Sep-2009", emp_length="< 1 year", grade="F", sub_grade="F2",
                          home_ownership="RENT", verification_status="Not Verified", purpose="small_business", addr_state="NV",
                          acc_open_past_24mths=9, bc_open_to_buy=800, total_bc_limit=21000, bc_util=96.2, tot_cur_bal=24800, num_tl_op_past_12m=4,
                          mo_sin_rcnt_tl=2, mths_since_recent_inq=1, percent_bc_gt_75=100.0),
}
