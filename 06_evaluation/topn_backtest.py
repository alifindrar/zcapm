"""Step 06c - concentrated long-only baskets: top N by Z* inside the largest stocks by market cap (default 300).

Rule at each formation month T (same filters as the live basket): market-cap rank <= --top-mcap, Z* in the top quintile of all
eligible stocks in >= 2 of the 3 previous formation months, avg daily value (60d) >= MIN_ADV, trades >= 90% of the last
60 days, beta <= 2, p >= 0.6, n_obs >= 200. Pick the N highest Z*, equal weight, hold T -> T+1, net of costs.
The final (partial) month is excluded.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import load, log, write_table  # noqa: E402
from lib.portfolios import holding_returns, turnover_cost  # noqa: E402

STEP = "06c"
NS, TOP_MCAP, MIN_ADV = (3, 5, 10), 300, 3e9
START = pd.Period("2016-02", "M")


def main():
    global TOP_MCAP, MIN_ADV
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-mcap", type=int, default=TOP_MCAP)
    ap.add_argument("--min-adv", type=float, default=MIN_ADV)
    a = ap.parse_args()
    # non-default runs write to suffixed tables so the top-300 baseline is kept
    sfx = ("" if a.top_mcap == TOP_MCAP else f"_top{a.top_mcap}") + ("" if a.min_adv == MIN_ADV else f"_adv{a.min_adv / 1e9:.0f}bn")
    TOP_MCAP, MIN_ADV = a.top_mcap, a.min_adv
    est = load(S.INTERIM / "zcapm_estimates.pkl")
    rm = load(S.INTERIM / "returns_monthly.pkl")
    mc = load(S.INTERIM / "mcap_daily.pkl")
    tr = load(S.INTERIM / "traded_daily.pkl")
    ld = load(S.INTERIM / "last_date.pkl")
    dl = load(S.INTERIM / "delist_return.pkl")
    susp = load(S.INTERIM / "susp_monthly.pkl")
    agg = load(S.PROCESSED / "aggregates_monthly.pkl")
    data_end = load(S.INTERIM / "factors_daily.pkl").index[-1]
    sd = pd.read_csv(S.RAW / "stock_daily.csv.gz", usecols=["date", "code", "value"], parse_dates=["date"])
    val = sd.pivot_table(index="date", columns="code", values="value").reindex(mc.index)
    adv = val.rolling(60, min_periods=40).mean()
    tr60 = tr.rolling(60, min_periods=40).mean()

    Ts = sorted(est["T"].unique())
    est = est.set_index(["T", "code"])
    q = {T: est.loc[T, "zstar"].rank(pct=True) >= 0.8 for T in Ts}
    W = {n: {} for n in NS}
    ret = {n: {} for n in NS}
    cnt = {n: {} for n in NS}
    ew300 = {}
    for i, T in enumerate(Ts):
        m1 = T.to_period("M") + 1
        if i < 3 or m1 not in rm.index or m1 > Ts[-1].to_period("M"):
            continue
        e = est.loc[T]
        e = e[e.zstar.notna()].copy()
        row = mc.index[mc.index <= T][-1]
        e["mrank"] = mc.loc[row].rank(ascending=False).reindex(e.index)
        e["persist"] = sum(q[t].reindex(e.index).fillna(False).astype(int) for t in Ts[i - 3:i])
        e["adv"], e["tr60"] = adv.loc[row].reindex(e.index), tr60.loc[row].reindex(e.index)
        big = e[e.mrank <= TOP_MCAP]
        ew300[m1] = float(holding_returns(big.index, m1, rm, ld, data_end, dl, susp).mean())
        c = big[(big.persist >= 2) & (big.adv >= MIN_ADV) & (big.tr60 >= .9) & (big.beta <= 2)
                & (big.p >= .6) & (big.n_obs >= 200)].sort_values("zstar", ascending=False)
        for n in NS:
            pick = c.head(n).index
            if len(pick) == 0:
                ret[n][m1], cnt[n][m1] = np.nan, 0
                continue
            w = pd.Series(1 / len(pick), index=pick)
            W[n][T] = w
            ret[n][m1] = float((holding_returns(pick, m1, rm, ld, data_end, dl, susp) * w).sum())
            cnt[n][m1] = len(pick)
    rf = agg["Rf"]
    rows, series = {}, {}
    for n in NS:
        r = pd.Series(ret[n]); r.index = pd.PeriodIndex(r.index, freq="M")
        Wn = pd.DataFrame(W[n]).T.fillna(0).sort_index()
        c, t = turnover_cost(Wn, S.COST_BUY, S.COST_SELL)
        c.index = pd.PeriodIndex(c.index.to_period("M") + 1, freq="M")
        series[f"Top {n}"] = r - c.reindex(r.index).fillna(0)
        series[f"Top {n}"].attrs["turn"] = 100 * t.iloc[1:].mean()
        series[f"Top {n}"].attrs["cnt"] = pd.Series(cnt[n]).mean()
    e3 = pd.Series(ew300); e3.index = pd.PeriodIndex(e3.index, freq="M")
    series[f"EW top-{TOP_MCAP} mcap (all)"] = e3
    series["Market (own VW)"] = agg["M"]
    series["Risk-free"] = rf
    windows = (("1y", pd.Period("2025-10", "M")), ("3y", pd.Period("2023-10", "M")), ("5y", pd.Period("2021-10", "M")),
               ("7y", pd.Period("2019-10", "M")), ("10y", START), ("since 2012", pd.Period("2012-02", "M")))
    for label, start in windows:
        for name, r in series.items():
            r = r[(r.index >= start) & (r.index <= pd.Period("2026-09", "M"))].dropna()
            ex = r - rf.reindex(r.index)
            w = (1 + r).cumprod(); y = len(r) / 12
            rows[(label, name)] = {"months": len(r), "CAGR_%": 100 * (w.iloc[-1] ** (1 / y) - 1),
                                   "ann_vol_%": 100 * r.std() * np.sqrt(12), "sharpe": ex.mean() / r.std() * np.sqrt(12),
                                   "max_DD_%": 100 * (w / w.cummax() - 1).min(), "worst_month_%": 100 * r.min(),
                                   "hit_%": 100 * (r > 0).mean(), "pos_in_cnt": r.attrs.get("cnt", np.nan)}
    t = pd.DataFrame(rows).T
    t.index.names = ["window", "portfolio"]
    for name in series:
        if name.startswith("Top"):
            t.loc[(slice(None), name), "turnover_%/m"] = series[name].attrs["turn"]
    write_table(t.reset_index(), "topn_backtest" + sfx,
                f"Top-N Z* baskets within the {TOP_MCAP} largest by market cap, net of costs, monthly rebalance. "
                f"Filters: ADV >= Rp {MIN_ADV / 1e9:.0f} bn, trade share >= 90%, beta <= 2, p >= 0.6, persistence >= 2/3.")
    yr = pd.DataFrame({name: r[r.index <= pd.Period("2026-09", "M")].groupby(lambda p: p.year).apply(
        lambda x: 100 * ((1 + x.dropna()).prod() - 1) if x.notna().any() else np.nan)
        for name, r in series.items()})
    yr.index.name = "year"
    write_table(yr.reset_index(), "topn_backtest_annual" + sfx,
                "Calendar-year total returns (%) of the top-N Z* baskets, net of costs; 2026 is year-to-date through September.")
    pd.set_option("display.width", 220)
    print(t.round(2).to_string())
    print(yr.round(1).to_string())
    print({n: pd.Series(cnt[n]).loc[lambda s: s.index >= START].describe()[["min", "mean"]].tolist() for n in NS})


if __name__ == "__main__":
    main()
