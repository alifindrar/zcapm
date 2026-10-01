"""Audit of steps 00-01 - data coverage, suspicious returns and market caps, eligibility filters, survivorship.

    python audit/a01_data.py
"""
import numpy as np
import pandas as pd

from common import S, db, interim, processed, show, write
from lib.io import month_ends, window_mask

STEP = "a01"
RET_LIMIT = 0.35          # widest IDX auto-rejection band; a larger daily move needs an explanation
SHARE_JUMP = 1.5
SPLIT_K = np.array([2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 25, 30, 40, 50, 100, 200, 500, 1000], dtype=float)
ZERO_ALTS = (0.35, 0.50, 1.00)


def split_like(q, tol=0.10):
    q = np.asarray(q, float)[:, None]
    return (np.abs(q * SPLIT_K - 1).min(axis=1) <= tol) | (np.abs(q / SPLIT_K - 1).min(axis=1) <= tol)


def near(events, code, date, before, after):
    """True where (code, date) has an event of the same code in [date - before, date + after] days."""
    ev = events.groupby("code")["date"].apply(lambda s: s.to_numpy()).to_dict()
    out = np.zeros(len(code), bool)
    for i, (c, d) in enumerate(zip(code, date)):
        e = ev.get(c)
        if e is not None:
            dd = (e - np.datetime64(d)) / np.timedelta64(1, "D")
            out[i] = ((dd >= -before) & (dd <= after)).any()
    return out


def load_rows():
    sd = db("select date, code, close, previous, volume, listed_shares, source, price_scale from stock_daily "
            "where date >= '2000-01-01'", dates=["date"])
    sd = sd[sd["code"].str.match(S.CODE_REGEX) & ~sd["code"].str.startswith(S.EXCLUDE_PREFIXES)]
    sd = sd.sort_values(["code", "date"]).reset_index(drop=True)
    g = sd.groupby("code")
    sd["obs_no"] = g.cumcount() + 1
    sd["prev_source"] = g["source"].shift(1)
    sd["gap_days"] = (sd["date"] - g["date"].shift(1)).dt.days
    sd["sh_ratio"] = sd["listed_shares"] / g["listed_shares"].shift(1)
    for k in (1, 2, 3):
        sd[f"close_f{k}"] = g["close"].shift(-k)
    return sd


def coverage(sd, r, traded, elig, last_date):
    yr = sd["date"].dt.year
    src = sd.groupby([yr, "source"]).size().unstack(fill_value=0).add_prefix("rows_")
    cov = pd.DataFrame({"codes": sd.groupby(yr)["code"].nunique(),
                        "valid_returns_per_day": r.notna().sum(axis=1).groupby(r.index.year).mean(),
                        "traded_per_day": traded.sum(axis=1).groupby(r.index.year).mean(),
                        "eligible_per_month": elig.sum(axis=1).groupby(elig.index.year).mean(),
                        "codes_last_seen_this_year": last_date.dt.year.value_counts()}).join(src)
    cov["codes_last_seen_this_year"] = cov["codes_last_seen_this_year"].fillna(0)
    cov.index.name = "year"
    return cov


def extreme_returns(sd, r, mcap, elig, events):
    w = mcap.shift(1).where(r.notna() & (mcap.shift(1) > 0))
    w = w.div(w.sum(axis=1), axis=0)
    st = r.stack()
    st = st[(st.abs() > RET_LIMIT) & (st.index.get_level_values(0) >= "2005-01-01")].rename("r").reset_index()
    st.columns = ["date", "code", "r"]
    x = st.merge(sd, on=["date", "code"], how="left")
    x["weight"] = [w.at[d, c] for d, c in zip(x["date"], x["code"])]
    mes = elig.index
    prior = mes.searchsorted(x["date"].to_numpy(), side="left") - 1
    x["eligible_prev_month_end"] = [bool(elig.iat[p, elig.columns.get_loc(c)]) if p >= 0 else False
                                    for p, c in zip(prior, x["code"])]
    base = x["previous"]
    x["reverts"] = False
    for k in (1, 2, 3):
        x["reverts"] |= (x[f"close_f{k}"] / base - 1).abs() <= 0.15
    x["split_like"] = split_like(1 + x["r"])
    x["near_price_break"] = near(events["price"], x["code"], x["date"], 5, 5)
    x["near_split_table"] = near(events["split"], x["code"], x["date"], 15, 15)
    x["near_rights"] = near(events["rights"], x["code"], x["date"], 30, 30)
    x["near_share_break"] = near(events["share"], x["code"], x["date"], 10, 100)   # quarter-end stamp after the event

    def label(row):
        if row["obs_no"] <= 5:
            return "first 5 rows of the code (IPO / data start)"
        if row["source"] != row["prev_source"]:
            return "seam between data sources"
        if row["reverts"]:
            return "spike that reverts within 3 rows (glitch)"
        if row["split_like"] and (row["near_share_break"] or row["near_split_table"] or row["near_price_break"]):
            return "split-like jump next to a recorded split (unadjusted)"
        if row["near_rights"]:
            return "rights issue window"
        if row["split_like"]:
            return "split-like jump, no recorded event"
        if row["gap_days"] > 10:
            return "first trade after a gap > 10 days"
        return "unexplained"
    x["class"] = x.apply(label, axis=1)
    keep = ["date", "code", "r", "close", "previous", "volume", "source", "prev_source", "obs_no", "gap_days",
            "weight", "eligible_prev_month_end", "reverts", "split_like", "near_price_break", "near_split_table",
            "near_rights", "near_share_break", "class"]
    return x[keep].sort_values(["date", "code"])


