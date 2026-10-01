# Config
Shared parameters (`settings.py`) — defaults listed in step.md §3.

`DB_VERSION` (env `ZCAPM_DB`, default `v2`) selects the data source version and the folders every step reads/writes:
`v1` → `data/raw|interim|processed`, `outputs/tables|figures`; `v2` → the same names with a `_v2` suffix.
`data/external/` (rf.csv) is shared. Example: `ZCAPM_DB=v1 python 01_universe_cleaning/run.py`.
