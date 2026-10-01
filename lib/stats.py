"""Performance statistics: summary/Sharpe, GRS test, Newey-West t, ex-post beta."""
import numpy as np
import pandas as pd
from scipy import stats


def ols_hac(y, X, lags):
    """OLS with Newey-West (Bartlett) covariance and n/(n-k) small-sample correction
    (same as statsmodels OLS(...).fit(cov_type='HAC') defaults). Returns (params, tvalues)."""
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    g = X * (y - X @ b)[:, None]
    S = g.T @ g
    for j in range(1, lags + 1):
        G = g[j:].T @ g[:-j]
        S += (1 - j / (lags + 1)) * (G + G.T)
    V = XtX_inv @ S @ XtX_inv * n / (n - k)
    return b, b / np.sqrt(np.diag(V))


def summary(r, rf=None):
    """Mean, SD and Sharpe (in % for mean/SD). Sharpe = mean(r - rf)/SD(r); no rf for zero-investment."""
    r = r.dropna()
    ex = r - rf.reindex(r.index) if rf is not None else r
    return pd.Series({"mean_%": 100 * r.mean(), "sd_%": 100 * r.std(), "sharpe": ex.mean() / r.std(), "T": len(r)})


def grs(assets, factors):
    """Gibbons-Ross-Shanken (1989) test that all alphas are zero. assets: T x N excess returns, factors: T x L."""
    df = pd.concat([assets, factors], axis=1).dropna()
    A = df[assets.columns].to_numpy()
    F = df[factors.columns].to_numpy()
    T, N = A.shape
    L = F.shape[1]
    if T <= N + L + 1:
        return pd.Series({"GRS": np.nan, "p_value": np.nan, "T": T, "N": N, "L": L})
    X = np.column_stack([np.ones(T), F])
    coef, *_ = np.linalg.lstsq(X, A, rcond=None)
    alpha = coef[0]
    resid = A - X @ coef
    Sigma = resid.T @ resid / (T - L - 1)
    mu = F.mean(0)
    Omega = np.atleast_2d(np.cov(F, rowvar=False))
    stat = (T / N) * ((T - N - L) / (T - L - 1)) * (alpha @ np.linalg.solve(Sigma, alpha)) / \
        (1 + mu @ np.linalg.solve(Omega, mu))
    return pd.Series({"GRS": stat, "p_value": 1 - stats.f.cdf(stat, N, T - N - L), "T": T, "N": N, "L": L,
                      "mean_abs_alpha_%": 100 * np.abs(alpha).mean()})


def nw_mean(r, lags):
    """Mean with Newey-West t-statistic."""
    r = r.dropna()
    b, t = ols_hac(r.to_numpy(), np.ones((len(r), 1)), lags)
    return pd.Series({"mean_%": 100 * b[0], "t_nw": t[0]})


def ex_post_beta(r, mkt_ex, lags):
    """CAPM beta of r on market excess return, with Newey-West t."""
    df = pd.concat([r, mkt_ex], axis=1).dropna()
    X = np.column_stack([np.ones(len(df)), df.iloc[:, 1].to_numpy()])
    b, t = ols_hac(df.iloc[:, 0].to_numpy(), X, lags)
    return pd.Series({"alpha_%": 100 * b[0], "t_alpha": t[0], "beta": b[1], "t_beta": t[1]})
