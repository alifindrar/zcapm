# Changes made after the audit

Date: 2026-10-02. Responds to `AUDIT_REPORT.md` (findings F1–F14, decisions in its section 7).

**Status: the code is changed and tested on synthetic data. The real data has not been rerun**, because the price
databases were not available on the machine where the changes were made. `outputs/tables_v2` and
`outputs/audit_v2` still describe the run before these changes.

## Decisions

| # | Decision | Implemented as |
|---|---|---|
| 1 | Deciles as the headline sort | `SORT_SCHEME = "deciles"`; `ZCAPM_SCHEME=book24` runs the book scheme into `*_book24` folders |
| 2 | Zero-return threshold 35% | `MAX_ZERO_FRAC = 0.35`; `ZCAPM_ZERO=0.20` / `0.50` run the alternatives into `*_z20` / `*_z50` folders |
| 3 | 1-month bill yield as the risk-free rate | `02_market_factors/build_rf.py` → `data/external/rf.csv` (see "Open items") |
| 4 | Symmetric return screen with a reversal filter | `lib/cleaning.py`, called by step 01 |
| 5 | Delisted stocks | Delisting list wired into step 01 with reasons; prices not obtained (see "Open items") |

## What changed, by finding

| Finding | Change | Where |
|---|---|---|
| F1, F2 | Deciles by default. A formation month is skipped when any leg would hold fewer than 5 stocks | `config/settings.py`, `lib/portfolios.py` (`form_ls`), steps 04 and 07 |
| F3 | Zero-return threshold 20% → 35%, alternatives by environment variable | `config/settings.py` |
| F4 | Outside the first 5 rows of a code, a daily return beyond ±35% is removed in both directions. A move that returns to within 15% of the old level within 3 rows is a spike and the whole round trip is removed. Everything removed is listed in `returns_flagged.csv` | `lib/cleaning.py`, step 01 |
| F5 | `START_DATE` 2000 → 2005. The Yahoo years 2005–2011 are not replaced; the screen above removes their extreme returns | `config/settings.py` |
| F6 | Step 01 reads `delistings.csv` and `data/external/delistings_extra.csv` and reports listed delistings with no price data | step 01 (`delistings_status.csv`) |
| F7 | `rf.csv` is a short rate: the BI policy rate throughout (FRED to 2016-07, bi.go.id 7-day reverse repo rate from 2016-08), replaced by the 1-month bill yield from its first month once that file is supplied (see below). Mean 6.0% p.a. over 2007-04..2026-06, against 7.8% for the 10-year yield | `02_market_factors/build_rf.py` |
| F8 | Share-count jumps beyond 1.5× and days with one stock above 25% of the index are counted and listed. They are **not repaired** | step 01 (`share_jumps.csv`, `cleaning_log.csv`) |
| F9 | The 5% cap on g is kept and documented as a deviation from the book | `config/settings.py`, `step.md` |
| F10 | Z\* is stored and reported × 21 from step 04 on; the `0.01` offset in the g weight is applied on that scale | step 04, `lib/portfolios.py` (`g_weights`) |
| F11 | Delisting return per code: −30% for a forced or unclassified delisting, 0 for a voluntary delisting or merger, none for a code that stops trading without being on the list. Size cut uses the last market cap within 20 rows of the year end. Price floor uses the nominal price where `price_scale` is available | step 01, `build_dbv2.py` (exports `price_scale`) |
| F12 | No code change; documented | `step.md` |
| F13 | One cost rule for both scripts: turnover × (buy + sell), first month = one full purchase | `lib/portfolios.py` (`turnover_cost`), step 07, `long_only_backtest.py` |
| F14 | `step.md` and the READMEs corrected | docs |

Also: the long-only backtest buckets follow the scheme (deciles: top 10/20/30%, bottom 30%); the robustness
subperiods are 2005–2013, 2014–2019, 2020–; `make_synthetic.py` no longer overwrites `data/external/rf.csv`.

## Open items

1. **Rerun on the real data.** `build_dbv2.py` first (to export `price_scale`), then steps 01–07. Review
   `data/interim_v2/returns_flagged.csv` and `delistings_status.csv` before reading the tables.
2. **Risk-free rate from 2012-08.** Trading Economics sells the history of its 1-month bill series (it starts
   2012-08-16). Until `data/external/rf_idn1m_tradingeconomics.csv` is supplied, `rf.csv` is the BI policy rate
   for the whole sample. The series drops 1.25 points at 2016-08 (6.50 → 5.25), where BI changed its policy rate
   from the BI rate to the 7-day reverse repo rate; that is a change of definition, not an easing. Save the export
   under that name and rerun `build_rf.py`.
3. **Prices of delisted stocks.** Yahoo returns nothing for delisted IDX tickers (tested: CTRS, BRAU, DAJK, BORN,
   TURI). idx.co.id answers HTTP 403 (Cloudflare) from the machine used. The survivor-free route is the per-date IDX
   stock summary that `sync_idx_history.ts` already fetches, with a browser session in `.idx_session.json`; how far
   back IDX serves it is untested. No list of delistings before 2017 was found in a usable form.
4. **`delistings_extra.csv` needs checking.** The reasons (RMBA, TURI, MASA, MFIN voluntary; SCBD voluntary; FREN
   merger; APOL forced) and the three dates marked "approx" were entered from memory, not from IDX announcements.
5. **The audit scripts are written for the book scheme** (columns `L1..L12`). They run against
   `ZCAPM_ZERO=0.20 ZCAPM_SCHEME=book24` output folders only after `audit/common.py` is pointed at them, and would
   overwrite `outputs/audit_v2`.
6. **Share-count basis errors (F8)** are still in the market caps and so in the index weights.

## Test on synthetic data

`ZCAPM_DB=synth`, 300 stocks, 2011–2019, with three injected errors (a +80% spike that reverts, an unadjusted 1:2
split, a −45% level shift):

- the screen removed exactly the four affected returns, with classes `spike` (2), `split` (1), `other` (1);
- against the code before the changes, on the same data and the 20% threshold: 4 return cells differ (the injected
  ones), 0 eligibility cells differ, the market return differs on 4 days, Z\* correlation 0.9998;
- delisting returns: 0 for a code marked voluntary, −30% for listed codes, none for a code taken off the list;
- steps 01–07 and the long-only backtest run to the end under `deciles` and step 04 under `book24`.
