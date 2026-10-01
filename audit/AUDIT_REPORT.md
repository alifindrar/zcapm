# Audit report — ZCAPM Chapter 9 replication on IHSG

Audit date: 2026-10-01. Scope: pipeline steps 00–07 as described in `step.md`, checked against the book's method
text and MATLAB code in `audit.md`. Data version: v2 (`dbv2`, default). Report only: no pipeline code, data or
output was changed. Every number below comes from a script in `audit/` and is stored in `outputs/audit_v2/`.

## 1. Verdict

1. **The code implements the book's method correctly.** The EM estimator, Eq. 9.5, the portfolio construction,
   the aggregates, Tables 9.1–9.5 and the GRS test all reproduce with independent code.
2. **The book's 24-portfolio scheme does not work on this universe.** With a median of 151 eligible stocks, the 1% and
   2% legs hold one to three stocks and the 5% slices hold eight. Results for individual portfolios are noise:
   they change sign across subperiods and move materially when the EM starting point changes.
3. **A Z\*–return relation does appear once the sort is coarse enough.** With deciles, mean long/short return
   rises with Z\* (Spearman 0.9–1.0), the top decile spread is 1.2–2.2% per month (t ≈ 1.9–2.9), and this
   survives removing suspicious returns and widening the liquidity filter. It is weaker after 2020.
4. **The input data has defects that the pipeline does not catch**: 783 daily returns beyond ±35%, share-count
   jumps, 2005–2011 still mostly Yahoo data, and delisted stocks missing before 2020. They do not overturn finding 3
   in the tests run here, but they do distort the market index on specific days and bias the sample toward survivors.
5. **The risk-free rate is a 10-year bond yield**, which lowers every Sharpe ratio and excess return.

The current `outputs/tables_v2` should not be presented as a replication of Tables 9.1–9.5 in their present form.
A decile version on cleaned data would be defensible.

## 2. Summary of findings

| # | Finding | Severity | Step | Evidence |
|---|---|---|---|---|
| F1 | Tail legs hold 1–3 stocks; 1% and 2% legs identical in 74 months | High | 04 | `a04_leg_sizes_by_year.csv` |
| F2 | Individual portfolio results unstable across time and estimator start | High | 03–06 | `a06_ls_stability.csv`, `a03_ls_repo_vs_port.csv` |
| F3 | Zero-return filter removes most of the universe | High | 01 | `a01_eligibility_waterfall.csv` |
| F4 | 783 daily returns beyond ±35%, 95 below −50% | High | 00–01 | `a01_extreme_returns.csv` |
| F5 | 2005–2011 is mostly Yahoo data; pre-2005 unusable | High | 00 | `a01_coverage_by_year.csv` |
| F6 | Survivorship: no dead stocks before 2020; 19 listed delistings absent | High | 00 | `a01_delistings.csv` |
| F7 | Risk-free rate is the 10-year government yield | Medium | 02 | `a02_rf_sensitivity.csv` |
| F8 | Share-count jumps; one stock above 25% of the index on 15 days | Medium | 00, 02 | `a01_share_jumps.csv`, `a02_single_weight_over_25pct.csv` |
| F9 | Portfolio g: 5% cap binds in 182 of 227 months; volatility filter never binds | Low | 04 | `a05_g_variants.csv` |
| F10 | Z\* reported on the daily scale; book uses ×21 | Low | 06 | `a06_table_9_1_vs_book.csv` |
| F11 | Delisting return never applied; size cut and price floor edge cases | Low | 01, 04 | `a01_delist_return_holdings.csv`, `a01_eligibility_waterfall.csv` |
| F12 | `converged` flag reads 74% but is a tolerance artefact | Info | 03 | `a03_convergence_recheck.csv` |
| F13 | Cost convention for the first month differs between two scripts | Info | 07 | `a07_cost_check.csv` |
| F14 | `step.md` statements that do not match the code or data | Info | docs | section 5 |

## 3. What matches the book

