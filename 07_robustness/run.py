"""Step 07 - robustness: factor-beta sorts (Fig 9.7), transaction costs, NW t-stats / ex-post beta, subperiods."""
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
from lib.io import is_synthetic, load, log, window_mask, write_table  # noqa: E402
from lib.portfolios import form_ls, holding_returns, turnover_cost  # noqa: E402
from lib.stats import ex_post_beta, nw_mean, summary  # noqa: E402

STEP = "07"


def factor_betas(Y, F):
    """Masked OLS of each column of Y (T x N) on [1, F] (T x k). Returns N x (k+1) coefficients."""
    M = np.isfinite(Y)
    Y0 = np.where(M, Y, 0.0)
    X = np.column_stack([np.ones(len(F)), F])
    A = np.einsum("ti,tj,tn->nij", X, X, M.astype(float))
    b = np.einsum("ti,tn->ni", X, Y0)
    with np.errstate(all="ignore"):
        ok = np.linalg.cond(A) < 1e10
        coef = np.full(b.shape, np.nan)
        coef[ok] = np.linalg.solve(A[ok], b[ok][..., None])[..., 0]
    return coef


def beta_sorts(agg):
    est = load(S.INTERIM / "zcapm_estimates.pkl")
    r = load(S.INTERIM / "returns_daily.pkl")
    traded = load(S.INTERIM / "traded_daily.pkl")
    rm = load(S.INTERIM / "returns_monthly.pkl")
    last_date = load(S.INTERIM / "last_date.pkl")
    delist = load(S.INTERIM / "delist_return.pkl")
    f = load(S.INTERIM / "factors_daily.pkl")
    min_leg = S.MIN_LEG_SIZE if S.ENFORCE_MIN_LEG else None
    facs = [c for c in S.FACTOR_SORTS if f[c].notna().any()]
    if not facs:
        log(STEP, "no local factors - skipping factor-beta sorts")
        return None
    out = {fac: {} for fac in facs}
    for T, e in est.groupby("T"):
        m1 = T.to_period("M") + 1
        if m1 not in rm.index:
            continue
        codes = pd.Index(e.loc[e["zstar"].notna(), "code"])
        win = window_mask(r.index, T, S.WINDOW_MONTHS)
        fw = f.loc[win, ["Ra", "Rf"] + facs].dropna()
        Y = r.loc[fw.index, codes].where(traded.loc[fw.index, codes]).sub(fw["Rf"], axis=0)
        F = np.column_stack([fw["Ra"] - fw["Rf"]] + [fw[c] for c in facs])
        coef = factor_betas(Y.to_numpy(), F)
        R = holding_returns(codes, m1, rm, last_date, f.index[-1], delist)
        for i, fac in enumerate(facs):
            score = pd.Series(coef[:, 2 + i], index=codes)
            res = form_ls(score, R, S.SORT_SCHEME, min_leg)
            if res is not None:
                out[fac][m1] = {k: v for k, v in res[0].items() if k.startswith("LS")}
    res = {}
    for fac, d in out.items():
        df = pd.DataFrame.from_dict(d, orient="index")
        df.index = pd.PeriodIndex(df.index, freq="M")
        res[fac] = df.sort_index()
    return res


def costs(agg, legs):
    hold = load(S.PROCESSED / "holdings.pkl")
    cost, turn = {}, {}
    for name, h in hold.groupby("portfolio"):
        W = h.pivot_table(index="T", columns="code", values="weight", fill_value=0.0).sort_index()
        c, turnover = turnover_cost(W, S.COST_BUY, S.COST_SELL)
        c.index = pd.PeriodIndex(c.index.to_period("M") + 1, freq="M")
        turnover.index = c.index
        cost[name], turn[name] = c, turnover
    cost = pd.DataFrame(cost).reindex(legs.index).fillna(0)
    turn = pd.DataFrame(turn).reindex(legs.index).iloc[1:].mean()      # rebalancing months only
    K = sum(c.startswith("LS") for c in legs.columns)
    rows = {}
    for k in range(1, K + 1):
        cls = cost[f"L{k}"] + cost[f"S{k}"]
        gross, net = agg[f"M+LS{k}"], agg[f"M+LS{k}"] - cls
        rows[f"M+LS{k}"] = {"turnover_L": turn[f"L{k}"],
                            "cost_%/m": 100 * cls.mean(),
                            "gross_mean_%": 100 * gross.mean(), "net_mean_%": 100 * net.mean(),
                            "gross_sharpe": summary(gross, agg["Rf"])["sharpe"],
                            "net_sharpe": summary(net, agg["Rf"])["sharpe"]}
    rows["g"] = {"turnover_L": turn["g"], "cost_%/m": 100 * cost["g"].mean(),
                 "gross_mean_%": 100 * agg["g"].mean(), "net_mean_%": 100 * (agg["g"] - cost["g"]).mean(),
                 "gross_sharpe": summary(agg["g"], agg["Rf"])["sharpe"],
                 "net_sharpe": summary(agg["g"] - cost["g"], agg["Rf"])["sharpe"]}
    t = pd.DataFrame(rows).T
    t.index.name = "Portfolio"
    return t


