"""Portfolio construction shared by step 04 (zeta sorts) and step 07 (factor-beta sorts)."""
import numpy as np
import pandas as pd

SCHEMES = {
    # tails: nested top/bottom fractions; then n_slices consecutive slices of `width` from each end
    "book24": dict(tails=(0.01, 0.02), width=0.05, n_slices=10),
    "deciles": dict(tails=(), width=0.10, n_slices=5),
    "quintiles": dict(tails=(), width=0.20, n_slices=2),
}


def n_ls(scheme):
    spec = SCHEMES[scheme]
    return len(spec["tails"]) + spec["n_slices"]


def ls_labels(scheme):
    spec = SCHEMES[scheme]
    labels = [f"Top +{t:.0%}/-{t:.0%}" for t in spec["tails"]]
    w = spec["width"]
    labels += [f"slice {j * w:.0%}-{(j + 1) * w:.0%}" for j in range(spec["n_slices"])]
    return labels


def long_only_order(K):
    """Long-only portfolios numbered from lowest to highest Z*: S1..SK, LK..L1 (book Tables 9.4/9.5)."""
    return [f"S{k}" for k in range(1, K + 1)] + [f"L{k}" for k in range(K, 0, -1)]


def leg_members(score, scheme):
    """Split stocks ranked on `score` (descending) into long legs L1..LK and short legs S1..SK."""
    spec = SCHEMES[scheme]
    score = score.dropna()
    N = len(score)
    desc = score.sort_values(ascending=False, kind="mergesort").index
    asc = desc[::-1]
    legs, k = {}, 0
    for t in spec["tails"]:
        k += 1
        m = max(1, int(round(t * N)))
        legs[f"L{k}"], legs[f"S{k}"] = desc[:m], asc[:m]
    w = spec["width"]
    for j in range(spec["n_slices"]):
        k += 1
        lo = int(round(j * w * N))
        hi = max(lo + 1, int(round((j + 1) * w * N)))
        legs[f"L{k}"], legs[f"S{k}"] = desc[lo:hi], asc[lo:hi]
    return legs


def cap_weights(w, cap):
    if cap is None or cap * len(w) < 1:
        return w
    w = w.copy()
    for _ in range(100):
        over = w > cap + 1e-12
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        rest = ~over & (w < cap)
        w[rest] += excess * w[rest] / w[rest].sum()
    return w


def g_weights(est, mkt_sd, vol_ratio, offset, cap, zscale=1.0):
    """Proxy minimum-variance portfolio g: w ~ 1/(offset+|Z*|) * 1/var(u), low-vol stocks removed.
    `zscale` puts Z* on the scale the offset is defined for (the book: monthly, daily Z* x 21)."""
    e = est.dropna(subset=["zstar", "resid_var"])
    e = e[(e["sd_daily"] >= vol_ratio * mkt_sd) & (e["resid_var"] > 0)]
    w = 1.0 / (offset + zscale * e["zstar"].abs()) / e["resid_var"]
    return cap_weights(w / w.sum(), cap)


def holding_returns(codes, month, returns_monthly, last_date, data_end, delist_return):
    """Month-`month` returns for `codes`, with a delisting return for stocks that stop trading.
    `delist_return`: Series code -> return (step 01 `delist_return.pkl`; 0 when none applies) or one number."""
    base = returns_monthly.loc[month].reindex(codes) if month in returns_monthly.index \
        else pd.Series(np.nan, index=codes)
    ld = last_date.reindex(codes)
    delisted = (ld <= month.end_time) & (ld < data_end - pd.Timedelta(days=10))
    if isinstance(delist_return, pd.Series):
        delist_return = delist_return.reindex(codes).fillna(0.0).to_numpy()
    return (1 + base.fillna(0)) * (1 + np.where(delisted, delist_return, 0.0)) - 1


def turnover_cost(W, buy, sell):
    """Monthly cost and one-way turnover of target weights W (formation date x code).
    Rebalancing sells and buys the same amount; the first month is a purchase of the whole portfolio."""
    turnover = 0.5 * W.sort_index().diff().abs().sum(axis=1)
    cost = turnover * (buy + sell)
    turnover.iloc[0], cost.iloc[0] = 1.0, buy
    return cost, turnover


def form_ls(score, month_ret, scheme, min_leg=None):
    """Equal-weighted leg returns, L/S returns, avg score and counts for one formation date.
    Returns None when there are too few scored stocks to fill every leg (with `min_leg` stocks each, if given)."""
    score = score.dropna()
    if len(score) < 2 * n_ls(scheme):
        return None
    legs = leg_members(score, scheme)
    if min_leg and min(len(c) for c in legs.values()) < min_leg:
        return None
    K = n_ls(scheme)
    ret, avg, cnt, hold = {}, {}, {}, {}
    for name, codes in legs.items():
        ret[name] = month_ret.reindex(codes).mean()
        avg[name] = score.reindex(codes).mean()
        cnt[name] = len(codes)
        hold[name] = pd.Series(1.0 / len(codes), index=codes)
    for k in range(1, K + 1):
        ret[f"LS{k}"] = ret[f"L{k}"] - ret[f"S{k}"]
        avg[f"LS{k}"] = avg[f"L{k}"] - avg[f"S{k}"]
    for j, name in enumerate(long_only_order(K), start=1):
        ret[f"LO{j}"] = ret[name]
        avg[f"LO{j}"] = avg[name]
    return ret, avg, cnt, hold
