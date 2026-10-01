"""Audit of step 07 and the long-only backtest - transaction costs, factor-beta sorts, long-only buckets.

    python audit/a07_robust.py          # uses outputs/audit_v2/a01_extreme_returns.csv when present
"""
import importlib.util

import numpy as np
import pandas as pd

from common import OUT, ROOT, S, SUBPERIODS, interim, processed, show, write
from lib.io import log
from lib.portfolios import holding_returns
from lib.stats import nw_mean, summary

STEP = "a07"
BUCKETS = {"Top 5% Z*": ["L3"], "Top 10% Z*": ["L3", "L4"], "Top 25% Z*": ["L3", "L4", "L5", "L6", "L7"],
           "Bottom 25% Z*": ["S3", "S4", "S5", "S6", "S7"]}


def weights(hold, legs):
    h = hold[hold["portfolio"].isin(legs)]
    if legs == ["g"]:
        return h.pivot_table(index="T", columns="code", values="weight", aggfunc="sum", fill_value=0.0)
    h = h.drop_duplicates(["T", "code"])
    W = h.assign(one=1.0).pivot_table(index="T", columns="code", values="one", fill_value=0.0)
    return W.div(W.sum(axis=1), axis=0)


def turnover(W, rm, last_date, data_end):
    """One-way turnover per rebalance: (a) target-to-target as in the pipeline, (b) from drifted weights."""
    W = W.sort_index()
    naive = 0.5 * W.diff().abs().sum(axis=1)
    drift = pd.Series(np.nan, index=W.index)
    prev = None
    for T, w in W.iterrows():
        if prev is not None:
            drift[T] = 0.5 * w.sub(prev, fill_value=0.0).abs().sum()
        held = w[w > 0]
        R = holding_returns(held.index, T.to_period("M") + 1, rm, last_date, data_end, S.DELIST_RETURN)
        end = held * (1 + R)
        prev = (end / end.sum()).reindex(W.columns).fillna(0.0)
    return naive.iloc[1:], drift.iloc[1:]


def cagr(r):
    r = r.dropna()
    return 100 * ((1 + r).prod() ** (12 / len(r)) - 1) if len(r) else np.nan


