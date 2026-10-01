"""Audit of step 03 - the repo's EM (lib/em.py) against a port of the book's MATLAB routine.

The port follows solve_hidden_variable_v2.m / solve_lineq_v2.m from audit.md: start from the sign of the
no-intercept market-model residual, iterate E-step / linear solve, stop when the largest relative change in
(beta, Z, p, sigma2) is <= 0.001. It is run on every formation window with the same inputs as step 03.

    python audit/a03_em.py
"""
import numpy as np
import pandas as pd

from common import OUT, S, interim, show, write
from lib.em import fit_zcapm
from lib.io import log, window_mask
from lib.portfolios import form_ls, holding_returns, leg_members, n_ls

STEP = "a03"
PORT_MAXIT = 5000
RECHECK_EVERY = 24        # every n-th window is refitted with a larger iteration cap
RECHECK_MAXIT = 5000


def matlab_em(Y, x, s, tol=1e-3, maxit=PORT_MAXIT):
    """Book EM for all columns of Y at once (NaN = missing day). Returns beta, Z, p, iterations, stopped."""
    M = np.isfinite(Y) & np.isfinite(x)[:, None] & np.isfinite(s)[:, None]
    Mf = M.astype(float)
    Y0 = np.where(M, Y, 0.0)
    X, Sg = np.nan_to_num(x)[:, None], np.nan_to_num(s)[:, None]
    n = Mf.sum(0)
    Sxx, Sss, Sxy = (Mf * X ** 2).sum(0), (Mf * Sg ** 2).sum(0), (X * Y0).sum(0)

    def solve(d):
        a12, r2 = (X * Sg * d).sum(0), (Sg * Y0 * d).sum(0)
        det = Sxx * Sss - a12 ** 2
        return (Sxy * Sss - a12 * r2) / det, (Sxx * r2 - a12 * Sxy) / det

    u = (Y0 - Sxy / Sxx * X) * Mf                       # ols_estimator(X, Y), market only, no intercept
    d = np.where(u >= 0, 1.0, -1.0) * Mf
    b, z = solve(d)                                     # ols_estimator(Z, Y) with the signed RD column
    p = (d > 0).sum(0) / n
    s2 = (((Y0 - b * X - z * d * Sg) * Mf) ** 2).sum(0) / n
    it = np.zeros(Y.shape[1], int)
    stopped = np.zeros(Y.shape[1], bool)
    act = np.arange(Y.shape[1])
    for _ in range(maxit):
        y, m = Y0[:, act], Mf[:, act]
        R = y - b[act] * X
        ep = np.exp(-(R - z[act] * Sg) ** 2 / 2 / s2[act])
        en = np.exp(-(R + z[act] * Sg) ** 2 / 2 / s2[act])
        tau = ep * p[act] / (ep * p[act] + en * (1 - p[act])) * m
        dt = 2 * tau - m
        a12, r2 = (X * Sg * dt).sum(0), (Sg * y * dt).sum(0)
        det = Sxx[act] * Sss[act] - a12 ** 2
        bn = (Sxy[act] * Sss[act] - a12 * r2) / det
        zn = (Sxx[act] * r2 - a12 * Sxy[act]) / det
        pn = tau.sum(0) / n[act]
        R = y - bn * X
        sn = ((R ** 2 - 2 * R * zn * dt * Sg + zn ** 2 * Sg ** 2) * m).sum(0) / n[act]
        delta = np.max(np.abs([(bn - b[act]) / b[act], (zn - z[act]) / z[act], (pn - p[act]) / p[act],
                               (sn - s2[act]) / s2[act]]), axis=0)
        b[act], z[act], p[act], s2[act] = bn, zn, pn, sn
        it[act] += 1
        done = ~(delta > tol)                           # NaN delta also stops, as `while (delta>0.001)` would
        stopped[act[done]] = True
        act = act[~done]
        if act.size == 0:
            break
    return b, z, p, it, stopped


def leg_of(score, scheme):
    """Slice label per stock (5% slices only, i.e. L3..L12 / S3..S12), for comparing assignments."""
    out = pd.Series("", index=score.index)
    for name, codes in leg_members(score, scheme).items():
        if int(name[1:]) > 2:
            out[codes] = name
    return out


