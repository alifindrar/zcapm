"""Vectorised EM estimation of the empirical ZCAPM (Eq. 9.2-9.4).

    y_t = beta * x_t + Z * D_t * s_t + u_t,   D_t = +1 (prob p) / -1 (prob 1-p),  u_t ~ N(0, sigma2)

y = stock excess return, x = market excess return, s = return dispersion (RD).
All stocks in a window are estimated at once: Y is T x N with NaN for missing days.
"""
import numpy as np
import pandas as pd

_LOG2PI = np.log(2 * np.pi)


def _em_from_start(Y0, Mf, n, X, Sg, Sxx, Sss, Sxy, p0, b0, z0, s20, tol, maxit):
    N = Y0.shape[1]
    b, z, s2 = b0.copy(), z0.copy(), s20.copy()
    p = np.full(N, p0)
    ll = np.full(N, -np.inf)
    conv = np.zeros(N, bool)
    act = np.arange(N)
    for _ in range(maxit):
        y, m = Y0[:, act], Mf[:, act]
        # E-step: posterior probability that D_t = +1
        R = y - b[act] * X
        zs = z[act] * Sg
        v = s2[act]
        c = -0.5 * (_LOG2PI + np.log(v))
        l1 = np.log(p[act]) + c - (R - zs) ** 2 / (2 * v)
        l0 = np.log1p(-p[act]) + c - (R + zs) ** 2 / (2 * v)
        mx = np.maximum(l1, l0)
        lse = mx + np.log(np.exp(l1 - mx) + np.exp(l0 - mx))
        tau = np.exp(l1 - lse) * m
        ll_new = (lse * m).sum(0)
        d = 2 * tau - m                      # E[D_t] on observed days, 0 on missing days
        # M-step
        nn = n[act]
        p_new = np.clip(tau.sum(0) / nn, 1e-6, 1 - 1e-6)
        a12 = (X * Sg * d).sum(0)
        r2 = (Sg * y * d).sum(0)
        det = Sxx[act] * Sss[act] - a12 ** 2
        b_new = (Sxy[act] * Sss[act] - a12 * r2) / det
        z_new = (Sxx[act] * r2 - a12 * Sxy[act]) / det
        R = y - b_new * X
        zs = z_new * Sg
        s2_new = np.maximum((tau * (R - zs) ** 2 + (m - tau) * (R + zs) ** 2).sum(0) / nn, 1e-12)
        bad = ~(np.isfinite(b_new) & np.isfinite(z_new) & np.isfinite(ll_new))
        done = (np.abs(ll_new - ll[act]) < tol * (1 + np.abs(ll_new))) | bad
        b[act], z[act], p[act], s2[act], ll[act] = b_new, z_new, p_new, s2_new, ll_new
        conv[act[done & ~bad]] = True
        ll[act[bad]] = -np.inf
        act = act[~done]
        if act.size == 0:
            break
    return b, z, p, s2, ll, conv


def fit_zcapm(Y, x, s, codes=None, tol=1e-8, maxit=500, starts=(0.25, 0.5, 0.75), min_obs=30):
    """Estimate the empirical ZCAPM for every column of Y. Returns one row per stock."""
    Y = np.asarray(Y, float)
    x = np.asarray(x, float)
    s = np.asarray(s, float)
    M = np.isfinite(Y) & np.isfinite(x)[:, None] & np.isfinite(s)[:, None]
    Mf = M.astype(float)
    Y0 = np.where(M, Y, 0.0)
    X = np.nan_to_num(x)[:, None]
    Sg = np.nan_to_num(s)[:, None]
    n = Mf.sum(0)
    ok = n >= min_obs
    n1 = np.maximum(n, 1)

    Sxx = (Mf * X ** 2).sum(0)
    Sss = (Mf * Sg ** 2).sum(0)
    Sxy = (X * Y0).sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        b0 = Sxy / Sxx
        rb = (Y0 - b0 * X) * Mf
        vr = (rb ** 2).sum(0) / n1
        z0 = 0.5 * np.sqrt(vr) / ((Mf * Sg).sum(0) / n1)
    s20 = np.maximum(0.75 * vr, 1e-12)
    b0, z0 = np.nan_to_num(b0), np.nan_to_num(z0, nan=0.1)

    best = None
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        for p0 in starts:
            res = _em_from_start(Y0, Mf, n1, X, Sg, Sxx, Sss, Sxy, p0, b0, z0, s20, tol, maxit)
            if best is None:
                best = [r.copy() for r in res]
            else:
                better = res[4] > best[4]
                for k in range(6):
                    best[k][better] = res[k][better]
    b, z, p, s2, ll, conv = best

    # identification: Z >= 0 (sign carried by p)
    flip = z < 0
    z = np.where(flip, -z, z)
    p = np.where(flip, 1 - p, p)
    zstar = z * (2 * p - 1)

    e = (Y0 - b * X - zstar * Sg) * Mf
    e_mean = e.sum(0) / n1
    resid_var = (((e - e_mean) * Mf) ** 2).sum(0) / np.maximum(n - 1, 1)
    y_mean = Y0.sum(0) / n1
    sd = np.sqrt((((Y0 - y_mean) * Mf) ** 2).sum(0) / np.maximum(n - 1, 1))

    out = pd.DataFrame({"beta": b, "Z": z, "p": p, "zstar": zstar, "sigma2": s2,
                        "resid_var": resid_var, "sd_daily": sd, "n_obs": n.astype(int),
                        "loglik": ll, "converged": conv},
                       index=pd.Index(codes if codes is not None else range(Y.shape[1]), name="code"))
    out.loc[~ok, ["beta", "Z", "p", "zstar", "sigma2", "resid_var", "loglik"]] = np.nan
    out.loc[~ok, "converged"] = False
    return out