def share_jumps(sd, events):
    x = sd[(sd["date"] >= "2005-01-01") & sd["sh_ratio"].notna()
           & ((sd["sh_ratio"] > SHARE_JUMP) | (sd["sh_ratio"] < 1 / SHARE_JUMP))].copy()
    x["split_like"] = split_like(x["sh_ratio"], tol=0.05)
    x["near_share_break"] = near(events["share"], x["code"], x["date"], 100, 100)
    x["near_rights"] = near(events["rights"], x["code"], x["date"], 60, 60)
    x["near_split_table"] = near(events["split"], x["code"], x["date"], 30, 30)
    x["price_move"] = x["close"] / x["previous"] - 1
    x["mcap_ratio"] = x["sh_ratio"] * (1 + x["price_move"])

    def label(row):
        if row["source"] != row["prev_source"]:
            return "seam between data sources"
        if row["near_rights"] or row["near_split_table"]:
            return "recorded rights issue / split nearby"
        if row["split_like"]:
            return "share count jumps by a split ratio, price does not (basis mismatch)"
        return "share count change, no recorded event"
    x["class"] = x.apply(label, axis=1)
    return x[["date", "code", "sh_ratio", "price_move", "mcap_ratio", "source", "prev_source", "split_like",
              "near_share_break", "near_rights", "near_split_table", "class"]].sort_values(["date", "code"])


def waterfall(r, traded, mcap, close, nominal, elig):
    dates = r.index
    mes = month_ends(dates)
    year_ends = mes[mes.month == 12]
    close_ff, nominal_ff, mcap_ff = close.ffill(limit=5), nominal.ffill(limit=5), mcap.ffill(limit=20)
    rows = {}
    for T in mes:
        if dates[0] > (T.to_period("M") - (S.WINDOW_MONTHS - 1)).start_time:
            continue
        win = window_mask(dates, T, S.WINDOW_MONTHS)
        tr, rr = traded[win], r[win]
        n_valid = tr.sum()
        zero = ((rr == 0) & tr).sum() / n_valid.clip(lower=1)
        listed = rr.notna().sum() > 0
        obs = n_valid >= S.MIN_OBS
        z = obs & (zero <= S.MAX_ZERO_FRAC)
        price = close_ff.loc[T] > S.MIN_PRICE
        ye = year_ends[year_ends <= T]
        size = pd.Series(True, index=r.columns)
        size_ff = size.copy()
        ye_nan = pd.Series(False, index=r.columns)
        if len(ye):
            mc, mcf = mcap.loc[ye[-1]], mcap_ff.loc[ye[-1]]
            size, size_ff, ye_nan = ~(mc < mc.quantile(S.SIZE_CUT)), ~(mcf < mcf.quantile(S.SIZE_CUT)), mc.isna()
        final = z & price & size
        nom = nominal_ff.loc[T]
        row = {"listed": listed.sum(), "obs>=200": (obs & listed).sum(), "+zero<=20%": z.sum(),
               "+price": (z & price).sum(), "+size": final.sum(), "eligible_pkl": elig.loc[T].sum(),
               "median_zero_frac": zero[obs].median(),
               "eligible_with_no_year_end_mcap": (final & ye_nan).sum(),
               "eligible_failing_size_if_mcap_carried": (final & ~size_ff).sum(),
               "adj<=50_nominal>50 (wrongly out)": (z & size & ~price & (nom > S.MIN_PRICE)).sum(),
               "adj>50_nominal<=50 (wrongly in)": (final & (nom <= S.MIN_PRICE)).sum()}
        for a in ZERO_ALTS:
            row[f"eligible_if_zero<={a:.0%}"] = (obs & (zero <= a) & price & size).sum()
        rows[T] = row
    return pd.DataFrame(rows).T


