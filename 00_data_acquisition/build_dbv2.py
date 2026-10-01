"""Step 00 (v2 source) - combine the existing idx-api based DB (v1) with STOCKDB into dbv2.

Inputs (read-only, never modified):
  00_data_acquisition/idx_data.sqlite          v1: most current prices (to 2026-06-30), IHSG, dividends, delistings
  00_data_acquisition/stockdb/*.csv.gz         STOCKDB export from fetch_stockdb.py (prices from 1990, fundamentals)
Outputs:
  00_data_acquisition/dbv2.sqlite              combined DB + STOCKDB fundamentals + QA tables
  data/raw_v2/{stock_daily.csv.gz,index_daily.csv,dividends.csv,delistings.csv,ratios.csv}   pipeline contract

Merge rules (per code):
  * STOCKDB wins wherever both sources have the same code/date; v1 rows are used only before the first and after
    the last STOCKDB date (v1 rows inside the STOCKDB span are ignored, STOCKDB has them or the stock did not trade).
  * STOCKDB closes are raw: splits appear as one-day jumps and some rows are glitches (spike that reverts within
    3 rows). Glitch rows are dropped; split-like jumps (ratio ~ 1/k or k for common IDX ratios) are removed by
    back-adjusting earlier prices, so dbv2 prices are on the basis of the LAST STOCKDB segment (= STOCKDB as given).
  * v1 rows before the STOCKDB span are rescaled to the STOCKDB level at the first common date; rows after the span are
    chained with v1's own returns (close / previous - 1), which already handle splits.
  * listed_shares: STOCKDB key_ratios.share_outstanding (point-in-time, quarterly, ffilled from period end), split-
    normalised to the same basis as the prices so close x listed_shares is the true market cap. After the STOCKDB span
    and for codes without STOCKDB fundamentals: v1 market cap / dbv2 close.
  * dividends / ratios: dividends from v1 rescaled to the dbv2 price basis; ratios (pbv) from STOCKDB key_ratios.
  * Codes absent from STOCKDB prices keep their v1 rows unchanged.
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
HERE = Path(__file__).resolve().parent
V1_DB = HERE / "idx_data.sqlite"
SDB = HERE / "stockdb"
OUT_DB = HERE / "dbv2.sqlite"

SPLIT_K = np.array([2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 25, 30, 40, 50, 100, 200, 500, 1000], dtype=float)
PRICE_TOL = 0.10      # |q*k - 1| for a price jump q to count as a split of ratio k (daily move on top of the split)
SHARE_TOL = 0.03      # same for share-count jumps between quarters
GLITCH_JUMP = 1.6     # row deviating from the previous level by this factor (either way) ...
GLITCH_BACK = 0.15    # ... and returning to within this band of that level within GLITCH_WIN rows is a glitch
GLITCH_WIN = 3


# ---------------------------------------------------------------------------------------------- price processing
def drop_glitches(c):
    """Boolean keep-mask: spikes/dips that revert to the pre-spike level within GLITCH_WIN rows are dropped."""
    n = len(c)
    keep = np.ones(n, bool)
    i = 1
    while i < n:
        f = c[i] / c[i - 1]
        if f >= GLITCH_JUMP or f <= 1 / GLITCH_JUMP:
            for j in range(i + 1, min(i + 1 + GLITCH_WIN, n)):
                if abs(c[j] / c[i - 1] - 1) <= GLITCH_BACK:
                    keep[i:j] = False
                    i = j
                    break
        i += 1
    return keep


def snap_k(q, tol):
    """For a ratio q, return (k, kind) if q ~ 1/k (kind 'split') or q ~ k (kind 'reverse'), else (1, None)."""
    if 0.8 < q < 1.25:
        return 1.0, None
    ks = SPLIT_K
    e_split, e_rev = np.abs(q * ks - 1), np.abs(q / ks - 1)
    a, b = e_split.argmin(), e_rev.argmin()
    if e_split[a] <= tol and e_split[a] <= e_rev[b]:
        return ks[a], "split"
    if e_rev[b] <= tol:
        return ks[b], "reverse"
    return 1.0, None


def process_stockdb_prices(g, tol=PRICE_TOL):
    """g: STOCKDB rows of one code sorted by date. Returns (frame with adj close, list of break events, n_glitch)."""
    g = g.reset_index(drop=True)
    keep = drop_glitches(g["close"].to_numpy(float))
    n_glitch = int((~keep).sum())
    glitches = g.loc[~keep, ["date", "close"]]
    g = g[keep].reset_index(drop=True)
    c = g["close"].to_numpy(float)
    factor = np.ones(len(g))          # multiplier applied to rows BEFORE break i (to reach the post-break basis)
    events = []
    for i in range(1, len(g)):
        q = c[i] / c[i - 1]
        k, kind = snap_k(q, tol)
        if kind == "split":
            factor[i] = 1.0 / k
            events.append((g.at[i, "date"], "split", k, q))
        elif kind == "reverse":
            factor[i] = k
            events.append((g.at[i, "date"], "reverse", k, q))
        elif q < 0.5 or q > 2.0:
            events.append((g.at[i, "date"], "unexplained", np.nan, q))
    # A[i] = product of factor[j] for j > i
    A = np.ones(len(g))
    A[:-1] = np.cumprod(factor[::-1])[::-1][1:]
    g["scale"] = A
    g["close_adj"] = c * A
    return g, events, glitches, n_glitch


# ---------------------------------------------------------------------------------------------- shares
def quarter_end(period):
    y, q = period.str[:4].astype(int), period.str[5].astype(int)
    return pd.to_datetime(y.astype(str) + "-" + (q * 3).astype(str).str.zfill(2) + "-01") + pd.offsets.MonthEnd(0)


def shares_series(k):
    """k: key_ratios rows of one code. Returns Series date -> split-normalised shares (latest basis)."""
    k = k.dropna(subset=["share_outstanding"]).sort_values("period")
    k = k[k.share_outstanding > 0]
    if k.empty:
        return pd.Series(dtype=float), []
    sh = k["share_outstanding"].to_numpy(float)
    dates = quarter_end(k["period"]).to_numpy()
    mult = np.ones(len(sh))               # multiplier carried by rows BEFORE jump i
    ev = []
    for i in range(1, len(sh)):
        q = sh[i] / sh[i - 1]
        if 0.8 < q < 1.25:
            continue
        ks = SPLIT_K
        e_f, e_r = np.abs(q / ks - 1), np.abs(q * ks - 1)       # forward split: shares x k ; reverse: shares / k
        a, b = e_f.argmin(), e_r.argmin()
        if e_f[a] <= SHARE_TOL and e_f[a] <= e_r[b]:
            mult[i] = ks[a]
            ev.append((dates[i], "split", ks[a], q))
        elif e_r[b] <= SHARE_TOL:
            mult[i] = 1.0 / ks[b]
            ev.append((dates[i], "reverse", ks[b], q))
    F = np.ones(len(sh))
    F[:-1] = np.cumprod(mult[::-1])[::-1][1:]
    return pd.Series(sh * F, index=pd.DatetimeIndex(dates)), ev


# ---------------------------------------------------------------------------------------------- main
def read_v1():
    con = sqlite3.connect(f"file:{V1_DB.as_posix()}?mode=ro", uri=True)
    d = {t: pd.read_sql_query(f"select * from {t}", con) for t in
         ["stock_daily", "index_daily", "dividends", "delistings", "ratios", "stock_splits", "right_offerings"]}
    con.close()
    d["stock_daily"]["date"] = pd.to_datetime(d["stock_daily"]["date"])
    return d


KEEP_BAND = (0.6, 1.67)   # dbv2/v1 market-cap ratio treated as agreement (real share issuance, noise)
SNAP_TOL = 0.12


def calibrate_shares(out, sh, o):
    """Compare dbv2 market cap with v1 on common traded dates (rolling-median ratio rho).
    rho inside KEEP_BAND -> keep STOCKDB shares; rho ~ k or 1/k for a split ratio k -> basis error, shares rescaled by
    1/rho_snapped; anything else (bad STOCKDB share data) -> v1-implied shares (v1 market cap / dbv2 close).
    Returns (shares, n_rows_rescaled, n_rows_v1_implied)."""
    if o.empty or sh.isna().all():
        return sh, 0, 0
    vo = o.drop_duplicates("date").set_index("date")
    mc_o = (vo["close"] * vo["listed_shares"]).where(vo["volume"] > 0).reindex(out["date"]).to_numpy()
    rho = pd.Series(out["close"].to_numpy() * sh.to_numpy() / mc_o, index=out.index)
    rho = rho.where((rho > 0) & np.isfinite(rho))
    # STOCKDB share counts change only at report dates, so rho is ~constant within a run of equal share counts:
    # classify each run once (median rho) instead of row by row, which avoids flicker.
    seg = (sh != sh.shift()).cumsum()
    rho_seg = rho.groupby(seg).agg(lambda x: x.median() if x.notna().sum() >= 3 else np.nan)
    if rho_seg.notna().sum() == 0:
        return sh, 0, 0
    cand = np.r_[SPLIT_K, 1 / SPLIT_K]
    st_seg = pd.Series(np.nan, index=rho_seg.index)    # 0 keep, 1 rescale, 2 v1-implied
    lam_seg = pd.Series(1.0, index=rho_seg.index)
    for g, r in rho_seg.dropna().items():
        if KEEP_BAND[0] <= r <= KEEP_BAND[1]:
            st_seg[g] = 0
            continue
        j = np.abs(np.log(r / cand)).argmin()
        if abs(r / cand[j] - 1) <= SNAP_TOL:
            st_seg[g], lam_seg[g] = 1, 1 / cand[j]
        else:
            st_seg[g] = 2
    st_seg = st_seg.ffill().bfill()                    # segments without v1 data inherit the nearest known class
    lam_seg = lam_seg.where(st_seg == 1).ffill().bfill().where(st_seg == 1, 1.0)
    state, lam = seg.map(st_seg), seg.map(lam_seg)
    new = sh * lam
    fb = state == 2
    if fb.any():
        implied = pd.Series(mc_o, index=out.index).ffill().bfill() / out["close"]
        new = new.where(~fb, implied)
    return new, int((state == 1).sum()), int(fb.sum())


def build_code(code, o, s, shares):
    """Combine v1 rows `o` (may be empty) and STOCKDB rows `s` for one code. Returns (frame, info dict)."""
    s, events, glitches, n_gl = process_stockdb_prices(s)
    d0, d1 = s["date"].iloc[0], s["date"].iloc[-1]
    info = {"code": code, "n_glitch": n_gl, "n_events": len(events), "pre_rows": 0, "pre_dropped": 0, "post_rows": 0,
            "inside_v1_ignored": 0}

    cols = ["date", "code", "open", "high", "low", "close", "previous", "volume", "value", "listed_shares",
            "tradable_shares", "remarks", "source", "price_scale"]
    sc = s["scale"].to_numpy()
    mid = pd.DataFrame({"date": s["date"], "code": code, "open": s["open"] * sc, "high": s["high"] * sc,
                        "low": s["low"] * sc, "close": s["close_adj"], "volume": s["volume"],
                        "source": "stockdb", "price_scale": sc})
    mid["previous"] = mid["close"].shift(1)
    mid.loc[mid.index[0], "previous"] = mid["close"].iloc[0] / (1 + s["change_pct"].iloc[0] / 100)

    pre = post = None
    if len(o):
        info["inside_v1_ignored"] = int(((o.date >= d0) & (o.date <= d1)).sum())
        # ---- before the STOCKDB span: rescale v1 to the STOCKDB level at the first common date
        pr = o[o.date < d0]
        if len(pr):
            common = o[o.date.isin(s["date"])]
            if len(common):
                dstar = common.date.min()
                c = s.loc[s.date == dstar, "close_adj"].iloc[0] / common.loc[common.date == dstar, "close"].iloc[0]
                pre = pr.copy()
                for col in ("open", "high", "low", "close"):
                    pre[col] = pre[col] * c
                pre["previous"] = pre["close"].shift(1)
                pre.iloc[0, pre.columns.get_loc("previous")] = pr["previous"].iloc[0] * c
                pre["source"] = pre["source"].astype(str)
                pre["price_scale"] = c
                info["pre_rows"] = len(pre)
                mid.loc[mid.index[0], "previous"] = pre["close"].iloc[-1]   # link v1 -> STOCKDB
            else:
                info["pre_dropped"] = len(pr)
        # ---- after the STOCKDB span: chain v1 returns onto the last STOCKDB close
        po = o[o.date > d1].sort_values("date")
        if len(po):
            r = (po["close"] / po["previous"] - 1).where((po["close"] > 0) & (po["previous"] > 0)).fillna(0.0)
            lvl = mid["close"].iloc[-1] * (1 + r).cumprod()
            k = (lvl / po["close"]).to_numpy()          # basis ratio dbv2 / v1 on each row (1 unless splits)
            post = po.copy()
            post["close"] = lvl.to_numpy()
            for col in ("open", "high", "low"):
                post[col] = po[col].to_numpy() * k
            post["previous"] = np.r_[mid["close"].iloc[-1], lvl.to_numpy()[:-1]]
            post["price_scale"] = k
            post["_v1_mcap"] = po["close"].to_numpy() * po["listed_shares"].to_numpy()
            info["post_rows"] = len(post)

    mid["_v1_mcap"] = np.nan
    out = pd.concat([x for x in (pre, mid, post) if x is not None], ignore_index=True)
    out["code"] = code
    out = out.sort_values("date").reset_index(drop=True)
    out["value"] = out["close"] * out["volume"]
    # ---- shares on the dbv2 price basis
    sh = pd.Series(np.nan, index=out.index)
    if len(shares):
        sh = pd.Series(shares.reindex(shares.index.union(out["date"])).ffill().bfill().reindex(out["date"]).to_numpy(),
                       index=out.index)
    info["shares_rescaled"] = info["shares_v1_implied"] = 0
    if len(shares) and len(o):
        span = out["date"] <= d1
        sh_span, info["shares_rescaled"], info["shares_v1_implied"] = calibrate_shares(
            out[span].reset_index(drop=True), sh[span].reset_index(drop=True), o)
        sh[span] = sh_span.to_numpy()
    if post is not None:
        m = (out["date"] > d1)
        sh[m] = out.loc[m, "_v1_mcap"] / out.loc[m, "close"]  # exact v1 market cap after the STOCKDB span
    if sh.isna().any() and len(o):                            # codes without STOCKDB fundamentals
        osh = o.set_index("date")
        implied = (osh["close"] * osh["listed_shares"]).reindex(out["date"]).to_numpy() / out["close"].to_numpy()
        sh = sh.fillna(pd.Series(implied, index=out.index)).ffill().bfill()
    out["listed_shares"] = sh
    return out.reindex(columns=cols + ["_v1_mcap"]).drop(columns="_v1_mcap"), info, events, glitches


def rescale_dividends(div, v1_close, new_close):
    """Express v1 cash dividends on the dbv2 price basis using the dbv2/v1 close ratio on the nearest earlier common date."""
    ratio = (new_close.set_index(["code", "date"])["close"] / v1_close.set_index(["code", "date"])["close"]).dropna()
    ratio = ratio.rename("k").reset_index().sort_values("date")
    d = div.sort_values("ex_date").copy()
    out = pd.merge_asof(d, ratio, left_on="ex_date", right_on="date", by="code", direction="backward",
                        tolerance=pd.Timedelta(days=30))
    fwd = pd.merge_asof(d, ratio, left_on="ex_date", right_on="date", by="code", direction="forward",
                        tolerance=pd.Timedelta(days=30))
    k = out["k"].fillna(fwd["k"]).fillna(1.0)
    out["cash_dividend"] = out["cash_dividend"] * k
    return out[["code", "ex_date", "cash_dividend", "source"]].sort_values(["ex_date", "code"]).reset_index(drop=True), \
        int((k.eq(1.0)).sum()), int(((k - 1).abs() > 1e-6).sum())


def main():
    t0 = time.time()
    v1 = read_v1()
    v1sd = v1["stock_daily"]
    P = pd.read_csv(SDB / "prices.csv.gz", parse_dates=["date"]).sort_values(["ticker", "date"])
    KR = pd.read_csv(SDB / "key_ratios.csv.gz")
    FN = pd.read_csv(SDB / "financial_normalized.csv.gz")
    INFO = pd.read_csv(SDB / "stock_info.csv")
    log(STEP, f"v1 {len(v1sd):,} rows / {v1sd.code.nunique()} codes; STOCKDB {len(P):,} rows / {P.ticker.nunique()} codes")

    ov = {c: g for c, g in v1sd.groupby("code")}
    kr = {c: g for c, g in KR.groupby("ticker")}
    frames, infos, price_ev, share_ev, glitch_rows = [], [], [], [], []
    for code, s in P.groupby("ticker"):
        o = ov.get(code, v1sd.iloc[0:0]).sort_values("date")
        sh, sev = shares_series(kr[code]) if code in kr else (pd.Series(dtype=float), [])
        out, info, ev, gl = build_code(code, o, s, sh)
        frames.append(out)
        infos.append(info)
        price_ev += [(code, *e) for e in ev]
        share_ev += [(code, *e) for e in sev]
        glitch_rows += [(code, d, c) for d, c in gl.itertuples(index=False)]
    only_v1 = v1sd[~v1sd.code.isin(P.ticker.unique())].copy()
    only_v1["price_scale"] = 1.0
    stock = pd.concat(frames + [only_v1], ignore_index=True)
    stock["source"] = stock["source"].replace({"idx": "idx", "yahoo": "yahoo"})
    stock = stock.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="first").reset_index(drop=True)
    cols = ["date", "code", "open", "high", "low", "close", "previous", "volume", "value", "frequency", "listed_shares",
            "tradable_shares", "remarks", "source", "price_scale"]
    stock = stock.reindex(columns=cols)
    # codes with no share count in any source cannot get a market cap (size filter / cap weights) -> excluded, listed in QA
    no_sh = stock.groupby("code")["listed_shares"].apply(lambda x: x.isna().all())
    qa_drop = stock[stock.code.isin(no_sh.index[no_sh])].groupby("code").agg(
        rows=("date", "size"), first_date=("date", "min"), last_date=("date", "max")).reset_index()
    qa_drop["reason"] = "no listed_shares in STOCKDB key_ratios or v1"
    stock = stock[~stock.code.isin(qa_drop.code)].reset_index(drop=True)
    log(STEP, f"excluded {len(qa_drop)} codes without any share count: {qa_drop.code.tolist()}")
    log(STEP, f"stock_daily: {len(stock):,} rows, {stock.code.nunique()} codes, {stock.date.min():%Y-%m-%d}..{stock.date.max():%Y-%m-%d}; "
              f"sources {stock.source.value_counts().to_dict()}")

    qa_info = pd.DataFrame(infos)
    qa_pe = pd.DataFrame(price_ev, columns=["code", "date", "kind", "k", "q"])
    qa_se = pd.DataFrame(share_ev, columns=["code", "date", "kind", "k", "q"])
    qa_gl = pd.DataFrame(glitch_rows, columns=["code", "date", "close"])
    log(STEP, f"price breaks {qa_pe.kind.value_counts().to_dict()}; glitch rows {len(qa_gl)}; share-count splits {len(qa_se)}; "
              f"v1 rows ignored inside STOCKDB span: {qa_info.inside_v1_ignored.sum():,}; "
              f"v1 pre-span rows unlinked: {qa_info.pre_dropped.sum():,}")
    log(STEP, f"shares calibrated vs v1 market cap: {(qa_info.shares_rescaled > 0).sum()} codes rescaled "
              f"({qa_info.shares_rescaled.sum():,} rows), {(qa_info.shares_v1_implied > 0).sum()} codes use v1-implied shares "
              f"({qa_info.shares_v1_implied.sum():,} rows)")

    # ---- dividends / ratios / others
    div, n_k1, n_resc = rescale_dividends(v1["dividends"].assign(ex_date=lambda d: pd.to_datetime(d["ex_date"])),
                                          v1sd[["code", "date", "close"]], stock[["code", "date", "close"]])
    log(STEP, f"dividends: {len(div):,} (rescaled to dbv2 basis: {n_resc:,}; unscaled: {n_k1:,})")
    rat = KR[["ticker", "period", "price_to_book_value_quarter"]].dropna().rename(
        columns={"ticker": "code", "price_to_book_value_quarter": "pbv"})
    rat["date"] = quarter_end(rat["period"])
    rat = rat[rat.pbv > 0][["code", "date", "pbv"]].sort_values(["code", "date"]).reset_index(drop=True)
    idx = v1["index_daily"]
    dl = v1["delistings"]
    log(STEP, f"ratios {len(rat):,} (STOCKDB key_ratios), index_daily {len(idx):,}, delistings {len(dl)}")

    # ---- database
    tmp = OUT_DB.with_suffix(".sqlite.tmp")
    tmp.unlink(missing_ok=True)
    out = sqlite3.connect(tmp)
    txt = lambda df, cs: df.assign(**{c: pd.to_datetime(df[c]).dt.strftime("%Y-%m-%d") for c in cs})  # noqa: E731
    txt(stock, ["date"]).to_sql("stock_daily", out, index=False, chunksize=100_000)
    idx.to_sql("index_daily", out, index=False)
    txt(div, ["ex_date"]).to_sql("dividends", out, index=False)
    dl.to_sql("delistings", out, index=False)
    txt(rat, ["date"]).to_sql("ratios", out, index=False)
    v1["stock_splits"].to_sql("stock_splits", out, index=False)
    v1["right_offerings"].to_sql("right_offerings", out, index=False)
    INFO.to_sql("stock_info", out, index=False)
    KR.to_sql("key_ratios", out, index=False)
    FN.to_sql("financial_normalized", out, index=False, chunksize=200_000)
    qa_info.to_sql("qa_code", out, index=False)
    txt(qa_pe, ["date"]).to_sql("qa_price_breaks", out, index=False)
    txt(qa_se, ["date"]).to_sql("qa_share_breaks", out, index=False)
    txt(qa_gl, ["date"]).to_sql("qa_glitch_rows", out, index=False)
    txt(qa_drop, ["first_date", "last_date"]).to_sql("qa_excluded_codes", out, index=False)
    pd.DataFrame({"key": ["built_at", "v1_db", "stockdb_dir", "stock_first", "stock_last", "price_tol", "share_tol"],
                  "value": [time.strftime("%Y-%m-%d %H:%M:%S"), str(V1_DB), str(SDB), f"{stock.date.min():%Y-%m-%d}",
                            f"{stock.date.max():%Y-%m-%d}", str(PRICE_TOL), str(SHARE_TOL)]}).to_sql("meta", out, index=False)
    out.executescript("""
        create unique index ix_stock on stock_daily(code, date);
        create index ix_stock_date on stock_daily(date);
        create unique index ix_index on index_daily(code, date);
        create index ix_div on dividends(code, ex_date);
        create index ix_fn on financial_normalized(ticker, period);
    """)
    out.commit()
    out.close()
    tmp.replace(OUT_DB)
    log(STEP, f"database written: {OUT_DB} ({OUT_DB.stat().st_size / 1e6:.0f} MB)")

    # ---- canonical CSVs for steps 01-07
    raw = S.RAW
    raw.mkdir(parents=True, exist_ok=True)
    stock[["date", "code", "close", "previous", "volume", "value", "listed_shares", "remarks"]].to_csv(
        raw / "stock_daily.csv.gz", index=False)
    idx[["date", "code", "close"]].to_csv(raw / "index_daily.csv", index=False)
    div[["code", "ex_date", "cash_dividend"]].to_csv(raw / "dividends.csv", index=False)
    dl[["code", "delisting_date"]].to_csv(raw / "delistings.csv", index=False)
    rat.to_csv(raw / "ratios.csv", index=False)
    (raw / "SYNTHETIC").unlink(missing_ok=True)
    log(STEP, f"canonical CSVs written to {raw} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
