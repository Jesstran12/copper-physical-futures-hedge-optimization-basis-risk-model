"""Regenerate figures/rolling_hedge_ratio.png and print the out-of-sample numbers.

Run from the repo root: uv run python scripts/rolling_hedge_figure.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from copper_hedge.data import load_aligned
from copper_hedge.hedge import (
    exclude_roll_days,
    one_step_ahead_hedge_ratios,
    optimal_hedge_report,
    out_of_sample_report,
    price_changes,
)

aligned, dropped = load_aligned(Path("data"))
flags = pd.read_csv(
    "data/hg_roll_flags.csv", parse_dates=["date"], index_col="date"
)["is_roll"]

delta_s = exclude_roll_days(price_changes(aligned["lme_usd_per_lb"]), flags)
delta_f = exclude_roll_days(price_changes(aligned["hg_usd_per_lb"]), flags)

in_sample = optimal_hedge_report(delta_s, delta_f)
print(f"[LME spot leg, $/lb]  n={len(delta_s)} obs (roll days excluded)")
print(f"  in-sample (Phase 3) : h* {in_sample['hedge_ratio']:.4f}, "
      f"effectiveness {in_sample['effectiveness']:+.1%}")

schemes = [("60d", 60), ("120d", 120), ("expanding", None)]
paths = {}
for label, window in schemes:
    report = out_of_sample_report(delta_s, delta_f, window=window)
    paths[label] = one_step_ahead_hedge_ratios(delta_s, delta_f, window=window)
    print(f"\n[{label} window]  n={report['n_days']:.0f} evaluation days")
    print(f"  OOS effectiveness       : {report['oos_effectiveness']:+.1%}")
    print(f"  naive 1:1 on same days  : {report['naive_effectiveness']:+.1%}")
    h = paths[label].dropna()
    print(f"  hedge-ratio path        : min {h.min():.4f}, "
          f"median {h.median():.4f}, max {h.max():.4f}")

fig, ax = plt.subplots(figsize=(10, 5))
for label, style in [("60d", "-"), ("120d", "-"), ("expanding", "--")]:
    ax.plot(paths[label].index, paths[label], style, lw=1.2,
            label=f"{label} window")
ax.axhline(in_sample["hedge_ratio"], color="gray", lw=0.8, ls=":",
           label=f"full-sample h* = {in_sample['hedge_ratio']:.2f}")
ax.axhline(0, color="black", lw=0.5)
ax.set_title("One-step-ahead hedge ratio, LME leg (no lookahead)")
ax.set_ylabel("hedge ratio h*")
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig("figures/rolling_hedge_ratio.png", dpi=150)
print("\nSaved figures/rolling_hedge_ratio.png")