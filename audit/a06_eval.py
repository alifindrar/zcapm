"""Audit of step 06 - Tables 9.1-9.5 and GRS rebuilt with independent code, stability of the results, and the
step.md success criteria.

    python audit/a06_eval.py
"""
import numpy as np
import pandas as pd
from scipy import stats

from common import S, SUBPERIODS, processed, show, write
from lib.io import log
from lib.stats import nw_mean

STEP = "a06"
MONTHLY_SCALE = 21
# Book Table 9.1 (US, 1965-2018): long-short Z*, long-short mean return %, SD %, Sharpe
BOOK = pd.DataFrame({"book_Z*": [10.73, 9.68, 7.91, 4.82, 3.52, 2.68, 2.05, 1.54, 1.12, 0.76, 0.44, 0.14],
                     "book_R_%": [2.34, 2.16, 1.96, 1.29, 1.04, 0.75, 0.52, 0.43, 0.24, 0.15, 0.13, 0.07],
                     "book_sd_%": [9.12, 7.67, 6.78, 4.98, 3.92, 3.35, 2.72, 2.18, 1.80, 1.54, 1.22, 1.05],
                     "book_sharpe": [.26, .28, .29, .26, .27, .22, .19, .20, .13, .10, .11, .07]},
                    index=[f"LS{k}" for k in range(1, 13)])


def perf(r, rf):
    """mean %, sd %, Sharpe = mean(r - rf)/sd(r), T - written without lib.stats.summary."""
    x = np.asarray(r, float)
    ok = np.isfinite(x)
    x, e = x[ok], (np.asarray(r, float) - np.asarray(rf, float))[ok]
    sd = np.sqrt(((x - x.mean()) ** 2).sum() / (len(x) - 1))
    return [100 * x.mean(), 100 * sd, e.mean() / sd, len(x)]


def grs_test(assets, factors, ml_omega=False):
    """GRS statistic from asset-by-asset OLS. ml_omega=True uses the factor covariance with divisor T."""
    df = pd.concat([assets, factors], axis=1).dropna()
    A, F = df[assets.columns].to_numpy(), df[factors.columns].to_numpy()
    T, N = A.shape
    L = F.shape[1]
    X = np.column_stack([np.ones(T), F])
    alpha, E = np.empty(N), np.empty((T, N))
    for i in range(N):
        c = np.linalg.solve(X.T @ X, X.T @ A[:, i])
        alpha[i], E[:, i] = c[0], A[:, i] - X @ c
    Sigma = E.T @ E / (T - L - 1)
    mu = F.mean(0)
    Fc = F - mu
    Omega = Fc.T @ Fc / (T if ml_omega else T - 1)
    q = alpha @ np.linalg.inv(Sigma) @ alpha / (1 + mu @ np.linalg.inv(Omega) @ mu)
    stat = T / N * (T - N - L) / (T - L - 1) * q
    return stat, stats.f.sf(stat, N, T - N - L), T


def compare(mine, name, cols):
    ref = pd.read_csv(S.OUT_TABLES / f"{name}.csv", index_col=0)
    d = (mine[cols].to_numpy(float) - ref[cols].to_numpy(float))
    return {"table": name, "rows": len(ref), "max_abs_diff": np.nanmax(np.abs(d)),
            "nan_pattern_equal": bool((np.isnan(d) == np.isnan(ref[cols].to_numpy(float))).all())}


