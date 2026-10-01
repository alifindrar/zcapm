"""Step 00 - read the idx-api SQLite DB, clean it, and write
   (a) a local SQLite database 00_data_acquisition/idx_data.sqlite, and
   (b) the canonical CSV files in data/raw/ read by steps 01-07.

Source rows come from two feeds inside the idx-api DB:
  * idx   - idx.co.id daily summaries (2020-01-02 onward), nominal prices, remarks present
  * yahoo - backfill_2005_2019.py (yfinance), rows with id >= 10,000,000 and no remarks

Fixes applied to the yahoo rows (see qa_boundary / meta tables):
  1. Yahoo prices are adjusted for every later split/rights issue while listed_shares is the 2020
     count, so close x shares is wrong. Each code is rescaled by k = IDX `previous` on its first
     2020 day / last Yahoo close, which restores nominal prices (and dividends, volume / k).
  2. Codes with an implausible k (bad Yahoo data) lose their Yahoo history.
  3. Yahoo pads exchange holidays with stale rows: days on which no stock traded are dropped.
  4. Yahoo dividends overlapping an IDX dividend (same code, +/- 10 days) are dropped.
Fetching into the idx-api DB is done separately by sync_idx_history.ts / backfill_2005_2019.py.

Default (config DB_VERSION = "v2"): runs fetch_stockdb.py + build_dbv2.py instead (dbv2 = this v1 DB + STOCKDB).
The logic below runs only with ZCAPM_DB=v1 and rewrites idx_data.sqlite and data/raw/.
"""
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import log  # noqa: E402

STEP = "00"
OUT_DB = Path(__file__).resolve().parent / "idx_data.sqlite"
YAHOO_ID_MIN = 10_000_000
K_RANGE = (0.1, 1000.0)          # plausible boundary ratio; outside -> drop that code's yahoo rows
DIV_MATCH_DAYS = 10


def ms_to_date(col):
    """idx-api stores epoch milliseconds; convert via Jakarta time so both UTC- and WIB-midnight stamps map to the right day."""
    return pd.to_datetime(col, unit="ms", utc=True).dt.tz_convert("Asia/Jakarta").dt.tz_localize(None).dt.normalize()


def read(con, sql):
    return pd.read_sql_query(sql, con)


def load_stock(con):
    s = read(con, "select id, date, code, open, high, low, close, previous, volume, value, frequency, "
                  "listed_shares, tradable_shares, remarks from stock_summary")
    if s.empty:
        sys.exit("stock_summary is empty - run 00_data_acquisition/sync_idx_history.ts first "
                 "(or use make_synthetic.py for a plumbing test).")
    s["date"] = ms_to_date(s["date"])
    s["source"] = np.where(s.pop("id") >= YAHOO_ID_MIN, "yahoo", "idx")
    return s.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="last").reset_index(drop=True)


def boundary_scale(s):
    """k per code = first IDX `previous` / last Yahoo close (only codes present in both feeds)."""
    y = s[s.source == "yahoo"].groupby("code").last()[["date", "close"]]
    i = s[s.source == "idx"].groupby("code").first()[["date", "previous"]]
    b = y.join(i, how="inner", lsuffix="_yahoo", rsuffix="_idx")
    b["k"] = b["previous"] / b["close"]
    b["action"] = np.where(b.k.between(*K_RANGE), "rescaled", "dropped_yahoo")
    b.loc[b.action.eq("rescaled") & np.isclose(b.k, 1.0, atol=1e-6), "action"] = "unchanged"
    b = b.reset_index().rename(columns={"date_yahoo": "last_yahoo_date", "close": "last_yahoo_close",
                                        "date_idx": "first_idx_date", "previous": "first_idx_previous"})
    # yahoo-only codes (never seen on IDX from 2020) cannot be anchored
    orphans = sorted(set(s.code[s.source == "yahoo"]) - set(b.code))
    if orphans:
        b = pd.concat([b, pd.DataFrame({"code": orphans, "action": "dropped_yahoo_no_anchor"})], ignore_index=True)
    return b


