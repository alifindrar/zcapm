"""Step 08 - Rp 30 m top-10 Z* basket: lot-level account simulation, monthly reports and the live starting order sheet.

Selection is the 06c rule (06_evaluation/topn_backtest.py --top-mcap 200 --min-adv 10e9): market-cap rank <= 200,
Z* top quintile in >= 2 of the 3 previous formation months, ADV (60d) >= Rp 10 bn, trades >= 90% of the last 60 days, beta <= 2, p >= 0.6,
n_obs >= 200; the 10 highest Z*, equal weight, formed at month-end T and held T -> T+1.

Account mechanics (what the percentage backtest ignores):
- Rp CAPITAL at the first formation date, cash earns nothing, dividends are reinvested through the total return.
- At each T the account is rebalanced to equal weight at T's close in whole IDX lots (100 shares); leftover is cash.
- Costs (Stockbit): COST_BUY on buys, COST_SELL on sells, charged on the traded value, plus STAMP_DUTY when the
  rebalance day's total buy + sell value is above STAMP_DUTY_MIN.
- A pick with no trade on T cannot be bought: the next-ranked eligible stock takes its slot.
- A holding with no trade on T cannot be sold: it is carried unchanged (frozen) until it trades again.
- Position values move with the step 01 holding return (delisting and suspension handling included); a delisted
  position is cashed out at its delisting value at the next T.

Outputs (08_basket/): reports/YYYY-MM.md per holding month, nav.csv, trades.csv, holdings.csv, README.md (summary and
index) and start_YYYY-MM.md (fresh-capital order sheet for the next month, sized at the latest close).

Entry prices: a limit buy at the latest close minus k x ATR(14) (average daily true range as a share of the previous
close, from dbv2 OHLC), rounded down to the IDX tick, and good for ENTRY_DAYS sessions; whatever is unfilled is bought
at the close of the last session. k is the value that gave the lowest average entry price, relative to buying at the
first session's open, over every new position in the simulation (entry_study.csv).
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import load, to_markdown  # noqa: E402
from lib.portfolios import holding_returns  # noqa: E402

STEP = "08"
N, TOP_MCAP, MIN_ADV, LOT = 10, 200, 10e9, 100
CAPITAL = 30e6
ENTRY_KS, ENTRY_DAYS = (0.0, 0.25, 0.5, 0.75, 1.0), 3
FIRST = pd.Period(sys.argv[1] if len(sys.argv) > 1 else "2016-02", "M")   # first holding month
OUT = ROOT / "08_basket"
BUFFER = 0.004      # slot budget haircut so lot rounding plus costs never overdraws cash


def rp(x):
    return f"{x:,.0f}"


def main():
    est = load(S.INTERIM / "zcapm_estimates.pkl")
    rm = load(S.INTERIM / "returns_monthly.pkl")
    mc = load(S.INTERIM / "mcap_daily.pkl")
    tr = load(S.INTERIM / "traded_daily.pkl")
    ld = load(S.INTERIM / "last_date.pkl")
    dl = load(S.INTERIM / "delist_return.pkl")
    susp = load(S.INTERIM / "susp_monthly.pkl")
    agg = load(S.PROCESSED / "aggregates_monthly.pkl")
    data_end = load(S.INTERIM / "factors_daily.pkl").index[-1]
    sd = pd.read_csv(S.RAW / "stock_daily.csv.gz", usecols=["date", "code", "close", "value", "listed_shares",
                                                           "price_scale"], parse_dates=["date"])
    # orders are placed at the nominal (traded) price; `close` is on the adjusted basis (close / price_scale = nominal)
    sd["nominal"] = sd.close / sd.price_scale.where(sd.price_scale > 0).fillna(1.0)
    val = sd.pivot_table(index="date", columns="code", values="value").reindex(mc.index)
    px = sd.pivot_table(index="date", columns="code", values="nominal").reindex(mc.index)
    adv = val.rolling(60, min_periods=40).mean()
    tr60 = tr.rolling(60, min_periods=40).mean()

    Ts = sorted(est["T"].unique())
    est = est.set_index(["T", "code"])
    q = {T: est.loc[T, "zstar"].rank(pct=True) >= 0.8 for T in Ts}

    def candidates(i, T):
        """Top-TOP_MCAP universe at T and its filtered candidates ranked by Z* (all of them, not just the top N).
        Market cap is step 01's (adjusted close x calibrated shares = the IDX market cap); only orders use the
        nominal price."""
        e = est.loc[T]
        e = e[e.zstar.notna()].copy()
        row = mc.index[mc.index <= T][-1]
        e["mcap_rank"] = mc.loc[row].rank(ascending=False).reindex(e.index)
        e["persist"] = sum(q[t].reindex(e.index).fillna(False).astype(int) for t in Ts[i - 3:i])
        e["adv_bn"], e["tr60"] = adv.loc[row].reindex(e.index) / 1e9, tr60.loc[row].reindex(e.index)
        big = e[e.mcap_rank <= TOP_MCAP]
        c = big[(big.persist >= 2) & (big.adv_bn >= MIN_ADV / 1e9) & (big.tr60 >= .9) & (big.beta <= 2)
                & (big.p >= .6) & (big.n_obs >= 200)].sort_values("zstar", ascending=False)
        return big, c, row

    def size(budget, price):
        return int(budget // (price * LOT)) * LOT if price > 0 else 0

    cash, pos = CAPITAL, {}          # pos: code -> {"value", "shares", "cost"} (cost = Rp paid incl. fees, for P&L)
    nav_rows, trade_rows, hold_rows, reports = [], [], [], []
    OUT.joinpath("reports").mkdir(parents=True, exist_ok=True)
    rf, mkt = agg["Rf"], agg["M"]

    for i, T in enumerate(Ts):
        m1 = T.to_period("M") + 1
        if i < 3 or m1 < FIRST or m1 > Ts[-1].to_period("M") or m1 not in rm.index:
            continue
        big, c, row = candidates(i, T)
        p_t, traded = px.loc[row], tr.loc[row]
        nav0 = cash + sum(h["value"] for h in pos.values())

        # 1. cash out delisted positions, freeze untradeable ones
        notes, trades = [], []
        for k in list(pos):
            if ld.get(k, data_end) <= T and ld.get(k, data_end) < data_end - pd.Timedelta(days=10):
                cash += pos[k]["value"]
                trades.append(dict(code=k, action="DELISTED", shares=-pos[k]["shares"], price=np.nan,
                                   value=pos[k]["value"], fee=0.0))
                notes.append(f"{k} delisted; cashed out at Rp {rp(pos[k]['value'])}.")
                del pos[k]
        frozen = {k for k in pos if not bool(traded.get(k, False))}
        for k in sorted(frozen):
            notes.append(f"{k} did not trade on {row.date()}; position carried unchanged.")

        # 2. pick N tradeable names
        pick, skipped = [], []
        for k in c.index:
            if len(pick) == N:
                break
            if k in frozen or (bool(traded.get(k, False)) and p_t.get(k, np.nan) > 0):
                pick.append(k)
            else:
                skipped.append(k)
        if skipped:
            notes.append(f"Skipped (no trade on {row.date()}): {', '.join(skipped)}.")

        # 3. rebalance: sells first, then buys, whole lots at T's close
        pool = cash + sum(h["value"] for k, h in pos.items() if k not in frozen) - S.STAMP_DUTY   # duty reserved
        slots = [k for k in pick if k not in frozen]
        budget = pool / max(len(slots), 1) * (1 - BUFFER)
        target = {k: size(budget, p_t[k]) for k in slots}
        for k in [k for k in pos if k not in frozen]:
            price, h = p_t[k], pos[k]
            cur_sh = h["value"] / price
            tgt_sh = target.get(k, 0)
            if tgt_sh * price < h["value"] - 0.5 * LOT * price:       # sell down (or out) by at least half a lot
                sell = h["value"] - tgt_sh * price
                fee = sell * S.COST_SELL
                cash += sell - fee
                trades.append(dict(code=k, action="SELL" if tgt_sh == 0 else "TRIM",
                                   shares=-round(cur_sh - tgt_sh), price=price, value=sell, fee=fee))
                h["cost"] *= tgt_sh * price / h["value"]
                h["value"], h["shares"] = tgt_sh * price, tgt_sh
                if tgt_sh == 0:
                    del pos[k]
        for k in slots:
            price, tgt_sh = p_t[k], target[k]
            h = pos.get(k)
            cur = h["value"] if h else 0.0
            buy = tgt_sh * price - cur
            if buy <= 0.5 * LOT * price:                               # hold (drift within half a lot)
                if h:
                    h["shares"] = round(h["value"] / price)
                continue
            fee = buy * S.COST_BUY
            if buy + fee > cash - S.STAMP_DUTY:                         # rounding guard: one lot fewer
                tgt_sh -= LOT
                buy = tgt_sh * price - cur
                fee = buy * S.COST_BUY
                if buy <= 0:
                    continue
            cash -= buy + fee
            trades.append(dict(code=k, action="ADD" if h else "BUY", shares=round(buy / price), price=price,
                               value=buy, fee=fee))
            pos[k] = {"value": tgt_sh * price, "shares": tgt_sh, "cost": (h["cost"] if h else 0.0) + buy + fee}
        if sum(t["value"] for t in trades if t["action"] != "DELISTED") > S.STAMP_DUTY_MIN:   # one confirmation
            cash -= S.STAMP_DUTY
            trades.append(dict(code="-", action="STAMP", shares=0, price=np.nan, value=0.0, fee=float(S.STAMP_DUTY)))
        nav1 = cash + sum(h["value"] for h in pos.values())
        fees = sum(t["fee"] for t in trades)

        # 4. hold through m1
        codes = list(pos)
        r = holding_returns(pd.Index(codes), m1, rm, ld, data_end, dl, susp)
        r = pd.Series(np.asarray(r, dtype=float), index=codes)
        hold = []
        for k in codes:
            h = pos[k]
            v0 = h["value"]
            h["value"] = v0 * (1 + r[k])
            meta = c.loc[k] if k in c.index else big.loc[k] if k in big.index else None
            hold.append(dict(code=k, rank=pick.index(k) + 1 if k in pick else np.nan, frozen=k in frozen,
                             shares=h["shares"], price_T=p_t.get(k, np.nan), value_start=v0,
                             weight_pct=100 * v0 / nav1, return_pct=100 * r[k], pnl=h["value"] - v0,
                             value_end=h["value"],
                             zstar=np.nan if meta is None else meta["zstar"],
                             beta=np.nan if meta is None else meta["beta"],
                             p=np.nan if meta is None else meta["p"],
                             mcap_rank=np.nan if meta is None else meta["mcap_rank"]))
        nav2 = cash + sum(h["value"] for h in pos.values())
        ew = float(holding_returns(big.index, m1, rm, ld, data_end, dl, susp).mean())
        nav_rows.append(dict(month=str(m1), formed=row.date(), nav_start=nav0, fees=fees, nav_after_trades=nav1,
                             cash=cash, n_hold=len(codes), nav_end=nav2, ret_pct=100 * (nav2 / nav0 - 1),
                             ew_univ_pct=100 * ew, market_pct=100 * mkt.get(m1, np.nan),
                             rf_pct=100 * rf.get(m1, np.nan)))
        for t in trades:
            trade_rows.append(dict(month=str(m1), date=row.date(), **t))
        for h in hold:
            hold_rows.append(dict(month=str(m1), **h))
        reports.append((m1, row, nav0, nav1, nav2, cash, fees, trades, hold, notes, nav_rows[-1]))

    nav = pd.DataFrame(nav_rows)
    nav["value_idx"] = 100 * nav.nav_end / CAPITAL
    nav["drawdown_pct"] = 100 * (nav.nav_end / np.maximum(nav.nav_end.cummax(), CAPITAL) - 1)
    trades = pd.DataFrame(trade_rows)
    holds = pd.DataFrame(hold_rows)

    for m1, row, nav0, nav1, nav2, cash_m, fees, tr_m, hold, notes, nr in reports:
        write_report(m1, row, nav0, nav1, nav2, cash_m, fees, tr_m, hold, notes, nr,
                     nav.loc[nav.month == str(m1)].iloc[0])

    nav.to_csv(OUT / "nav.csv", index=False)
    trades.to_csv(OUT / "trades.csv", index=False)
    holds.to_csv(OUT / "holdings.csv", index=False)

    # live order sheet: fresh capital into the basket formed at the last T, sized at the latest close
    i, T = len(Ts) - 1, Ts[-1]
    big, c_all, row = candidates(i, T)
    last = px.index[px.notna().any(axis=1)][-1]
    ok = [k for k in c_all.index if bool(tr.loc[row].get(k, False))]
    c = c_all.loc[ok]
    skipped = [k for k in c_all.index[:N + 3] if k not in ok]
    ohlc = load_ohlc()
    study, k_best = entry_study(trades, ohlc)
    study.to_csv(OUT / "entry_study.csv", index=False)
    write_start(T.to_period("M") + 1, row, last, c, px.loc[row], px.loc[last], skipped, ohlc, k_best, study,
                set(holds.loc[holds.month == holds.month.iloc[-1], "code"]) if len(holds) else set())

    write_readme(nav, trades, study, k_best)
    pd.set_option("display.width", 200)
    print(nav.round(2).tail(15).to_string(index=False))
    print(f"\nFinal NAV Rp {rp(nav.nav_end.iloc[-1])} from Rp {rp(CAPITAL)} ({nav.month.iloc[0]}..{nav.month.iloc[-1]})")


def stats(r, rf):
    r = r.dropna()
    v = (1 + r).cumprod()
    return {"months": len(r), "total_%": 100 * (v.iloc[-1] - 1), "CAGR_%": 100 * (v.iloc[-1] ** (12 / len(r)) - 1),
            "ann_vol_%": 100 * r.std() * np.sqrt(12),
            "sharpe": (r - rf.reindex(r.index)).mean() / r.std() * np.sqrt(12),
            "max_DD_%": 100 * (v / v.cummax().clip(lower=1) - 1).min(), "worst_month_%": 100 * r.min(),
            "hit_%": 100 * (r > 0).mean()}


def write_report(m1, row, nav0, nav1, nav2, cash, fees, trades, hold, notes, nr, navrow):
    L = [f"# Basket report {m1}", "",
         f"Top-{N} Z* basket, top-{TOP_MCAP} market cap, equal weight. Rebalanced at the close of {row.date()}, "
         f"held through {m1}.", "",
         "| | Rp |", "|---|---:|",
         f"| NAV before rebalance | {rp(nav0)} |", f"| Trading fees | {rp(fees)} |",
         f"| NAV after rebalance | {rp(nav1)} |", f"| Cash after rebalance | {rp(cash)} |",
         f"| NAV at end of {m1} | {rp(nav2)} |", "",
         f"**Month return:** {nr['ret_pct']:+.2f}% (EW top-{TOP_MCAP}: {nr['ew_univ_pct']:+.2f}%, market: "
         f"{nr['market_pct']:+.2f}%). **Since start:** {navrow['value_idx'] - 100:+.1f}% "
         f"(drawdown {navrow['drawdown_pct']:.1f}%).", ""]
    if notes:
        L += ["**Notes:** " + " ".join(notes), ""]
    L += [f"## Orders at {row.date()} close", ""]
    if trades:
        t = pd.DataFrame(trades)
        t["lots"] = (t.shares / LOT).round(1)
        t = t[["code", "action", "lots", "shares", "price", "value", "fee"]]
        L += [to_markdown(t.assign(value=t.value.map(rp), fee=t.fee.map(rp), price=t.price.map(
            lambda x: "" if pd.isna(x) else rp(x))).set_index("code")), ""]
    else:
        L += ["No trades.", ""]
    L += [f"## Holdings for {m1}", ""]
    h = pd.DataFrame(hold).sort_values(["rank"], na_position="last")
    h["lots"] = h.shares / LOT
    out = pd.DataFrame({"rank": h["rank"].map(lambda x: "frozen" if pd.isna(x) else int(x)),
                        "code": h.code, "lots": h.lots.map(lambda x: f"{x:,.0f}"), "price_T": h.price_T.map(rp),
                        "value_start": h.value_start.map(rp), "weight_%": h.weight_pct.round(1),
                        "return_%": h.return_pct.round(2), "P&L": h.pnl.map(rp), "value_end": h.value_end.map(rp),
                        "zstar": h.zstar.round(3), "beta": h.beta.round(2), "p": h.p.round(2),
                        "mcap_rank": h.mcap_rank.map(lambda x: "" if pd.isna(x) else int(x))})
    L += [to_markdown(out.set_index("rank")), ""]
    (OUT / "reports" / f"{m1}.md").write_text("\n".join(L), encoding="utf-8")


def tick(price):
    """IDX price fraction for a stock at `price`."""
    return 1 if price < 200 else 2 if price < 500 else 5 if price < 2000 else 10 if price < 5000 else 25


def load_ohlc():
    """Daily OHLC (dbv2 basis, continuous across splits) and ATR(14) as a share of the previous close."""
    con = sqlite3.connect(ROOT / "00_data_acquisition" / "dbv2.sqlite")
    d = pd.read_sql("select date, code, open, high, low, close from stock_daily where date >= '2015-01-01'", con,
                    parse_dates=["date"])
    d[["open", "high", "low", "close"]] = d[["open", "high", "low", "close"]].where(d[["open", "high", "low",
                                                                                     "close"]] > 0)  # 0 = no trade
    o = {c: d.pivot_table(index="date", columns="code", values=c) for c in ("open", "high", "low", "close")}
    pc = o["close"].shift(1)
    true_range = np.maximum(o["high"], pc) - np.minimum(o["low"], pc)
    o["atr"] = (true_range / pc).rolling(14, min_periods=10).mean()
    return o


def entry_study(trades, o):
    """Average entry cost of the limit rule for each k over the simulation's new positions (BUY orders)."""
    idx, cols = o["close"].index, o["close"].columns
    res = {k: [] for k in ENTRY_KS}
    for t in trades[trades.action == "BUY"].itertuples():
        d = pd.Timestamp(t.date)
        if t.code not in cols or d not in idx:
            continue
        i = idx.get_loc(d)
        if i + ENTRY_DAYS >= len(idx):
            continue
        ref, atr = o["close"].at[d, t.code], o["atr"].at[d, t.code]
        days = idx[i + 1:i + 1 + ENTRY_DAYS]
        op, lo, cl = (o[c].loc[days, t.code].to_numpy() for c in ("open", "low", "close"))
        if np.isnan([ref, atr]).any() or np.isnan(op).any() or np.isnan(lo).any() or np.isnan(cl[-1]):
            continue
        for k in ENTRY_KS:
            lim, fill = ref * (1 - k * atr), None
            for j in range(ENTRY_DAYS):
                if op[j] <= lim:
                    fill = op[j]
                    break
                if lo[j] <= lim:
                    fill = lim
                    break
            res[k].append((fill is not None, (fill if fill is not None else cl[-1]) / op[0] - 1))
    rows = []
    for k, v in res.items():
        f = np.array([x[0] for x in v]); c = np.array([x[1] for x in v])
        rows.append({"k": k, "orders": len(v), "filled_%": 100 * f.mean(), "avg_cost_%": 100 * c.mean(),
                     "median_cost_%": 100 * np.median(c),
                     "avg_cost_if_unfilled_%": 100 * c[~f].mean() if (~f).any() else np.nan})
    study = pd.DataFrame(rows).round(2)
    return study, float(study.loc[study["avg_cost_%"].idxmin(), "k"])