| Item | Book reference (`audit.md`) | Check | Result |
|---|---|---|---|
| Market return and RD | Eq. 9.5, lagged cap weights | Recomputed with separate code | Max difference 2.8e-17 |
| EM estimator | `solve_hidden_variable_v2.m`, `solve_lineq_v2.m` | MATLAB routine ported, run on all 272 windows | Mean rank correlation of Z\* 0.995 (min 0.976); beta correlation 1.000; top/bottom 5% overlap 93% / 98% |
| 24 legs, 12 long/short | steps 3–4 | In-memory rerun vs `legs_monthly.pkl` | Difference 0 |
| Long-only numbering | long-only paragraph | LO1 = S1, LO13 = L12, LO24 = L1 | Confirmed |
| Aggregates | `M + LS`, 50/50 long-only | Recomputed 74 series | Difference 0 |
| Portfolio g weights | g steps 1–4 | Rebuilt from estimates | Difference 0 |
| Tables 9.1–9.5 | — | Independent statistics code | Max difference 3.6e-15 |
| GRS | — | Asset-by-asset OLS implementation | Difference 3.5e-14; dividing the factor covariance by T instead of T−1 changes p by 0.0001 |
| Out-of-sample timing | step 5 | Code review | Estimates use data to month-end T, returns from T+1, risk-free rate lagged |
| Eligibility rule | bottom-10% size rule | Re-implemented | 0 cells differ from `eligible_monthly.pkl` |
| Turnover, factor-beta sorts, long-only backtest | — | Recomputed | Reproduce the pipeline tables |

Mean daily RD is 2.43% against a mean market return of 0.05% (book: 1.81% and 0.04%).

## 4. Findings

### F1. Tail legs hold one to three stocks (High)

Book: portfolios 1 and 2 are the top/bottom 1% and 2% "of all sample stocks"; portfolios 3–12 are 5% slices.
With thousands of CRSP stocks each leg is diversified. Here it is not.

| Holding years | Median eligible stocks | Median stocks in 1% / 2% / 5% leg | Months 1% leg = 2% leg |
|---|---|---|---|
| 2007–2013 | 26–67 | 1 / 1 / 1–3 | 74 of 77 |
| 2014–2020 | 117–201 | 1–2 / 2–4 / 6–10 | 0 |
| 2021–2026 | 300–481 | 3–5 / 6–10 / 15–24 | 0 |

- The 1% leg is a single stock in 111 of 227 months; a 5% slice has fewer than 5 stocks in 79 months.
- At least one leg is below `MIN_LEG_SIZE` in 222 of 227 months. The pipeline logs this and continues.
- LS1 monthly SD is 38.8% (book 9.1%); LS3 is 17.2% (book 6.8%).

Suggested fix: use `SORT_SCHEME = "deciles"` as the main specification, or require a minimum universe size.

### F2. Individual portfolio results are unstable (High)

Mean long/short return, % per month (`a06_ls_stability.csv`):

| | Full | t (NW) | 2007–13 | 2014–19 | 2020–26 | Excl. best 5 months |
|---|---|---|---|---|---|---|
| LS1 | 0.65 | 0.23 | 6.04 | −3.88 | −0.48 | −1.31 |
| LS2 | 1.54 | 0.75 | 6.41 | −0.43 | −1.45 | −0.01 |
| LS3 | 2.35 | 1.81 | 5.11 | 2.68 | −0.67 | 1.37 |
| Average LS3–LS12 | 0.79 | 2.27 | 0.71 | 0.94 | 0.72 | 0.52 |

- Return does not rise with Z\* across the 12 portfolios: Spearman 0.49, R² 0.18 (success criterion 1 fails).
- Only LS6, LS8 and LS11 have t above 2, with no pattern.
- Forming the same portfolios on the MATLAB-port Z\* (rank correlation 0.995) moves 25% of stocks to a different
  5% slice and changes the middle portfolios: LS9 from −0.10% to 0.63%, LS12 from −0.48% to 0.55%, LS8 from 1.65%
  to 1.03%. Monthly correlation between the two versions falls to 0.49–0.56 for LS9–LS12.
- GRS rejects the market over the full sample (2.09, p = 0.019) but not in any subperiod
  (p = 0.155, 0.125, 0.059).

What is stable is the broad sort. Sensitivity runs (`a04_variants.csv`), mean long/short return in % per month:

| Variant | Months | Median N | Spearman(Z\*, return) | Top spread (t) | Avg of all L/S: 2007–13 / 2014–19 / 2020–26 |
|---|---|---|---|---|---|
| Book scheme as run | 227 | 151 | 0.49 | LS3 2.35 (1.81) | 1.63 / 0.43 / 0.44 |
| Book scheme, months with N ≥ 100 | 147 | 204 | −0.05 | LS3 1.00 (0.73) | — / 0.48 / 0.44 |
| Deciles | 248 | 147 | 0.90 | 1.70 (1.93) | 0.67 / 0.95 / 0.73 |
| Deciles, zero-return filter ≤ 35% | 248 | 223 | 1.00 | 1.20 (1.89) | 0.67 / 0.99 / 0.78 |
| Deciles, zero-return filter ≤ 50% | 248 | 241 | 1.00 | 1.65 (2.63) | 1.07 / 0.99 / 0.77 |
| Deciles, flagged returns removed, re-estimated | 248 | 147 | 0.90 | 2.19 (2.40) | 1.15 / 0.98 / 0.82 |
| Deciles, flagged removed + filter ≤ 35% | 248 | 223 | 1.00 | 1.69 (2.71) | 0.91 / 0.96 / 0.82 |

The top-decile spread itself fades after 2020 (−0.16% to 0.88% per month depending on variant, against 1.4–2.9%
before). Factor-beta sorts on the same structure show less: the average LS3–LS12 spread has t = 2.27 for Z\*,
against 0.20 (SMB), 1.11 (HML) and 1.27 (MOM) (`a07_factor_beta_sorts.csv`).

Long-only buckets (`a07_long_only_buckets.csv`): the top 25% of Z\* beats the market in each subperiod
(gross CAGR 23.4 / 14.3 / 9.9% against 12.3 / 11.6 / 2.4%), and the bottom 25% earns 0.8% over the full sample.
The top 5% bucket depends on few names (median 8, minimum 1) and on a few months: its 21.6% gross CAGR falls to
10.5% without its best five months, and to 15.5% with stock returns capped at +100%.

### F3. The zero-return filter removes most of the universe (High)

`MAX_ZERO_FRAC = 0.20` is an addition to the book (which only drops the bottom 10% by size). It is the binding
filter in every year (`a01_eligibility_waterfall.csv`, December month-ends):

| Year | Listed | ≥ 200 traded days | + zero-return ≤ 20% | Eligible | Eligible at ≤ 35% | at ≤ 50% |
|---|---|---|---|---|---|---|
| 2007 | 318 | 153 | 33 | 33 | 106 | 131 |
| 2010 | 361 | 318 | 56 | 56 | 143 | 183 |
| 2015 | 480 | 262 | 151 | 143 | 208 | 229 |
| 2020 | 716 | 453 | 269 | 259 | 359 | 382 |
| 2025 | 970 | 816 | 456 | 438 | 660 | 714 |

The median zero-return share among stocks with 200 traded days is 17–41%, so a 20% threshold sits in the middle of
the distribution. Raising it to 35% moves the first usable month from 2007-04 to 2005-11 and the median universe
from 151 to 223. Suggested fix: treat the threshold as a documented choice and report results at 35% or 50%.

### F4. Suspicious daily returns (High)

The widest regular IDX auto-rejection band is ±35%, so a larger daily move outside a listing day needs an
explanation (the bands changed over the sample, so the threshold is a screen, not a rule). Since 2005 there are
783 such returns (`a01_extreme_returns_by_class.csv`):

| Class | n | Negative | Below −50% | In an eligible stock |
|---|---|---|---|---|
| Unexplained | 423 | 72 | 25 | 42 |
| Spike that reverts within 3 rows | 209 | 59 | 29 | 12 |
| First 5 rows of the code (IPO or data start) | 80 | 3 | 0 | 0 |
| Split-like jump, no recorded event | 61 | 55 | 38 | 4 |
| Other (trading gap, source seam, recorded split, rights) | 10 | 6 | 3 | 0 |

- 431 of the 783 are Yahoo rows from 2005–2009.
- The pipeline's `|r| > 100%` rule cannot catch negative errors. Example: LPPF −99.7% on 2005-11-17 with a 16.6%
  index weight, which accounts for the whole 16.7-point gap between the own index and IHSG that day. ANTM shows a
  run of ±40–70% moves in 2008–2009.
- Only 58 of the 783 fall in stocks that were eligible, so the direct effect on Z\* estimates is limited; the
  larger effect is on the market return and RD of those days, which enter every stock's regression.
- Limit of this check: the split and rights tables in `dbv2.sqlite` start in 2017, so events before then cannot be
  confirmed. "Unexplained" means not matched to any available record, not proven wrong.

Suggested fix: add a lower bound and a reversal filter in step 01, and rebuild the affected Yahoo-era series.

### F5. Data coverage is not what `step.md` and the step-00 README describe (High)

