"""Local Fama-French style factors (SMB, HML, MOM) from 2x3 value-weighted sorts."""
import numpy as np
import pandas as pd


def sort_2x3(size, signal, breaks):
    """Six value-weight portfolios: size median x signal (low/mid/high by `breaks`). Returns name -> weights."""
    df = pd.DataFrame({"size": size, "sig": signal}).dropna()
    df = df[df["size"] > 0]
    if len(df) < 12:
        return {}
    small = df["size"] <= df["size"].median()
    lo, hi = df["sig"].quantile(list(breaks))
    grp = np.where(df["sig"] <= lo, "L", np.where(df["sig"] >= hi, "H", "M"))
    out = {}
    for sz, sm in (("S", small), ("B", ~small)):
        for g in ("L", "M", "H"):
            sel = df[sm & (grp == g)]
            if len(sel):
                out[f"{sz}/{g}"] = sel["size"] / sel["size"].sum()
    return out


def factor_from_ports(port_ret, kind):
    """port_ret: dict name -> return (scalar or Series). kind: 'SMB' or 'HL' (high minus low)."""
    need = [f"{a}/{b}" for a in "SB" for b in "LMH"]
    if any(k not in port_ret for k in need):
        return np.nan
    if kind == "SMB":
        return sum(port_ret[f"S/{g}"] for g in "LMH") / 3 - sum(port_ret[f"B/{g}"] for g in "LMH") / 3
    return (port_ret["S/H"] + port_ret["B/H"]) / 2 - (port_ret["S/L"] + port_ret["B/L"]) / 2


def port_returns(weights, ret):
    """Apply fixed weights to returns. `ret`: Series (one period) or DataFrame (dates x codes)."""
    out = {}
    for name, w in weights.items():
        if isinstance(ret, pd.DataFrame):
            out[name] = ret.reindex(columns=w.index).fillna(0).to_numpy() @ w.to_numpy()
        else:
            out[name] = float(ret.reindex(w.index).fillna(0) @ w)
    return out
