# ZCAPM Chapter 9 Replication on IHSG — Plan & Pipeline

Replicates Kolari, Liu & Huang (2021), *A New Model of Capital Asset Prices*, Ch. 9
("Efficient Investment Portfolios: An Application of the ZCAPM") using Indonesian stocks
(IDX / IHSG) instead of CRSP. Source text: [zcapm_chapter_9_pages_225_255.md](.archieve/zcapm_chapter_9_pages_225_255.md).

Audit of the first full run: [audit/AUDIT_REPORT.md](audit/AUDIT_REPORT.md). Changes made in response: [audit/FIXES.md](audit/FIXES.md).

---

## 0. Folder layout

```
zcapm/
├── step.md                      ← this file (plan + pipeline contract)
├── config/                      ← shared parameters (one file, read by every step)
├── lib/                         ← shared Python code (EM, portfolio sorts, stats, IO)
├── data/
│   ├── raw/                     ← output of step 00 (canonical exports from idx-api)
│   ├── external/                ← manually supplied files (risk-free rate, etc.)
│   ├── interim/                 ← outputs of steps 01–03
│   └── processed/               ← outputs of steps 04–05
├── outputs/
│   ├── tables/                  ← Tables 9.1–9.5 equivalents (CSV + Markdown)
│   └── figures/                 ← Figs 9.1–9.7 equivalents (PNG)
├── 00_data_acquisition/         ← idx-api → data/raw
├── 01_universe_cleaning/        ← returns, market cap, eligibility filters
├── 02_market_factors/           ← R_a, σ_a (RD), R_f, IHSG, local SMB/HML/MOM
├── 03_zcapm_estimation/         ← rolling EM estimation of β, Z, p, Z*
├── 04_portfolio_formation/      ← 24 legs, 12 long/short, 24 long-only, portfolio g
├── 05_aggregate_portfolios/     ← index/g + L/S (leveraged), 50/50 long-only
├── 06_evaluation/               ← tables, figures, Sharpe, GRS
└── 07_robustness/               ← factor-beta sorts (Fig 9.7), costs, NW-t, subperiods
```

Robustness runs use environment variables and write to their own folders (suffix `_z20`, `_z50`, `_book24`):
`ZCAPM_ZERO=0.20` (rerun from step 01) and `ZCAPM_SCHEME=book24` (rerun from step 04).

Each step folder holds its own `README.md` (inputs / outputs / scripts) and a `run.py`
entry point. Steps communicate **only through files in `data/`** — any step can be rerun
independently once its inputs exist.

Run order:

```
python 00_data_acquisition/run.py      # export from idx-api SQLite (fetching itself is separate)
python 01_universe_cleaning/run.py
python 02_market_factors/build_rf.py   # only when the risk-free inputs in data/external change
python 02_market_factors/run.py
python 03_zcapm_estimation/run.py      # slowest step
python 04_portfolio_formation/run.py
python 05_aggregate_portfolios/run.py
python 06_evaluation/run.py
python 06_evaluation/long_only_backtest.py   # investable long-only Z* buckets + cumulative chart
python 07_robustness/run.py
```

---

## 1. Method recap (what we replicate)

Empirical ZCAPM per stock, estimated on 12 months of daily data, no intercept (Eq. 9.2–9.4):

$$R_{it}-R_{ft}=\beta_i(R_{at}-R_{ft})+Z_i D_{it}\sigma_{at}+u_{it},\qquad D_{it}=\begin{cases}+1 & p_i\\-1 & 1-p_i\end{cases}$$

$$Z^*_i = Z_i(2p_i-1) \quad\text{(sorting variable)}$$

Return dispersion (Eq. 9.5), lagged cap weights:

$$\sigma_{at}=\sqrt{\tfrac{n}{n-1}\textstyle\sum_i w_{i,t-1}(R_{it}-R_{at})^2}$$

Monthly loop: estimate → rank on $\hat Z^*$ → form portfolios → hold one month (out-of-sample) → roll.

