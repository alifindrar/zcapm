# Step 01 — Universe & returns

- Inputs: `data/raw*/stock_daily.csv.gz`, `dividends.csv`, `delistings.csv`; `data/external/delistings_extra.csv`
- Outputs (`data/interim*/`): `returns_daily.pkl`, `traded_daily.pkl`, `mcap_daily.pkl`, `returns_monthly.pkl`,
  `last_date.pkl`, `eligible_monthly.pkl`, `delist_return.pkl`
- Review files: `cleaning_log.csv` (counts), `returns_flagged.csv` (every return removed by the ±35% screen, with class),
  `share_jumps.csv` (share-count jumps beyond 1.5×, not changed), `delistings_status.csv` (delisting return per code,
  codes that stop trading without being on the list, listed delistings with no price data)
- Scripts: `run.py`; the return screen is `lib/cleaning.py`. Spec: step.md §2 Step 01
