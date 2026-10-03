"""Shared parameters for the ZCAPM Chapter 9 replication on IHSG (see step.md §3)."""
import os
from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[1]

# Data source version: "v2" = dbv2 (v1 + STOCKDB, build_dbv2.py), "v1" = original idx-api based data.
# Each version has its own raw/interim/processed/outputs folders so runs never overwrite each other.
# Override with the ZCAPM_DB environment variable (e.g. ZCAPM_DB=v1).
DB_VERSION = os.environ.get("ZCAPM_DB", "v2")
_SFX = "" if DB_VERSION == "v1" else f"_{DB_VERSION}"

# Specification switches. The headline run uses the defaults; a robustness run sets an environment variable and
# writes to its own folders, so it never overwrites the headline files:
#   ZCAPM_ZERO=0.20|0.50   zero-return threshold  -> interim/processed/outputs get a "_z20" / "_z50" suffix
#   ZCAPM_SCHEME=book24    sort scheme            -> processed/outputs get a "_book24" suffix (estimates are shared)
_ZERO_DEFAULT, _SCHEME_DEFAULT = 0.35, "deciles"
MAX_ZERO_FRAC = float(os.environ.get("ZCAPM_ZERO", _ZERO_DEFAULT))   # max share of zero-return traded days
SORT_SCHEME = os.environ.get("ZCAPM_SCHEME", _SCHEME_DEFAULT)        # "deciles", "book24", "quintiles"
_ZSFX = "" if MAX_ZERO_FRAC == _ZERO_DEFAULT else f"_z{round(100 * MAX_ZERO_FRAC):d}"
_PSFX = _ZSFX + ("" if SORT_SCHEME == _SCHEME_DEFAULT else f"_{SORT_SCHEME}")

DATA = ROOT / "data"
RAW = DATA / f"raw{_SFX}"
EXTERNAL = DATA / "external"            # shared by all versions
INTERIM = DATA / f"interim{_SFX}{_ZSFX}"
PROCESSED = DATA / f"processed{_SFX}{_PSFX}"
OUT_TABLES = ROOT / "outputs" / f"tables{_SFX}{_PSFX}"
OUT_FIGS = ROOT / "outputs" / f"figures{_SFX}{_PSFX}"

# idx-api (Deno + SQLite) — data source for step 00
IDX_API_DIR = ROOT.parent / "_arcip" / "idx-api"
IDX_API_DB = IDX_API_DIR / "data" / "database.sqlite"

# ---------------------------------------------------------------- sample
START_DATE = "2005-01-01"       # 2000-2004 holds 17-28 codes, one of them 45-98% of the index (audit F5)
END_DATE = None                 # None = latest available
TRADING_DAYS = 242              # IDX trading days per year

# ---------------------------------------------------------------- universe (step 01)
CODE_REGEX = r"^[A-Z]{4}$"      # common stocks only (drops warrants/rights "-W", "-R", DIRE/DINFRA)
EXCLUDE_PREFIXES = ("X",)       # ETFs
EXCLUDE_REMARK_REGEX = None     # e.g. r"X" once the IDX remarks notation for Papan Pemantauan Khusus is verified
MAX_ABS_DAILY_RET = 1.0         # |r| > 100% set to NaN and logged (backstop, applies to listing days too)
RET_LIMIT = 0.35                # widest regular IDX auto-rejection band; larger moves are screened (lib/cleaning.py)
RET_TOL = 0.02                  # screen only beyond RET_LIMIT + RET_TOL: a limit move lands at +35.0..36.x% after float
                                # noise and tick rounding (Rp 1 tick at Rp 50 = 2%) and is a genuine return
RET_LISTING_ROWS = 5            # first rows of a code are exempt from the screen (IPO days / data start)
RET_REVERT_ROWS = 3             # a move beyond RET_LIMIT that returns to the old level within this many rows ...
RET_REVERT_BAND = 0.15          # ... (to within this band) is a data spike: every return of the round trip is dropped
RET_LEVEL_ROWS = 10             # a screened level shift ('other') reversed by one opposite move within this many rows:
                                # the reversing return is dropped too, so the level ends where it started (e.g. APIC 2005)
