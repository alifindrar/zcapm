"""Step 05 - aggregate portfolios: M/g + L/S (leveraged) and 50/50 M/g + long-only legs."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import load, log, save  # noqa: E402

STEP = "05"


def main():
    legs = load(S.PROCESSED / "legs_monthly.pkl")
    fm = load(S.INTERIM / "factors_monthly.pkl")
    M = fm["M_own" if S.MARKET_PROXY == "own_vw" else "IHSG"].reindex(legs.index)
    g = legs["g"]
    K = sum(c.startswith("LS") for c in legs.columns)
    J = sum(c.startswith("LO") for c in legs.columns)

    agg = {"M": M, "g": g, "Rf": fm["Rf"].reindex(legs.index)}
    for k in range(1, K + 1):
        agg[f"M+LS{k}"] = M + legs[f"LS{k}"]
        agg[f"g+LS{k}"] = g + legs[f"LS{k}"]
    for j in range(1, J + 1):
        agg[f"LOA_M_{j}"] = 0.5 * M + 0.5 * legs[f"LO{j}"]
        agg[f"LOA_g_{j}"] = 0.5 * g + 0.5 * legs[f"LO{j}"]
    for fac in ["SMB", "HML", "MOM"]:
        if fac in fm and fm[fac].notna().any():
            agg[f"M+{fac}"] = M + fm[fac].reindex(legs.index)
            agg[f"g+{fac}"] = g + fm[fac].reindex(legs.index)
            agg[fac] = fm[fac].reindex(legs.index)
    agg = pd.DataFrame(agg)
    save(agg, S.PROCESSED / "aggregates_monthly.pkl")
    log(STEP, f"{agg.shape[1]} series x {agg.shape[0]} months; market proxy = {S.MARKET_PROXY}")


if __name__ == "__main__":
    main()
