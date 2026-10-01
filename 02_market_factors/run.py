"""Step 02 - market return R_a, return dispersion sigma_a (Eq. 9.5), R_f, IHSG, local SMB/HML/MOM."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.factors import factor_from_ports, port_returns, sort_2x3  # noqa: E402
from lib.io import compound_monthly, load, log, month_ends, save  # noqa: E402

STEP = "02"


def market_and_rd(r, mcap):
    """Cap-weighted return with lagged weights and cross-sectional dispersion (Eq. 9.5)."""
    w = mcap.shift(1).where(r.notna() & (mcap.shift(1) > 0))
    w = w.div(w.sum(axis=1), axis=0)
    Ra = (w * r).sum(axis=1, min_count=1)
    n = w.notna().sum(axis=1)
    dev2 = (w * r.sub(Ra, axis=0) ** 2).sum(axis=1, min_count=1)
    sigma = np.sqrt(n / (n - 1) * dev2).where(n > 1)
    return Ra, sigma


def risk_free(dates):
    if S.RF_FILE.exists():
        rf = pd.read_csv(S.RF_FILE, parse_dates=["date"]).set_index("date")["rate_annual_pct"].sort_index()
        rate = rf.reindex(rf.index.union(dates)).ffill()
        if rate.loc[dates].isna().any():
            log(STEP, "WARNING: rf.csv starts after the sample - back-filling the first rate")
            rate = rate.bfill()
        rate = rate.loc[dates]
    elif S.RF_FALLBACK_ANNUAL_PCT is not None:
        log(STEP, f"WARNING: {S.RF_FILE} missing - using constant {S.RF_FALLBACK_ANNUAL_PCT}% p.a.")
        rate = pd.Series(S.RF_FALLBACK_ANNUAL_PCT, index=dates)
    else:
        sys.exit(f"{S.RF_FILE} missing (columns: date, rate_annual_pct) - or set RF_FALLBACK_ANNUAL_PCT")
    known = rate.shift(1).bfill() / 100            # rate known at the start of each day
    rf_d = (1 + known) ** (1 / S.TRADING_DAYS) - 1
    month_start_rate = known.groupby(dates.to_period("M")).first()
    rf_m = (1 + month_start_rate) ** (1 / 12) - 1   # rate known at the start of each month
    return rf_d, rf_m


def local_factors(r, mcap, rm, elig):
    """Monthly-rebalanced 2x3 VW factors; daily series (for betas) and monthly series (for tables/GRS)."""
    ratios = pd.read_csv(S.RAW / "ratios.csv", parse_dates=["date"])
    have_bm = len(ratios) > 0
    if have_bm:
        ratios = ratios[ratios["pbv"] > 0]
        ratios["avail"] = ratios["date"] + pd.DateOffset(months=S.RATIO_LAG_MONTHS)
        bm = ratios.pivot_table(index="avail", columns="code", values="pbv", aggfunc="last").rdiv(1.0)
    else:
        log(STEP, "WARNING: ratios.csv empty - HML not built")
    cri = (1 + r.fillna(0)).cumprod()
    mes = month_ends(r.index)
    daily = pd.DataFrame(np.nan, index=r.index, columns=["SMB", "HML", "MOM"])
    monthly = {}
    for i, T in enumerate(mes[:-1]):
        uni = elig.columns[elig.loc[T]] if T in elig.index else []
        if len(uni) < 12 or i < 12:
            continue
        size = mcap.loc[T, uni]
        nxt = T.to_period("M") + 1
        ddays = r.index[r.index.to_period("M") == nxt]
        dret = r.loc[ddays, uni]
        mret = rm.loc[nxt, uni] if nxt in rm.index else None
        mom = cri.loc[mes[i - 1], uni] / cri.loc[mes[i - 12], uni] - 1
        sigs = {"MOM": mom}
        if have_bm:
            b = bm[bm.index <= T]
            if len(b):
                sigs["HML"] = b.ffill().iloc[-1].reindex(uni)
        row = {}
        for name, sig in sigs.items():
            w = sort_2x3(size, sig, S.FACTOR_BREAKS)
            if not w:
                continue
            daily.loc[ddays, name] = factor_from_ports(port_returns(w, dret), "HL")
            if mret is not None:
                row[name] = factor_from_ports(port_returns(w, mret), "HL")
            if name == ("HML" if "HML" in sigs else "MOM"):   # SMB from the size x B/M sort (size x MOM fallback)
                daily.loc[ddays, "SMB"] = factor_from_ports(port_returns(w, dret), "SMB")
                if mret is not None:
                    row["SMB"] = factor_from_ports(port_returns(w, mret), "SMB")
        monthly[nxt] = row
    monthly = pd.DataFrame.from_dict(monthly, orient="index").reindex(columns=["SMB", "HML", "MOM"])
    monthly.index = pd.PeriodIndex(monthly.index, freq="M")
    return daily, monthly


def main():
    r = load(S.INTERIM / "returns_daily.pkl")
    mcap = load(S.INTERIM / "mcap_daily.pkl")
    rm = load(S.INTERIM / "returns_monthly.pkl")
    elig = load(S.INTERIM / "eligible_monthly.pkl")
    dates = r.index

    Ra, sigma = market_and_rd(r, mcap)
    rf_d, rf_m = risk_free(dates)
    idx = pd.read_csv(S.RAW / "index_daily.csv", parse_dates=["date"])
    ihsg = idx[idx["code"] == S.IHSG_CODE].set_index("date")["close"].sort_index()
    ihsg_r = ihsg.pct_change().reindex(dates)
    if ihsg.empty:
        log(STEP, f"WARNING: no {S.IHSG_CODE} rows in index_daily.csv")

    fd, fm = local_factors(r, mcap, rm, elig)
    daily = pd.DataFrame({"Ra": Ra, "sigma_a": sigma, "Rf": rf_d, "IHSG": ihsg_r}).join(fd)
    monthly = pd.DataFrame({"M_own": compound_monthly(Ra), "IHSG": compound_monthly(ihsg_r), "Rf": rf_m})
    monthly = monthly.join(fm)

    save(daily, S.INTERIM / "factors_daily.pkl")
    save(monthly, S.INTERIM / "factors_monthly.pkl")
    log(STEP, f"mean daily R_a {100 * Ra.mean():.3f}%, mean daily RD {100 * sigma.mean():.3f}% "
              f"(book US: 0.04% / 1.81%)")
    log(STEP, f"corr(own VW, IHSG) daily = {Ra.corr(ihsg_r):.3f}")
    log(STEP, f"monthly own VW mean {100 * monthly.M_own.mean():.2f}% sd {100 * monthly.M_own.std():.2f}%; "
              f"factors available: {[c for c in ['SMB', 'HML', 'MOM'] if monthly[c].notna().any()]}")


if __name__ == "__main__":
    main()