def main():
    legs, zs, agg = processed("legs_monthly"), processed("legs_zstar"), processed("aggregates_monthly")
    rf, M = agg["Rf"], agg["M"]
    K, J = 12, 24
    ls = [f"LS{k}" for k in range(1, K + 1)]
    facs = [c for c in ("SMB", "HML", "MOM") if c in agg]

    # ---- 1. tables rebuilt
    checks = []
    t91 = pd.DataFrame({k: {"Long Z*": zs[f"L{k}"].mean(), "Short Z*": zs[f"S{k}"].mean(),
                            "L-S Z*": zs[f"L{k}"].mean() - zs[f"S{k}"].mean(),
                            "Long R %": 100 * legs[f"L{k}"].mean(), "Long sd %": 100 * legs[f"L{k}"].std(),
                            "Short R %": 100 * legs[f"S{k}"].mean(), "Short sd %": 100 * legs[f"S{k}"].std(),
                            "L-S R %": 100 * (legs[f"L{k}"] - legs[f"S{k}"]).mean(),
                            "L-S sd %": 100 * (legs[f"L{k}"] - legs[f"S{k}"]).std(),
                            "Sharpe": (legs[f"L{k}"] - legs[f"S{k}"]).mean() / (legs[f"L{k}"] - legs[f"S{k}"]).std()}
                        for k in range(1, K + 1)}).T
    for nm, x in (("M", M - rf), ("g", legs["g"] - rf)):
        t91.loc[nm, ["L-S R %", "L-S sd %", "Sharpe"]] = [100 * x.mean(), 100 * x.std(), x.mean() / x.std()]
    checks.append(compare(t91, "table_9_1", list(t91.columns)))
    pc = ["mean_%", "sd_%", "sharpe", "T"]
    sets = {"table_9_2": [f"M+LS{k}" for k in range(1, K + 1)] + [f"M+{c}" for c in facs] + ["M"],
            "table_9_3": [f"g+LS{k}" for k in range(1, K + 1)] + [f"g+{c}" for c in facs] + ["g"],
            "table_9_4": [f"LOA_M_{j}" for j in range(1, J + 1)] + ["M"],
            "table_9_5": [f"LOA_g_{j}" for j in range(1, J + 1)] + ["g"]}
    tabs = {}
    for name, cols in sets.items():
        tabs[name] = pd.DataFrame({c: perf(agg[c], rf) for c in cols}, index=pc).T
        checks.append(compare(tabs[name], name, pc))
    ex = agg.sub(rf, axis=0)
    mkt = ex[["M"]].rename(columns={"M": "MKT"})
    grs_rows, ref = {}, pd.read_csv(S.OUT_TABLES / "grs.csv", index_col=0)
    for base in ("M", "g"):
        assets = ex[[f"{base}+LS{k}" for k in range(1, K + 1)]]
        for label, F in ((f"{base}+LS vs market", mkt),
                         (f"{base}+LS vs market+{'+'.join(facs)}", pd.concat([mkt, agg[facs]], axis=1))):
            st, p, T = grs_test(assets, F)
            st2, p2, _ = grs_test(assets, F, ml_omega=True)
            grs_rows[label] = {"GRS": st, "p": p, "T": T, "GRS_pipeline": ref.at[label, "GRS"],
                               "p_pipeline": ref.at[label, "p_value"], "GRS_omega_div_T": st2, "p_omega_div_T": p2}
    g = pd.DataFrame(grs_rows).T
    checks.append({"table": "grs", "rows": len(g), "max_abs_diff": (g["GRS"] - g["GRS_pipeline"]).abs().max(),
                   "nan_pattern_equal": True})
    chk = pd.DataFrame(checks).set_index("table")
    show(STEP, "independent rebuild vs outputs/tables_v2", chk)
    write(chk, "a06_table_rebuild_check", STEP)
    show(STEP, "GRS: independent, pipeline, and with factor covariance divided by T", g.round(4))
    write(g, "a06_grs", STEP)

    # ---- 2. Table 9.1 next to the book
    cmp = pd.DataFrame({"Z*_daily": t91.loc[range(1, K + 1), "L-S Z*"].to_numpy(),
                        "Z*_x21": MONTHLY_SCALE * t91.loc[range(1, K + 1), "L-S Z*"].to_numpy(),
                        "R_%": t91.loc[range(1, K + 1), "L-S R %"].to_numpy(),
                        "sd_%": t91.loc[range(1, K + 1), "L-S sd %"].to_numpy(),
                        "sharpe": t91.loc[range(1, K + 1), "Sharpe"].to_numpy(),
                        "t_nw": [nw_mean(legs[c], S.NW_LAGS)["t_nw"] for c in ls]}, index=ls).join(BOOK)
    show(STEP, "long/short portfolios next to book Table 9.1", cmp.round(2))
    write(cmp, "a06_table_9_1_vs_book", STEP)

    # ---- 3. stability
    rows = {}
    for c in ls + ["avg LS3..LS12 (top half minus bottom half)", "avg LS1..LS12"]:
        s = legs[ls[2:]].mean(axis=1) if c.startswith("avg LS3") else legs[ls].mean(axis=1) if c.startswith("avg") \
            else legs[c]
        srt = s.sort_values()
        row = {"mean_%": 100 * s.mean(), "t_nw": nw_mean(s, S.NW_LAGS)["t_nw"], "median_%": 100 * s.median(),
               "mean_excl_best5_%": 100 * srt[:-5].mean(), "mean_excl_worst5_%": 100 * srt[5:].mean(),
               "share_months>0": (s > 0).mean()}
        for a, b in SUBPERIODS:
            row[f"{a[:4]}-{b[:4]}_%"] = 100 * s.loc[a:b].mean()
            row[f"{a[:4]}-{b[:4]}_t"] = nw_mean(s.loc[a:b], S.NW_LAGS)["t_nw"]
        rows[c] = row
    st = pd.DataFrame(rows).T
    show(STEP, "stability of long/short returns", st.round(2))
    write(st, "a06_ls_stability", STEP)

    sub = {}
    for a, b in SUBPERIODS + [("2014-01", "2026-06")]:
        e = ex.loc[a:b]
        stt, p, T = grs_test(e[[f"M+LS{k}" for k in range(1, K + 1)]], e[["M"]])
        sub[f"{a}..{b}"] = {"T": T, "GRS": stt, "p": p, "sharpe_M": perf(agg["M"].loc[a:b], rf.loc[a:b])[2],
                            "best_M+LS_sharpe": max(perf(agg[f"M+LS{k}"].loc[a:b], rf.loc[a:b])[2]
                                                    for k in range(1, K + 1)),
                            "M+LS_beating_M": sum(perf(agg[f"M+LS{k}"].loc[a:b], rf.loc[a:b])[2]
                                                  > perf(agg["M"].loc[a:b], rf.loc[a:b])[2] for k in range(1, K + 1))}
    sub = pd.DataFrame(sub).T
    show(STEP, "GRS (M+LS vs market) and Sharpe by subperiod", sub.round(3))
    write(sub, "a06_grs_subperiods", STEP)

    # ---- 4. step.md section 4 success criteria
    z, R, sd = cmp["Z*_daily"], cmp["R_%"], cmp["sd_%"]
    shM, shg = tabs["table_9_2"].loc["M", "sharpe"], tabs["table_9_3"].loc["g", "sharpe"]
    sM = tabs["table_9_2"]["sharpe"].iloc[:K].to_numpy()
    sg = tabs["table_9_3"]["sharpe"].iloc[:K].to_numpy()
    lo = tabs["table_9_4"]["sharpe"].iloc[:J].to_numpy()
    log_g = tabs["table_9_5"]["sharpe"].iloc[:J].to_numpy()
    crit = pd.DataFrame([
        ("1 L/S return rises with Z*", f"Spearman {stats.spearmanr(z, R).statistic:.2f}, R2 {np.corrcoef(z, R)[0, 1] ** 2:.2f}; "
                                       f"LS1..LS4 = {R.iloc[0]:.2f}, {R.iloc[1]:.2f}, {R.iloc[2]:.2f}, {R.iloc[3]:.2f}"),
        ("1 L/S return rises with SD", f"Spearman {stats.spearmanr(sd, R).statistic:.2f}, R2 {np.corrcoef(sd, R)[0, 1] ** 2:.2f}"),
        ("2 M+LS Sharpe above M", f"{int((sM > shM).sum())} of {K} (M {shM:.3f}, best {sM.max():.3f}, LS1 {sM[0]:.3f})"),
        ("2 g-set dominates M-set", f"{int((sg > sM).sum())} of {K}, mean Sharpe gain {np.mean(sg - sM):.3f}"),
        ("3 long-only aggregates, high-Z* half beats M", f"{int((lo[J // 2:] > shM).sum())} of {J // 2}; "
                                                         f"low-Z* half {int((lo[:J // 2] > shM).sum())} of {J // 2}"),
        ("3 same with g", f"{int((log_g[J // 2:] > shg).sum())} of {J // 2}; low-Z* half {int((log_g[:J // 2] > shg).sum())} of {J // 2}"),
        ("4 GRS rejects M", "; ".join(f"{i}: {r_.GRS:.2f} (p {r_.p:.3f})" for i, r_ in g.iterrows())),
    ], columns=["criterion", "evidence"]).set_index("criterion")
    pd.set_option("display.max_colwidth", 200, "display.width", 250)
    show(STEP, "step.md success criteria", crit)
    write(crit, "a06_success_criteria", STEP)
    lot = tabs["table_9_4"].iloc[:J].assign(avg_zstar=[zs[f"LO{j}"].mean() for j in range(1, J + 1)])
    log(STEP, f"long-only legs: Spearman(avg Z*, Sharpe of 50/50 aggregate) = "
              f"{stats.spearmanr(lot['avg_zstar'], lot['sharpe']).statistic:.2f}")


if __name__ == "__main__":
    main()