def clean_stock(s, b):
    k = b.set_index("code")["k"]
    y = s.source.eq("yahoo")
    drop_codes = set(b.code[b.action.str.startswith("dropped")])
    s = s[~(y & s.code.isin(drop_codes))].copy()
    y = s.source.eq("yahoo")
    kk = s.loc[y, "code"].map(k)
    for col in ("open", "high", "low", "close", "previous"):
        s.loc[y, col] = s.loc[y, col] * kk
    s.loc[y, "volume"] = (s.loc[y, "volume"] / kk).round()
    s.loc[y, "value"] = s.loc[y, "close"] * s.loc[y, "volume"]
    s["price_scale"] = 1.0
    s.loc[y, "price_scale"] = kk

    # holiday padding: yahoo days on which (almost) nothing traded
    ydays = s[s.source == "yahoo"].groupby("date")["volume"].apply(lambda v: (v > 0).mean())
    dead = ydays.index[ydays < 0.05]
    s = s[~(s.date.isin(dead) & s.source.eq("yahoo"))]
    # `previous` needs no re-link: a padded holiday repeats the prior close, so the next row's previous is unchanged
    return s.reset_index(drop=True), pd.DatetimeIndex(dead)


def load_dividends(con, b):
    d = read(con, "select code, ex_dividend, cum_dividend, payment_date, cash_dividend from company_dividend "
                  "where ex_dividend is not null")
    d["source"] = np.where((d.cum_dividend == d.ex_dividend) & (d.ex_dividend == d.payment_date), "yahoo", "idx")
    d["ex_date"] = ms_to_date(d["ex_dividend"])
    d = d[["code", "ex_date", "cash_dividend", "source"]]
    idx, yah = d[d.source == "idx"], d[d.source == "yahoo"].copy()

    m = yah.reset_index().merge(idx, on="code", suffixes=("", "_i"))
    dup = m.loc[(m.ex_date - m.ex_date_i).abs() <= pd.Timedelta(days=DIV_MATCH_DAYS), "index"].unique()
    yah = yah.drop(index=dup)

    k = b.set_index("code")["k"]
    keep = set(b.code[~b.action.str.startswith("dropped")])
    yah = yah[yah.code.isin(keep)]
    yah["cash_dividend"] = yah["cash_dividend"] * yah["code"].map(k)
    out = pd.concat([idx, yah]).sort_values(["ex_date", "code"]).drop_duplicates(["code", "ex_date"])
    return out.reset_index(drop=True), len(dup)