SIZE_CUT = 0.10                 # drop bottom share of market cap at latest year-end
SIZE_FFILL_DAYS = 20            # year-end market cap carried forward this many rows when the stock did not trade
MIN_OBS = 200                   # min traded days in the estimation window
MIN_PRICE = 50                  # exclude stocks at/below the Rp 50 floor (nominal price when the raw file has it)
BUY_TRADE_ROWS = 10             # eligible only with a trade in the last this-many rows up to T (not suspended at T)

# ---------------------------------------------------------------- market factors (step 02)
MARKET_PROXY = "own_vw"         # "own_vw" (cap-weighted from universe) or "ihsg"
IHSG_CODE = "COMPOSITE"
RF_FILE = EXTERNAL / "rf.csv"   # columns: date, rate_annual_pct; built by 02_market_factors/build_rf.py
RF_FALLBACK_ANNUAL_PCT = None   # e.g. 5.0 for a prototype run without rf.csv (warns)
RATIO_LAG_MONTHS = 4            # financial ratios usable this many months after period end
FACTOR_BREAKS = (0.3, 0.7)      # 2x3 sort breakpoints for HML / MOM

# ---------------------------------------------------------------- estimation (step 03)
WINDOW_MONTHS = 12
EM_TOL = 1e-8
EM_MAXIT = 500
EM_STARTS = (0.25, 0.5, 0.75)   # initial p values; best log-likelihood kept

# ---------------------------------------------------------------- portfolios (step 04)
# SORT_SCHEME (top of file): "deciles" (5 x 10%, headline), "book24" (1%, 2%, 10 x 5%, appendix), "quintiles" (2 x 20%)
MIN_LEG_SIZE = 5                # smallest number of stocks in a leg
ENFORCE_MIN_LEG = SORT_SCHEME != "book24"   # skip formation months with a smaller leg (book24: only warn)
ZSTAR_SCALE = 21                # Z* is reported and used in g on the book's monthly scale (daily Z* x 21)
G_VOL_RATIO = 0.2               # drop stocks with daily SD < ratio x market SD (portfolio g)
G_ZETA_OFFSET = 0.01            # added to |Z*| on the ZSTAR_SCALE scale, as in the book
G_WEIGHT_CAP = 0.05             # None = no cap. Not in the book: without it one stock reaches 66% of g (audit F9)
DELIST_RETURN = -0.30           # month a stock stops trading, forced or unclassified delisting
DELIST_RETURN_VOLUNTARY = 0.0   # voluntary delisting / merger (holders are bought out or swapped)
DELIST_EXTRA_FILE = EXTERNAL / "delistings_extra.csv"   # code, delisting_date, reason, note - adds to / overrides raw
VOLUNTARY_REASONS = ("voluntary", "merger")

# ---------------------------------------------------------------- robustness (step 07)
# Stockbit Sekuritas fee schedule (help.stockbit.com, "Berapa biaya trading di Stockbit Sekuritas"), regular stocks.
# ETF / right / warrant (0.15% both ways) are outside the universe; deposits are free, a withdrawal costs Rp 6,500.
COST_BUY = 0.0015               # buy fee
COST_SELL = 0.0025              # sell fee, incl. 0.1% final income tax (PPh)
STAMP_DUTY = 10_000             # Rp per trade confirmation (one per trading day) ...
STAMP_DUTY_MIN = 10e6           # ... when the day's total buy + sell value is above this (Rp); step 08 only
NW_LAGS = 6
SUBPERIODS = [("2005-01", "2013-12"), ("2014-01", "2019-12"), ("2020-01", None)]
FACTOR_SORTS = ("SMB", "HML", "MOM")
