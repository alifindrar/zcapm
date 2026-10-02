"""Build data/external/rf.csv - the short risk-free rate used by step 02 (audit F7).

    python 02_market_factors/build_rf.py [--fetch]

Series sources:
  1995-01 .. 2016-07: Bank Indonesia discount rate / BI policy rate via FRED (IRSTCB01IDM156N)
                      -> data/external/rf_bi_rate_fred.csv
  2016-08 .. present: Bank Indonesia 7-Day (Reverse) Repo Rate / BI-Rate via bi.go.id
                      -> data/external/rf_bi_rate_bi_go_id.csv
  (optional override): if data/external/rf_idn1m_tradingeconomics.csv exists, it splices
                      the 1-month bill yield from its first available month.

Monthly series are stamped at the month end so step 02 (which uses the rate known at
the start of each day) never uses a value before it existed.
"""
import argparse
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import settings as S  # noqa: E402
from lib.io import log  # noqa: E402

STEP = "02-rf"
BILL_FILE = S.EXTERNAL / "rf_idn1m_tradingeconomics.csv"
FRED_FILE = S.EXTERNAL / "rf_bi_rate_fred.csv"
BI_GO_ID_FILE = S.EXTERNAL / "rf_bi_rate_bi_go_id.csv"
SPLICE_DATE_BI7DRR = pd.Timestamp("2016-08-31")  # official start of BI 7-day reverse repo rate
START_DATE = "1995-01-01"


def fetch_fred():
    """Fetch central bank policy rate for Indonesia from FRED (IRSTCB01IDM156N)."""
    log(STEP, "Fetching FRED series IRSTCB01IDM156N...")
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCB01IDM156N"
    cmd = ["curl", "-s", "-f", "-L", url]
    out = subprocess.check_output(cmd)
    from io import StringIO
    df = pd.read_csv(StringIO(out.decode("utf-8")), parse_dates=["observation_date"])
    df.rename(columns={"observation_date": "month", "IRSTCB01IDM156N": "rate_annual_pct"}, inplace=True)
    df["rate_annual_pct"] = pd.to_numeric(df["rate_annual_pct"], errors="coerce")
    df = df.dropna(subset=["rate_annual_pct"]).sort_values("month")
    df.to_csv(FRED_FILE, index=False)
    log(STEP, f"Saved {FRED_FILE.name}: {len(df)} months ({df['month'].iloc[0]:%Y-%m}..{df['month'].iloc[-1]:%Y-%m})")


