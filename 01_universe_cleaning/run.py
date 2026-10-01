"""Step 01 - universe, daily/monthly returns, market cap and month-end eligibility."""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import compound_monthly, log, month_ends, save, window_mask  # noqa: E402

STEP = "01"


def load_raw():
    raw = pd.read_csv(S.RAW / "stock_daily.csv.gz", parse_dates=["date"], dtype={"code": str, "remarks": str})
    raw = raw[raw["date"] >= pd.Timestamp(S.START_DATE)]
    if S.END_DATE:
        raw = raw[raw["date"] <= pd.Timestamp(S.END_DATE)]
    keep = raw["code"].str.match(S.CODE_REGEX) & ~raw["code"].str.startswith(S.EXCLUDE_PREFIXES)
    log(STEP, f"raw {len(raw):,} rows; dropped {(~keep).sum():,} non-common-stock rows "
              f"({raw.loc[~keep, 'code'].nunique()} codes)")
    return raw[keep]


def main():
    raw = load_raw()
    wide = {c: raw.pivot(index="date", columns="code", values=c)
            for c in ["close", "previous", "volume", "listed_shares"]}
    close, prev, vol = wide["close"], wide["previous"], wide["volume"]
    dates = close.index
    logrows = []

    # daily return: IDX adjusts `previous` for splits/rights on ex-date
    r = (close / prev - 1).where((close > 0) & (prev > 0))
    mismatch = ((prev - close.shift(1)).abs() / close.shift(1) > 0.005) & close.shift(1).notna() & prev.notna()
    logrows.append(("previous != lagged close (corporate-action adjustments)", int(mismatch.sum().sum())))

    # cash dividends on ex-date (next trading day if ex-date is a holiday)
    div = pd.read_csv(S.RAW / "dividends.csv", parse_dates=["ex_date"])
    added = 0
    for code, ex, dps in div[["code", "ex_date", "cash_dividend"]].itertuples(index=False):
        if code not in r.columns or pd.isna(ex) or ex > dates[-1] or ex < dates[0]:
            continue
        d = dates[dates.searchsorted(ex)]
        if pd.notna(r.at[d, code]) and prev.at[d, code] > 0:
            r.at[d, code] += dps / prev.at[d, code]
            added += 1
    logrows.append(("dividends added to returns", added))

    outlier = r.abs() > S.MAX_ABS_DAILY_RET
    logrows.append((f"|r| > {S.MAX_ABS_DAILY_RET:.0%} set to NaN", int(outlier.sum().sum())))
    r = r.mask(outlier)

    traded = (vol > 0) & r.notna()
    shares = wide["listed_shares"].ffill()
    mcap = close * shares
    last_date = close.apply(lambda c: c.last_valid_index())

    # month-end eligibility
    mes = month_ends(dates)
    close_ff = close.ffill(limit=5)
    remarks = raw.pivot(index="date", columns="code", values="remarks") if S.EXCLUDE_REMARK_REGEX else None
    year_ends = mes[mes.month == 12]
    elig = pd.DataFrame(False, index=mes, columns=close.columns)
    for T in mes:
        if dates[0] > (T.to_period("M") - (S.WINDOW_MONTHS - 1)).start_time:
            continue  # not enough history for a full window
        win = window_mask(dates, T, S.WINDOW_MONTHS)
        tr, rr = traded[win], r[win]
        n_valid = tr.sum()
        zero_frac = ((rr == 0) & tr).sum() / n_valid.clip(lower=1)
        ok = (n_valid >= S.MIN_OBS) & (zero_frac <= S.MAX_ZERO_FRAC)
        ok &= close_ff.loc[T] > S.MIN_PRICE
        ye = year_ends[year_ends <= T]
        if len(ye):
            mc = mcap.loc[ye[-1]]
            ok &= ~(mc < mc.quantile(S.SIZE_CUT))
        if remarks is not None:
            rem = remarks.loc[:T].ffill().iloc[-1].fillna("")
            ok &= ~rem.str.contains(S.EXCLUDE_REMARK_REGEX, flags=re.I, regex=True)
        elig.loc[T] = ok.fillna(False)
    n_elig = elig.sum(axis=1)
    n_elig = n_elig[n_elig > 0]
    logrows.append(("formation months with eligible stocks", len(n_elig)))
    logrows.append(("eligible stocks per month (min/median/max)",
                    f"{n_elig.min()}/{int(n_elig.median())}/{n_elig.max()}" if len(n_elig) else "0"))

    save(r, S.INTERIM / "returns_daily.pkl")
    save(traded, S.INTERIM / "traded_daily.pkl")
    save(mcap, S.INTERIM / "mcap_daily.pkl")
    save(compound_monthly(r), S.INTERIM / "returns_monthly.pkl")
    save(last_date, S.INTERIM / "last_date.pkl")
    save(elig, S.INTERIM / "eligible_monthly.pkl")
    pd.DataFrame(logrows, columns=["item", "value"]).to_csv(S.INTERIM / "cleaning_log.csv", index=False)
    for item, v in logrows:
        log(STEP, f"{item}: {v}")
    log(STEP, f"returns {r.shape[0]} days x {r.shape[1]} stocks")


if __name__ == "__main__":
    main()
