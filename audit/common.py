"""Shared read-only loaders for the audit scripts. Nothing here writes outside outputs/audit_<version>/."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import load, log  # noqa: E402

OUT = ROOT / "outputs" / f"audit_{S.DB_VERSION}"
DB = ROOT / "00_data_acquisition" / "dbv2.sqlite"
SUBPERIODS = [("2007-04", "2013-12"), ("2014-01", "2019-12"), ("2020-01", "2026-06")]

if S.DB_VERSION != "v2":
    sys.exit("the audit covers the v2 data only (unset ZCAPM_DB)")


def interim(name):
    return load(S.INTERIM / f"{name}.pkl")


def processed(name):
    return load(S.PROCESSED / f"{name}.pkl")


def db(sql, dates=()):
    """Query dbv2.sqlite (opened read-only)."""
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(sql, con, parse_dates=list(dates))
    finally:
        con.close()


def write(df, name, step, index=True):
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / f"{name}.csv", index=index)
    log(step, f"{name}.csv: {len(df):,} rows")


def show(step, title, df):
    log(step, title)
    print(df.to_string(), flush=True)
