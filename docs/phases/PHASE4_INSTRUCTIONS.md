# Phase 4 Instructions — The Out-of-Sample Engine

This document specifies the Phase 4 work: the function signatures, docstrings, and
tests already exist in the repo — **the bodies of 3 functions** (marked `TODO 11` …
`TODO 13` in `src/copper_hedge/hedge.py`) are left to implement. The tests define
the acceptance criteria: the phase's code is complete when the suite goes green,
after which one script produces the phase's real-data numbers and its figure.

Nothing else in the repo needs to change. Background on the whole project is in
`README.md` and `docs/PROJECT_LOG.md` (Phase 4 is this piece of work). Phase 3's
in-sample numbers are the benchmark this phase is measured against.

---

## 1. What this phase does, in plain English

Phase 3 produced a flattering number: fit the optimal hedge ratio h\* on the full
2019–2026 history, measure how well it hedges *that same history*, get +34.1%.
That is "in-sample" — the ratio saw the answers before taking the test. No desk
can trade that way: on any given morning you only know the past.

Phase 4 builds the honest version. For **each day t**, estimate h\* using only
data **strictly before t** — never day t itself, never anything after — apply
that ratio to day t's price moves, and then measure effectiveness over all the
days traded this way. Three estimation schemes run side by side:

- **60d rolling** — use exactly the 60 most recent observations. Adapts fast,
  but noisy (60 points is a small sample).
- **120d rolling** — the 120 most recent. Steadier, slower to adapt.
- **Expanding** — all history so far (after a 60-observation burn-in). The
  steadiest of all, and the slowest to forget an old regime.

That trio is the classic **bias/variance tradeoff** made visible: short windows
chase the market (high variance), long windows average over regimes that may no
longer apply (bias).

The centerpiece of the phase is the **no-lookahead rule**. Backtests are easy to
accidentally cheat: let one future data point leak into an estimate and the
results inflate. Three tests attack this rule head-on — perturbing future data
must leave every past estimate bitwise unchanged, changing day t's own
observation must not move the ratio applied *at* t (the desk sets its hedge
before the day trades), and a rolling window must fully forget observations that
fell out of it. If your implementation passes those, the headline number is
defensible in a way the in-sample one is not.

Roll-flagged days (the contract-splice jumps flagged in
`data/hg_roll_flags.csv`) are excluded *before* the engine runs, same convention
as Phase 3 — so "60 observations" means 60 clean trading days.

## 2. Setup

Follow `docs/SETUP.md` if the environment isn't set up yet. Then:

```bash
uv sync          # one-time: reproduce the exact environment
uv run pytest    # run the full test suite
```

**Expected starting state: `18 failed, 58 passed`.** Every failure says
`NotImplementedError: TODO n` with n in 11–13 — those are the 3 functions to
implement, all in `src/copper_hedge/hedge.py`. The 58 passes are Phases 1–3,
which must stay green throughout. An import error or any other failure mode
instead means an environment problem — fix that first.

## 3. Where the code goes

| TODO | Function | Verified by (`tests/test_oos_hedge.py`) |
|---|---|---|
| 11 | `one_step_ahead_hedge_ratios` | `TestOneStepAheadHedgeRatios` |
| 12 | `apply_hedge_path` | `TestApplyHedgePath` |
| 13 | `out_of_sample_report` | `TestOutOfSampleReport` |

Each TODO site has a comment block with step-by-step notes and the pandas methods
worth looking at. The **docstring above each TODO is the contract** — it states
exactly what goes in and what must come out.

Suggested order: 11 → 12 → 13 (11 is the engine and carries all the subtlety,
12 is a small selector, 13 composes everything).

### `one_step_ahead_hedge_ratios` (TODO 11)

The engine. For each date, the hedge ratio is the same Cov/Var moment as
Phase 3's `optimal_hedge_ratio`, but computed over a trailing window of **prior**
observations only. The pandas idiom: compute the rolling (or expanding)
covariance and variance *including* each date, divide, then `.shift(1)` the
result — that one shift moves every estimate forward a step, so the value landing
on date t was computed from data through t−1. It is the entire no-lookahead
guarantee, and the tests probe it from three directions.