def survivorship(sd, last_date, data_end):
    dl = pd.read_csv(S.RAW / "delistings.csv", parse_dates=["delisting_date"])
    flagged = last_date[last_date < data_end - pd.Timedelta(days=10)]
    t = pd.DataFrame({"last_price_date": flagged, "delist_return_applied": True})
    t = t.join(dl.set_index("code")["delisting_date"], how="outer")
    t["in_price_data"] = t.index.isin(sd["code"].unique())
    t["last_price_date"] = t["last_price_date"].fillna(last_date.reindex(t.index))
    t["delist_return_applied"] = t["delist_return_applied"].fillna(False)
    t["in_delisting_list"] = t["delisting_date"].notna()
    t.index.name = "code"
    hold = processed("holdings")
    h = hold[hold["code"].isin(flagged.index)].copy()
    h["m1"] = h["T"].dt.to_period("M") + 1
    h = h[h["m1"] == h["code"].map(flagged).dt.to_period("M")]
    return t.sort_values("last_price_date"), h


def main():
    r, traded, mcap = interim("returns_daily"), interim("traded_daily"), interim("mcap_daily")
    elig, last_date, f = interim("eligible_monthly"), interim("last_date"), interim("factors_daily")
    sd = load_rows()
    ev = {"price": db("select code, date from qa_price_breaks", ["date"]),
          "share": db("select code, date from qa_share_breaks", ["date"]),
          "split": db("select code, listing_date as date from stock_splits", ["date"]).dropna(),
          "rights": db("select code, recording_date as date from right_offerings", ["date"]).dropna()}
    span = pd.DataFrame({k: {"events": len(v), "first": v["date"].min(), "last": v["date"].max()}
                         for k, v in ev.items()}).T
    show(STEP, "corporate-action tables available for cross-checking", span)
    write(span, "a01_event_tables", STEP)

    cov = coverage(sd, r, traded, elig, last_date)
    show(STEP, "coverage by year", cov.round(0))
    write(cov, "a01_coverage_by_year", STEP)

    x = extreme_returns(sd, r, mcap, elig, ev)
    write(x, "a01_extreme_returns", STEP, index=False)
    by = x.groupby("class").agg(n=("r", "size"), negative=("r", lambda s: (s < 0).sum()),
                                below_minus50=("r", lambda s: (s < -0.5).sum()),
                                eligible_stock=("eligible_prev_month_end", "sum"),
                                max_index_weight=("weight", "max")).sort_values("n", ascending=False)
    show(STEP, f"{len(x)} daily returns beyond +/-{RET_LIMIT:.0%} since 2005, by class", by.round(3))
    write(by, "a01_extreme_returns_by_class", STEP)
    xs = x.groupby([x["date"].dt.year, "source"]).size().unstack(fill_value=0)
    show(STEP, "extreme returns by year and source", xs)
    write(xs, "a01_extreme_returns_by_year_source", STEP)
    show(STEP, "largest index-weighted cases", x.assign(impact_pp=100 * x["weight"] * x["r"]).sort_values(
        "impact_pp", key=abs, ascending=False).head(12)[["date", "code", "r", "weight", "impact_pp", "source", "class"]])

    sj = share_jumps(sd, ev)
    write(sj, "a01_share_jumps", STEP, index=False)
    show(STEP, f"{len(sj)} share-count jumps beyond {SHARE_JUMP}x since 2005, by class",
         sj.groupby("class").agg(n=("code", "size"), codes=("code", "nunique")).sort_values("n", ascending=False))

    close = sd.pivot(index="date", columns="code", values="close").reindex(index=r.index, columns=r.columns)
    known = sd["source"].isin(["stockdb", "idx"])
    nominal = sd.assign(nom=(sd["close"] / sd["price_scale"]).where(known)).pivot(
        index="date", columns="code", values="nom").reindex(index=r.index, columns=r.columns)
    wf = waterfall(r, traded, mcap, close, nominal, elig)
    write(wf, "a01_eligibility_waterfall", STEP)
    dec = wf[wf.index.month == 12]
    dec.index = dec.index.year
    show(STEP, "eligibility waterfall at December month-ends", dec.round(2))
    log_mismatch = int((wf["+size"] != wf["eligible_pkl"]).sum())
    show(STEP, "waterfall totals", pd.Series({
        "months where audit count != eligible_monthly.pkl": log_mismatch,
        "stock-months wrongly in (nominal price <= floor)": wf["adj>50_nominal<=50 (wrongly in)"].sum(),
        "stock-months wrongly out (nominal price > floor)": wf["adj<=50_nominal>50 (wrongly out)"].sum(),
        "eligible stock-months with no year-end market cap": wf["eligible_with_no_year_end_mcap"].sum(),
        "eligible stock-months failing size cut if market cap carried forward":
            wf["eligible_failing_size_if_mcap_carried"].sum(),
        "eligible stock-months in total": wf["+size"].sum()}).to_frame("value"))

    sv, h = survivorship(sd, last_date, f.index[-1])
    write(sv, "a01_delistings", STEP)
    show(STEP, "codes that stop trading before the sample end, or are on the delisting list", sv)
    show(STEP, "holdings that received the delisting return", h.groupby("portfolio").size().to_frame("n").T
         if len(h) else pd.DataFrame({"n": [0]}))
    write(h, "a01_delist_return_holdings", STEP, index=False)


if __name__ == "__main__":
    main()
