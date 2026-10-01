"""Audit of step 02 - market return R_a, return dispersion (Eq. 9.5), risk-free rate, local factors.

    python audit/a02_factors.py
"""
import numpy as np
import pandas as pd

from common import S, interim, show, write
from lib.io import month_ends
from lib.stats import summary

STEP = "a02"


def recompute(r, mcap):
    """Independent numpy implementation of the lagged-cap-weighted mean and Eq. 9.5."""
    R = r.to_numpy()
    W = mcap.shift(1).to_numpy()
    Ra, sg = np.full(len(R), np.nan), np.full(len(R), np.nan)
    for t in range(len(R)):
        ok = np.isfinite(R[t]) & np.isfinite(W[t]) & (W[t] > 0)
        n = ok.sum()
        if n == 0:
            continue
        w = W[t, ok] / W[t, ok].sum()
        Ra[t] = w @ R[t, ok]
        if n > 1:
            sg[t] = np.sqrt(n / (n - 1) * (w @ (R[t, ok] - Ra[t]) ** 2))
    return pd.Series(Ra, r.index), pd.Series(sg, r.index)


def main():
    r, mcap = interim("returns_daily"), interim("mcap_daily")
    f, fm, elig = interim("factors_daily"), interim("factors_monthly"), interim("eligible_monthly")

    # ---- 1. R_a and sigma_a recomputed
    Ra, sg = recompute(r, mcap)
    chk = pd.DataFrame({"max_abs_diff": [(Ra - f["Ra"]).abs().max(), (sg - f["sigma_a"]).abs().max()],
                        "nan_mismatch": [int((Ra.isna() != f["Ra"].isna()).sum()),
                                         int((sg.isna() != f["sigma_a"].isna()).sum())]}, index=["Ra", "sigma_a"])
    show(STEP, "recomputed vs factors_daily.pkl", chk)
    write(chk, "a02_recompute_check", STEP)

    # ---- 2. yearly profile of the own index
    w = mcap.shift(1).where(r.notna() & (mcap.shift(1) > 0))
    w = w.div(w.sum(axis=1), axis=0)
    yr = f.index.year
    prof = pd.DataFrame({
        "n_stocks": w.notna().sum(axis=1).groupby(yr).mean(),
        "max_weight_mean": w.max(axis=1).groupby(yr).mean(),
        "max_weight_max": w.max(axis=1).groupby(yr).max(),
        "Ra_mean_%": 100 * f["Ra"].groupby(yr).mean(), "RD_mean_%": 100 * f["sigma_a"].groupby(yr).mean(),
        "IHSG_mean_%": 100 * f["IHSG"].groupby(yr).mean(),
        "corr_Ra_IHSG": pd.concat([f["Ra"], f["IHSG"]], axis=1).groupby(yr).apply(lambda d: d["Ra"].corr(d["IHSG"])),
        "days_|Ra-IHSG|>1pp": ((f["Ra"] - f["IHSG"]).abs() > 0.01).groupby(yr).sum()})
    show(STEP, "own value-weighted index by year", prof.round(3))
    write(prof, "a02_index_by_year", STEP)

    # ---- 3. days where the own index departs from IHSG, attributed to the largest contributor
    gap = (f["Ra"] - f["IHSG"]).dropna()
    days = gap.index[gap.abs() > 0.01]
    contrib = w.loc[days] * r.loc[days].sub(f["IHSG"].loc[days], axis=0)
    top = contrib.abs().idxmax(axis=1)
    rows = pd.DataFrame({"gap_pp": 100 * gap.loc[days], "top_code": top,
                         "top_weight": [w.at[d, c] for d, c in top.items()],
                         "top_return": [r.at[d, c] for d, c in top.items()],
                         "top_contrib_pp": [100 * contrib.at[d, c] for d, c in top.items()]})
    rows["share_of_gap"] = rows["top_contrib_pp"] / rows["gap_pp"]
    write(rows.sort_values("gap_pp", key=abs, ascending=False), "a02_index_gap_days", STEP)
    show(STEP, f"{len(rows)} days with |Ra - IHSG| > 1pp; worst 10", rows.sort_values("gap_pp", key=abs,
                                                                                    ascending=False).head(10).round(3))
    heavy = w.max(axis=1)
    hd = heavy[(heavy > 0.25) & (heavy.index >= "2005-01-01")]
    hv = pd.DataFrame({"code": w.loc[hd.index].idxmax(axis=1), "weight": hd})
    write(hv, "a02_single_weight_over_25pct", STEP)
    show(STEP, "days from 2005 with one stock above 25% of the index, by code", hv.groupby("code").size().to_frame("days"))

    # ---- 4. risk-free rate
    rf = pd.read_csv(S.RF_FILE, parse_dates=["date"])
    files = sorted(p.name for p in S.EXTERNAL.iterdir())
    m = fm.loc["2007-04":]
    rows = {}
    for label, cut in (("rf.csv as used (10Y yield)", 0.0), ("illustration: yield - 2pp p.a.", 2.0),
                       ("illustration: yield - 3pp p.a.", 3.0)):
        ann = (1 + m["Rf"]) ** 12 - 1 - cut / 100
        alt = (1 + ann) ** (1 / 12) - 1
        s = summary(m["M_own"], alt)
        rows[label] = {"Rf_mean_%/m": 100 * alt.mean(), "Rf_ann_%": 100 * ann.mean(),
                       "M_excess_%/m": 100 * (m["M_own"] - alt).mean(), "M_sharpe": s["sharpe"]}
    rft = pd.DataFrame(rows).T
    show(STEP, f"risk-free rate ({rf['date'].min():%Y-%m}..{rf['date'].max():%Y-%m}, {len(rf)} rows); "
               f"files in data/external: {files}", rft.round(3))
    write(rft, "a02_rf_sensitivity", STEP)

    # ---- 5. local factors: coverage and age of the price-to-book value used for HML
    cov = pd.DataFrame({"months": fm[["SMB", "HML", "MOM"]].notna().sum(),
                        "first": fm[["SMB", "HML", "MOM"]].apply(lambda s: s.first_valid_index()),
                        "mean_%/m": 100 * fm[["SMB", "HML", "MOM"]].mean(),
                        "sd_%/m": 100 * fm[["SMB", "HML", "MOM"]].std()})
    show(STEP, "local factor coverage", cov)
    write(cov, "a02_factor_coverage", STEP)
    ratios = pd.read_csv(S.RAW / "ratios.csv", parse_dates=["date"])
    ratios = ratios[ratios["pbv"] > 0]
    ratios["avail"] = ratios["date"] + pd.DateOffset(months=S.RATIO_LAG_MONTHS)
    period = ratios.pivot_table(index="avail", columns="code", values="date", aggfunc="last")
    age = {}
    for T in month_ends(r.index):
        uni = elig.columns[elig.loc[T]]
        p = period[period.index <= T]
        if len(uni) < 12 or p.empty:
            continue
        last = p.ffill().iloc[-1].reindex(uni)
        months = (T - last).dt.days / 30.44
        age[T] = {"eligible": len(uni), "no_pbv": int(last.isna().sum()), "median_age_m": months.median(),
                  "older_than_12m": int((months > 12).sum()), "older_than_24m": int((months > 24).sum())}
    age = pd.DataFrame(age).T
    write(age, "a02_pbv_age", STEP)
    by = age.groupby(age.index.year).mean()
    show(STEP, "age of price-to-book value at formation (yearly mean of month-end counts)", by.round(1))


if __name__ == "__main__":
    main()