Conventions the tests pin down: `window=60` means the ratio is `NaN` until 60
prior observations exist (rolling's default `min_periods` does this for you);
`window=None` means expanding, `NaN` until `min_obs` prior observations exist.
The result keeps the input index and length.

### `apply_hedge_path` (TODO 12)

Given the (partly-NaN) ratio path, return the hedged daily changes
`ΔS − h_t·ΔF` on the dates where the ratio is defined, dropping the warm-up
entirely. Same arithmetic as the existing `hedged_changes`, with a Series of
ratios in place of the constant.

### `out_of_sample_report` (TODO 13)

Compose the pieces: build the path, hedge along it, and evaluate. One rule
matters: restrict **both** change series to the evaluation dates (the days with
a defined ratio) before computing anything — every number in the report,
including the naive 1:1 comparison (reuse `hedged_changes` and
`variance_reduction`), must be measured on that same set of days, or the
comparisons are apples to oranges. Return a dict with exactly the keys
`"n_days"`, `"unhedged_variance"`, `"hedged_variance"`, `"oos_effectiveness"`,
`"naive_effectiveness"` (plain floats).

## 4. How to test as you go

```bash
uv run pytest                                     # everything
uv run pytest tests/test_oos_hedge.py -q          # this phase only
uv run pytest tests/test_oos_hedge.py -q -x       # stop at first failure
uv run pytest tests/test_oos_hedge.py -k lookahead  # the centerpiece tests
```

Constraints (same as previous phases):

- **Don't edit the tests** — they are the acceptance criteria for this phase.
  Same for the other source modules (`data.py`, `roll.py`) and the CSVs in
  `data/`.
- Keep the functions **pure** (inputs → return value; no printing, no file I/O,
  no global state) and keep the type hints.
- Any pandas/numpy API is fair game; the TODO comments name the useful ones.

**The code is complete when: `uv run pytest` → `76 passed`.**

## 5. Produce the real numbers and the figure

With all tests green, run this from the repo root. It runs the engine on the
real 2019–2026 LME-vs-futures data (roll-flagged days excluded via the committed
`data/hg_roll_flags.csv`), prints the phase's headline numbers, and saves the
phase's figure to `figures/rolling_hedge_ratio.png`:

```bash
uv run python - <<'EOF'
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

# LME (primary) spot leg vs futures, both with roll-flagged days excluded
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

# The Phase 4 figure: the three one-step-ahead hedge-ratio paths
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
EOF
```

### Expected numbers (checked against a reference implementation)

An implementation that follows the contracts exactly should reproduce these on
the committed data snapshot (2019-01-02 → 2026-08-12; 1,845 observations after
excluding the 29 flagged roll days). The in-sample line must print h\* 0.5025,
effectiveness +34.1% — Phase 3's numbers, unchanged.

| Quantity | 60d window | 120d window | Expanding |
|---|---|---|---|
| Evaluation days | **1,785** | **1,725** | **1,785** |
| OOS effectiveness | **+33.5%** | **+33.1%** | **+33.8%** |
| Naive 1:1 on the same days | **+0.6%** | **+0.6%** | **+0.6%** |
| Ratio path: min | 0.0479 | 0.1331 | 0.4246 |
| Ratio path: median | 0.5272 | 0.5191 | 0.5190 |
| Ratio path: max | 0.7838 | 0.7150 | 0.5641 |

What the numbers are saying:

- **The headline: ≈ +33–34% out-of-sample, vs +0.6% for the naive hedge.** The
  optimal-hedge advantage survives the honest test almost intact — a hedge
  ratio estimated only from the past removes a third of daily variance, where
  hedging 1:1 removes essentially nothing.
- **OOS sits just below the in-sample +34.1% (by less than one point).** The
  degradation is small because the LME–COMEX relationship is fairly stable —
  h\* has hovered near 0.5 for most of seven years, so estimating it honestly
  from history costs little. Small degradation is the *good* outcome; a large
  gap would mean the in-sample number was an artifact.
- **The three schemes finish within 0.7 points of each other** (expanding
  slightly best, 120d slightly worst). With a mostly-stable beta, the
  low-variance expanding estimate wins; the window sizes matter more in the
  *path* than in the total (see the figure).
- **The 60d path's excursions are real events, not bugs**: it dips to ≈ 0.11 in
  late 2020 and to its 0.048 minimum on 2025-10-23, deep in the US-tariff
  dislocation when COMEX decoupled from LME — the engine responded by cutting
  the hedge to almost nothing, which is exactly what a moment-matching hedger
  would have done.

### What the figure should look like

Three lines oscillating around the dotted full-sample h\* ≈ 0.50: the 60d line
visibly jumpiest, the 120d line a smoothed version of it, and the expanding line
almost flat (drifting within ≈ 0.42–0.56). Two episodes stand out — a dip in
late 2020 and a much deeper plunge toward zero in late 2025. No line ever goes
above ≈ 0.8 or meaningfully below 0. If your figure shows ratios near 1, wild
oscillation in the expanding line, or lines starting on day one (no warm-up
gap), something is wrong even if the tests pass.

## 6. Completion checklist

- [ ] `uv run pytest` → **76 passed**, with `tests/` unmodified
- [ ] The Section 5 script runs, prints all four blocks, and saves
      `figures/rolling_hedge_ratio.png`
- [ ] The printed numbers match the expected table above and the figure matches
      the description
- [ ] **Report the numbers back before pushing anything to main** — reply with
      the script output (or the table) plus anything that looked off or
      surprising. This is the step that keeps slipping: in Phases 2 and 3 the
      implementation landed on main before the numbers were cross-checked.
      Both times the check passed, but the order exists for the time it
      doesn't — numbers first, push after they're confirmed.

Committing locally is fine (conventional message, e.g.
`feat: implement out-of-sample hedge engine (phase 4)`).
