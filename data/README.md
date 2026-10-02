# data
Folders are versioned by `DB_VERSION` (config; default `v2` = dbv2). `v1` folders have no suffix, `v2` folders end in `_v2`.
- `raw/`, `raw_v2/` — step 00 output (canonical exports; v2 = dbv2, see `00_data_acquisition/README.md`)
- `external/` — manual inputs, e.g. `rf.csv` (`date, rate_annual_pct`), shared by all versions
- `interim/`, `interim_v2/` — steps 01–03
- `processed/`, `processed_v2/` — steps 04–05
- suffixes `_z20`, `_z50`, `_book24` — robustness runs (config `ZCAPM_ZERO`, `ZCAPM_SCHEME`)
- `external/delistings_extra.csv` — additions to, and reasons for, the delisting list (step 01)
- `external/rf_*.csv` — inputs of `02_market_factors/build_rf.py`, which writes `rf.csv`
