"""Step 06d - the top-10 Z* basket (06c rule) simulated from the start of 2026: monthly path and each month's constituents.

Same selection as topn_backtest.py: market-cap rank <= 300, Z* top quintile in >= 2 of the 3 previous formation months,
ADV (60d) >= MIN_ADV, trades >= 90% of the last 60 days, beta <= 2, p >= 0.6, n_obs >= 200; the 10 highest Z*,
equal weight, formed at month-end T and held T -> T+1. The first month pays the full purchase cost.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import load, write_table  # noqa: E402
from lib.portfolios import holding_returns, turnover_cost  # noqa: E402

STEP = "06d"
N, TOP_MCAP, MIN_ADV = 10, 300, 3e9
FIRST, LAST = pd.Period("2026-01", "M"), pd.Period("2026-09", "M")


def main():
    est = load(S.INTERIM / "zcapm_estimates.pkl")
    rm = load(S.INTERIM / "returns_monthly.pkl")
    mc = load(S.INTERIM / "mcap_daily.pkl")
    tr = load(S.INTERIM / "traded_daily.pkl")
    ld = load(S.INTERIM / "last_date.pkl")
    dl = load(S.INTERIM / "delist_return.pkl")
    susp = load(S.INTERIM / "susp_monthly.pkl")
    agg = load(S.PROCESSED / "aggregates_monthly.pkl")
    data_end = load(S.INTERIM / "factors_daily.pkl").index[-1]
    sd = pd.read_csv(S.RAW / "stock_daily.csv.gz", usecols=["date", "code", "close", "value"], parse_dates=["date"])
    val = sd.pivot_table(index="date", columns="code", values="value").reindex(mc.index)
    px = sd.pivot_table(index="date", columns="code", values="close")
    adv = val.rolling(60, min_periods=40).mean()
    tr60 = tr.rolling(60, min_periods=40).mean()

    Ts = sorted(est["T"].unique())
    est = est.set_index(["T", "code"])
    q = {T: est.loc[T, "zstar"].rank(pct=True) >= 0.8 for T in Ts}

    def universe(i, T):
        """Eligible top-300 stocks at formation T with the filter inputs, and the selected top-N basket."""
        e = est.loc[T]
        e = e[e.zstar.notna()].copy()
        row = mc.index[mc.index <= T][-1]
        e["mcap_rank"] = mc.loc[row].rank(ascending=False).reindex(e.index)
        e["mcap_tn"] = mc.loc[row].reindex(e.index) / 1e12
        e["persist"] = sum(q[t].reindex(e.index).fillna(False).astype(int) for t in Ts[i - 3:i])
        e["adv_bn"], e["tr60"] = adv.loc[row].reindex(e.index) / 1e9, tr60.loc[row].reindex(e.index)
        big = e[e.mcap_rank <= TOP_MCAP]
        c = big[(big.persist >= 2) & (big.adv_bn >= MIN_ADV / 1e9) & (big.tr60 >= .9) & (big.beta <= 2)
                & (big.p >= .6) & (big.n_obs >= 200)].sort_values("zstar", ascending=False).head(N)
        return big, c

    W, gross, ew300, cons = {}, {}, {}, []
    for i, T in enumerate(Ts):
        m1 = T.to_period("M") + 1
        if i < 3 or not FIRST <= m1 <= LAST or m1 not in rm.index:
            continue
        big, c = universe(i, T)
        ew300[m1] = float(holding_returns(big.index, m1, rm, ld, data_end, dl, susp).mean())
        w = pd.Series(1 / len(c), index=c.index)
        r = holding_returns(c.index, m1, rm, ld, data_end, dl, susp)
        W[T], gross[m1] = w, float((r * w).sum())
        cons.append(c[["zstar", "beta", "p", "persist", "mcap_rank", "mcap_tn", "adv_bn"]].assign(
            formed=T.date(), month=str(m1), rank=range(1, len(c) + 1), weight_pct=100 * w,
            return_pct=100 * r, contrib_pct=100 * r * w).reset_index())

    Wd = pd.DataFrame(W).T.fillna(0).sort_index()
    cost, turn = turnover_cost(Wd, S.COST_BUY, S.COST_SELL)
    cost.index = turn.index = pd.PeriodIndex(cost.index.to_period("M") + 1, freq="M")
    g = pd.Series(gross); g.index = pd.PeriodIndex(g.index, freq="M")
    net = g - cost.reindex(g.index)
    value = (1 + net).cumprod()
    e3 = pd.Series(ew300); e3.index = g.index
    rf = agg["Rf"].reindex(g.index)
    mkt = agg["M"].reindex(g.index)

    monthly = pd.DataFrame({"n_stocks": Wd.gt(0).sum(axis=1).values, "gross_%": 100 * g, "cost_%": 100 * cost,
                            "net_%": 100 * net, "turnover_%": 100 * turn, "value_idx": 100 * value,
                            "drawdown_%": 100 * (value / value.cummax().clip(lower=1) - 1),
                            "EW300_%": 100 * e3, "market_%": 100 * mkt, "rf_%": 100 * rf})
    monthly.index.name = "month"

    def stats(r):
        v = (1 + r).cumprod()
        return {"months": len(r), "total_return_%": 100 * (v.iloc[-1] - 1),
                "ann_return_%": 100 * (v.iloc[-1] ** (12 / len(r)) - 1),
                "ann_vol_%": 100 * r.std() * np.sqrt(12),
                "sharpe": (r - rf).mean() / r.std() * np.sqrt(12),
                "max_DD_%": 100 * (v / v.cummax().clip(lower=1) - 1).min(),
                "best_month_%": 100 * r.max(), "worst_month_%": 100 * r.min(), "hit_%": 100 * (r > 0).mean()}
    summary = pd.DataFrame({"Top 10 (net)": stats(net), "EW top-300 mcap (all)": stats(e3),
                            "Market (own VW)": stats(mkt)}).T
    summary.index.name = "portfolio"

    cons = pd.concat(cons, ignore_index=True)
    cons = cons[["month", "formed", "rank", "code", "weight_pct", "return_pct", "contrib_pct", "zstar", "beta", "p",
                 "persist", "mcap_rank", "mcap_tn", "adv_bn"]]
    span = f"{FIRST}..{LAST}"
    write_table(summary.reset_index(), "top10_2026_summary",
                f"Top-10 Z* basket (top-{TOP_MCAP} mcap), {span}, monthly rebalance, net of costs. "
                "Volatility annualised from monthly returns; drawdown measured on month-end values from a start of 100.")
    write_table(monthly.reset_index().astype({"month": str}), "top10_2026_monthly",
                f"Top-10 Z* basket, monthly path {span}. Cost includes the initial purchase in {FIRST}.")
    write_table(cons, "top10_2026_constituents",
                f"Top-10 Z* basket constituents per holding month {span}: formation date, Z* rank, stock return "
                "(incl. delisting / suspension handling) and contribution to the basket's gross return.")
    # projected basket for the month after the last formation date (no returns yet)
    T = Ts[-1]
    nxt = T.to_period("M") + 1
    _, c = universe(len(Ts) - 1, T)
    prev = set(Wd.iloc[-1][lambda s: s > 0].index) if Wd.index[-1] < T else set()
    row = px.index[px.index <= T][-1]
    proj = c[["zstar", "beta", "p", "persist", "mcap_rank", "mcap_tn", "adv_bn"]].assign(
        rank=range(1, len(c) + 1), weight_pct=100 / len(c), close=px.loc[row].reindex(c.index),
        status=["held" if k in prev else "new" for k in c.index]).reset_index()
    proj = proj[["rank", "code", "status", "weight_pct", "close", "zstar", "beta", "p", "persist", "mcap_rank",
                 "mcap_tn", "adv_bn"]]
    dropped = sorted(prev - set(c.index))
    write_table(proj, f"top10_basket_{nxt}",
                f"Projected top-10 Z* basket for {nxt}, formed {T.date()} (close prices as of {row.date()}). "
                f"Dropped vs {nxt - 1}: {', '.join(dropped) or 'none'}.")

    pd.set_option("display.width", 220)
    print(summary.round(2).to_string())
    print(monthly.round(2).to_string())
    for m, d in cons.groupby("month", sort=False):
        print(f"\n{m}: " + ", ".join(f"{r.code} {r.return_pct:+.1f}%" for r in d.itertuples()))
    print(f"\nProjected {nxt} basket (formed {T.date()}), dropped: {dropped}")
    print(proj.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
