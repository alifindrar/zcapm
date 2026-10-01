"""Audit of steps 04-05 - proxy minimum-variance portfolio g (book steps 1-4 for g) and the aggregate portfolios.

    python audit/a05_g.py
"""
import numpy as np
import pandas as pd

from common import S, interim, processed, show, write
from lib.io import log, window_mask
from lib.portfolios import g_weights, holding_returns
from lib.stats import summary

STEP = "a05"
MONTHLY_SCALE = 21        # book: Z* on a monthly scale = daily Z* x 21 (audit.md, MATLAB notes)


def build(est, rm, fm, f, last_date, cap, zscale, monthly_sd, use_sigma2):
    """Monthly return of g under one specification, plus diagnostics."""
    out = {}
    for T, e in est.groupby("T"):
        e = e.set_index("code")
        e = e[e["zstar"].notna()].copy()
        m1 = T.to_period("M") + 1
        if m1 not in rm.index or len(e) < 24:
            continue
        fw = f.loc[window_mask(f.index, T, S.WINDOW_MONTHS)]
        mkt_sd = (fw["Ra"] - fw["Rf"]).std()
        n0 = len(e)
        if monthly_sd:
            win = pd.period_range(T.to_period("M") - (S.WINDOW_MONTHS - 1), T.to_period("M"), freq="M")
            e["sd_daily"] = rm.reindex(win)[e.index].std()
            mkt_sd = fm["M_own"].reindex(win).std()
        e["zstar"] = e["zstar"] * zscale
        if use_sigma2:
            e["resid_var"] = e["sigma2"]
        w = g_weights(e, mkt_sd, S.G_VOL_RATIO, S.G_ZETA_OFFSET, cap)
        R = holding_returns(w.index, m1, rm, last_date, f.index[-1], S.DELIST_RETURN)
        out[m1] = {"ret": float((R * w).sum()), "n": len(w), "dropped_by_vol_filter": n0 - len(w),
                   "max_w": w.max(), "eff_n": 1 / (w ** 2).sum(),
                   "w_abs_zstar_daily": float((e["zstar"].reindex(w.index).abs() * w).sum()) / zscale}
    df = pd.DataFrame(out).T
    df.index = pd.PeriodIndex(df.index, freq="M")
    return df.sort_index()


def main():
    est, rm, last_date = interim("zcapm_estimates"), interim("returns_monthly"), interim("last_date")
    f, fm = interim("factors_daily"), interim("factors_monthly")
    legs, agg = processed("legs_monthly"), processed("aggregates_monthly")
    rf, M = agg["Rf"], agg["M"]
    K = sum(c.startswith("LS") for c in legs.columns)
    J = sum(c.startswith("LO") for c in legs.columns)

    specs = {
        "as run (cap 5%, daily Z*, daily SD, var of Eq 9.4 residual)": dict(cap=S.G_WEIGHT_CAP, zscale=1, monthly_sd=False, use_sigma2=False),
        "no cap": dict(cap=None, zscale=1, monthly_sd=False, use_sigma2=False),
        "Z* x21 in the weight (cap 5%)": dict(cap=S.G_WEIGHT_CAP, zscale=MONTHLY_SCALE, monthly_sd=False, use_sigma2=False),
        "monthly-SD filter (cap 5%)": dict(cap=S.G_WEIGHT_CAP, zscale=1, monthly_sd=True, use_sigma2=False),
        "EM sigma2 as var(u) (cap 5%)": dict(cap=S.G_WEIGHT_CAP, zscale=1, monthly_sd=False, use_sigma2=True),
        "book-literal: no cap, Z* x21, monthly SD": dict(cap=None, zscale=MONTHLY_SCALE, monthly_sd=True, use_sigma2=False),
    }
    res = {name: build(est, rm, fm, f, last_date, **kw) for name, kw in specs.items()}
    base = res[next(iter(specs))]
    log(STEP, f"as-run rebuild vs legs_monthly.pkl['g']: max abs diff {(base['ret'] - legs['g']).abs().max():.2e}")

    rows = {}
    for name, d in res.items():
        g = d["ret"].astype(float)
        s = summary(g, rf)
        sh = pd.Series({k: summary(g + legs[f"LS{k}"], rf)["sharpe"] for k in range(1, K + 1)})
        rows[name] = {"mean_%": s["mean_%"], "sd_%": s["sd_%"], "sharpe": s["sharpe"],
                      "corr_with_as_run": g.corr(base["ret"].astype(float)), "corr_with_M": g.corr(M),
                      "median_n": d["n"].median(), "median_dropped_by_vol_filter": d["dropped_by_vol_filter"].median(),
                      "median_max_weight": d["max_w"].median(), "max_max_weight": d["max_w"].max(),
                      "median_effective_n": d["eff_n"].median(),
                      "months_cap_binding": int((d["max_w"] >= S.G_WEIGHT_CAP - 1e-9).sum()) if "cap 5%" in name
                      else np.nan,
                      "weighted_|Z*|_daily": d["w_abs_zstar_daily"].mean(),
                      "best_g+LS_sharpe": sh.max(), "n_g+LS_beating_M+LS": int(sum(
                          sh[k] > summary(M + legs[f"LS{k}"], rf)["sharpe"] for k in range(1, K + 1)))}
    rows["market M (own VW)"] = {"mean_%": 100 * M.mean(), "sd_%": 100 * M.std(), "sharpe": summary(M, rf)["sharpe"],
                                 "corr_with_M": 1.0}
    t = pd.DataFrame(rows).T
    show(STEP, f"portfolio g under alternative readings of the book ({len(base)} months)", t.round(3))
    write(t, "a05_g_variants", STEP)
    write(pd.DataFrame({k: v["ret"] for k, v in res.items()}), "a05_g_returns", STEP)

    # ---- aggregates recomputed from the legs
    re = {"M": fm["M_own" if S.MARKET_PROXY == "own_vw" else "IHSG"].reindex(legs.index), "g": legs["g"]}
    for k in range(1, K + 1):
        re[f"M+LS{k}"] = re["M"] + legs[f"L{k}"] - legs[f"S{k}"]
        re[f"g+LS{k}"] = re["g"] + legs[f"L{k}"] - legs[f"S{k}"]
    order = [f"S{k}" for k in range(1, K + 1)] + [f"L{k}" for k in range(K, 0, -1)]   # low -> high Z*
    for j, leg in enumerate(order, start=1):
        re[f"LOA_M_{j}"] = (re["M"] + legs[leg]) / 2
        re[f"LOA_g_{j}"] = (re["g"] + legs[leg]) / 2
    re = pd.DataFrame(re)
    d = (re - agg[re.columns]).abs().max()
    chk = pd.DataFrame({"series": [len(re.columns)], "max_abs_diff": [d.max()], "worst_series": [d.idxmax()],
                        "LO_count": [J], "LO24_is_L1": [bool((legs["LO24"] - legs["L1"]).abs().max() < 1e-15)],
                        "LO13_is_L12": [bool((legs["LO13"] - legs["L12"]).abs().max() < 1e-15)],
                        "LO1_is_S1": [bool((legs["LO1"] - legs["S1"]).abs().max() < 1e-15)]})
    show(STEP, "aggregates recomputed from legs vs aggregates_monthly.pkl", chk.T)
    write(chk, "a05_aggregates_check", STEP, index=False)


if __name__ == "__main__":
    main()
