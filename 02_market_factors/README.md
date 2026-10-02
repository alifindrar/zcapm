# Step 02 — Market factors (R_a, RD, R_f, IHSG, SMB/HML/MOM)

- Inputs: `data/interim/returns_daily.pkl`, `mcap_daily.pkl`, `data/raw/index_daily.csv`, `ratios.csv`, `data/external/rf.csv`
- Outputs: `data/interim/factors_daily.pkl`, `factors_monthly.pkl`
- Scripts: `run.py` — implemented. Spec: step.md §2 Step 02
- `build_rf.py` writes `data/external/rf.csv`: Bank Indonesia policy rate from 1995 onwards (`rf_bi_rate_fred.csv` before 2016-08, and `rf_bi_rate_bi_go_id.csv` from 2016-08 onwards from bi.go.id). If `rf_idn1m_tradingeconomics.csv` is provided, it splices the 1-month government bill yield. Run with `--fetch` to refresh data from online sources.
