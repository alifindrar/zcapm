"""File IO, logging and calendar helpers shared by all steps."""
import time
from pathlib import Path

import numpy as np
import pandas as pd

from config import settings as S


def log(step, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{step}] {msg}", flush=True)


def save(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(obj, path)


def load(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found - run the step that produces it (see step.md)")
    return pd.read_pickle(path)


def is_synthetic():
    return (S.RAW / "SYNTHETIC").exists()


def month_ends(dates):
    """Last trading date of each calendar month present in `dates`."""
    dates = pd.DatetimeIndex(dates)
    s = pd.Series(dates, index=dates)
    return pd.DatetimeIndex(s.groupby(dates.to_period("M")).max().to_numpy())


def window_mask(dates, T, months):
    """Boolean mask of `dates` inside the `months` calendar months ending with T's month."""
    start = (T.to_period("M") - (months - 1)).start_time
    return (dates >= start) & (dates <= T)


def compound_monthly(daily):
    """Compound daily returns to calendar months (PeriodIndex); NaN if no observation in the month."""
    key = daily.index.to_period("M")
    out = (1 + daily.fillna(0)).groupby(key).prod() - 1
    has = daily.notna().groupby(key).any()
    return out.where(has)


def to_markdown(df, floatfmt="{:.2f}"):
    cols = [str(df.index.name or "")] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for idx, row in df.iterrows():
        cells = [str(idx)]
        for v in row:
            if isinstance(v, (float, np.floating)):
                cells.append("" if np.isnan(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_table(df, name, note=""):
    S.OUT_TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(S.OUT_TABLES / f"{name}.csv")
    header = f"# {name}\n\n" + ("> SYNTHETIC DATA - plumbing test only\n\n" if is_synthetic() else "")
    (S.OUT_TABLES / f"{name}.md").write_text(header + to_markdown(df) + ("\n" + note + "\n" if note else ""),
                                             encoding="utf-8")
