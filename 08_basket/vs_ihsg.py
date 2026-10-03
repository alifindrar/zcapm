"""Step 08b - the basket account (nav.csv from run.py) against the IDX Composite (IHSG).

IHSG is the price index (no dividends, no costs); the basket is net of fees with dividends reinvested, so the
comparison flatters the basket by the index's dividend yield (roughly 2-3% a year).
Outputs (08_basket/): vs_ihsg.png, vs_ihsg.md, vs_ihsg.csv (monthly series).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import load, to_markdown  # noqa: E402

OUT = ROOT / "08_basket"
BASKET, INDEX = "Z* basket", "IHSG"
COLORS = {BASKET: "#2a78d6", INDEX: "#eb6834"}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"


def stats(r, rf):
    v = (1 + r).cumprod()
    return {"months": len(r), "total_%": 100 * (v.iloc[-1] - 1), "CAGR_%": 100 * (v.iloc[-1] ** (12 / len(r)) - 1),
            "ann_vol_%": 100 * r.std() * np.sqrt(12),
            "sharpe": (r - rf.reindex(r.index)).mean() / r.std() * np.sqrt(12),
            "max_DD_%": 100 * (v / v.cummax().clip(lower=1) - 1).min(), "worst_month_%": 100 * r.min(),
            "hit_%": 100 * (r > 0).mean()}


def main():
    nav = pd.read_csv(OUT / "nav.csv")
    idx = pd.PeriodIndex(nav.month, freq="M")
    fm = load(S.INTERIM / "factors_monthly.pkl")
    rf = load(S.PROCESSED / "aggregates_monthly.pkl")["Rf"]
    r = pd.DataFrame({BASKET: nav.ret_pct.values / 100, INDEX: fm["IHSG"].reindex(idx).values}, index=idx)
    capital = nav.nav_start.iloc[0]

    rows = {}
    for label, n in (("full", len(r)), ("10y", 120), ("5y", 60), ("3y", 36), ("1y", 12)):
        for name in r:
            rows[(label, name)] = stats(r[name].iloc[-n:], rf)
    st = pd.DataFrame(rows).T.round(2)
    st.index.names = ["window", "portfolio"]
    yr = (100 * ((1 + r).groupby(r.index.year).prod() - 1)).round(1)
    yr["excess_pp"] = (yr[BASKET] - yr[INDEX]).round(1)
    yr.index.name = "year"
    ex = r[BASKET] - r[INDEX]
    beta = r[BASKET].cov(r[INDEX]) / r[INDEX].var()
    alpha = 12 * ((r[BASKET] - rf.reindex(idx)).mean() - beta * (r[INDEX] - rf.reindex(idx)).mean())
    rel = {"months basket beat IHSG_%": 100 * (ex > 0).mean(), "years basket beat IHSG": f"{(yr.excess_pp > 0).sum()} of {len(yr)}",
           "correlation": r[BASKET].corr(r[INDEX]), "beta to IHSG": beta, "alpha_%/yr": 100 * alpha,
           "tracking_error_%/yr": 100 * ex.std() * np.sqrt(12),
           "information_ratio": ex.mean() / ex.std() * np.sqrt(12)}
    rel = pd.DataFrame({"value": {k: v if isinstance(v, str) else f"{v:.2f}" for k, v in rel.items()}})
    rel.index.name = "measure"

    w = capital * (1 + r).cumprod()
    w.loc[idx[0] - 1] = capital
    w = w.sort_index()
    dd = 100 * (w / w.cummax() - 1)
    x = w.index.to_timestamp(how="end")
    w.assign(**{f"dd_{c}": dd[c] for c in dd}).round(2).to_csv(OUT / "vs_ihsg.csv", index_label="month")

    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
                         "axes.edgecolor": "#c3c2b7", "text.color": INK, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED})
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]},
                                  facecolor=SURFACE)
    for name in (INDEX, BASKET):
        ax.plot(x, w[name], color=COLORS[name], lw=2, label=name)
        ax.annotate(f"{name}\nRp {w[name].iloc[-1] / 1e6:,.0f} m ({100 * (w[name].iloc[-1] / capital - 1):+,.0f}%)",
                    (x[-1], w[name].iloc[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8.5,
                    color=INK)
        ax2.plot(x, dd[name], color=COLORS[name], lw=1.6, label=name)
        off, ha = ((0, -11), "center") if name == BASKET else ((34, -3), "left")   # IHSG low sits inside the basket's
        ax2.annotate(f"{name} {dd[name].min():.0f}%", (x[dd[name].argmin()], dd[name].min()), xytext=off,
                     textcoords="offset points", ha=ha, fontsize=8, color=INK)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1e6:,.0f}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v / 1e6:,.0f}" if str(v)[0] in "25" else ""))
    ax.set_ylabel("Account value, Rp million (log scale)")
    ax.set_title(f"Top-10 Z* basket vs IHSG: Rp {capital / 1e6:.0f} m invested {idx[0]}, through {idx[-1]}\n"
                 "Basket net of fees, whole lots, monthly rebalance; IHSG is the price index (no dividends)",
                 fontsize=10.5, loc="left")
    ax2.set_ylabel("Drawdown from peak, %")
    ax2.set_ylim(dd.min().min() * 1.22, 2)
    for a in (ax, ax2):
        a.set_facecolor(SURFACE)
        a.grid(color=GRID, lw=0.8, which="major")
        a.spines[["top", "right"]].set_visible(False)
        a.tick_params(which="both", length=0, labelsize=8.5)
    ax.legend(*[h[::-1] for h in ax.get_legend_handles_labels()], fontsize=9, loc="upper left", frameon=False)
    ax.set_xlim(x[0], x[-1] + pd.Timedelta(days=560))     # room for the end labels
    ax.set_xticks(pd.date_range(f"{x[0].year}", f"{x[-1].year}", freq="2YS"))
    ax.set_xticklabels([str(y) for y in range(x[0].year, x[-1].year + 1, 2)])
    fig.tight_layout()
    fig.savefig(OUT / "vs_ihsg.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)

    L = [f"# Basket vs IHSG, {idx[0]}..{idx[-1]}", "",
         f"Rp {capital:,.0f} in the top-10 Z* basket account (net of fees, whole lots, dividends reinvested) against the "
         "same amount in the IDX Composite. IHSG is the price index: it excludes dividends (roughly 2-3% a year) and "
         "any cost of holding it, so the basket's edge is overstated by about that much.", "",
         "![Basket vs IHSG](vs_ihsg.png)", "",
         "## Performance by window", "", to_markdown(st.reset_index()), "",
         "## Relative to IHSG (full period)", "", to_markdown(rel), "",
         "## Calendar years (%)", "", to_markdown(yr.reset_index()), ""]
    (OUT / "vs_ihsg.md").write_text("\n".join(L), encoding="utf-8")
    pd.set_option("display.width", 200)
    print(st.to_string()); print(rel.to_string()); print(yr.to_string())


if __name__ == "__main__":
    main()
