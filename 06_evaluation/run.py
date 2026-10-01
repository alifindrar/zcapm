"""Step 06 - Tables 9.1-9.5, Figures 9.1-9.6 and GRS tests."""
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
from lib.portfolios import ls_labels  # noqa: E402
from lib.stats import grs, summary  # noqa: E402

STEP = "06"
FACS = ["SMB", "HML", "MOM"]


def table_9_1(legs, zs, rf, K):
    rows = {}
    for k, lab in zip(range(1, K + 1), ls_labels(S.SORT_SCHEME)):
        L, Sh, LS = legs[f"L{k}"], legs[f"S{k}"], legs[f"LS{k}"]
        rows[f"LS{k} {lab}"] = {
            "Long Z*": zs[f"L{k}"].mean(), "Short Z*": zs[f"S{k}"].mean(), "L-S Z*": zs[f"LS{k}"].mean(),
            "Long R %": 100 * L.mean(), "Long sd %": 100 * L.std(),
            "Short R %": 100 * Sh.mean(), "Short sd %": 100 * Sh.std(),
            "L-S R %": 100 * LS.mean(), "L-S sd %": 100 * LS.std(), "Sharpe": LS.mean() / LS.std()}
    for name, r in (("Market - Rf", legs["_M"] - rf), ("Portfolio g - Rf", legs["g"] - rf)):
        rows[name] = {"L-S R %": 100 * r.mean(), "L-S sd %": 100 * r.std(), "Sharpe": r.mean() / r.std()}
    t = pd.DataFrame(rows).T
    t.index.name = "Portfolio"
    return t


def perf_table(agg, cols, rf, extra):
    t = pd.DataFrame({c: summary(agg[c], rf) for c in cols + extra if c in agg}).T
    t.index.name = "Portfolio"
    return t


def scatter(ax, t, label, **kw):
    ax.plot(t["sd_%"], t["mean_%"], marker="o", label=label, **kw)


def points(ax, t, names):
    for n in names:
        if n in t.index:
            ax.scatter(t.loc[n, "sd_%"], t.loc[n, "mean_%"], marker="s", zorder=5)
            ax.annotate(n, (t.loc[n, "sd_%"], t.loc[n, "mean_%"]), fontsize=8, xytext=(4, 4),
                        textcoords="offset points")


def finish(fig, ax, name, title, xlabel="Standard deviation (% per month)", ylabel="Mean return (% per month)"):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title + (" [SYNTHETIC]" if is_synthetic() else ""), fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    S.OUT_FIGS.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(S.OUT_FIGS / f"{name}.png", dpi=150)
    plt.close(fig)


