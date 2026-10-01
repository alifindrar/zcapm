"""Run pipeline steps in order.

    python run_all.py                 # steps 01-07 (step 00 export must have been run)
    python run_all.py --from 3 --to 6
    python run_all.py --synthetic     # generate synthetic data first, then 01-07 (plumbing test)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = {0: "00_data_acquisition/run.py", 1: "01_universe_cleaning/run.py", 2: "02_market_factors/run.py",
         3: "03_zcapm_estimation/run.py", 4: "04_portfolio_formation/run.py", 5: "05_aggregate_portfolios/run.py",
         6: "06_evaluation/run.py", 7: "07_robustness/run.py"}


def arg(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    if "--synthetic" in sys.argv:
        subprocess.run([sys.executable, str(ROOT / "00_data_acquisition/make_synthetic.py"), "--force"], check=True)
    for k in range(arg("--from", 1), arg("--to", 7) + 1):
        print(f"\n===== step {k:02d}: {STEPS[k]} =====", flush=True)
        subprocess.run([sys.executable, str(ROOT / STEPS[k])], check=True)


if __name__ == "__main__":
    main()
