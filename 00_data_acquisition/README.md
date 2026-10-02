# Step 00 — Data acquisition

Two source versions (config `DB_VERSION`, default **`v2`**; override with env `ZCAPM_DB=v1`). Each version has its own
`data/raw*`, `interim*`, `processed*`, `outputs/tables*`, `outputs/figures*` folders, so runs never overwrite each other.

| | v1 (`ZCAPM_DB=v1`) | **v2 = dbv2 (default)** |
|---|---|---|
| Source | `../_arcip/idx-api` SQLite | v1 DB (`idx_data.sqlite`) **+ STOCKDB** (`G:/My Drive/QUANT/STOCKDB/databases`) |
| Prices | idx 2020-01-02 → 2026-06-30, Yahoo 2005–2019 | STOCKDB where it has the code (a handful of codes from 1990; broad coverage from 2012), v1 before/after. 2005–2011 is still over 90% Yahoo rows |
| Database | `idx_data.sqlite` | `dbv2.sqlite` |
| Pipeline files | `data/raw/` | `data/raw_v2/` |
| Script | `run.py` (with `ZCAPM_DB=v1`) | `run.py` → `fetch_stockdb.py` + `build_dbv2.py` |

`idx_data.sqlite`, `data/raw/` and the STOCKDB `.db` files are never written by the v2 path.

## v1 (idx-api)

Source: `../_arcip/idx-api` SQLite (`_arcip/idx-api/data/database.sqlite`, opened read-only). Two feeds live in it:
`idx` (idx.co.id daily summaries, 2020-01-02 → 2026-06-30) and `yahoo` (`backfill_2005_2019.py`, 2005–2019, rows with id ≥ 10,000,000).

- Inputs: idx-api tables `stock_summary`, `index_summary`, `company_dividend`, `company_delisting`, `financial_ratio`, `stock_split`, `right_offering`; `data/external/rf.csv` (manual)
- Outputs:
  - `00_data_acquisition/idx_data.sqlite` — cleaned tables `stock_daily` (with `source`, `price_scale`), `index_daily`, `dividends` (with `source`), `delistings`, `ratios`, `stock_splits`, `right_offerings`, plus QA tables `qa_boundary`, `qa_dropped_days`, `qa_coverage`, `meta`
  - `data/raw/stock_daily.csv.gz`, `index_daily.csv`, `dividends.csv`, `delistings.csv`, `ratios.csv` (pipeline contract)
- Scripts: `run.py` (idx-api SQLite → cleaned DB + canonical CSV); `backfill_2005_2019.py` (Yahoo backfill into idx-api DB); `sync_idx_history.ts` (Deno history sync, state in `batches/`); `make_synthetic.py` (test data)

Cleaning in `run.py` (yahoo rows only):
1. Yahoo prices are adjusted for later splits/rights while `listed_shares` is the 2020 count → each code is rescaled by
   k = first IDX `previous` / last Yahoo close (prices, dividends ×k; volume ÷k). Codes with k outside [0.1, 1000] lose their Yahoo history (BCIC, BNBR).
2. Yahoo holiday padding (days with no stock traded, 89 days) dropped from stocks and IHSG.
3. Yahoo dividends within ±10 days of an IDX dividend for the same code dropped (2017–2019 overlap).

Known gaps: 2005–2019 only covers codes still listed in 2020 (survivorship bias); `listed_shares` is constant before 2020;
IDX-feed dividends (2020+) are ~100/yr vs ~350/yr before.

## v2 — dbv2 (v1 + STOCKDB)

`fetch_stockdb.py` flattens the 951 per-ticker STOCKDB SQLite files (read-only) into `stockdb/`: `stock_info.csv`,
`prices.csv.gz`, `key_ratios.csv.gz`, `financial_normalized.csv.gz`, `fetch_log.csv`.
`build_dbv2.py` merges that with `idx_data.sqlite` into `dbv2.sqlite` (stock_daily, index_daily, dividends, delistings,
ratios, stock_splits, right_offerings, stock_info, key_ratios, financial_normalized, QA tables, meta) and writes the
pipeline contract files to `data/raw_v2/` (same columns as v1).

**Rule: where both sources have a value for the same code/date, STOCKDB wins.** Concretely, per code:
1. Inside the STOCKDB date span only STOCKDB rows are used (v1 rows there are ignored: 1.86M rows; STOCKDB has the trading
   days, v1 adds only zero-volume padding and ~37k trades STOCKDB lacks). v1 supplies rows before the first STOCKDB date
   (rescaled to the STOCKDB level at the first common date) and after the last (chained with v1's own `close/previous − 1`).
   Codes absent from STOCKDB prices (92) keep their v1 rows.
2. STOCKDB closes are raw. **Glitch rows** (a spike or dip ≥ 1.6× that reverts to the old level within 3 rows, e.g. 5× on the
   2014-07-09 holiday) are dropped (102 rows). **Split-like jumps** (one-day ratio ≈ 1/k or k, k from common IDX ratios,
   tol 10%) are back-adjusted so the series is continuous on the basis of the last STOCKDB segment, i.e. STOCKDB as given
   (127 splits, 9 reverse, 12 unexplained |jump| > 2× left untouched; table `qa_price_breaks`). `previous` = prior dbv2 close.
3. `listed_shares` = STOCKDB `key_ratios.share_outstanding` (point-in-time, quarterly, forward-filled from period end, split-normalised
   by detecting share-count jumps ≈ k). Because STOCKDB share counts and prices are not always on the same split basis,
   each run of equal share counts is compared with v1 market cap on common dates: ratio 0.6–1.67 → keep STOCKDB
   (real issuance); ratio ≈ k or 1/k → STOCKDB shares rescaled by the split ratio (154 codes); otherwise STOCKDB share data
   judged bad → v1-implied shares (76 codes). After the STOCKDB span: v1 market cap / dbv2 close. 10 STOCKDB-only codes with no
   share count anywhere are excluded (`qa_excluded_codes`).
4. `ratios.csv` (pbv for HML) come from STOCKDB `key_ratios` (35k rows vs 633 in v1); dividends, IHSG, delistings from v1
   (STOCKDB has none); dividends are rescaled to the dbv2 price basis.

Limits: `close` is split-adjusted to the latest basis. `stock_daily.csv.gz` carries `price_scale` (adjusted / nominal close) for STOCKDB and idx
rows, so step 01 applies the Rp 50 floor (`MIN_PRICE`) to the nominal price; Yahoo rows have no factor and use the adjusted price. `volume` is as reported (only `> 0` is used). STOCKDB rows have no `remarks`. Vendor series are
sometimes partly adjusted with the break dated before the true ex-date (e.g. BBCA 2019-09-19), which is why shares are
calibrated against v1; a few tickers (TMAS, KOPI, APIC) still show mcap jumps because the two sources' prices disagree.
Validation vs v1 on common traded rows (2.24M): daily return within 0.5% on 99.0%; market cap ratio within 0.8–1.25 on 95%.
Prices end 2025-10-10 for STOCKDB; 2025-10-11 → 2026-06-30 comes from v1.