def fetch_bi_go_id():
    """Fetch BI-Rate / BI7DRR history from bi.go.id."""
    log(STEP, "Fetching BI-Rate export from bi.go.id...")
    from bs4 import BeautifulSoup

    page_url = "https://www.bi.go.id/en/statistik/indikator/bi-rate.aspx"
    scratch_dir = ROOT / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    cookie_jar = scratch_dir / "bi_cookies.txt"
    cmd_get = [
        "curl", "-s", "-f", "-L", "-c", str(cookie_jar),
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        page_url,
    ]
    html = subprocess.check_output(cmd_get).decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    form_data = {}
    for inp in soup.find_all("input"):
        name = inp.get("name")
        val = inp.get("value", "")
        if name:
            form_data[name] = val

    btn_export_key = next((k for k in form_data if "ButtonExport" in k), None)
    btn_search_key = next((k for k in form_data if "ButtonSearch" in k), None)
    date_start_key = next((k for k in form_data if "TextBoxDateStart" in k), None)
    date_end_key = next((k for k in form_data if "TextBoxDateEnd" in k), None)

    if not btn_export_key or not date_start_key:
        raise RuntimeError("Unable to locate ASP.NET export form elements on bi.go.id")

    form_data[date_start_key] = "01/01/2016"
    form_data[date_end_key] = "31/12/2030"
    form_data[btn_export_key] = "Download"
    if btn_search_key in form_data:
        del form_data[btn_search_key]

    post_file = scratch_dir / "bi_post.bin"
    post_file.write_bytes(urllib.parse.urlencode(form_data).encode("utf-8"))

    raw_xlsx = scratch_dir / "bi_rate_export.xlsx"
    cmd_post = [
        "curl", "-s", "-f", "-L", "-b", str(cookie_jar),
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "-d", f"@{post_file}", page_url, "-o", str(raw_xlsx),
    ]
    subprocess.run(cmd_post, check=True)

    with zipfile.ZipFile(raw_xlsx, "r") as z:
        shared_strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in tree.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                text = "".join(t.text or "" for t in si.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
                shared_strings.append(text)

        sheet_tree = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        rows = []
        for r in sheet_tree.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
            row_vals = []
            for c in r.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                t = c.get("t")
                v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                val = v.text if v is not None else ""
                if t == "s" and val.isdigit():
                    val = shared_strings[int(val)]
                row_vals.append(val)
            rows.append(row_vals)

    months_map = {
        "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
        "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    }
    bi_rows = []
    for r in rows[2:]:
        if len(r) >= 3:
            parts = r[1].strip().split()
            if len(parts) == 3:
                day, mon_str, year = int(parts[0]), parts[1].lower(), int(parts[2])
                mon = months_map.get(mon_str)
                if mon is not None:
                    rate = float(r[2].replace("%", "").strip())
                    bi_rows.append({"date": f"{year:04d}-{mon:02d}-{day:02d}", "rate_annual_pct": rate})

    df_bi = pd.DataFrame(bi_rows).sort_values("date")
    df_bi.to_csv(BI_GO_ID_FILE, index=False)
    log(STEP, f"Saved {BI_GO_ID_FILE.name}: {len(df_bi)} decisions ({df_bi['date'].iloc[0]}..{df_bi['date'].iloc[-1]})")


def fred_monthly(path):
    d = pd.read_csv(path, parse_dates=["month"])
    return pd.Series(d["rate_annual_pct"].to_numpy(), index=d["month"] + pd.offsets.MonthEnd(0)).dropna()


def bi_monthly(path):
    d = pd.read_csv(path, parse_dates=["date"])
    d["month_end"] = d["date"] + pd.offsets.MonthEnd(0)
    m = d.groupby("month_end")["rate_annual_pct"].last().sort_index()
    return m


def bill_monthly(path):
    """Any export with one date column and one yield column (% p.a.) -> last value of each month."""
    d = pd.read_csv(path)
    dcol = next(c for c in d.columns if c.strip().lower() in ("date", "datetime", "time", "observation_date"))
    num = d.drop(columns=dcol).apply(pd.to_numeric, errors="coerce")
    vcol = next((c for c in num.columns if c.strip().lower() in ("close", "value", "price", "last", "yield")),
                num.notna().sum().idxmax())
    s = pd.Series(num[vcol].to_numpy(), index=pd.to_datetime(d[dcol])).dropna().sort_index()
    if not 0 < s.median() < 40:
        sys.exit(f"{path.name}: column '{vcol}' does not look like a yield in % p.a. (median {s.median():.3f})")
    m = s.groupby(s.index.to_period("M")).last()
    return pd.Series(m.to_numpy(), index=m.index.to_timestamp(how="end").normalize())


def main():
    parser = argparse.ArgumentParser(description="Build data/external/rf.csv from BI rate and 1-month bill yield")
    parser.add_argument("--fetch", action="store_true", help="Download fresh series from FRED and bi.go.id")
    args = parser.parse_args()

    if args.fetch or not FRED_FILE.exists():
        fetch_fred()
    if args.fetch or not BI_GO_ID_FILE.exists():
        fetch_bi_go_id()

    pre = fred_monthly(FRED_FILE)
    post_bi = bi_monthly(BI_GO_ID_FILE)

    # Core BI rate series: FRED before 2016-08-31, BI website from 2016-08-31
    pre = pre[pre.index < SPLICE_DATE_BI7DRR]
    post_bi = post_bi[post_bi.index >= SPLICE_DATE_BI7DRR]

    df_pre = pd.DataFrame({"date": pre.index, "rate_annual_pct": pre.values, "source": "bi_rate_fred"}).set_index("date")
    df_post = pd.DataFrame({"date": post_bi.index, "rate_annual_pct": post_bi.values, "source": "bi_rate_bi_go_id"}).set_index("date")
    bi_combined = pd.concat([df_pre, df_post]).sort_index()

    if BILL_FILE.exists():
        post_bill = bill_monthly(BILL_FILE)
        splice = post_bill.index[0]
        out_pre = bi_combined[bi_combined.index < splice]
        out_post = pd.DataFrame({"rate_annual_pct": post_bill[post_bill.index >= splice], "source": "idn_1m_bill_tradingeconomics"})
        out = pd.concat([out_pre, out_post]).sort_index()
        log(STEP, f"Spliced 1-month bill yield from {splice:%Y-%m}")
    else:
        out = bi_combined

    out = out[out.index >= START_DATE]
    out.index.name = "date"
    out.to_csv(S.RF_FILE, date_format="%Y-%m-%d")

    log(STEP, f"{S.RF_FILE.name}: {len(out)} months {out.index[0]:%Y-%m}..{out.index[-1]:%Y-%m}")
    log(STEP, f"mean {out.rate_annual_pct.mean():.2f}% p.a. "
              f"(since 2007-04: {out.loc['2007-04':, 'rate_annual_pct'].mean():.2f}%)")


if __name__ == "__main__":
    main()