| Book (US) | This replication (IHSG) |
|---|---|
| CRSP NYSE/AMEX/NASDAQ, 1964–2018 | IDX common stocks, sample decided by data availability (target 2000/2001 → latest) |
| $R_{at}$ = CRSP VW index | Own cap-weighted index from the universe (default); IHSG `COMPOSITE` as robustness |
| $R_{ft}$ = T-bill | BI policy rate (7-day reverse repo rate from 2016-08); the 1-month government bill yield replaces it from 2012-08 once its export is supplied; built by `02_market_factors/build_rf.py` |
| Drop bottom 10% mkt cap | Same + IDX-specific liquidity / board / price-floor filters |
| 24 portfolios: 1%, 2%, 10 × 5% from each end | **Deciles** (5 × 10% from each end) as the headline; the book scheme as an appendix (`ZCAPM_SCHEME=book24`) — with a median of ~220 stocks a 1% leg holds 1–3 names |
| Kenneth French SMB/HML/RMW/CMA/MOM | Locally built SMB, HML, MOM from IDX data (RMW/CMA optional) |
| 648 out-of-sample months | ~230–250 months (sample starts 2005; months with fewer than 5 stocks per leg are skipped) |

---

## 2. Pipeline steps

### Step 00 — Data acquisition (`00_data_acquisition/`)

**Source: `../_arcip/idx-api`** (Deno + Drizzle wrapper around idx.co.id endpoints, stores into
`_arcip/idx-api/data/database.sqlite`).

> **Status: acknowledged, not wired yet.** The fetcher is out of scope for now. As of
> 2026-09-27 the price tables in the SQLite DB are empty (`company_profile` = 957 rows,
> `financial_ratio` = 25 rows, `stock_summary` / `index_summary` = 0). The pipeline is
> designed so this step only has to *produce the canonical files below*; any other vendor
> (Bloomberg, LSEG, Yahoo `.JK` for prototyping) can be dropped in by writing the same files.

idx-api tables/functions that feed this project:

| Need | idx-api sync function | SQLite table | Key columns |
|---|---|---|---|
| Daily stock OHLC, volume, shares (survivor-free, per date) | `syncStockSummary('YYYYMMDD')` | `stock_summary` | `date` (epoch ms), `code`, `close`, `previous`, `volume`, `value`, `listed_shares`, `tradable_shares`, `remarks` |
| Daily IHSG level | `syncIndexSummary('YYYYMMDD')` | `index_summary` | `code`='COMPOSITE', `date`, `close` |
| Cash dividends | `syncCompanyDividend(year, month)` | `company_dividend` | `code`, `cash_dividend`, `ex_dividend` |
| Delistings | `syncCompanyDelisting(year, month)` | `company_delisting` | `code`, `delisting_date` |
| Splits / rights (for audit of adjustments) | `syncStockSplit`, `syncRightOffering` | `stock_split`, `right_offering` | ratio, dates |
| Book-to-market (for HML) | `syncFinancialRatio(year, month)` | `financial_ratio` | `code`, `period`, `pbv` |

Fetch: `deno run -A --config ../_arcip/idx-api/deno.json 00_data_acquisition/sync_idx_history.ts [batch]`
— one batch per run (no arg = next pending): `2025-2026` (2025-01-01..2026-06-30), then `2024`, …, `1995`.
Resumable, throttled; per-batch state/row counts/failures in `00_data_acquisition/batches/<batch>.json`;
a Cloudflare block (non-JSON reply) aborts the batch with status `blocked` rather than logging empty days.

**This step's job now:** `run.py` reads the SQLite DB and writes canonical files:

| Output (`data/raw/`) | Columns |
|---|---|
| `stock_daily.csv.gz` | `date, code, close, previous, volume, value, listed_shares, remarks` |
| `index_daily.csv` | `date, code, close` |
| `dividends.csv` | `code, ex_date, cash_dividend` |
| `delistings.csv` | `code, delisting_date` |
| `ratios.csv` | `code, date, pbv` |

External input (`data/external/`): `rf.csv` → `date, rate_annual_pct` (monthly or daily; forward-filled), written by
`02_market_factors/build_rf.py`; `delistings_extra.csv` → additions and reasons for the delisting list (step 01).
`stock_daily.csv.gz` may carry an optional `price_scale` column (adjusted / nominal close, dbv2 only).

### Step 01 — Universe & returns (`01_universe_cleaning/`)

1. Keep common stocks: code matches `^[A-Z]{4}$`, exclude ETFs (`X…`), warrants/rights (suffix), REITs/DINFRA.
2. Daily return `r = close/previous − 1` (IDX adjusts `previous` for splits/rights on ex-date)
   `+ cash_dividend/previous` on ex-dividend dates. (In dbv2 `previous` is built from the prior close, so the
   count of `previous ≠ close_{t−1}` says nothing about corporate actions.)