`a01_coverage_by_year.csv`:

- 2000–2004: 17–28 codes, one stock is 45–98% of the own index. Unusable; the first formation month with more than
  4 stocks is 2005-10.
- 2005–2011: over 90% of rows are Yahoo (`rows_yahoo` 53,813–80,203 per year against 3,469–8,318 from STOCKDB).
  The v2 merge only becomes STOCKDB-based from 2012.
- `START_DATE = 2000-01-01` therefore adds nothing; the effective sample is 2005-10 onward for estimation and
  2007-04 onward for the book scheme.

### F6. Survivorship bias (High)

`a01_delistings.csv`:

- No code has its last price before 2020. The 22 codes that stop early all stop in 2020–2025.
- 19 companies on the delisting list (delisted 2017–2019) have no price data at all. Delistings before 2017 are
  not listed anywhere in the database.
- 11 codes stop on 2025-07-18 without appearing on the delisting list; this looks like a feed artefact and should
  be checked.
- `delistings.csv` is exported by step 00 but never read by steps 01–07.

The sample before 2020 is a sample of survivors. This biases returns upward, most plausibly for volatile small
stocks, which is where extreme Z\* values sit.

### F7. Risk-free rate (Medium)

Book: Treasury bill rate. `rf.csv` is the Indonesian 10-year government yield (the other files in
`data/external/` are also 10-year series). Over 2007-04..2026-06 it averages 7.8% p.a., 0.63% per month, against a
market mean of 0.86% (`a02_rf_sensitivity.csv`):

| Risk-free assumption | Market excess, % per month | Market Sharpe |
|---|---|---|
| As used (10-year yield) | 0.30 | 0.052 |
| Illustration: yield − 2 points | 0.46 | 0.079 |
| Illustration: yield − 3 points | 0.53 | 0.093 |

The two lower rows are illustrations of a term-premium adjustment, not data. A short-rate series (BI rate,
INDONIA, SBI/SPN) is needed. Long/short returns are unaffected; Sharpe ratios in Tables 9.2–9.5 and the excess
returns in the EM and GRS are.

### F8. Share counts and index weights (Medium)

- 206 day-to-day share-count jumps beyond 1.5× since 2005 (`a01_share_jumps.csv`): 118 with no recorded event,
  48 next to a recorded rights issue or split, 29 where the share count moves by a split ratio and the price does
  not, 11 at source seams.
- One stock exceeds 25% of the own index on 15 days (BBRI 13, HMSP 2); BBRI reaches 49% in May 2008.
- 75 days have a gap above 1 point between the own index and IHSG, 60 of them in 2005–2009
  (`a02_index_gap_days.csv`). Correlation with IHSG is 0.93–0.999 per year from 2006.

### F9. Portfolio g (Low)

`a05_g_variants.csv`:

| Reading | Mean % | SD % | Sharpe | Median max weight | Largest weight |
|---|---|---|---|---|---|
| As run (5% cap) | 0.94 | 6.13 | 0.052 | 5.0% | 5.0% |
| No cap | 0.98 | 6.05 | 0.059 | 7.6% | 26.3% |
| Book-literal (no cap, Z\* ×21, monthly SD) | 0.94 | 6.22 | 0.051 | 17.3% | 66.1% |
| Market | 0.86 | 5.67 | 0.041 | | |

- The 5% cap is not in the book and binds in 182 of 227 months, so g is largely a capped portfolio. The cap is a
  reasonable safeguard: without it one stock reaches 66%.
- The 20% volatility filter removes no stock in the median month, on either the daily or the monthly reading.
- g behaves like the market (correlation 0.91) and adds 0.007 of Sharpe on average to the aggregates. The book's
  claim that g dominates the index is not reproduced in any reading.

### F10. Z\* scale (Low)

Z in Eq. 9.2 is unit-free. The book reports Z\* multiplied by 21 (monthly scale; MATLAB `coeff(:,2).*(2*coeff(:,3)-1)*21`).
The pipeline reports the daily value, so Table 9.1's Z\* column is not comparable to the book without ×21
(long-minus-short for portfolio 1: 0.73 daily, 15.4 at ×21, book 10.7). The `0.01` offset in the g weight is 21
times heavier on the daily scale; the effect on g is small (F9).

### F11. Smaller rule deviations (Low)

- **Delisting return**: the −30% rule was applied to no holding in 227 months (`a01_delist_return_holdings.csv`),
  because the stocks that stop trading were not held. It is untested rather than wrong.