def write_start(m, row, last, c, p_t, p_last, skipped, o, k_best, study, prev):
    """Fresh-capital order sheet: the first N tradeable candidates with limit prices, plus three alternates."""
    budget = CAPITAL / max(min(N, len(c)), 1) * (1 - BUFFER)   # fewer than N candidates: equal weight, as in the simulation
    rows, spent, locked = [], float(S.STAMP_DUTY if CAPITAL > S.STAMP_DUTY_MIN else 0), []
    for rank, (k, e) in enumerate(c.head(N + 3).iterrows(), 1):
        price = p_last.get(k, np.nan)
        atr = o["atr"][k].loc[:last].dropna().iloc[-1] if k in o["atr"] else np.nan
        lim = price * (1 - k_best * atr) if pd.notna(atr) else price
        lim = np.floor(lim / tick(lim)) * tick(lim)
        hist = pd.DataFrame({x: o[x][k].loc[:last] for x in ("high", "low", "close")}).dropna().tail(15)
        r = hist.close.pct_change()
        streak = 0
        for j in range(len(hist) - 1, 0, -1):
            if hist.high.iloc[j] == hist.low.iloc[j] and abs(r.iloc[j]) >= 0.09:
                streak += 1
            else:
                break
        note = ""
        if streak:
            note = f"locked limit-{'down' if r.iloc[-1] < 0 else 'up'} {streak} session{'s' if streak > 1 else ''}"
            if rank <= N:
                locked.append(f"{k} ({note})")
        sh = int(budget // (price * LOT)) * LOT if rank <= N else 0
        val = sh * price
        spent += val * (1 + S.COST_BUY)
        rows.append({"rank": rank if rank <= N else f"alt {rank - N}", "code": k,
                     "vs_sim_Sep": "held" if k in prev else "new",
                     f"px_{row.date()}": rp(p_t.get(k)), f"px_{last.date()}": rp(price),
                     "ATR_%": round(100 * atr, 1), "limit": rp(lim), "below_%": round(100 * (lim / price - 1), 1),
                     "lots": sh // LOT if rank <= N else "", "value_at_close": rp(val) if rank <= N else "",
                     "weight_%": round(100 * val / CAPITAL, 1) if rank <= N else "",
                     "zstar": round(e.zstar, 3), "beta": round(e.beta, 2), "p": round(e.p, 2),
                     "mcap_rank": int(e.mcap_rank), "adv_bn": round(e.adv_bn, 1), "note": note})
    t = pd.DataFrame(rows).set_index("rank")
    sb = study.set_index("k")
    short = f" Only {len(c)} stocks pass the filters this month, so the capital is split {len(c)} ways." if len(c) < N else ""
    L = [f"# Starting order sheet - {m}", "",
         f"Fresh Rp {rp(CAPITAL)} into the top-{N} Z* basket formed at {row.date()} (top-{TOP_MCAP} market cap, "
         f"equal weight, rebalance at each month-end).{short} Prices are nominal (traded) prices; lots are sized at the "
         f"{last.date()} close with a {100 * BUFFER:.1f}% haircut so fees fit. Re-check prices before placing orders.",
         "", "## Entry rule", "",
         f"Place a limit buy at **limit** (the {last.date()} close minus {k_best:g} x ATR(14), rounded down to the "
         f"IDX tick) for {ENTRY_DAYS} sessions. Whatever is still unfilled after session {ENTRY_DAYS}, buy at market "
         "at that session's close. Do not skip the name: missing a pick costs more than a few ticks.", "",
         f"Over {int(sb.loc[k_best, 'orders'])} historical entries this rule filled "
         f"{sb.loc[k_best, 'filled_%']:.0f}% of the time and cost {sb.loc[k_best, 'avg_cost_%']:+.2f}% on average "
         "against simply buying at the first open, so it mainly guards against paying up on a gap. Deeper limits "
         f"(k = 0.5) save {-sb.loc[0.5, 'median_cost_%']:.1f}% on a typical fill but fill only "
         f"{sb.loc[0.5, 'filled_%']:.0f}% of the time, and the names that run away cost "
         f"{sb.loc[0.5, 'avg_cost_if_unfilled_%']:+.1f}% when bought later, so on average waiting below the market "
         "does not pay. The full table is in README.md.", "",
         "## Orders", "", to_markdown(t), "",
         "| | Rp |", "|---|---:|",
         f"| Invested at the {last.date()} close incl. buy fees ({100 * S.COST_BUY:.2f}%) and stamp duty | "
         f"{rp(spent)} |",
         f"| Cash left | {rp(CAPITAL - spent)} |", ""]
    if locked:
        L += [f"**Locked at the price limit:** {'; '.join(locked)}. Open, high, low and close were equal, so the "
              "stock only traded at the auto-rejection limit. A limit order may not fill until the lock breaks; "
              f"the rule still applies (buy at the close of session {ENTRY_DAYS} if unfilled).", ""]
    if skipped:
        L += [f"**Skipped:** {', '.join(skipped)} did not trade on {row.date()} (rule: an untradeable pick gives its "
              "slot to the next-ranked name).", ""]
    L += ["Next rebalance: after the last trading day of the month, once step 03 has run on month-end data. "
          "Sell names that drop out, buy the new ones and re-size everything to equal weight in whole lots.", ""]
    (OUT / f"start_{m}.md").write_text("\n".join(L), encoding="utf-8")


def write_readme(nav, trades, study, k_best):
    agg = load(S.PROCESSED / "aggregates_monthly.pkl")
    r = pd.Series(nav.ret_pct.values / 100, index=pd.PeriodIndex(nav.month, freq="M"))
    e3 = pd.Series(nav.ew_univ_pct.values / 100, index=r.index)
    mk = pd.Series(nav.market_pct.values / 100, index=r.index)
    rf = agg["Rf"]
    rows = {}
    for label, start in (("full", r.index[0]), ("10y", pd.Period("2016-10", "M")), ("5y", pd.Period("2021-10", "M")),
                         ("3y", pd.Period("2023-10", "M")), ("1y", pd.Period("2025-10", "M")),
                         ("2026 YTD", pd.Period("2026-01", "M"))):
        for name, s in ((f"Rp {CAPITAL / 1e6:.0f}m basket (net, lots)", r), (f"EW top-{TOP_MCAP} mcap", e3), ("Market (own VW)", mk)):
            if start >= r.index[0]:
                rows[(label, name)] = stats(s[s.index >= start], rf)
    st = pd.DataFrame(rows).T.round(2)
    st.index.names = ["window", "portfolio"]
    yr = pd.DataFrame({n: s.groupby(lambda p: p.year).apply(lambda x: 100 * ((1 + x.dropna()).prod() - 1))
                       for n, s in (("basket_%", r), (f"EW{TOP_MCAP}_%", e3), ("market_%", mk))}).round(1)
    yr["NAV_end_Rp"] = nav.groupby(r.index.year.values).nav_end.last().map(rp).values
    yr.index.name = "year"
    idx = nav[["month", "formed", "nav_start", "fees", "nav_end", "ret_pct", "ew_univ_pct", "market_pct",
               "drawdown_pct"]].copy()
    idx["report"] = idx.month.map(lambda m: f"[{m}](reports/{m}.md)")
    for col in ("nav_start", "fees", "nav_end"):
        idx[col] = idx[col].map(rp)
    idx = idx.round(2)[["report", "formed", "nav_start", "fees", "nav_end", "ret_pct", "ew_univ_pct", "market_pct",
                        "drawdown_pct"]].iloc[::-1]
    n_tr = trades[trades.action.isin(["BUY", "SELL", "ADD", "TRIM"])]
    starts = sorted(OUT.glob("start_*.md"))
    L = [f"# Step 08 - Rp {CAPITAL / 1e6:.0f} m top-{N} Z* basket", "",
         f"Account simulation of the top-{N} Z* rule (top-{TOP_MCAP} market cap, ADV >= Rp {MIN_ADV / 1e9:.0f} bn) with "
         f"Rp {rp(CAPITAL)} starting in {nav.month.iloc[0]}: "
         f"whole IDX lots, buy fee {100 * S.COST_BUY:.2f}%, sell fee {100 * S.COST_SELL:.2f}%, stamp duty "
         f"Rp {rp(S.STAMP_DUTY)} on a rebalance above Rp {S.STAMP_DUTY_MIN / 1e6:.0f} m (Stockbit), idle cash at 0%. "
         "See the docstring of `run.py` for the full rules. Rebuild with `python 08_basket/run.py [YYYY-MM]` "
         "(first holding month, default 2016-02).", "",
         f"**Live start:** " + ", ".join(f"[{p.stem}]({p.name})" for p in starts), "",
         f"**Result:** Rp {rp(CAPITAL)} -> Rp {rp(nav.nav_end.iloc[-1])} by end {nav.month.iloc[-1]}; "
         f"total fees Rp {rp(nav.fees.sum())} over {len(n_tr)} orders; max drawdown "
         f"{nav.drawdown_pct.min():.1f}%.", "",
         "Caution: the gain comes mostly from a few outlier years (see the annual table) and drawdowns are deep. "
         "Treat it as a high-risk satellite position.", "",
         "## Performance by window", "", to_markdown(st.reset_index()), "",
         "## Entry-price study", "",
         f"Every new position in the simulation, bought over the {ENTRY_DAYS} sessions after formation with a limit at "
         f"formation close - k x ATR(14), the rest at the last session's close. Cost is relative to buying at the "
         f"first session's open (negative = cheaper). Chosen k = {k_best:g}.", "", to_markdown(study.set_index("k")), "",
         "## Calendar years", "", to_markdown(yr.reset_index()), "",
         "## Monthly reports", "", to_markdown(idx.set_index("report")), ""]
    (OUT / "README.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