3. Flags: `traded = volume > 0`; set |r| > 100% to NaN (logged).
   **Return screen** (`lib/cleaning.py`): outside the first `RET_LISTING_ROWS` (5) rows of a code, a move beyond
   `RET_LIMIT` (±35%, the widest regular auto-rejection band) is set to NaN in both directions. If the price is back
   within 15% of the pre-move level within 3 rows it is a spike and every return of the round trip is dropped.
   Every removed return is listed in `returns_flagged.csv` with its class (`spike`, `split`, `other`).
4. Market cap = `close × listed_shares`. Share-count jumps beyond 1.5× are listed in `share_jumps.csv` and not
   changed (the correct basis cannot be told without event data before 2017).
5. Eligibility at each month-end *T* (stored as a table, applied in step 03/04):
   - not in bottom `SIZE_CUT` (default 10%) of mkt cap at latest year-end ≤ T (last value within 20 rows if the
     stock did not trade on that date);
   - ≥ `MIN_OBS` (200) traded days in the 12-month window and ≤ `MAX_ZERO_FRAC` (35%) zero-return days. The zero-return
     rule is not in the book; 20% and 50% are robustness runs (`ZCAPM_ZERO=0.20`);
   - nominal close at T > `MIN_PRICE` (Rp 50 floor stocks excluded; adjusted close where `price_scale` is missing);
   - not suspended / not on Papan Pemantauan Khusus at T (via `remarks`, when available).

6. Delisting return per code (`delist_return.pkl`): a code that stops trading and is on the delisting list
   (`delistings.csv` + `data/external/delistings_extra.csv`) gets `DELIST_RETURN` (−30%), or
   `DELIST_RETURN_VOLUNTARY` (0) for a voluntary delisting or merger. A code that stops trading without being on
   the list gets none (feed gap). `delistings_status.csv` lists both, and listed delistings with no price data.

Outputs (`data/interim/`): `returns_daily.pkl` (wide date×code), `traded_daily.pkl`,
`mcap_daily.pkl`, `eligible_monthly.pkl` (month-end×code bool), `delist_return.pkl`, `cleaning_log.csv`,
`returns_flagged.csv`, `share_jumps.csv`, `delistings_status.csv`.

### Step 02 — Market factors (`02_market_factors/`)

1. $R_{at}$: cap-weighted return with weights $w_{i,t-1}$ over all stocks with a valid return.
2. $\sigma_{at}$ (RD) per Eq. 9.5. Sanity: mean RD ≫ mean $R_a$ (US: 1.81% vs 0.04%).
3. $R_{ft}$: annual % → daily $(1+r)^{1/242}-1$, monthly $(1+r)^{1/12}-1$.
4. IHSG daily/monthly returns from `index_daily.csv` (price index — no dividends; note it).
5. Local factors, rebalanced monthly, 2×3 value-weighted sorts:
   SMB (size median), HML (B/M = 1/pbv, 30/70), MOM (t−12..t−2 return, 30/70).
   Produce both daily (for betas in step 07) and monthly (for tables/GRS) series.

Outputs: `factors_daily.pkl` (`Ra, sigma_a, Rf, IHSG, SMB, HML, MOM`), `factors_monthly.pkl`.

### Step 03 — Rolling ZCAPM estimation (`03_zcapm_estimation/`)

For every month-end *T* with 12 months of history:
`y = r_i − Rf`, `x = Ra − Rf`, `s = sigma_a`, over the window's traded days, eligible stocks only.

EM for the two-component mixture regression (vectorised across stocks, NaN-masked):

```
E-step:  τ_t = p·φ(y; βx+Zs, σ²) / [p·φ(y; βx+Zs, σ²) + (1−p)·φ(y; βx−Zs, σ²)],  d_t = 2τ_t − 1
M-step:  p = mean(τ)
         [Σx²      Σxsd] [β]   [Σxy ]
         [Σxsd     Σs² ] [Z] = [Σsyd]
         σ² = mean( τ(r−Zs)² + (1−τ)(r+Zs)² ),  r = y − βx
Stop:    |Δ log-lik| < 1e-8 or 500 iterations; multiple starts p0 ∈ {0.25, 0.5, 0.75}, keep best LL
Identify: if Z < 0 → Z = −Z, p = 1 − p;   Z* = Z(2p − 1)
Also:    resid_var = var(y − βx − Z*s)   (used for portfolio g)
```

