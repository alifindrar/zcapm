# Step 04 — Portfolio formation (legs, L/S, long-only, g)

- Inputs: `data/interim*/zcapm_estimates.pkl`, `returns_monthly.pkl`, `last_date.pkl`, `delist_return.pkl`, `factors_daily.pkl`
- Outputs (`data/processed*/`): `legs_monthly.pkl`, `legs_zstar.pkl` (Z* × 21, book scale), `legs_count.pkl`, `holdings.pkl`
- Scheme: `SORT_SCHEME` = `deciles` (headline, 5 L/S + 10 long-only); `ZCAPM_SCHEME=book24` writes the book's
  12 L/S + 24 long-only to `processed*_book24`. Months with a leg below `MIN_LEG_SIZE` are skipped (deciles).
- Scripts: `run.py`. Spec: step.md §2 Step 04
