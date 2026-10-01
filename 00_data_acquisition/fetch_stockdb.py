"""Step 00 (alt. source) - consolidate the per-ticker STOCKDB SQLite files into flat files.

Source : G:/My Drive/QUANT/STOCKDB/databases/{TICKER}.db   (opened read-only, one DB per stock)
Output : 00_data_acquisition/stockdb/
    stock_info.csv              one row per ticker (profile, board, sector, data coverage)
    prices.csv.gz               ticker, date, open, high, low, close, volume, change_pct
    key_ratios.csv.gz           ticker, period, <all key_ratios columns>   (quarterly, IDR / ratios)
    financial_normalized.csv.gz ticker, period, statement, line_item, value_idr, unit   (EAV, IDR)
    fetch_log.csv               ticker, tables found, row counts, status

Does NOT touch idx_data.sqlite or data/raw/ (the idx-api based pipeline contract). Prices here are
the STOCKDB history (see README); compare with data/raw/stock_daily.csv.gz before swapping sources.
Wide statement tables (income_statement, balance_sheet, cash_flow) are skipped: their columns differ
per company and are fully contained in financial_normalized.
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.io import log  # noqa: E402

STEP = "00"
SRC = Path(r"G:/My Drive/QUANT/STOCKDB/databases")
OUT = Path(__file__).resolve().parent / "stockdb"


def has(con, table):
    return con.execute("select 1 from sqlite_master where type='table' and name=?", (table,)).fetchone() is not None


def table(con, name, ticker):
    """Return table `name` with a leading ticker column, or None if absent/empty."""
    if not has(con, name):
        return None
    df = pd.read_sql_query(f'select * from "{name}"', con)
    if df.empty:
        return None
    if "ticker" not in df.columns:      # stock_info carries its own
        df.insert(0, "ticker", ticker)
    return df


def main():
    files = sorted(SRC.glob("*.db"))
    if not files:
        sys.exit(f"no .db files in {SRC}")
    OUT.mkdir(exist_ok=True)

    parts = {"stock_info": [], "prices": [], "key_ratios": [], "financial_normalized": []}
    status = []
    for f in files:
        t = f.stem
        row = {"ticker": t, "status": "ok"}
        try:
            con = sqlite3.connect(f"file:{f.as_posix()}?mode=ro", uri=True)
            for name in parts:
                df = table(con, name, t)
                row[name] = 0 if df is None else len(df)
                if df is not None:
                    parts[name].append(df)
            con.close()
        except sqlite3.Error as e:
            row["status"] = f"error: {e}"
        status.append(row)

    for name, dfs in parts.items():
        df = pd.concat(dfs, ignore_index=True)
        if name == "prices":
            df = df.sort_values(["ticker", "date"])
        elif name in ("key_ratios", "financial_normalized"):
            df = df.sort_values(["ticker", "period"])
        path = OUT / (f"{name}.csv" if name == "stock_info" else f"{name}.csv.gz")
        df.to_csv(path, index=False)
        log(STEP, f"{path.name}: {len(df):,} rows, {df.ticker.nunique()} tickers")

    st = pd.DataFrame(status)
    st.to_csv(OUT / "fetch_log.csv", index=False)
    bad = st[st.status != "ok"]
    log(STEP, f"{len(files)} DBs read, {len(bad)} errors; no prices: {(st.prices == 0).sum()}, "
              f"no fundamentals: {(st.key_ratios == 0).sum()}")


if __name__ == "__main__":
    main()
