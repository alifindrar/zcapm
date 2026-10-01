"""Step 03 - rolling 12-month EM estimation of the empirical ZCAPM for every eligible stock.

    python 03_zcapm_estimation/run.py [--last N]     # N = only the last N formation months (quick test)
"""
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.em import fit_zcapm  # noqa: E402
from lib.io import load, log, save, window_mask  # noqa: E402

STEP = "03"


def main():
    r = load(S.INTERIM / "returns_daily.pkl")
    traded = load(S.INTERIM / "traded_daily.pkl")
    elig = load(S.INTERIM / "eligible_monthly.pkl")
    f = load(S.INTERIM / "factors_daily.pkl")
    dates = r.index

    months = [T for T in elig.index[:-1] if elig.loc[T].any()]   # last month has no holding period
    if "--last" in sys.argv:
        months = months[-int(sys.argv[sys.argv.index("--last") + 1]):]
    log(STEP, f"{len(months)} formation months: {months[0]:%Y-%m} .. {months[-1]:%Y-%m}")

    out, t0 = [], time.time()
    for i, T in enumerate(months, 1):
        win = window_mask(dates, T, S.WINDOW_MONTHS)
        codes = elig.columns[elig.loc[T]]
        fw = f.loc[win]
        Y = r.loc[win, codes].where(traded.loc[win, codes]).sub(fw["Rf"], axis=0)
        est = fit_zcapm(Y.to_numpy(), (fw["Ra"] - fw["Rf"]).to_numpy(), fw["sigma_a"].to_numpy(),
                        codes=codes, tol=S.EM_TOL, maxit=S.EM_MAXIT, starts=S.EM_STARTS, min_obs=S.MIN_OBS)
        est.insert(0, "T", T)
        out.append(est.reset_index())
        if i % 12 == 0 or i == len(months):
            log(STEP, f"{i}/{len(months)} {T:%Y-%m}: {len(codes)} stocks, "
                      f"converged {est.converged.mean():.0%}, {time.time() - t0:.0f}s")

    est = pd.concat(out, ignore_index=True)
    save(est, S.INTERIM / "zcapm_estimates.pkl")
    log(STEP, f"{len(est):,} stock-month estimates; median Z* {est.zstar.median():.3f}, "
              f"IQR {est.zstar.quantile(.25):.3f}..{est.zstar.quantile(.75):.3f}; "
              f"median beta {est.beta.median():.2f}")


if __name__ == "__main__":
    main()
