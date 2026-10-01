"""Simulation check: does the EM estimator recover known (beta, Z, p, Z*)?

    python 03_zcapm_estimation/test_em.py
"""
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.em import fit_zcapm  # noqa: E402


def main():
    rng = np.random.default_rng(0)
    T, N = 242, 400
    x = rng.normal(0.0003, 0.01, T)
    s = 0.018 * np.exp(rng.normal(0, 0.3, T))
    beta = rng.normal(1, 0.3, N)
    Z = rng.uniform(0.3, 1.5, N)
    p = rng.uniform(0.1, 0.9, N)
    D = np.where(rng.random((T, N)) < p, 1.0, -1.0)
    Y = beta * x[:, None] + Z * D * s[:, None] + rng.normal(0, 0.01, (T, N))
    Y[rng.random((T, N)) < 0.05] = np.nan            # missing days

    est = fit_zcapm(Y, x, s)
    zstar = Z * (2 * p - 1)
    checks = {
        "corr(beta)": np.corrcoef(beta, est.beta)[0, 1],
        "corr(Z)": np.corrcoef(Z, est.Z)[0, 1],
        "corr(p)": np.corrcoef(p, est.p)[0, 1],
        "corr(Z*)": np.corrcoef(zstar, est.zstar)[0, 1],
        "rank corr(Z*)": spearmanr(zstar, est.zstar).statistic,
        "converged share": est.converged.mean(),
    }
    for k, v in checks.items():
        print(f"{k:>16}: {v:.3f}")
    assert checks["rank corr(Z*)"] > 0.9, "Z* ranking not recovered"
    assert checks["corr(beta)"] > 0.9, "beta not recovered"
    print("OK - EM recovers simulated parameters")


if __name__ == "__main__":
    main()
