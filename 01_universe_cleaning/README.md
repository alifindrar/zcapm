# Step 01 — Universe & returns

- Inputs: `data/raw*/stock_daily.csv.gz`, `dividends.csv`, `delistings.csv`; `data/external/delistings_extra.csv`
- Outputs (`data/interim*/`): `returns_daily.pkl`, `traded_daily.pkl`, `mcap_daily.pkl`, `returns_monthly.pkl`,
  `last_date.pkl`, `eligible_monthly.pkl`, `delist_return.pkl`, `susp_monthly.pkl`
- Review files: `cleaning_log.csv` (counts), `returns_flagged.csv` (every return removed by the screen at
  ±(`RET_LIMIT` + `RET_TOL`) = ±37%, with class; `revert` = the move that undoes a screened level shift),
  `share_jumps.csv` (share-count jumps beyond 1.5×, not changed), `delistings_status.csv` (delisting return per code,
  codes that stop trading without being on the list, listed delistings with no price data)
- Suspension: `susp_monthly.pkl` holds, for a month with no trade, the return of a holder who cannot sell (last traded
  close before the month to the first traded close after it; the delisting return if it never trades again). Steps
  04/06/07 pass it to `holding_returns`. A stock with no trade in the last `BUY_TRADE_ROWS` rows before T is not eligible.
- Scripts: `run.py`; the return screen is `lib/cleaning.py`. Spec: step.md §2 Step 01