def main():
    if S.DB_VERSION != "v1":
        # v2 source: STOCKDB export + v1 DB (idx_data.sqlite, read-only) -> dbv2.sqlite + data/raw_v2/
        import build_dbv2
        import fetch_stockdb
        fetch_stockdb.main()
        build_dbv2.main()
        return
    if not S.IDX_API_DB.exists():
        sys.exit(f"idx-api database not found: {S.IDX_API_DB}")
    con = sqlite3.connect(f"file:{S.IDX_API_DB.as_posix()}?mode=ro", uri=True)

    stock = load_stock(con)
    b = boundary_scale(stock)
    n0 = len(stock)
    stock, dead = clean_stock(stock, b)
    log(STEP, f"stock_daily: {len(stock):,} rows ({n0 - len(stock):,} dropped: {len(dead)} yahoo holiday days, "
              f"{b.action.str.startswith('dropped').sum()} codes without usable anchor), "
              f"{stock.code.nunique()} codes, {stock.date.min():%Y-%m-%d} .. {stock.date.max():%Y-%m-%d}")
    log(STEP, f"yahoo boundary: {b.action.value_counts().to_dict()}")

    idx = read(con, "select date, code, previous, high, low, close, volume, value from index_summary")
    idx["date"] = ms_to_date(idx["date"])
    idx = idx.sort_values(["code", "date"]).drop_duplicates(["code", "date"], keep="last")
    idx = idx[~(idx.code.eq(S.IHSG_CODE) & idx.date.isin(dead))].reset_index(drop=True)
    log(STEP, f"index_daily: {len(idx):,} rows ({(idx.code == S.IHSG_CODE).sum()} {S.IHSG_CODE})")

    div, ndup = load_dividends(con, b)
    log(STEP, f"dividends: {len(div):,} ({ndup} yahoo duplicates of IDX records dropped)")

    dl = read(con, "select code, name, listing_date, delisting_date from company_delisting")
    for c in ("listing_date", "delisting_date"):
        dl[c] = ms_to_date(dl[c])
    rat = read(con, "select code, period as date, pbv from financial_ratio")
    rat["date"] = ms_to_date(rat["date"])
    spl = read(con, "select code, type, ratio, old_nominal, new_nominal, additional_shares, listed_shares, "
                    "listing_date from stock_split")
    spl["listing_date"] = ms_to_date(spl["listing_date"])
    rig = read(con, "select code, ratio, exercise_price, recording_date, trading_period from right_offering")
    rig["recording_date"] = ms_to_date(rig["recording_date"])
    con.close()
    log(STEP, f"delistings {len(dl)}, ratios {len(rat)}, splits {len(spl)}, rights {len(rig)}")

    # ------------------------------------------------ (a) local SQLite database
    tmp = OUT_DB.with_suffix(".sqlite.tmp")
    tmp.unlink(missing_ok=True)
    out = sqlite3.connect(tmp)
    as_text = lambda df, cols: df.assign(**{c: df[c].dt.strftime("%Y-%m-%d") for c in cols})  # noqa: E731
    as_text(stock, ["date"]).to_sql("stock_daily", out, index=False, chunksize=100_000)
    as_text(idx, ["date"]).to_sql("index_daily", out, index=False)
    as_text(div, ["ex_date"]).to_sql("dividends", out, index=False)
    as_text(dl, ["listing_date", "delisting_date"]).to_sql("delistings", out, index=False)
    as_text(rat, ["date"]).to_sql("ratios", out, index=False)
    as_text(spl, ["listing_date"]).to_sql("stock_splits", out, index=False)
    as_text(rig, ["recording_date"]).to_sql("right_offerings", out, index=False)
    as_text(b, ["last_yahoo_date", "first_idx_date"]).to_sql("qa_boundary", out, index=False)
    pd.DataFrame({"date": dead.strftime("%Y-%m-%d")}).to_sql("qa_dropped_days", out, index=False)
    cov = stock.groupby([stock.date.dt.year.rename("year"), "source"]).agg(
        rows=("code", "size"), days=("date", "nunique"), codes=("code", "nunique")).reset_index()
    cov.to_sql("qa_coverage", out, index=False)
    pd.DataFrame({"key": ["built_at", "source_db", "stock_first", "stock_last", "yahoo_id_min", "k_range"],
                  "value": [time.strftime("%Y-%m-%d %H:%M:%S"), str(S.IDX_API_DB),
                            f"{stock.date.min():%Y-%m-%d}", f"{stock.date.max():%Y-%m-%d}",
                            str(YAHOO_ID_MIN), str(K_RANGE)]}).to_sql("meta", out, index=False)
    out.executescript("""
        create unique index ix_stock on stock_daily(code, date);
        create index ix_stock_date on stock_daily(date);
        create unique index ix_index on index_daily(code, date);
        create index ix_div on dividends(code, ex_date);
    """)
    out.commit()
    out.close()
    tmp.replace(OUT_DB)
    log(STEP, f"database written: {OUT_DB} ({OUT_DB.stat().st_size / 1e6:.0f} MB)")

    # ------------------------------------------------ (b) canonical CSVs for steps 01-07
    S.RAW.mkdir(parents=True, exist_ok=True)
    stock[["date", "code", "close", "previous", "volume", "value", "listed_shares", "remarks"]].to_csv(
        S.RAW / "stock_daily.csv.gz", index=False)
    idx[["date", "code", "close"]].to_csv(S.RAW / "index_daily.csv", index=False)
    div[["code", "ex_date", "cash_dividend"]].to_csv(S.RAW / "dividends.csv", index=False)
    dl[["code", "delisting_date"]].to_csv(S.RAW / "delistings.csv", index=False)
    rat.to_csv(S.RAW / "ratios.csv", index=False)
    (S.RAW / "SYNTHETIC").unlink(missing_ok=True)
    log(STEP, f"canonical CSVs written to {S.RAW}")
    if not S.RF_FILE.exists():
        log(STEP, f"WARNING: {S.RF_FILE} missing - supply risk-free rates (date, rate_annual_pct) before step 02")


if __name__ == "__main__":
    main()
