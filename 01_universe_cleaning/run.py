"""Step 01 - universe, daily/monthly returns, market cap and month-end eligibility."""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.cleaning import screen_returns  # noqa: E402
from lib.io import compound_monthly, log, month_ends, save, window_mask  # noqa: E402

STEP = "01"


def delisting_returns(codes, last_date, data_end):
    """Return applied in the month a stock stops trading, per code (audit F6/F11).

    A code that stops trading and is on the delisting list gets DELIST_RETURN, or DELIST_RETURN_VOLUNTARY when the
    reason is a voluntary delisting or a merger. A code that stops trading without being on the list gets no
    delisting return: in this data that is a gap in the price feed, not a delisting. Both cases are logged.
    """
    dl = pd.read_csv(S.RAW / "delistings.csv", parse_dates=["delisting_date"])
    dl = dl.assign(reason="", note="") if "reason" not in dl else dl
    if S.DELIST_EXTRA_FILE.exists():
        extra = pd.read_csv(S.DELIST_EXTRA_FILE, parse_dates=["delisting_date"], comment="#")
        dl = pd.concat([dl, extra], ignore_index=True)
    dl["reason"] = dl["reason"].fillna("").str.strip().str.lower()
    # later rows win; a row without a date (reason-only override) keeps the date of an earlier row
    dl = dl.groupby("code").agg(delisting_date=("delisting_date", "last"), reason=("reason", "last"))
    stopped = last_date < data_end - pd.Timedelta(days=10)
    t = pd.DataFrame({"last_price_date": last_date, "stopped": stopped}).join(dl, how="outer")
    t["in_price_data"] = t.index.isin(codes)
    t["stopped"] = t["stopped"].fillna(False).astype(bool)
    t["on_list"] = t["delisting_date"].notna() | t["reason"].fillna("").ne("")
    t["delist_return"] = 0.0
    held = t["stopped"] & t["on_list"]
    t.loc[held, "delist_return"] = np.where(t.loc[held, "reason"].isin(S.VOLUNTARY_REASONS),
                                            S.DELIST_RETURN_VOLUNTARY, S.DELIST_RETURN)
    t["status"] = np.select(
        [held, t["stopped"], t["on_list"] & ~t["in_price_data"], t["on_list"]],
        ["delisted", "stops trading, not on the delisting list (no delisting return)",
         "on the delisting list, no price data (survivorship gap)", "on the delisting list, still trading"], "")
    t.index.name = "code"
    return t[t["status"] != ""].sort_values(["status", "last_price_date"])