def main():
    r, traded = interim("returns_daily"), interim("traded_daily")
    elig, f, est = interim("eligible_monthly"), interim("factors_daily"), interim("zcapm_estimates")
    rm, last_date = interim("returns_monthly"), interim("last_date")
    dates = r.index
    months = sorted(est["T"].unique())
    rows, port, recheck, ls_port, ls_repo = {}, [], {}, {}, {}
    with np.errstate(all="ignore"):
        for i, T in enumerate(months):
            T = pd.Timestamp(T)
            win = window_mask(dates, T, S.WINDOW_MONTHS)
            codes = elig.columns[elig.loc[T]]
            fw = f.loc[win]
            Y = r.loc[win, codes].where(traded.loc[win, codes]).sub(fw["Rf"], axis=0).to_numpy()
            x, s = (fw["Ra"] - fw["Rf"]).to_numpy(), fw["sigma_a"].to_numpy()
            b, z, p, it, stopped = matlab_em(Y, x, s)
            m = pd.DataFrame({"T": T, "beta": b, "Z": z, "p": p, "zstar": z * (2 * p - 1), "iters": it,
                              "stopped": stopped}, index=codes)
            port.append(m.reset_index(names="code"))
            e = est[est["T"] == T].set_index("code").reindex(codes)
            row = {"N": len(codes), "port_not_stopped": int((~stopped).sum()), "port_median_iters": np.median(it),
                   "repo_converged_share": e["converged"].mean(),
                   "rank_corr_zstar": m["zstar"].corr(e["zstar"], method="spearman"),
                   "corr_beta": m["beta"].corr(e["beta"]),
                   "median_abs_zstar_port": m["zstar"].abs().median(),
                   "median_abs_zstar_repo": e["zstar"].abs().median()}
            both = m["zstar"].notna() & e["zstar"].notna()
            if both.sum() >= 2 * n_ls(S.SORT_SCHEME):
                lp, lr = leg_of(m.loc[both, "zstar"], S.SORT_SCHEME), leg_of(e.loc[both, "zstar"], S.SORT_SCHEME)
                row["share_in_different_slice"] = (lp != lr).mean()
                k = max(1, int(round(0.05 * both.sum())))
                row["top5%_overlap"] = len(set(m.loc[both, "zstar"].nlargest(k).index)
                                           & set(e.loc[both, "zstar"].nlargest(k).index)) / k
                row["bottom5%_overlap"] = len(set(m.loc[both, "zstar"].nsmallest(k).index)
                                              & set(e.loc[both, "zstar"].nsmallest(k).index)) / k
                m1 = T.to_period("M") + 1
                if m1 in rm.index:
                    R = holding_returns(codes[both], m1, rm, last_date, dates[-1], S.DELIST_RETURN)
                    for store, score in ((ls_port, m.loc[both, "zstar"]), (ls_repo, e.loc[both, "zstar"])):
                        res = form_ls(score, R, S.SORT_SCHEME)
                        if res is not None:
                            store[m1] = {k_: v for k_, v in res[0].items() if k_.startswith("LS")}
            rows[T] = row
            if i % RECHECK_EVERY == 0:
                e2 = fit_zcapm(Y, x, s, codes=codes, tol=S.EM_TOL, maxit=RECHECK_MAXIT, starts=S.EM_STARTS,
                               min_obs=S.MIN_OBS)
                nc = ~e["converged"].astype(bool)
                recheck[T] = {"N": len(codes), "not_converged_at_500": int(nc.sum()),
                              f"not_converged_at_{RECHECK_MAXIT}": int((~e2["converged"]).sum()),
                              "rank_corr_zstar_500_vs_more": e["zstar"].corr(e2["zstar"], method="spearman"),
                              "max_abs_zstar_change": (e["zstar"] - e2["zstar"]).abs().max(),
                              "max_abs_zstar_change_unconverged": (e["zstar"] - e2["zstar"])[nc].abs().max()}
            if (i + 1) % 24 == 0 or i + 1 == len(months):
                log(STEP, f"{i + 1}/{len(months)} windows")

    OUT.mkdir(parents=True, exist_ok=True)
    pd.concat(port, ignore_index=True).to_csv(OUT / "a03_matlab_port_estimates.csv.gz", index=False)
    t = pd.DataFrame(rows).T
    write(t, "a03_em_by_window", STEP)
    big = t[t["N"] >= 24]
    summ = pd.DataFrame({"all windows": t.mean(), "min": t.min(), "windows N>=24 (mean)": big.mean(),
                         "N>=24 (min)": big.min()})
    show(STEP, f"port vs repo over {len(t)} windows ({len(big)} with N >= 24)", summ.round(4))
    write(summ, "a03_em_summary", STEP)

    lp, lr = pd.DataFrame(ls_port).T.sort_index(), pd.DataFrame(ls_repo).T.sort_index()
    cmp = pd.DataFrame({"repo_mean_%": 100 * lr.mean(), "port_mean_%": 100 * lp.mean(),
                        "corr_monthly": lr.corrwith(lp), "max_abs_diff_%": 100 * (lr - lp).abs().max()})
    show(STEP, f"L/S returns formed on repo Z* vs MATLAB-port Z* ({len(lr)} months)", cmp.round(3))
    write(cmp, "a03_ls_repo_vs_port", STEP)

    rc = pd.DataFrame(recheck).T
    show(STEP, f"repo EM refitted with maxit {RECHECK_MAXIT} on every {RECHECK_EVERY}th window", rc.round(4))
    write(rc, "a03_convergence_recheck", STEP)


if __name__ == "__main__":
    main()
