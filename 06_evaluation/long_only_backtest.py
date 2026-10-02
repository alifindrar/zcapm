"""Step 06b - investable long-only Z* strategies, rebalanced monthly: performance table + cumulative return chart.

Buckets are built from the step-04 legs (equal-weighted, bought at each month-end T, held to T+1), see BUCKETS:
deciles -> top 10/20/30% and bottom 30%; book24 -> top 5/10/25% and bottom 25%. Portfolio g and
50% M + 50% top-10% are also long-only. Net returns deduct turnover x (COST_BUY + COST_SELL) from holdings.pkl.
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import is_synthetic, load, log, write_table  # noqa: E402
from lib.portfolios import holding_returns, turnover_cost  # noqa: E402

STEP = "06b"
BUCKETS = {
    "deciles": {"Top 10% Z*": ["L1"], "Top 20% Z*": ["L1", "L2"], "Top 30% Z*": ["L1", "L2", "L3"],
                "Bottom 30% Z*": ["S1", "S2", "S3"]},
    "book24": {"Top 5% Z*": ["L3"], "Top 10% Z*": ["L3", "L4"], "Top 25% Z*": ["L3", "L4", "L5", "L6", "L7"],
               "Bottom 25% Z*": ["S3", "S4", "S5", "S6", "S7"]},
    "quintiles": {"Top 20% Z*": ["L1"], "Top 40% Z*": ["L1", "L2"], "Bottom 40% Z*": ["S1", "S2"]},
}[S.SORT_SCHEME]
BUCKETS["Portfolio g"] = ["g"]
BLEND_OF = "Top 10% Z*" if "Top 10% Z*" in BUCKETS else next(iter(BUCKETS))
BLEND = (f"50% M + 50% {BLEND_OF.replace(' Z*', '')}", BLEND_OF)
COLORS = ["tab:cyan", "tab:blue", "tab:green"]


def bucket_weights(hold, legs):
    """Holdings of a bucket at each T: stocks pooled across its legs, equal weight."""
    h = hold[hold["portfolio"].isin(legs)]
    if legs == ["g"]:
        return h.pivot_table(index="T", columns="code", values="weight", aggfunc="sum", fill_value=0.0)
    h = h.drop_duplicates(["T", "code"])
    W = h.assign(one=1.0).pivot_table(index="T", columns="code", values="one", fill_value=0.0)
    return W.div(W.sum(axis=1), axis=0)


def cost_series(W, index):
    c, turnover = turnover_cost(W, S.COST_BUY, S.COST_SELL)
    c.index = pd.PeriodIndex(c.index.to_period("M") + 1, freq="M")
    return c.reindex(index).fillna(0), turnover


def bucket_return(W, rm, last_date, data_end, index, delist):
    """Month-T+1 return of the pooled bucket, same holding-return convention as step 04."""
    out = {}
    for T, w in W.iterrows():
        m1 = T.to_period("M") + 1
        if m1 in index:
            w = w[w > 0]
            R = holding_returns(w.index, m1, rm, last_date, data_end, delist)
            out[m1] = float((R * w).sum())
    return pd.Series(out).reindex(index)


def stats(r, rf):
    r = r.dropna()
    ex = r - rf.reindex(r.index)
    wealth = (1 + r).cumprod()
    years = len(r) / 12
    dd = wealth / wealth.cummax() - 1
    return pd.Series({"CAGR_%": 100 * (wealth.iloc[-1] ** (1 / years) - 1),
                      "ann_vol_%": 100 * r.std() * np.sqrt(12),
                      "sharpe_ann": ex.mean() / r.std() * np.sqrt(12),
                      "max_DD_%": 100 * dd.min(),
                      "hit_rate_%": 100 * (r > 0).mean(),
                      "final_wealth": wealth.iloc[-1], "T": len(r)})


def main():
    legs = load(S.PROCESSED / "legs_monthly.pkl")
    agg = load(S.PROCESSED / "aggregates_monthly.pkl")
    hold = load(S.PROCESSED / "holdings.pkl")
    rm = load(S.INTERIM / "returns_monthly.pkl")
    fm = load(S.INTERIM / "factors_monthly.pkl")
    last_date = load(S.INTERIM / "last_date.pkl")
    delist = load(S.INTERIM / "delist_return.pkl")
    data_end = load(S.INTERIM / "factors_daily.pkl").index[-1]
    idx = legs.index
    rf = agg["Rf"]

    gross, net, turn = {}, {}, {}
    for name, members in BUCKETS.items():
        W = bucket_weights(hold, members)
        r = legs["g"] if members == ["g"] else (legs[members[0]] if len(members) == 1 else bucket_return(W, rm, last_date, data_end, idx, delist))
        c, t = cost_series(W, idx)
        gross[name], net[name], turn[name] = r, r - c, t.iloc[1:].mean()
    gross[BLEND[0]] = 0.5 * agg["M"] + 0.5 * gross[BLEND[1]]
    net[BLEND[0]] = 0.5 * agg["M"] + 0.5 * net[BLEND[1]]     # market sleeve treated as costless index
    turn[BLEND[0]] = 0.5 * turn[BLEND[1]]
    bench = {"Market (own VW)": agg["M"], "IHSG (price)": fm["IHSG"].reindex(idx), "Risk-free": rf}

    rows = {}
    for name in gross:
        rows[name] = pd.concat([stats(gross[name], rf).add_prefix("gross_")[["gross_CAGR_%", "gross_sharpe_ann"]],
                                stats(net[name], rf), pd.Series({"turnover_%/m": 100 * turn[name]})])
    for name, r in bench.items():
        rows[name] = stats(r, rf)
    t = pd.DataFrame(rows).T
    t.index.name = "Portfolio"
    span = f"{idx[0]}..{idx[-1]} (T={len(idx)})"
    write_table(t, "long_only_backtest",
                f"Long-only, equal-weighted Z* buckets rebalanced monthly, {span}. Stats net of costs "
                f"(buy {S.COST_BUY:.2%}, sell {S.COST_SELL:.2%}); gross_* before costs. "
                f"Sharpe = mean(R - Rf)/sd(R) x sqrt(12). Rf = {S.RF_FILE.name}.")

    # ---------------- cumulative return chart (net of costs) + drawdowns
    tops = [n for n in BUCKETS if n.startswith("Top")]
    bottom = next(n for n in BUCKETS if n.startswith("Bottom"))
    series = {**{n: net[n] for n in tops + [BLEND[0], "Portfolio g", bottom]}, **bench}
    styles = {"Market (own VW)": dict(color="black", lw=2), "IHSG (price)": dict(color="grey", lw=1.5, ls="--"),
              "Risk-free": dict(color="grey", lw=1, ls=":"), bottom: dict(color="tab:red", lw=1.2, alpha=.8),
              **{n: dict(color=c, lw=1.5) for n, c in zip(tops, COLORS)},
              BLEND[0]: dict(color="tab:orange", lw=1.4), "Portfolio g": dict(color="tab:purple", lw=1.4)}
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
    for n, r in series.items():
        w = (1 + r.fillna(0)).cumprod()
        x = w.index.to_timestamp(how="end")
        ax.plot(x, w, label=f"{n} ({100 * (w.iloc[-1] - 1):+.0f}%)", **styles.get(n, dict(lw=1.4)))
        if n in (BLEND_OF, "Market (own VW)", "Portfolio g"):
            ax2.plot(x, 100 * (w / w.cummax() - 1), label=n, **styles.get(n, dict(lw=1.2)))
    ax.set_yscale("log")
    ax.set_ylabel("Growth of Rp 1 (log scale)")
    ax.set_title("Long-only Z* strategies, monthly rebalance, net of costs - " + span
                 + (" [SYNTHETIC]" if is_synthetic() else ""), fontsize=10)
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=8, loc="upper left")
    ax2.set_ylabel("Drawdown %")
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=7, loc="lower left")
    fig.tight_layout()
    S.OUT_FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(S.OUT_FIGS / "long_only_cumulative.png", dpi=150)
    plt.close(fig)

    # ---------------- calendar-year returns
    yr = pd.DataFrame({n: (1 + r).groupby(r.index.year).prod() - 1 for n, r in series.items()}) * 100
    yr.index.name = "Year"
    write_table(yr, "long_only_annual", "Calendar-year returns, % (net of costs; partial first/last year).")

    log(STEP, f"{span}; table -> long_only_backtest, figure -> long_only_cumulative.png")
    log(STEP, "net CAGR / Sharpe: " + "; ".join(f"{n} {t.loc[n, 'CAGR_%']:.1f}% / {t.loc[n, 'sharpe_ann']:.2f}"
                                                  for n in t.index))


if __name__ == "__main__":
    main()