Validation: `test_em.py` simulates series with known (β, Z, p) and checks recovery. The cross-check against the
authors' MATLAB routine is `audit/a03_em.py` (rank correlation of Z\* 0.995). `converged` is below 100% only because
of the 1e-8 tolerance; refitting with more iterations does not change the sorts (audit F12).

Output: `data/interim/zcapm_estimates.pkl` — `T, code, beta, Z, p, zstar, sigma2, resid_var, sd_daily, n_obs, loglik, converged`.

### Step 04 — Portfolio formation (`04_portfolio_formation/`)

At each *T*, rank eligible stocks by $\hat Z^*$ (descending), N stocks. `SORT_SCHEME`:

| Scheme | Leg | Long (top) | Short (bottom) |
|---|---|---|---|
| `deciles` (headline) | 1–5 | 10% slices from top: 0–10%, …, 40–50% | mirror from bottom |
| `book24` (appendix) | 1 | top 1% | bottom 1% |
| | 2 | top 2% | bottom 2% |
| | 3–12 | 5% slices from top: 0–5%, …, 45–50% | mirror from bottom |

- `LS_k = EW(L_k) − EW(S_k)`, k = 1..K (zero-investment); K = 5 for deciles, 12 for book24.
- Long-only 2K, numbered low→high Z*: `LO_1..K = S_1..S_K`, `LO_K+1..2K = L_K..L_1`
  (verified against Tables 9.4/9.1: LO24 = L1, LO13 = L12).
- Average Z\* per leg is stored on the book's monthly scale (daily Z\* × `ZSTAR_SCALE` = 21).
- Portfolio **g**: eligible stocks with daily SD ≥ 0.2 × index SD; weights
  $w_i \propto \frac{1}{0.01+|21\hat Z^*_i|}\cdot\frac{1}{\text{resid\_var}_i}$, normalised, capped at 5%
  (`G_WEIGHT_CAP`; the cap is not in the book — without it one stock reaches 66% of g).
- Holding return for month T+1: buy-and-hold compounded daily returns; delisted mid-month →
  returns up to last trade + the code's delisting return from step 01.
- Guard: a formation month where any leg would hold fewer than `MIN_LEG_SIZE` (5) stocks is skipped
  (`ENFORCE_MIN_LEG`; for `book24` it is only logged, since the 1% leg would fail in almost every month).

Outputs (`data/processed/`): `legs_monthly.pkl` (returns of L/S/LS/LO/g), `legs_zstar.pkl`
(avg Z* per leg), `legs_count.pkl`, `holdings.pkl` (T, portfolio, code, weight — for turnover).

### Step 05 — Aggregate portfolios (`05_aggregate_portfolios/`)

| Set | Formula | Book table |
|---|---|---|
| Leveraged, index | `M + LS_k`, k=1..12 | 9.2 |
| Leveraged, g | `g + LS_k` | 9.3 |
| Long-only, index | `0.5·M + 0.5·LO_j`, j=1..24 | 9.4 |
| Long-only, g | `0.5·g + 0.5·LO_j` | 9.5 |
| Benchmarks | `M + SMB/HML/MOM`, `g + SMB/HML/MOM` | 9.2 / 9.3 |

`M` = market proxy from config (`own_vw` default, `ihsg` alternative).
Output: `data/processed/aggregates_monthly.pkl`.

### Step 06 — Evaluation (`06_evaluation/`)

- **Table 9.1**: per leg avg Z*, mean, SD; L/S Sharpe = mean/SD (no Rf); rows `M−Rf`, `g−Rf`.
- **Tables 9.2–9.5**: mean, SD, Sharpe = (mean − Rf)/SD.
- **Figures**: 9.1 return vs Z* (with OLS line, R²), 9.2 return vs SD (+factors),
  9.3 leveraged frontiers (M and g), 9.4 long-only legs, 9.5/9.6 long-only aggregates.