- **Size cut**: 393 of 40,985 eligible stock-months have no market cap on the year-end date and skip the cut;
  71 would fail it with the last available value.
- **Price floor**: applied to split-adjusted prices; 86 stock-months are excluded although the nominal price was
  above Rp 50, 1 is included although it was not.
- **HML input**: price-to-book is at most a few months old (median age 5 months; fewer than 2% older than 12
  months), so the unlimited forward-fill is not a practical problem. The initial review flagged this; it is cleared.

### F12. Convergence flag (Info)

`converged` is 74% overall and about 65% in recent years. Refitting every 24th window with 5,000 iterations
converges every stock, with Z\* rank correlation of at least 0.9995 and a largest Z\* change of 0.019
(`a03_convergence_recheck.csv`). The flag reflects the tight 1e-8 tolerance and has no effect on sorts.

### F13. Costs (Info)

Turnover reproduces. The first month is charged 0.48% in `07_robustness/run.py` and 0.24% in
`long_only_backtest.py`; a pure purchase costs 0.19%. The effect on a 227-month mean is at most 0.002% per month.
Allowing for weight drift raises turnover by 1–4 points and lowers the Top 10% net CAGR from 15.8% to 15.6%.
Short-side borrowing costs are not modelled.

## 5. Statements in `step.md` to correct

- §5 "Z\* magnitude depends on return units": Z is unit-free; the difference from the book is the ×21 scaling (F10).
- §1 table, risk-free row: lists BI rate / SBI / SPN / INDONIA; the file used is the 10-year yield (F7).
- Header and §6: `zcapm_chapter_9_pages_225_255.md` and `run_all.py` are in `.archieve/`, not at the root.
- §2 Step 01, diagnostic "previous ≠ lagged close": in v2 `previous` is built from the prior close, so the count
  (24) says nothing about corporate actions.
- §2 Step 03, "cross-check against the authors' code": not done before this audit; now covered by `a03_em.py`.
- §2 Step 04, "fallback design = deciles (config switch)": there is no automatic fallback; the scheme stays `book24`.
- §6 dbv2 row and the step-00 README: "STOCKDB 1990-05-25 →" is true for a handful of codes only (F5).
- §4 reference "expect ~250–300 months": the book scheme has 227.

## 6. Success criteria in `step.md` §4

| Criterion | As run (book scheme) | Deciles |
|---|---|---|
| 1. L/S return rises with Z\* and with SD | No (Spearman 0.49 and 0.48) | Yes (Spearman 0.9–1.0) |
| 2. `M + LS` Sharpe above M; g-set dominates | 8 of 12 above M; g gain 0.007 | Not evaluated |
| 3. Long-only aggregates with high Z\* beat M | 9 of 12 high-Z\* legs, 4 of 12 low-Z\* legs | Not evaluated |
| 4. GRS rejects M at 5% | Yes full sample (p 0.019–0.034); no in any subperiod | Not evaluated |
| 5. Factor-beta sorts flat | Flatter than Z\*: no factor reaches t = 2 on the broad spread | Not evaluated |

## 7. Decisions needed

1. **Main sort scheme**: deciles as the headline with the book scheme as an appendix, or a minimum universe size.
2. **Zero-return threshold**: keep 20%, or move to 35–50% to gain universe and sample length.
3. **Risk-free series**: which short rate to use.
4. **Return cleaning**: adopt a lower bound and reversal filter, and whether to rebuild 2005–2011 from a better source.
5. **Survivorship**: obtain delisted-stock prices before 2020, or state the bias and restrict claims accordingly.

## 8. Reproducing this audit

```
python audit/a01_data.py      # ~2 min (database opens slowly from OneDrive)
python audit/a02_factors.py
python audit/a03_em.py        # ~5 min
python audit/a04_sorts.py     # ~35 min first run (four re-estimations, cached afterwards); needs a01 output
python audit/a05_g.py
python audit/a06_eval.py
python audit/a07_robust.py
```

Scripts read `data/*_v2`, `outputs/tables_v2` and `dbv2.sqlite` (read-only) and write only to
`outputs/audit_v2/`. A file listing with sizes and modification times of `config/`, `lib/`, the step folders,
`data/`, `outputs/tables_v2`, `outputs/figures_v2`, `step.md` and `audit.md` was identical before and after the
audit (131 files).
