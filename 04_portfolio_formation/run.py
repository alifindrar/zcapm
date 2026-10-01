"""Step 04 - sort on Z*: long/short legs, 12 L/S, 24 long-only, proxy min-variance portfolio g."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import load, log, save, window_mask  # noqa: E402
from lib.portfolios import form_ls, g_weights, holding_returns  # noqa: E402

STEP = "04"


def main():
    est = load(S.INTERIM / "zcapm_estimates.pkl")
    rm = load(S.INTERIM / "returns_monthly.pkl")
    last_date = load(S.INTERIM / "last_date.pkl")
    f = load(S.INTERIM / "factors_daily.pkl")
    data_end = f.index[-1]

    rets, avgs, cnts, holds = {}, {}, {}, []
    small = 0
    for T, e in est.groupby("T"):
        e = e.set_index("code")
        e = e[e["zstar"].notna()]
        m1 = T.to_period("M") + 1
        if m1 not in rm.index or e.empty:
            continue
        R = holding_returns(e.index, m1, rm, last_date, data_end, S.DELIST_RETURN)
        res = form_ls(e["zstar"], R, S.SORT_SCHEME)
        if res is None:
            continue
        ret, avg, cnt, hold = res
        if min(cnt.values()) < S.MIN_LEG_SIZE:
            small += 1

        fw = f.loc[window_mask(f.index, T, S.WINDOW_MONTHS)]
        w = g_weights(e, (fw["Ra"] - fw["Rf"]).std(), S.G_VOL_RATIO, S.G_ZETA_OFFSET, S.G_WEIGHT_CAP)
        ret["g"] = float((R.reindex(w.index) * w).sum())
        avg["g"] = float((e["zstar"].reindex(w.index) * w).sum())
        cnt["g"] = len(w)
        hold["g"] = w

        rets[m1], avgs[m1], cnts[m1] = ret, avg, cnt
        for name, wts in hold.items():
            holds.append(pd.DataFrame({"T": T, "portfolio": name, "code": wts.index, "weight": wts.to_numpy()}))

    def frame(d):
        df = pd.DataFrame.from_dict(d, orient="index")
        df.index = pd.PeriodIndex(df.index, freq="M", name="month")
        return df.sort_index()

    legs, zs, counts = frame(rets), frame(avgs), frame(cnts)
    save(legs, S.PROCESSED / "legs_monthly.pkl")
    save(zs, S.PROCESSED / "legs_zstar.pkl")
    save(counts, S.PROCESSED / "legs_count.pkl")
    save(pd.concat(holds, ignore_index=True), S.PROCESSED / "holdings.pkl")

    log(STEP, f"{len(legs)} holding months {legs.index[0]}..{legs.index[-1]}, scheme {S.SORT_SCHEME}")
    if small:
        log(STEP, f"WARNING: {small} months with a leg below {S.MIN_LEG_SIZE} stocks "
                  f"(consider SORT_SCHEME='deciles')")
    ls = [c for c in legs.columns if c.startswith("LS")]
    log(STEP, "mean L/S %/month: " + ", ".join(f"{c} {100 * legs[c].mean():.2f}" for c in ls))
    log(STEP, f"g: mean {100 * legs.g.mean():.2f}%/m, median #stocks {int(counts.g.median())}")


if __name__ == "__main__":
    main()