- **GRS** (Gibbons-Ross-Shanken), N = 12 aggregate portfolios, L benchmarks:
  $GRS=\frac{T}{N}\frac{T-N-L}{T-L-1}\frac{\hat\alpha'\hat\Sigma^{-1}\hat\alpha}{1+\bar\mu'\hat\Omega^{-1}\bar\mu}\sim F(N,T-N-L)$
  run with (a) `M−Rf` only; (b) `M−Rf, SMB, HML, MOM`; for both M- and g-based sets.

Outputs: `outputs/tables/table_9_*.csv|md`, `outputs/figures/fig_9_*.png`, `outputs/tables/grs.csv`.

### Step 07 — Robustness (`07_robustness/`)

1. **Fig 9.7**: rolling daily regressions on `Ra−Rf, SMB, HML, MOM`; sort on each factor beta
   into the same 12 L/S structure; combine with M; expect flat frontiers.
2. **Transaction costs**: turnover from `holdings.pkl` × (buy ≈ 0.15–0.20%, sell ≈ 0.25–0.30% incl. 0.1% sales tax);
   the first month is a purchase of the whole portfolio (`lib.portfolios.turnover_cost`, also used by the long-only backtest).
3. **Newey-West t-stats** of L/S means; **ex-post CAPM beta** of each L/S (should be ≈ 0).
4. **Subperiods**: pre/post-2008, COVID 2020–21; own index vs IHSG; EW vs VW legs.
5. **Universe variants**: LQ45 / Kompas100 with quintile/tercile sorts (small N).

Outputs: `outputs/tables/robust_*.csv`, `outputs/figures/fig_9_7.png`.

---

## 3. Config (`config/settings.py`) — defaults

| Key | Default | Note |
|---|---|---|
| `IDX_API_DB` | `../_arcip/idx-api/data/database.sqlite` | step 00 source |
| `START_DATE`, `END_DATE` | `2005-01-01`, latest | 2000–2004 has 17–28 codes |
| `WINDOW_MONTHS` | 12 | estimation window |
| `SIZE_CUT` | 0.10 | consider 0.20–0.30 for IDX |
| `MIN_OBS` / `MAX_ZERO_FRAC` | 200 / 0.35 | liquidity; env `ZCAPM_ZERO` for 0.20 / 0.50 runs (own folders) |
| `RET_LIMIT` | 0.35 | return screen, with `RET_LISTING_ROWS`, `RET_REVERT_ROWS`, `RET_REVERT_BAND` |
| `MIN_PRICE` | 50 | exclude floor stocks |
| `MARKET_PROXY` | `own_vw` | or `ihsg` |
| `RF_FILE` | `data/external/rf.csv` | required; `02_market_factors/build_rf.py` |
| `G_VOL_RATIO`, `G_WEIGHT_CAP`, `ZSTAR_SCALE` | 0.2, 0.05, 21 | portfolio g; Z\* reporting scale |
| `DELIST_RETURN`, `DELIST_RETURN_VOLUNTARY` | −0.30, 0 | forced / voluntary or merger |
| `MIN_LEG_SIZE`, `SORT_SCHEME` | 5, `deciles` | env `ZCAPM_SCHEME=book24` for the appendix (own folders) |
| `TRADING_DAYS` | 242 | IDX per year |

---

## 4. Success criteria (what "replicates" means)

1. L/S mean returns increase ~linearly with avg Z* (Fig 9.1) and with SD (Fig 9.2).
2. M+LS and g+LS aggregates have Sharpe > Sharpe(M); g-set dominates M-set (Fig 9.3).
3. Long-only aggregates with high-Z* legs beat M on Sharpe (Tables 9.4/9.5).
4. GRS rejects efficiency of M (p < 0.05), also with local SMB/HML/MOM.
5. Factor-beta sorts give flat frontiers (Fig 9.7).

Reference values (US, book): LS1 = 2.34%/m; Sharpe M+LS up to 0.33, g+LS up to 0.36 vs CRSP 0.11;
GRS 4.31–4.88. Expect lower Sharpe levels in IDR (Rf ≈ 0.4–0.6%/month) — compare to IHSG's own Sharpe.

---

## 5. Known issues & decisions

- **Shorting** on IDX is practically unavailable → long/short results are a model test;
  long-only (Tables 9.4/9.5) is the investable result.
