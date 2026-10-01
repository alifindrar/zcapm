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

DATA = ROOT / "data"
RAW = DATA / f"raw{_SFX}"
EXTERNAL = DATA / "external"            # shared by all versions
INTERIM = DATA / f"interim{_SFX}"
PROCESSED = DATA / f"processed{_SFX}"
OUT_TABLES = ROOT / "outputs" / f"tables{_SFX}"
OUT_FIGS = ROOT / "outputs" / f"figures{_SFX}"

# idx-api (Deno + SQLite) — data source for step 00
IDX_API_DIR = ROOT.parent / "_arcip" / "idx-api"
IDX_API_DB = IDX_API_DIR / "data" / "database.sqlite"

# ---------------------------------------------------------------- sample
START_DATE = "2000-01-01"
END_DATE = None                 # None = latest available
TRADING_DAYS = 242              # IDX trading days per year

# ---------------------------------------------------------------- universe (step 01)
CODE_REGEX = r"^[A-Z]{4}$"      # common stocks only (drops warrants/rights "-W", "-R", DIRE/DINFRA)
EXCLUDE_PREFIXES = ("X",)       # ETFs
EXCLUDE_REMARK_REGEX = None     # e.g. r"X" once the IDX remarks notation for Papan Pemantauan Khusus is verified
MAX_ABS_DAILY_RET = 1.0         # |r| > 100% set to NaN and logged
SIZE_CUT = 0.10                 # drop bottom share of market cap at latest year-end
MIN_OBS = 200                   # min traded days in the estimation window
MAX_ZERO_FRAC = 0.20            # max share of zero-return traded days in the window
MIN_PRICE = 50                  # exclude stocks at/below the Rp 50 floor

# ---------------------------------------------------------------- market factors (step 02)
MARKET_PROXY = "own_vw"         # "own_vw" (cap-weighted from universe) or "ihsg"
IHSG_CODE = "COMPOSITE"
RF_FILE = EXTERNAL / "rf.csv"   # columns: date, rate_annual_pct
RF_FALLBACK_ANNUAL_PCT = None   # e.g. 5.0 for a prototype run without rf.csv (warns)
RATIO_LAG_MONTHS = 4            # financial ratios usable this many months after period end
FACTOR_BREAKS = (0.3, 0.7)      # 2x3 sort breakpoints for HML / MOM

# ---------------------------------------------------------------- estimation (step 03)
WINDOW_MONTHS = 12
EM_TOL = 1e-8
EM_MAXIT = 500
EM_STARTS = (0.25, 0.5, 0.75)   # initial p values; best log-likelihood kept

# ---------------------------------------------------------------- portfolios (step 04)
SORT_SCHEME = "book24"          # "book24" (1%, 2%, 10 x 5%), "deciles" (5 x 10%), "quintiles" (2 x 20%)
MIN_LEG_SIZE = 5                # warn when the smallest leg holds fewer stocks
G_VOL_RATIO = 0.2               # drop stocks with daily SD < ratio x market SD (portfolio g)
G_ZETA_OFFSET = 0.01
G_WEIGHT_CAP = 0.05             # None = no cap
DELIST_RETURN = -0.30           # applied in the month a stock stops trading

# ---------------------------------------------------------------- robustness (step 07)
COST_BUY = 0.0019               # incl. broker + levy (approx.)
COST_SELL = 0.0029              # incl. 0.1% sales tax (approx.)
NW_LAGS = 6
SUBPERIODS = [("2001-01", "2007-12"), ("2008-01", "2019-12"), ("2020-01", None)]
FACTOR_SORTS = ("SMB", "HML", "MOM")