def main():
    legs = load(S.PROCESSED / "legs_monthly.pkl")
    agg = load(S.PROCESSED / "aggregates_monthly.pkl")
    rf = agg["Rf"]
    K = sum(c.startswith("LS") for c in legs.columns)
    mkt_ex = agg["M"] - rf

    # 1. NW t-stats and ex-post CAPM beta of L/S portfolios
    t = pd.DataFrame({f"LS{k}": pd.concat([nw_mean(legs[f"LS{k}"], S.NW_LAGS),
                                           ex_post_beta(legs[f"LS{k}"], mkt_ex, S.NW_LAGS)])
                      for k in range(1, K + 1)}).T
    t.index.name = "Portfolio"
    write_table(t, "robust_ls_nw_beta", f"Newey-West ({S.NW_LAGS} lags). Book footnote 6: L/S beta should be ~0.")

    # 2. transaction costs
    write_table(costs(agg, legs), "robust_costs",
                f"Costs: buy {S.COST_BUY:.2%}, sell {S.COST_SELL:.2%} per unit one-way turnover (drift ignored).")

    # 3. subperiods
    rows = {}
    for a, b in S.SUBPERIODS:
        sub = agg.loc[a:b] if b else agg.loc[a:]
        if len(sub) < 24:
            continue
        key = f"{a}..{b or 'end'}"
        rows[key] = {"T": len(sub), "Sharpe M": summary(sub["M"], rf)["sharpe"],
                     "Sharpe g": summary(sub["g"], rf)["sharpe"],
                     **{f"Sharpe M+LS{k}": summary(sub[f"M+LS{k}"], rf)["sharpe"] for k in range(1, K + 1)}}
    if rows:
        ts = pd.DataFrame(rows).T
        ts.index.name = "Subperiod"
        write_table(ts, "robust_subperiods")

    # 4. factor-beta sorts (Fig 9.7)
    bs = beta_sorts(agg)
    if bs:
        fig, ax = plt.subplots(figsize=(7, 5))
        z = pd.DataFrame({f"M+LS{k}": summary(agg[f"M+LS{k}"]) for k in range(1, K + 1)}).T
        ax.plot(z["sd_%"], z["mean_%"], "o-", label="M + L/S zeta")
        rows = {}
        for fac, df in bs.items():
            a = df.add(agg["M"].reindex(df.index), axis=0)
            s = pd.DataFrame({c: summary(a[c], rf) for c in a.columns}).T
            ax.plot(s["sd_%"], s["mean_%"], "o-", label=f"M + L/S beta_{fac}")
            for c in s.index:
                rows[f"M+{c} ({fac})"] = s.loc[c]
        m = summary(agg["M"])
        ax.scatter(m["sd_%"], m["mean_%"], marker="s", color="k", zorder=5, label="Market")
        ax.set_xlabel("Standard deviation (% per month)")
        ax.set_ylabel("Mean return (% per month)")
        ax.set_title("Fig 9.7 - Zeta vs factor-beta sorts" + (" [SYNTHETIC]" if is_synthetic() else ""), fontsize=10)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        S.OUT_FIGS.mkdir(parents=True, exist_ok=True)
        fig.savefig(S.OUT_FIGS / "fig_9_7.png", dpi=150)
        plt.close(fig)
        tb = pd.DataFrame(rows).T
        tb.index.name = "Portfolio"
        write_table(tb, "robust_factor_beta_sorts", "Aggregates of market + L/S sorted on factor betas.")
    log(STEP, f"robustness tables -> {S.OUT_TABLES}")


if __name__ == "__main__":
    main()
