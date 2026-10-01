"""Backfill 2005-2019 historical data for IHSG and IDX stocks using Yahoo Finance (yfinance).

Since idx.co.id API endpoints only host daily trading summaries starting from 2020-01-02,
this script backfills 2005-2019 directly into idx-api SQLite database, and regenerates
the canonical CSV files via run.py, fulfilling the pipeline data acquisition down to 2005.
"""
import sqlite3
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S
from lib.io import log

STEP = "00-backfill"
START_DATE = "2005-01-01"
END_DATE = "2020-01-01"


def to_ms(dt):
    ts = pd.Timestamp(dt)
    if ts.tz is None:
        ts = ts.tz_localize("Asia/Jakarta").normalize()
    else:
        ts = ts.tz_convert("Asia/Jakarta").normalize()
    return int(ts.timestamp() * 1000)


def get_db():
    if not S.IDX_API_DB.exists():
        sys.exit(f"Database not found: {S.IDX_API_DB}")
    return sqlite3.connect(S.IDX_API_DB)


def backfill_ihsg(con):
    cur = con.cursor()
    cur.execute("SELECT count(*) FROM index_summary WHERE code='COMPOSITE' AND date < 1577836800000")
    existing = cur.fetchone()[0]
    if existing > 1000:
        log(STEP, f"IHSG already backfilled ({existing:,} rows before 2020)")
        return

    log(STEP, "Fetching ^JKSE (IHSG) from Yahoo Finance (2005-2019)...")
    ihsg = yf.Ticker("^JKSE").history(start=START_DATE, end=END_DATE, auto_adjust=False)
    if ihsg.empty:
        log(STEP, "ERROR: No ^JKSE data returned from Yahoo Finance")
        return

    rows = []
    base_id = 10000000
    prev_close = None
    for idx, (dt, row) in enumerate(ihsg.iterrows()):
        close = float(row["Close"])
        high = float(row["High"]) if pd.notna(row["High"]) else close
        low = float(row["Low"]) if pd.notna(row["Low"]) else close
        vol = int(row["Volume"]) if pd.notna(row["Volume"]) else 0
        prev = prev_close if prev_close is not None else float(row["Open"]) if pd.notna(row["Open"]) else close
        chg = close - prev
        pct = (chg / prev * 100.0) if prev > 0 else 0.0
        val = close * vol
        
        ms = to_ms(dt)

        rows.append((
            base_id + idx,
            "COMPOSITE",
            "COMPOSITE",
            ms,
            prev,
            high,
            low,
            close,
            chg,
            pct,
            vol,
            val,
            0,     # frequency
            None   # market_cap
        ))
        prev_close = close

    cur.executemany("""
        INSERT OR REPLACE INTO index_summary (
            id, code, name, date, previous, high, low, close, change, percent, volume, value, frequency, market_cap
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    con.commit()
    log(STEP, f"Backfilled {len(rows):,} rows for COMPOSITE (IHSG) from {rows[0][3]} to {rows[-1][3]}")


def get_shares_and_splits(con, codes):
    cur = con.cursor()
    # Earliest listed shares per code in 2020
    cur.execute("""
        SELECT code, listed_shares
        FROM stock_summary
        WHERE date = (SELECT min(date) FROM stock_summary)
    """)
    base_shares = dict(cur.fetchall())
    # Fallback to overall earliest listed_shares
    cur.execute("""
        SELECT code, listed_shares
        FROM stock_summary
        WHERE listed_shares > 0
        GROUP BY code
        HAVING min(date)
    """)
    for c, s in cur.fetchall():
        if c not in base_shares or not base_shares[c]:
            base_shares[c] = s
    return base_shares


def backfill_stocks(con):
    cur = con.cursor()
    cur.execute("SELECT count(*) FROM stock_summary WHERE date < 1577836800000")
    existing = cur.fetchone()[0]
    if existing > 100000:
        log(STEP, f"Stocks already backfilled ({existing:,} rows before 2020)")
        return

    cur.execute("SELECT DISTINCT code FROM stock_summary WHERE length(code)=4 ORDER BY code")
    codes = [r[0] for r in cur.fetchall()]
    base_shares = get_shares_and_splits(con, codes)
    log(STEP, f"Starting backfill for {len(codes)} stock codes from {START_DATE} to {END_DATE}...")

    chunk_size = 50
    total_stock_rows = 0
    total_div_rows = 0
    cur_stock_id = 20000000

    for i in range(0, len(codes), chunk_size):
        chunk_codes = codes[i : i + chunk_size]
        tickers = [f"{c}.JK" for c in chunk_codes]
        t0 = time.time()
        try:
            df = yf.download(
                tickers,
                start=START_DATE,
                end=END_DATE,
                group_by="ticker",
                auto_adjust=False,
                threads=True,
                progress=False
            )
        except Exception as e:
            log(STEP, f"Chunk {i//chunk_size + 1} download error: {e}")
            continue

        stock_insert_rows = []
        div_insert_rows = []

        for code in chunk_codes:
            sym = f"{code}.JK"
            if len(chunk_codes) == 1:
                stock_data = df
            else:
                if sym not in df.columns.levels[0]:
                    continue
                stock_data = df[sym]

            c_close = stock_data["Close"].dropna()
            if c_close.empty:
                continue

            shares = base_shares.get(code, 1000000000)
            prev_close = None

            for dt, row in stock_data.iterrows():
                close = row["Close"]
                if pd.isna(close) or close <= 0:
                    continue
                close = float(close)
                high = float(row["High"]) if pd.notna(row["High"]) else close
                low = float(row["Low"]) if pd.notna(row["Low"]) else close
                op = float(row["Open"]) if pd.notna(row["Open"]) else close
                vol = int(row["Volume"]) if pd.notna(row["Volume"]) else 0
                prev = prev_close if prev_close is not None else op
                chg = close - prev
                val = close * vol

                ms = to_ms(dt)

                stock_insert_rows.append((
                    cur_stock_id,
                    code,
                    f"{code} Tbk.",
                    ms,
                    None,    # remarks
                    op,
                    high,
                    low,
                    close,
                    prev,
                    chg,
                    vol,
                    val,
                    0,       # frequency
                    op,      # first_trade
                    None,    # bid
                    0,       # bid_volume
                    None,    # offer
                    0,       # offer_volume
                    0,       # foreign_buy
                    0,       # foreign_sell
                    0,       # foreign_net
                    shares,
                    shares,  # tradable_shares
                    1.0,     # weight_for_index
                    1.0,     # individual_index
                    0, 0.0, 0
                ))
                cur_stock_id += 1
                prev_close = close

        if stock_insert_rows:
            cur.executemany("""
                INSERT OR REPLACE INTO stock_summary (
                    id, code, name, date, remarks, open, high, low, close, previous,
                    change, volume, value, frequency, first_trade, bid, bid_volume,
                    offer, offer_volume, foreign_buy, foreign_sell, foreign_net,
                    listed_shares, tradable_shares, weight_for_index, individual_index,
                    non_regular_volume, non_regular_value, non_regular_frequency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, stock_insert_rows)
            con.commit()
            total_stock_rows += len(stock_insert_rows)

        # Batch progress log
        elapsed = time.time() - t0
        log(STEP, f"Chunk {i//chunk_size + 1}/{(len(codes)-1)//chunk_size + 1} "
                  f"({len(chunk_codes)} codes): +{len(stock_insert_rows):,} rows in {elapsed:.1f}s "
                  f"(total {total_stock_rows:,})")

    log(STEP, f"Completed stocks backfill: {total_stock_rows:,} total rows inserted.")


def backfill_dividends(con):
    cur = con.cursor()
    cur.execute("SELECT count(*) FROM company_dividend WHERE ex_dividend < 1577836800000")
    existing = cur.fetchone()[0]
    if existing > 500:
        log(STEP, f"Dividends already backfilled ({existing:,} rows before 2020)")
        return

    cur.execute("SELECT DISTINCT code FROM stock_summary WHERE length(code)=4 ORDER BY code")
    codes = [r[0] for r in cur.fetchall()]
    log(STEP, f"Fetching 2005-2019 dividends for {len(codes)} stocks...")

    div_rows = []
    for code in codes:
        try:
            t = yf.Ticker(f"{code}.JK")
            d = t.dividends
            if d.empty:
                continue
            d = d[(d.index >= START_DATE) & (d.index < END_DATE)]
            for dt, val in d.items():
                if val <= 0:
                    continue
                ms = to_ms(dt)
                div_rows.append((
                    f"{code}-{ms}",
                    code,
                    f"{code} Tbk.",
                    float(val),
                    ms,   # cum_dividend
                    ms,   # ex_dividend
                    ms,   # record_date
                    ms,   # payment_date
                    ms    # period
                ))
        except Exception:
            pass

    if div_rows:
        cur.executemany("""
            INSERT OR IGNORE INTO company_dividend (
                id, code, name, cash_dividend, cum_dividend, ex_dividend, record_date, payment_date, period
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, div_rows)
        con.commit()
        log(STEP, f"Backfilled {len(div_rows):,} dividend records for 2005-2019.")


def main():
    con = get_db()
    try:
        backfill_ihsg(con)
        backfill_stocks(con)
        backfill_dividends(con)
    finally:
        con.close()

    # Regenerate canonical raw files
    log(STEP, "Updating canonical raw files via run.py...")
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "00_data_acquisition" / "run.py")], check=True)
    log(STEP, "All backfill and exports complete!")


if __name__ == "__main__":
    main()