- **Price limits (ARA/ARB)** and illiquidity → stale returns; zero-volume days excluded from estimation.
- **`previous` adjustment** assumption must be verified on known split/rights events before trusting returns.
- **Small N** → the book's 1% and 2% legs hold 1–3 stocks, so deciles are the headline scheme (audit F1–F2).
- **Z\* scale**: Z is unit-free. The book reports Z\* × 21 (monthly scale); so does this pipeline from step 04 on.
- **Survivorship**: no stock that died before 2020 is in the price data, and Yahoo does not serve delisted IDX
  tickers. Results before 2020 are for survivors until the IDX daily summaries are back-filled (`sync_idx_history.ts`).
- **Return screen** removes real moves beyond ±35% together with data errors; `returns_flagged.csv` lists them.
- Book ambiguities resolved here: slice boundaries (§ Step 04), LO numbering, L/S Sharpe without Rf,
  g volatility filter interpreted on daily SD in the window.

## 6. Status

| Step | Script(s) | Status |
|---|---|---|
| 00 idx-api fetch | `00_data_acquisition/sync_idx_history.ts` | One batch per run (2025-01..2026-06, then 2024 → 1995 yearly), state in `00_data_acquisition/batches/<batch>.json`. **Blocked 2026-09-28**: idx.co.id returns HTTP 403 Cloudflare challenge from this machine; DB empty |
| 00 export → `data/raw` + DB | `00_data_acquisition/run.py` | Working (2026-09-29): 2,724,384 stock rows, 983 codes, 2005-01-03..2026-06-30 → `00_data_acquisition/idx_data.sqlite` + `data/raw/*.csv`. 2005–2019 = Yahoo backfill rescaled to nominal prices; survivorship-biased |
| 00 synthetic data | `00_data_acquisition/make_synthetic.py` | Working (plumbing test; writes `data/raw/SYNTHETIC` marker) |
| 01–07 | `0X_*/run.py` | Working end-to-end on synthetic data; **run on real data 2026-09-29** (228 holding months 2007-04..2026-06, placeholder flat 5% `rf.csv`). `lib/stats.py` uses a numpy Newey-West OLS (statsmodels DLL blocked by Windows Application Control) |
| 02–07 rerun, new Rf | + `06_evaluation/long_only_backtest.py` | 2026-09-29: `rf.csv` = IDN 10Y yield (TradingView, monthly, 2004-08..2026-09, full coverage, no back-fill). Long-only EW Z* buckets (top 5/10/25%, bottom 25%, g, 50% M + 50% top 10%), monthly rebalance, net of costs → `outputs/tables/long_only_backtest.md`, `long_only_annual.md`, `outputs/figures/long_only_cumulative.png` |
| dbv2 (default source, 2026-10-01) | `00_data_acquisition/{fetch_stockdb,build_dbv2}.py` | v1 DB + STOCKDB (STOCKDB wins on conflicts; see `00_data_acquisition/README.md`) → `dbv2.sqlite` + `data/raw_v2/`. Steps 01–07 run on it (config `DB_VERSION=v2`, outputs in `*_v2` folders; v1 files untouched, `ZCAPM_DB=v1` reproduces them). 227 holding months 2007-04..2026-06; long-only Top 10% Z* net CAGR 15.8% / Sharpe 0.38 (v1: 12.7% / 0.31), market (own VW) 8.6% (v1 6.1%); GRS p ≈ 0.02–0.03 |
| 03 EM check | `03_zcapm_estimation/test_em.py` | Passing (rank corr Z* 0.99, β 0.96) |

| Audit fixes (2026-10-02) | see `audit/FIXES.md` | Code changed and tested on synthetic data only; **real data not rerun yet** (the databases are not on the machine where the changes were made). `outputs/tables_v2` still holds the pre-fix book24 run |

Shared code: `config/settings.py`, `lib/{io,em,cleaning,portfolios,factors,stats}.py`.
The old orchestrator `run_all.py` is in `.archieve/`.

```
python 03_zcapm_estimation/test_em.py     # EM recovery check
ZCAPM_DB=synth python 00_data_acquisition/make_synthetic.py   # plumbing test data -> data/raw_synth (then steps 01-07 with ZCAPM_DB=synth)
# real data: run order in section 0, after  python 02_market_factors/build_rf.py
```

Outputs are overwritten on each run; tables/figures from synthetic data are labelled `SYNTHETIC`.
