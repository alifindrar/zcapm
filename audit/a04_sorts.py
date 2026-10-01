"""Audit of step 04 - leg sizes and sensitivity of the long/short results to scheme, universe size, the
zero-return filter and suspicious returns. All reruns happen in memory; only outputs/audit_v2/ is written.

    python audit/a04_sorts.py          # needs outputs/audit_v2/a01_extreme_returns.csv (run a01_data.py first)

The variants that widen or clean the universe re-estimate the ZCAPM (slow); estimates are cached as
outputs/audit_v2/a04_estimates_<variant>.csv.gz and reused on later runs.
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from a02_factors import recompute
from common import OUT, S, SUBPERIODS, interim, processed, show, write
from lib.em import fit_zcapm
from lib.io import compound_monthly, log, month_ends, window_mask
from lib.portfolios import form_ls, holding_returns, n_ls
from lib.stats import nw_mean

STEP = "a04"


def eligibility(r, traded, mcap, close, zero_max):
    """Step-01 eligibility rule with a configurable zero-return threshold."""
    dates = r.index
    mes = month_ends(dates)
    close_ff = close.ffill(limit=5)
    year_ends = mes[mes.month == 12]
    elig = pd.DataFrame(False, index=mes, columns=r.columns)
    for T in mes:
        if dates[0] > (T.to_period("M") - (S.WINDOW_MONTHS - 1)).start_time:
            continue
        win = window_mask(dates, T, S.WINDOW_MONTHS)
        tr, rr = traded[win], r[win]
        n_valid = tr.sum()
        zero = ((rr == 0) & tr).sum() / n_valid.clip(lower=1)
        ok = (n_valid >= S.MIN_OBS) & (zero <= zero_max) & (close_ff.loc[T] > S.MIN_PRICE)
        ye = year_ends[year_ends <= T]
        if len(ye):
            mc = mcap.loc[ye[-1]]
            ok &= ~(mc < mc.quantile(S.SIZE_CUT))
        elig.loc[T] = ok.fillna(False)
    return elig


def estimate(name, r, traded, elig, f):
    """Step-03 loop; cached under outputs/audit_v2/."""
    cache = OUT / f"a04_estimates_{name}.csv.gz"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["T"])
    dates = r.index
    months = [T for T in elig.index[:-1] if elig.loc[T].sum() >= 2 * n_ls("quintiles")]
    out = []
    for i, T in enumerate(months, 1):
        win = window_mask(dates, T, S.WINDOW_MONTHS)
        codes = elig.columns[elig.loc[T]]
        fw = f.loc[win]
        Y = r.loc[win, codes].where(traded.loc[win, codes]).sub(fw["Rf"], axis=0)
        e = fit_zcapm(Y.to_numpy(), (fw["Ra"] - fw["Rf"]).to_numpy(), fw["sigma_a"].to_numpy(), codes=codes,
                      tol=S.EM_TOL, maxit=S.EM_MAXIT, starts=S.EM_STARTS, min_obs=S.MIN_OBS)
        e.insert(0, "T", T)
        out.append(e.reset_index()[["T", "code", "beta", "zstar", "converged"]])
        if i % 24 == 0 or i == len(months):
            log(STEP, f"estimating '{name}': {i}/{len(months)}")
    est = pd.concat(out, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    est.to_csv(cache, index=False)
    return est


def sorts(est, rm, last_date, data_end, scheme, keep=None, adjust=None):
    rets, avgs, cnts = {}, {}, {}
    for T, e in est.groupby("T"):
        e = e.set_index("code")
        e = e[e["zstar"].notna()]
        m1 = T.to_period("M") + 1
        if m1 not in rm.index or e.empty or (keep is not None and not keep(len(e))):
            continue
        R = holding_returns(e.index, m1, rm, last_date, data_end, S.DELIST_RETURN)
        if adjust is not None:
            R = adjust(R, m1)
        res = form_ls(e["zstar"], R, scheme)
        if res is None:
            continue
        rets[m1], avgs[m1], cnts[m1] = res[0], res[1], {**res[2], "N": len(e)}
    def frame(d):
        df = pd.DataFrame.from_dict(d, orient="index")
        df.index = pd.PeriodIndex(df.index, freq="M", name="month")
        return df.sort_index()
    return frame(rets), frame(avgs), frame(cnts)


def summarise(rets, avgs, cnts, scheme):
    K = n_ls(scheme)
    ls = [f"LS{k}" for k in range(1, K + 1)]
    t = pd.Series({c: nw_mean(rets[c], S.NW_LAGS)["t_nw"] for c in ls})
    first_slice = f"L{K - {'book24': 9, 'deciles': 4, 'quintiles': 1}[scheme]}"
    row = {"months": len(rets), "first": str(rets.index[0]), "median_N": cnts["N"].median(),
           "median_size_first_slice": cnts[first_slice].median(),
           "spearman_Z*_vs_return": spearmanr(avgs[ls].mean(), rets[ls].mean()).statistic,
           "n_LS_with_t>2": int((t > 2).sum()), "mean_of_all_LS_%": 100 * rets[ls].mean().mean()}
    for c in ls:
        row[f"{c}_%"] = 100 * rets[c].mean()
        row[f"{c}_t"] = t[c]
    for a, b in SUBPERIODS:
        sub = rets.loc[a:b, ls]
        row[f"mean_of_all_LS_% {a[:4]}-{b[:4]}"] = 100 * sub.mean().mean() if len(sub) else np.nan
        row[f"{first_slice.replace('L', 'LS')}_% {a[:4]}-{b[:4]}"] = \
            100 * sub[first_slice.replace("L", "LS")].mean() if len(sub) else np.nan
    return row


def main():
    r, traded, mcap = interim("returns_daily"), interim("traded_daily"), interim("mcap_daily")
    elig, f, est = interim("eligible_monthly"), interim("factors_daily"), interim("zcapm_estimates")
    rm, last_date = interim("returns_monthly"), interim("last_date")
    legs, cnt = processed("legs_monthly"), processed("legs_count")
    hold = processed("holdings")
    data_end = f.index[-1]

    # ---- 1. leg sizes
    N = est[est["zstar"].notna()].groupby("T").size()
    N.index = N.index.to_period("M") + 1
    c = cnt.join(N.rename("N"))
    lcols = [f"L{k}" for k in range(1, 13)]
    sets = hold[hold["portfolio"].isin(["L1", "L2"])].groupby(["T", "portfolio"])["code"].apply(frozenset).unstack()
    same = (sets["L1"] == sets["L2"])
    same.index = same.index.to_period("M") + 1
    c["L1_equals_L2"] = same.reindex(c.index).fillna(False).astype(bool)
    write(c, "a04_leg_sizes_by_month", STEP)
    by = pd.DataFrame({"months": c.groupby(c.index.year).size(), "median_N": c.groupby(c.index.year)["N"].median(),
                       "median_L1": c.groupby(c.index.year)["L1"].median(),
                       "median_L2": c.groupby(c.index.year)["L2"].median(),
                       "median_L3": c.groupby(c.index.year)["L3"].median(),
                       "months_L1_single_stock": (c["L1"] == 1).groupby(c.index.year).sum(),
                       "months_L1_equals_L2": c["L1_equals_L2"].groupby(c.index.year).sum(),
                       "months_any_leg<5": (c[lcols].min(axis=1) < S.MIN_LEG_SIZE).groupby(c.index.year).sum(),
                       "months_5%_slice<5": (c["L3"] < S.MIN_LEG_SIZE).groupby(c.index.year).sum()})
    by.loc["all"] = [len(c), c["N"].median(), c["L1"].median(), c["L2"].median(), c["L3"].median(),
                     (c["L1"] == 1).sum(), c["L1_equals_L2"].sum(), (c[lcols].min(axis=1) < S.MIN_LEG_SIZE).sum(),
                     (c["L3"] < S.MIN_LEG_SIZE).sum()]
    show(STEP, "leg sizes by holding year (book24 scheme)", by)
    write(by, "a04_leg_sizes_by_year", STEP)

    # ---- 2. the base rerun must reproduce step 04
    base = sorts(est, rm, last_date, data_end, "book24")
    ls = [f"LS{k}" for k in range(1, 13)]
    diff = (base[0][ls] - legs[ls]).abs().max().max()
    log(STEP, f"in-memory rerun vs legs_monthly.pkl: max abs diff {diff:.2e} over {len(base[0])} months")

    # ---- 3. variants on the stored estimates
    x = pd.read_csv(OUT / "a01_extreme_returns.csv", parse_dates=["date"])
    x = x[~x["class"].str.startswith("first 5 rows")]
    flagged = set(zip(x["date"].dt.to_period("M"), x["code"]))

    def drop_flagged(R, m1):
        return R.mask(np.array([(m1, code) in flagged for code in R.index], bool))

    variants = {
        "base (book24)": ("book24", base),
        "deciles": ("deciles", sorts(est, rm, last_date, data_end, "deciles")),
        "quintiles": ("quintiles", sorts(est, rm, last_date, data_end, "quintiles")),
        "book24, months with N>=100": ("book24", sorts(est, rm, last_date, data_end, "book24", keep=lambda n: n >= 100)),
        "book24, months with N>=200": ("book24", sorts(est, rm, last_date, data_end, "book24", keep=lambda n: n >= 200)),
        "deciles, months with N>=100": ("deciles", sorts(est, rm, last_date, data_end, "deciles",
                                                         keep=lambda n: n >= 100)),
        "book24, holding returns capped at +100%": ("book24", sorts(est, rm, last_date, data_end, "book24",
                                                                    adjust=lambda R, m: R.clip(upper=1.0))),
        "book24, holdings with a flagged return dropped": ("book24", sorts(est, rm, last_date, data_end, "book24",
                                                                           adjust=drop_flagged)),
    }

    # ---- 4. variants that need re-estimation
    raw = pd.read_csv(S.RAW / "stock_daily.csv.gz", usecols=["date", "code", "close"], parse_dates=["date"])
    close = raw.pivot(index="date", columns="code", values="close").reindex(index=r.index, columns=r.columns)
    chk = eligibility(r, traded, mcap, close, S.MAX_ZERO_FRAC)
    log(STEP, f"eligibility rule re-implemented: {int((chk != elig).sum().sum())} cells differ from eligible_monthly.pkl")
    for zmax in (0.35, 0.50):
        el = eligibility(r, traded, mcap, close, zmax)
        e2 = estimate(f"zero{int(100 * zmax)}", r, traded, el, f)
        for scheme in ("book24", "deciles"):
            variants[f"{scheme}, zero-return filter <= {zmax:.0%}"] = (scheme, sorts(e2, rm, last_date, data_end, scheme))

    bad = pd.DataFrame(False, index=r.index, columns=r.columns)
    for d, code in zip(x["date"], x["code"]):
        bad.at[d, code] = True
    rc = r.mask(bad)
    Ra, sg = recompute(rc, mcap)
    fc = f.assign(Ra=Ra, sigma_a=sg)
    tc = traded & rc.notna()
    elc = eligibility(rc, tc, mcap, close, S.MAX_ZERO_FRAC)
    ec = estimate("clean", rc, tc, elc, fc)
    rmc = compound_monthly(rc)
    for scheme in ("book24", "deciles"):
        variants[f"{scheme}, flagged returns removed everywhere (re-estimated)"] = \
            (scheme, sorts(ec, rmc, last_date, data_end, scheme))
    el35c = eligibility(rc, tc, mcap, close, 0.35)
    e35c = estimate("clean_zero35", rc, tc, el35c, fc)
    variants["deciles, flagged removed + zero-return filter <= 35%"] = \
        ("deciles", sorts(e35c, rmc, last_date, data_end, "deciles"))

    rows = {name: summarise(*res, scheme) for name, (scheme, res) in variants.items()}
    t = pd.DataFrame(rows).T
    write(t, "a04_variants", STEP)
    head = ["months", "first", "median_N", "median_size_first_slice", "spearman_Z*_vs_return", "n_LS_with_t>2",
            "mean_of_all_LS_%"] + [c for c in t.columns if c.startswith("mean_of_all_LS_% ")]
    show(STEP, "variants: overview", t[head])
    show(STEP, "variants: mean L/S return, % per month", t[[c for c in t.columns if c.endswith("_%") and
                                                            c.startswith("LS")]].astype(float).round(2))
    show(STEP, "variants: Newey-West t", t[[c for c in t.columns if c.endswith("_t")]].astype(float).round(2))
    show(STEP, "variants: first 5%/10%/20% slice by subperiod, % per month",
         t[[c for c in t.columns if c.startswith("LS") and " " in c]].astype(float).round(2))


if __name__ == "__main__":
    main()