def main():
    legs = load(S.PROCESSED / "legs_monthly.pkl")
    zs = load(S.PROCESSED / "legs_zstar.pkl")
    agg = load(S.PROCESSED / "aggregates_monthly.pkl")
    rf = agg["Rf"]
    legs["_M"] = agg["M"]
    K = sum(c.startswith("LS") for c in legs.columns)
    J = sum(c.startswith("LO") for c in legs.columns)
    span = f"{agg.index[0]}..{agg.index[-1]} (T={len(agg)})"

    # ---------------- tables
    t91 = table_9_1(legs, zs, rf, K)
    write_table(t91, "table_9_1", f"Long/short zeta portfolios, {span}. L/S Sharpe = mean/sd (zero investment).")
    fac_M = [f"M+{f}" for f in FACS]
    fac_g = [f"g+{f}" for f in FACS]
    t92 = perf_table(agg, [f"M+LS{k}" for k in range(1, K + 1)], rf, fac_M + ["M"])
    t93 = perf_table(agg, [f"g+LS{k}" for k in range(1, K + 1)], rf, fac_g + ["g"])
    t94 = perf_table(agg, [f"LOA_M_{j}" for j in range(1, J + 1)], rf, ["M"])
    t95 = perf_table(agg, [f"LOA_g_{j}" for j in range(1, J + 1)], rf, ["g"])
    for t, n, note in ((t92, "table_9_2", "Market + L/S (leveraged)"), (t93, "table_9_3", "g + L/S (leveraged)"),
                       (t94, "table_9_4", "50% market + 50% long-only leg"),
                       (t95, "table_9_5", "50% g + 50% long-only leg")):
        write_table(t, n, f"{note}, {span}. Sharpe = mean(R - Rf)/sd(R).")

    # ---------------- GRS
    facs = [f for f in FACS if f in agg]
    ex = agg.sub(rf, axis=0)
    rows = {}
    for base in ("M", "g"):
        assets = ex[[f"{base}+LS{k}" for k in range(1, K + 1)]]
        rows[f"{base}+LS vs market"] = grs(assets, ex[["M"]].rename(columns={"M": "MKT"}))
        if facs:
            F = pd.concat([ex[["M"]].rename(columns={"M": "MKT"}), agg[facs]], axis=1)
            rows[f"{base}+LS vs market+{'+'.join(facs)}"] = grs(assets, F)
    tg = pd.DataFrame(rows).T
    tg.index.name = "Test"
    write_table(tg, "grs", "Gibbons-Ross-Shanken test of zero alphas (H0: benchmark is efficient).")

    # ---------------- figures
    ls_stats = pd.DataFrame({f"LS{k}": {"z": zs[f"LS{k}"].mean(), "mean_%": 100 * legs[f"LS{k}"].mean(),
                                        "sd_%": 100 * legs[f"LS{k}"].std()} for k in range(1, K + 1)}).T
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(ls_stats["z"], ls_stats["mean_%"], "o", label="L/S zeta portfolios")
    b = np.polyfit(ls_stats["z"], ls_stats["mean_%"], 1)
    r2 = np.corrcoef(ls_stats["z"], ls_stats["mean_%"])[0, 1] ** 2
    xs = np.linspace(ls_stats["z"].min(), ls_stats["z"].max(), 10)
    ax.plot(xs, np.polyval(b, xs), "--", label=f"fit: slope {b[0]:.3f}, R2 {r2:.2f}")
    for n, row in ls_stats.iterrows():
        ax.annotate(n, (row["z"], row["mean_%"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
    finish(fig, ax, "fig_9_1", "Fig 9.1 - L/S return vs average Z*", xlabel="Average Z* (long - short)")

    fig, ax = plt.subplots(figsize=(7, 5))
    scatter(ax, ls_stats, "L/S zeta portfolios")
    others = pd.DataFrame({n: summary(s) for n, s in {"Market-Rf": agg["M"] - rf,
                                                     **{f: agg[f] for f in facs}}.items()}).T
    points(ax, others, others.index)
    finish(fig, ax, "fig_9_2", "Fig 9.2 - L/S zeta portfolios: return vs risk")

    fig, ax = plt.subplots(figsize=(7, 5))
    scatter(ax, t92.loc[[f"M+LS{k}" for k in range(1, K + 1)]], "Market + L/S")
    scatter(ax, t93.loc[[f"g+LS{k}" for k in range(1, K + 1)]], "g + L/S")
    points(ax, pd.concat([t92, t93]), ["M", "g"] + fac_M + fac_g)
    finish(fig, ax, "fig_9_3", "Fig 9.3 - Leveraged aggregate frontiers")

    lo = pd.DataFrame({f"LO{j}": summary(legs[f"LO{j}"]) for j in range(1, J + 1)}).T
    fig, ax = plt.subplots(figsize=(7, 5))
    scatter(ax, lo, "Long-only zeta legs (1 = lowest Z*)")
    points(ax, pd.concat([t92, t93]), ["M", "g"])
    finish(fig, ax, "fig_9_4", "Fig 9.4 - Long-only zeta portfolios")

    for t, n, lab in ((t94, "fig_9_5", "50% market + 50% long-only"), (t95, "fig_9_6", "50% g + 50% long-only")):
        fig, ax = plt.subplots(figsize=(7, 5))
        scatter(ax, t.iloc[:J], lab)
        points(ax, pd.concat([t92, t93]), ["M", "g"])
        finish(fig, ax, n, f"Fig {n[-3:].replace('_', '.')} - {lab}")

    log(STEP, f"tables -> {S.OUT_TABLES}, figures -> {S.OUT_FIGS}")
    log(STEP, f"Sharpe: M {t92.loc['M', 'sharpe']:.3f}, g {t93.loc['g', 'sharpe']:.3f}, "
              f"best M+LS {t92.iloc[:K]['sharpe'].max():.3f}, best g+LS {t93.iloc[:K]['sharpe'].max():.3f}")
    log(STEP, "GRS: " + "; ".join(f"{i}: {r.GRS:.2f} (p={r.p_value:.4f})" for i, r in tg.iterrows()))


if __name__ == "__main__":
    main()