def suspension_returns(close, vol, last_date, data_end, reason):
    """Month x code return for a holder of a stock with no trade in the month (suspension or delisting).

    The holder cannot sell, so the month carries the move from the last traded close before the month to the first
    traded close after it (price only). A stock that never trades again and has stopped in the data gets
    DELIST_RETURN_VOLUNTARY for a voluntary delisting or merger, else DELIST_RETURN (forced or unexplained stop).
    NaN where the stock traded in the month, before its first trade, or when it is still untraded at the data end."""
    tc = close.where((vol > 0) & (close > 0))
    key = tc.index.to_period("M")
    traded_m = tc.notna().groupby(key).any()
    prior = tc.ffill().groupby(key).last().shift(1)
    nxt = tc.bfill().groupby(key).first().shift(-1)
    stopped = last_date.reindex(close.columns) < data_end - pd.Timedelta(days=10)
    dr = pd.Series(S.DELIST_RETURN, index=close.columns)
    dr[reason.reindex(close.columns).isin(S.VOLUNTARY_REASONS)] = S.DELIST_RETURN_VOLUNTARY
    gone = nxt.isna() & stopped.to_numpy()[None, :]
    dr_wide = pd.DataFrame(np.broadcast_to(dr.to_numpy(), nxt.shape), index=nxt.index, columns=nxt.columns)
    return (nxt / prior - 1).mask(gone, dr_wide).where(~traded_m & prior.notna())


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
            for c in ["close", "previous", "volume", "listed_shares", "price_scale"] if c in raw}
    close, prev, vol = wide["close"], wide["previous"], wide["volume"]
    dates = close.index
    logrows = []
    S.INTERIM.mkdir(parents=True, exist_ok=True)

    # daily return: IDX adjusts `previous` for splits/rights on ex-date
    r = (close / prev - 1).where((close > 0) & (prev > 0))
    mismatch = ((prev - close.shift(1)).abs() / close.shift(1) > 0.005) & close.shift(1).notna() & prev.notna()
    logrows.append(("previous != lagged close", int(mismatch.sum().sum())))

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

    # moves beyond the auto-rejection band, outside listing days: removed in both directions and logged
    lim = S.RET_LIMIT + S.RET_TOL
    r, flagged = screen_returns(r, close, prev, lim, S.RET_LISTING_ROWS, S.RET_REVERT_ROWS, S.RET_REVERT_BAND,
                                S.RET_LEVEL_ROWS)
    flagged.to_csv(S.INTERIM / "returns_flagged.csv", index=False)
    for cls, n in flagged["class"].value_counts().items():
        logrows.append((f"|r| > {lim:.0%} screen, class '{cls}' set to NaN", int(n)))

    traded = (vol > 0) & r.notna()
    shares = wide["listed_shares"].ffill()
    mcap = close * shares
    last_date = close.apply(lambda c: c.last_valid_index())

    # share-count jumps are not repaired (the true basis is unknown without event data): listed for review
    sh_ratio = wide["listed_shares"] / wide["listed_shares"].ffill().shift(1)
    jumps = sh_ratio.where((sh_ratio > 1.5) | (sh_ratio < 1 / 1.5)).stack().dropna().rename("share_ratio").reset_index()
    jumps.to_csv(S.INTERIM / "share_jumps.csv", index=False)
    logrows.append(("share-count jumps beyond 1.5x (listed in share_jumps.csv, not changed)", len(jumps)))
    w = mcap.shift(1).where(r.notna() & (mcap.shift(1) > 0))
    w = w.div(w.sum(axis=1), axis=0)
    thick = w.notna().sum(axis=1) >= 100     # thin early dates (14-35 returns) put one stock above 25% by construction
    logrows.append(("days with one stock above 25% of the cap-weighted index (dates with >= 100 returns)",
                    int((w.max(axis=1) > 0.25)[thick].sum())))

    delist = delisting_returns(close.columns, last_date, dates[-1])
    delist.to_csv(S.INTERIM / "delistings_status.csv")
    for status, n in delist["status"].value_counts().items():
        logrows.append((f"delistings: {status}", int(n)))
    delist_return = delist["delist_return"].reindex(close.columns).fillna(0.0)
    susp = suspension_returns(close, vol, last_date, dates[-1], delist["reason"].fillna(""))

    # month-end eligibility
    mes = month_ends(dates)
    # price floor on the nominal price where the raw file carries the adjustment factor (dbv2), else adjusted close
    nominal = close / wide["price_scale"].where(wide["price_scale"] > 0) if "price_scale" in wide else None
    close_ff = (close if nominal is None else nominal.fillna(close)).ffill(limit=5)
    mcap_ff = mcap.ffill(limit=S.SIZE_FFILL_DAYS)        # a stock that did not trade on the year-end date
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
        ok &= (vol.loc[:T].tail(S.BUY_TRADE_ROWS) > 0).any()   # a suspended stock cannot be bought at T
        ye = year_ends[year_ends <= T]
        if len(ye):
            mc = mcap_ff.loc[ye[-1]]
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
    held = elig.set_axis(elig.index.to_period("M") + 1).reindex(susp.index).fillna(False).astype(bool)
    s_held = susp.where(held).stack().dropna()
    logrows.append(("eligible at formation, no trade in the holding month (suspension return applied)",
                    f"{len(s_held)} (mean {s_held.mean():+.1%}, at delisting return {int(s_held.eq(S.DELIST_RETURN).sum())})"
                    if len(s_held) else "0"))

    save(r, S.INTERIM / "returns_daily.pkl")
    save(traded, S.INTERIM / "traded_daily.pkl")
    save(mcap, S.INTERIM / "mcap_daily.pkl")
    save(compound_monthly(r), S.INTERIM / "returns_monthly.pkl")
    save(last_date, S.INTERIM / "last_date.pkl")
    save(delist_return, S.INTERIM / "delist_return.pkl")
    save(susp, S.INTERIM / "susp_monthly.pkl")
    save(elig, S.INTERIM / "eligible_monthly.pkl")
    pd.DataFrame(logrows, columns=["item", "value"]).to_csv(S.INTERIM / "cleaning_log.csv", index=False)
    for item, v in logrows:
        log(STEP, f"{item}: {v}")
    log(STEP, f"returns {r.shape[0]} days x {r.shape[1]} stocks")


if __name__ == "__main__":
    main()
