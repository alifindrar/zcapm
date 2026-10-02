"""Synthetic IDX-like data in the canonical raw format - for testing the pipeline plumbing only.

Returns follow the empirical ZCAPM with known beta, Z, p per stock, plus IPOs, delistings,
cash dividends (price drops on ex-date), stock splits (IDX-style adjusted `previous`) and zero-volume days.
Writes data/raw/* (and data/external/rf.csv if there is none), plus a data/raw/SYNTHETIC marker.

    python 00_data_acquisition/make_synthetic.py [--force]
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import log  # noqa: E402

STEP = "00-synth"
N_STOCKS, START, END, SEED = 300, "2011-01-03", "2019-12-31", 7
RF_ANNUAL = 5.0


def main():
    if (S.RAW / "stock_daily.csv.gz").exists() and not (S.RAW / "SYNTHETIC").exists() and "--force" not in sys.argv:
        sys.exit("data/raw already holds real data - pass --force to overwrite")
    rng = np.random.default_rng(SEED)
    dates = pd.bdate_range(START, END)
    T, N = len(dates), N_STOCKS
    letters = "ABCDEFGHIJKLMNOPQRSTUVW"
    codes = ["".join(c) for c in itertools.islice(itertools.product(letters, repeat=4), 0, 20000, 61)][:N]

    rf_d = (1 + RF_ANNUAL / 100) ** (1 / S.TRADING_DAYS) - 1
    mkt = rng.normal(0.0004, 0.010, T)
    s = 0.015 * np.exp(rng.normal(0, 0.3, T))
    beta = rng.normal(1.0, 0.3, N)
    Z = rng.uniform(0.2, 1.0, N)
    p = rng.uniform(0.40, 0.60, N)
    D = np.where(rng.random((T, N)) < p, 1.0, -1.0)
    ret = rf_d + beta * mkt[:, None] + Z * D * s[:, None] + rng.normal(0, 1, (T, N)) * 0.8 * s[:, None]

    volume = rng.poisson(5e5, (T, N)).astype(float)
    zero = rng.random((T, N)) < 0.03
    volume[zero] = 0
    ret[zero] = 0.0

    # listing window: 10% IPO in first half, 10% delist in second half
    first = np.zeros(N, int)
    last = np.full(N, T - 1)
    ipo = rng.choice(N, N // 10, replace=False)
    first[ipo] = rng.integers(0, T // 2, len(ipo))
    dl = rng.choice(np.setdiff1d(np.arange(N), ipo), N // 10, replace=False)
    last[dl] = rng.integers(T // 2, T - 30, len(dl))

    # dividends (price drop on ex-date) and splits
    div_rows, split_day = [], {}
    for j in rng.choice(N, N // 3, replace=False):
        for y in range(dates[0].year, dates[-1].year + 1):
            day = int(np.searchsorted(dates, pd.Timestamp(f"{y}-{rng.integers(3, 9):02d}-15")))
            if first[j] < day <= last[j]:
                div_rows.append((j, day))
    for j in rng.choice(N, 5, replace=False):
        split_day[j] = int(rng.integers(first[j] + 300, max(first[j] + 301, last[j] - 10)))

    shares = np.exp(rng.normal(21, 1.2, N)).round()
    rows, divs = [], []
    div_set = {}
    for j, day in div_rows:
        div_set.setdefault(j, set()).add(day)
    for j in range(N):
        price = float(np.exp(rng.normal(7, 1)))
        sh = shares[j]
        for t in range(first[j], last[j] + 1):
            prev = price
            if split_day.get(j) == t:
                prev, sh = price / 5, sh * 5
            r = ret[t, j]
            close = prev * (1 + r)
            if j in div_set and t in div_set[j]:
                dps = 0.02 * prev
                close -= dps
                divs.append((codes[j], dates[t], round(dps, 4)))
            close = max(close, 1.0)
            rows.append((dates[t], codes[j], close, prev, volume[t, j], volume[t, j] * close, sh, ""))
            price = close

    raw = pd.DataFrame(rows, columns=["date", "code", "close", "previous", "volume", "value", "listed_shares", "remarks"])
    S.RAW.mkdir(parents=True, exist_ok=True)
    S.EXTERNAL.mkdir(parents=True, exist_ok=True)
    raw.to_csv(S.RAW / "stock_daily.csv.gz", index=False)

    ihsg = 1000 * np.cumprod(1 + rf_d + mkt)
    pd.DataFrame({"date": dates, "code": S.IHSG_CODE, "close": ihsg}).to_csv(S.RAW / "index_daily.csv", index=False)
    pd.DataFrame(divs, columns=["code", "ex_date", "cash_dividend"]).to_csv(S.RAW / "dividends.csv", index=False)
    pd.DataFrame({"code": [codes[j] for j in dl], "delisting_date": dates[last[dl]]}).to_csv(
        S.RAW / "delistings.csv", index=False)
    qe = pd.date_range(START, END, freq="QE")
    pbv = np.exp(rng.normal(0.3, 0.6, N))[None, :] * np.exp(rng.normal(0, 0.1, (len(qe), N)))
    pd.DataFrame([(codes[j], qe[q], pbv[q, j]) for q in range(len(qe)) for j in range(N)],
                 columns=["code", "date", "pbv"]).to_csv(S.RAW / "ratios.csv", index=False)
    if not S.RF_FILE.exists():           # data/external is shared with real runs: never overwrite the real series
        pd.DataFrame({"date": pd.date_range(START, END, freq="MS"), "rate_annual_pct": RF_ANNUAL}).to_csv(
            S.RF_FILE, index=False)
    pd.DataFrame({"code": codes, "beta": beta, "Z": Z, "p": p, "zstar": Z * (2 * p - 1)}).to_csv(
        S.RAW / "synthetic_truth.csv", index=False)
    (S.RAW / "SYNTHETIC").write_text("synthetic data - plumbing test only\n")
    log(STEP, f"{len(raw):,} rows, {N} stocks, {T} days, {len(divs)} dividends, {len(split_day)} splits")


if __name__ == "__main__":
    main()
