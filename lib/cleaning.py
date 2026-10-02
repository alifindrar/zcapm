"""Screen of daily returns beyond the IDX auto-rejection band (audit F4).

A daily move larger than the widest regular band needs an explanation. Outside the first rows of a code there is
none in the data, so the return is removed, in both directions, and logged with a class for review:

    spike      the price returns to the pre-move level within a few rows: every return of the round trip is dropped
    split      the move matches a split ratio (unadjusted corporate action): the one return is dropped
    other      anything else: the one return is dropped
"""
import numpy as np
import pandas as pd

SPLIT_K = np.array([2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 25, 30, 40, 50, 100, 200, 500, 1000], dtype=float)
SPLIT_TOL = 0.10


def split_like(q, tol=SPLIT_TOL):
    """True when the price ratio q is within `tol` of 1/k or k for a common split ratio k."""
    return bool(min(np.abs(q * SPLIT_K - 1).min(), np.abs(q / SPLIT_K - 1).min()) <= tol)


def screen_returns(r, close, prev, limit, listing_rows, revert_rows, revert_band):
    """Returns (cleaned returns, log of removed returns). `r`, `close`, `prev` are wide date x code frames."""
    obs_no = close.notna().cumsum()
    extreme = (r.abs() > limit) & (obs_no > listing_rows)
    drop = np.zeros(r.shape, bool)
    rows = []
    R, C, P = r.to_numpy(), close.to_numpy(), prev.to_numpy()
    for j in np.flatnonzero(extreme.to_numpy().any(axis=0)):
        valid = np.flatnonzero(np.isfinite(C[:, j]))        # rows of this code
        pos = {t: i for i, t in enumerate(valid)}
        for t in np.flatnonzero(extreme.iloc[:, j].to_numpy()):
            if drop[t, j]:
                continue                                    # already removed as part of an earlier round trip
            i, base, cls, last = pos[t], P[t, j], None, t
            for k in range(1, revert_rows + 1):
                if i + k < len(valid) and abs(C[valid[i + k], j] / base - 1) <= revert_band:
                    cls, last = "spike", valid[i + k]
                    break
            if cls is None:
                cls = "split" if split_like(1 + R[t, j]) else "other"
            for u in valid[i:pos[last] + 1]:
                if np.isfinite(R[u, j]):
                    rows.append((r.index[u], r.columns[j], R[u, j], cls, r.index[t]))
                drop[u, j] = True
    log = pd.DataFrame(rows, columns=["date", "code", "r", "class", "trigger_date"])
    return r.mask(drop), log.sort_values(["date", "code"]).reset_index(drop=True)
