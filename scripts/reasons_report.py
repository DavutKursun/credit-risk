"""Reason codes on dev for the deployed pair: top-5 reasons for the three sample applications and for real dev rows (ids only),
the adverse-action text for the declines, the agreement rate of the two models' top-3 reasons over a random sample of dev rows,
and which feature leads the declines (#1 reason distribution over every declined dev row). Checks that no reason text carries a
raw column name or a NaN.

Usage: python scripts/reasons_report.py --variants lgbm-bureau,scorecard-bureau [--split dev] [--n 2000] [--policy-rate 0.85]
       [--thresholds-from eval/results/policy_dev.json]
Writes eval/results/reasons_<split>[@rate].json and .md. Test needs --final (M4).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, ID_COL, MODELS, RESULTS, REVIEW_BAND, SEED, TARGET
from credit_risk.data import load_split
from credit_risk.explain import adverse_action_text, contributions, reason_agreement, reason_codes
from credit_risk.features import ALL_RAW_COLUMNS, FEATURE_LABELS, application_frame, make_features
from credit_risk.models import ModelBundle
from credit_risk.policy import decide
from credit_risk.schema import SAMPLE_APPLICATIONS, Application

# Identifiers (raw column names and feature keys with an underscore, plus the bare 'dti' / 'fico' keys) must never appear verbatim in a
# reason text; plain words that happen to be column names (installment, grade, purpose) are legitimate English in a label.
RAW_TOKENS = {t for t in set(ALL_RAW_COLUMNS) | set(FEATURE_LABELS) if "_" in t} | {"dti", "fico"}


def _text_problems(reasons) -> list[str]:
    bad = []
    for r in reasons:
        tokens = set(r.text.replace("(", " ").replace(")", " ").replace(",", " ").replace(";", " ").split())
        if tokens & RAW_TOKENS or "nan" in r.text.lower().split() or "none" in r.text.lower().split():
            bad.append(r.text)
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", required=True, help="two bundle variants, LightGBM first, e.g. lgbm-bureau,scorecard-bureau")
    ap.add_argument("--split", default="dev", choices=["dev", "test"])
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--n", type=int, default=2000, help="dev rows sampled for the agreement rate")
    ap.add_argument("--thresholds-from", type=Path, default=None)
    ap.add_argument("--policy-rate", type=float, default=None, help="use the fixed-approval-rate thresholds (e.g. 0.85) from policy_dev.json instead of the EV ones")
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    a = ap.parse_args(argv)
    if a.split == "test" and not a.final:
        print("refusing: the test split is used once, at Milestone 4, with --final")
        return 3
    variants = a.variants.split(",")
    bundles = {v: ModelBundle.load(a.models_dir / f"{v}.joblib") for v in variants}
    thresholds_path = a.thresholds_from or (a.out / "policy_dev.json")
    policy = json.loads(thresholds_path.read_text(encoding="utf-8"))
    if a.policy_rate is not None:
        thresholds = {r["policy"].split("@")[0]: r["threshold"] for r in policy["policies"] if r["policy"].endswith(f"@{a.policy_rate:.0%}")}
    else:
        thresholds = policy["thresholds"]
    tag = f"@{round(100 * a.policy_rate)}" if a.policy_rate is not None else ""  # e.g. '@85': file names without a percent sign
    df = load_split(a.split, a.cohort_dir).reset_index(drop=True)
    y = df[TARGET].to_numpy()
    feats = {v: make_features(df, b.use_lc_grade, b.bureau) for v, b in bundles.items()}
    pds = {v: bundles[v].predict_pd(feats[v]) for v in variants}
    decisions = {v: decide(pds[v], thresholds[v], REVIEW_BAND) for v in variants}
    out = {"split": a.split, "variants": variants, "thresholds": {v: thresholds[v] for v in variants}, "policy_rate": a.policy_rate, "samples": {}, "examples": [], "problems": []}
    md = [f"# Reason codes on {a.split} ({', '.join(variants)}; thresholds {', '.join(f'{v} {thresholds[v]:.3f}' for v in variants)}{' = ' + tag[1:] + ' approval rate' if tag else ' = expected-value'})", ""]

    # 1. the three sample applications
    for name, app in SAMPLE_APPLICATIONS.items():
        fr = application_frame(Application(**app).model_dump())
        entry = {}
        md.append(f"## Sample: {name}")
        for v, b in bundles.items():
            X = make_features(fr, b.use_lc_grade, b.bureau)
            pd_ = float(b.predict_pd(X)[0])
            d = str(decide([pd_], thresholds[v], REVIEW_BAND)[0])
            rs = reason_codes(b, X, k=5)[0]
            out["problems"] += _text_problems(rs)
            entry[v] = {"pd": round(pd_, 4), "decision": d, "reasons": [r.model_dump() for r in rs], "adverse_action": adverse_action_text(rs) if d == "decline" else None}
            md += [f"**{v}**: PD {pd_:.3f}, {d}", ""] + [f"{i+1}. {r.text} ({'+' if r.direction == 'raises' else '−'}{abs(r.contribution):.3f})" for i, r in enumerate(rs)]
            if d == "decline":
                md += ["", f"> {adverse_action_text(rs)}"]
            md.append("")
        out["samples"][name] = entry

    # 2. real dev rows: five declines spread over the decline range of the first model, two approvals
    lead = variants[0]
    rng = np.random.default_rng(SEED)
    declined = np.where(decisions[lead] == "decline")[0]
    approved = np.where(decisions[lead] == "approve")[0]
    fallback = len(declined) < 5
    if fallback:  # a permissive threshold can leave fewer than five declines: show the five highest-PD rows instead and say so
        declined = np.argsort(pds[lead])[-max(5, len(declined)):]
    if len(approved) < 2:
        approved = np.argsort(pds[lead])[:2]
    out["examples_note"] = "declines are the five highest-PD rows (fewer than five declines at the threshold)" if fallback else "five declined rows spread over the decline range, two approved rows"
    order_d = declined[np.argsort(pds[lead][declined], kind="stable")]
    pick_d = list(dict.fromkeys(int(order_d[int(q * (len(order_d) - 1))]) for q in (0.05, 0.3, 0.5, 0.7, 0.95)))
    for i in order_d[::-1]:  # fill up to five distinct rows if quantiles collided
        if len(pick_d) >= 5:
            break
        if int(i) not in pick_d:
            pick_d.append(int(i))
    order_a = approved[np.argsort(pds[lead][approved], kind="stable")]
    pick_a = list(dict.fromkeys([int(order_a[0]), int(order_a[int(0.9 * (len(order_a) - 1))])]))
    for idx in pick_d + pick_a:
        row = df.iloc[idx]
        ex = {"id": str(row[ID_COL]), "grade": str(row["grade"]), "sub_grade": str(row["sub_grade"]), "int_rate": float(feats[lead].iloc[idx]["int_rate"]) if "int_rate" in feats[lead] else None,
              "outcome": "charged off" if y[idx] == 1 else "fully paid", "models": {}}
        md.append(f"## Dev loan {ex['id']} — grade {ex['sub_grade']}, outcome: {ex['outcome']}")
        for v, b in bundles.items():
            X = feats[v].iloc[[idx]]
            rs = reason_codes(b, X, k=5)[0]
            out["problems"] += _text_problems(rs)
            d = str(decisions[v][idx])
            ex["models"][v] = {"pd": round(float(pds[v][idx]), 4), "decision": d, "reasons": [r.model_dump() for r in rs],
                               "adverse_action": adverse_action_text(rs) if d == "decline" else None}
            md += [f"**{v}**: PD {pds[v][idx]:.3f}, {d}", ""] + [f"{i+1}. {r.text} ({'+' if r.direction == 'raises' else '−'}{abs(r.contribution):.3f})" for i, r in enumerate(rs)]
            if d == "decline":
                md += ["", f"> {adverse_action_text(rs)}"]
            md.append("")
        out["examples"].append(ex)

    # 3. agreement of the top-3 reasons over a random sample, and the #1 reason over every decline
    sample = rng.choice(len(df), size=min(a.n, len(df)), replace=False)
    codes = {v: reason_codes(bundles[v], feats[v].iloc[sample], k=3) for v in variants}
    for v in variants:
        for rs in codes[v]:
            out["problems"] += _text_problems(rs)
    out["agreement"] = {"n": len(sample), "top3_any_overlap": reason_agreement(codes[variants[0]], codes[variants[1]], top=3),
                        "top1_same": round(float(np.mean([c0[0].feature == c1[0].feature for c0, c1 in zip(codes[variants[0]], codes[variants[1]], strict=True)])), 4)}
    out["lead_reason_among_declines"] = {}
    md += ["## Agreement and leading reasons", "",
           (f"Top-3 reasons overlap in at least one feature for {out['agreement']['top3_any_overlap']:.1%} of {len(sample):,} sampled {a.split} rows; "
            f"the #1 reason is the same feature for {out['agreement']['top1_same']:.1%}."), ""]
    for v, b in bundles.items():
        dec = np.where(decisions[v] == "decline")[0]
        if len(dec) == 0:
            continue
        c = contributions(b, feats[v].iloc[dec])
        lead_feat = c.where(c > 0).idxmax(axis=1).fillna("none")
        dist = Counter(lead_feat.tolist())
        total = sum(dist.values())
        out["lead_reason_among_declines"][v] = {"n_declined": int(total), "share": {k: round(n / total, 4) for k, n in dist.most_common()}}
        md += [f"**{v}**: #1 reason over {total:,} declined rows: " + ", ".join(f"{FEATURE_LABELS.get(k, k)} {n / total:.1%}" for k, n in dist.most_common(8)), ""]
    out["problems"] = sorted(set(out["problems"]))
    out["checks"] = {"reason_texts_clean": len(out["problems"]) == 0, "all_reasons_have_5_entries": all(len(e["models"][v]["reasons"]) == 5 for e in out["examples"] for v in variants)}
    md += ["", f"Text check: {'no raw column names or NaN in any reason text' if not out['problems'] else 'PROBLEMS: ' + '; '.join(out['problems'][:5])}", ""]
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / f"reasons_{a.split}{tag}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (a.out / f"reasons_{a.split}{tag}.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[-12:]))
    print("checks:", out["checks"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