def main():
    hold, legs, agg = processed("holdings"), processed("legs_monthly"), processed("aggregates_monthly")
    rm, last_date, f = interim("returns_monthly"), interim("last_date"), interim("factors_daily")
    data_end, rf = f.index[-1], agg["Rf"]
    rt = S.COST_BUY + S.COST_SELL

    # ---- 1. turnover and costs
    rows = {}
    for name in [f"L{k}" for k in range(1, 13)] + [f"S{k}" for k in range(1, 13)] + ["g"]:
        nv, dr = turnover(weights(hold, [name]), rm, last_date, data_end)
        rows[name] = {"turnover_target_to_target": nv.mean(), "turnover_from_drifted_weights": dr.mean(),
                      "cost_%/m_pipeline_convention": 100 * nv.mean() * rt, "cost_%/m_with_drift": 100 * dr.mean() * rt}
    tc = pd.DataFrame(rows).T
    ref = pd.read_csv(S.OUT_TABLES / "robust_costs.csv", index_col=0)
    mine = pd.Series({f"M+LS{k}": tc.at[f"L{k}", "turnover_target_to_target"] for k in range(1, 13)})
    mine["g"] = tc.at["g", "turnover_target_to_target"]
    n = len(legs)
    first = pd.DataFrame({"turnover_L_pipeline": ref["turnover_L"], "turnover_L_audit_excl_first_month": mine,
                          "implied_with_first_month_at_1.0": (mine * (n - 1) + 1.0) / n})
    first["diff"] = first["turnover_L_pipeline"] - first["implied_with_first_month_at_1.0"]
    show(STEP, "turnover and cost per leg (one-way, monthly)", tc.round(4))
    write(tc, "a07_turnover", STEP)
    show(STEP, "step-07 turnover column reproduced (first month booked at 1.0 = buy + sell on the whole book)",
         first.round(4))
    write(first, "a07_cost_check", STEP)
    log(STEP, f"first-month cost: step 07 charges {100 * rt:.2f}%, long-only backtest {100 * rt / 2:.2f}%, "
              f"a pure purchase costs {100 * S.COST_BUY:.2f}%; effect on a {n}-month mean <= {100 * rt / n:.4f}%/m")

    # ---- 2. factor-beta sorts (Fig 9.7) rerun through the pipeline function, without writing
    spec = importlib.util.spec_from_file_location("step07", ROOT / "07_robustness" / "run.py")
    step07 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(step07)
    bs = step07.beta_sorts(agg)
    ref = pd.read_csv(S.OUT_TABLES / "robust_factor_beta_sorts.csv", index_col=0)
    rows, diffs = {}, []
    zeta = pd.DataFrame({f"LS{k}": legs[f"LS{k}"] for k in range(1, 13)})
    for fac, df in {"zeta (Z*)": zeta, **(bs or {})}.items():
        a = df.add(agg["M"].reindex(df.index), axis=0)
        s = pd.DataFrame({c: summary(a[c], rf) for c in a.columns}).T
        if fac in (bs or {}):
            diffs.append((s["sharpe"].to_numpy() - ref.loc[[f"M+{c} ({fac})" for c in s.index], "sharpe"].to_numpy()))
        t = pd.Series({c: nw_mean(df[c], S.NW_LAGS)["t_nw"] for c in df.columns})
        rows[fac] = {"months": len(df), "mean_LS_%_min": 100 * df.mean().min(), "mean_LS_%_max": 100 * df.mean().max(),
                     "mean_of_all_LS_%": 100 * df.mean().mean(),
                     "t_of_avg_LS3..12": nw_mean(df[[f"LS{k}" for k in range(3, 13)]].mean(axis=1), S.NW_LAGS)["t_nw"],
                     "n_LS_with_|t|>2": int((t.abs() > 2).sum()), "best_M+LS_sharpe": s["sharpe"].max(),
                     "n_M+LS_sharpe_above_M": int((s["sharpe"] > summary(agg["M"], rf)["sharpe"]).sum())}
    fb = pd.DataFrame(rows).T
    if diffs:
        log(STEP, f"factor-beta sorts rerun vs robust_factor_beta_sorts.csv: max abs Sharpe diff "
                  f"{np.abs(np.concatenate(diffs)).max():.2e}")
    show(STEP, "zeta sort vs factor-beta sorts (same 12 L/S structure)", fb.round(3))
    write(fb, "a07_factor_beta_sorts", STEP)

    # ---- 3. long-only buckets rebuilt from holdings
    flagged = set()
    p = OUT / "a01_extreme_returns.csv"
    if p.exists():
        x = pd.read_csv(p, parse_dates=["date"])
        x = x[~x["class"].str.startswith("first 5 rows")]
        flagged = set(zip(x["date"].dt.to_period("M"), x["code"]))
    ref = pd.read_csv(S.OUT_TABLES / "long_only_backtest.csv", index_col=0)
    rows = {}
    for name, members in BUCKETS.items():
        W = weights(hold, members).sort_index()
        gross, capped, clean, names, top_share = {}, {}, {}, {}, {}
        for T, w in W.iterrows():
            m1 = T.to_period("M") + 1
            if m1 not in legs.index:
                continue
            w = w[w > 0]
            R = holding_returns(w.index, m1, rm, last_date, data_end, S.DELIST_RETURN)
            gross[m1], capped[m1] = float((R * w).sum()), float((R.clip(upper=1.0) * w).sum())
            ok = np.array([(m1, c) not in flagged for c in w.index], bool)
            clean[m1] = float(R[ok].mean()) if ok.any() else np.nan
            names[m1] = len(w)
            contrib = (R * w).sort_values()
            top_share[m1] = contrib.iloc[-1]
        gross, capped, clean = (pd.Series(d).sort_index() for d in (gross, capped, clean))
        nv, dr = turnover(W, rm, last_date, data_end)
        row = {"gross_CAGR_%": cagr(gross), "gross_CAGR_pipeline_%": ref.at[name, "gross_CAGR_%"],
               "median_names": pd.Series(names).median(), "min_names": pd.Series(names).min(),
               "CAGR_returns_capped_+100%": cagr(capped), "CAGR_flagged_holdings_dropped": cagr(clean),
               "CAGR_excl_best_5_months": cagr(gross.sort_values()[:-5]),
               "mean_best_single_stock_contribution_%/m": 100 * pd.Series(top_share).mean(),
               "turnover_pipeline": nv.mean(), "turnover_with_drift": dr.mean(),
               "net_CAGR_with_drift_cost_%": cagr(gross - (dr * rt).set_axis(dr.index.to_period("M") + 1)
                                                  .reindex(gross.index).fillna(rt / 2)),
               "net_CAGR_pipeline_%": ref.at[name, "CAGR_%"]}
        for a, b in SUBPERIODS:
            row[f"gross_CAGR_% {a[:4]}-{b[:4]}"] = cagr(gross.loc[a:b])
        rows[name] = row
    rows["Market (own VW)"] = {"gross_CAGR_%": cagr(agg["M"]), "gross_CAGR_pipeline_%": ref.at["Market (own VW)", "CAGR_%"],
                               **{f"gross_CAGR_% {a[:4]}-{b[:4]}": cagr(agg["M"].loc[a:b]) for a, b in SUBPERIODS}}
    lo = pd.DataFrame(rows).T
    show(STEP, "long-only Z* buckets rebuilt from holdings", lo.T.round(2))
    write(lo, "a07_long_only_buckets", STEP)


if __name__ == "__main__":
    main()
