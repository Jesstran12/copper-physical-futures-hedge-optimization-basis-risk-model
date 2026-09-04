# Phase 5 Instructions — Robustness: Weekly Changes + Regime Table

This document specifies the Phase 5 work: the function signatures, docstrings, and
tests already exist in the repo — **the bodies of 4 functions** (marked `TODO 14` …
`TODO 17` in `src/copper_hedge/hedge.py`) are left to implement. The tests define
the acceptance criteria: the phase's code is complete when the suite goes green,
after which one script produces the phase's real-data numbers.

Nothing else in the repo needs to change. Background on the whole project is in
`README.md` and `docs/PROJECT_LOG.md` (Phase 5 is this piece of work). Phases 3–4's
daily numbers are the benchmark this phase is measured against.

---

## 1. What this phase does, in plain English

Every daily number so far carries a hidden handicap: the two price series are not
snapped at the same moment. The LME cash price is fixed around 1pm **London**
time; the COMEX futures settle around 1pm **New York** time — five hours later.
Part of every day's futures move only shows up in the *next* day's LME print, so
the daily correlation (and with it the +34.1% daily effectiveness) understates
how well the two markets actually track each other.

Phase 5 runs two credibility checks on that story:

- **Weekly re-run.** Measure the same core numbers on **Friday-to-Friday weekly
  changes** instead of daily ones. A few hours of timing mismatch inside a
  five-day move is noise that mostly cancels out — so if the async-close story
  is right, weekly effectiveness should come out clearly *higher* than daily.
  (It does — see the expected numbers.)
- **Sub-period table.** Re-fit the hedge inside five market regimes (2019 calm,
  2020 COVID, 2021–23 tightness, 2024 squeeze era, 2025+ tariff era) and report
  each regime's h\* and effectiveness. This shows whether the full-sample
  answer is one stable relationship or an average over wildly different ones.

Roll handling carries over from Phases 2–4, extended to the weekly frequency: a
weekly change that *contains* a roll-flagged day is contaminated by the same
splice jump, so that week is excluded from the weekly regression. The daily
sub-period table uses the same roll-excluded daily changes as Phases 3–4.

## 2. Setup

Follow `docs/SETUP.md` if the environment isn't set up yet. Then:

```bash
uv sync          # one-time: reproduce the exact environment
uv run pytest    # run the full test suite
```

**Expected starting state: `19 failed, 77 passed`.** Every failure says
`NotImplementedError: TODO n` with n in 14–17 — those are the 4 functions to
implement, all in `src/copper_hedge/hedge.py`. The 77 passes are Phases 1–4
plus one Phase 5 test of a provided constant, and they must stay green
throughout. An import error or any other failure mode instead means an
environment problem — fix that first.

## 3. Where the code goes

| TODO | Function | Verified by (`tests/test_robustness.py`) |
|---|---|---|
| 14 | `resample_weekly_last` | `TestResampleWeeklyLast` |
| 15 | `weekly_roll_flags` | `TestWeeklyRollFlags` |
| 16 | `weekly_hedge_report` | `TestWeeklyHedgeReport` |
| 17 | `sub_period_report` | `TestSubPeriodReport` |

Each TODO site has a comment block with step-by-step notes and the pandas methods
worth looking at. The **docstring above each TODO is the contract** — it states
exactly what goes in and what must come out. The five regime definitions are
already provided as the `SUB_PERIODS` constant just above the stubs (that is the
one Phase 5 test already passing).

Suggested order: 14 → 15 → 16 → 17 (14 and 15 are one-liners, 16 composes them
with existing Phase 2–3 functions, 17 is independent of the other three).

### `resample_weekly_last` (TODO 14)

Daily prices in, weekly prices out. Weeks are the pandas `"W-FRI"` convention —
Saturday through Friday, labeled by the Friday — and each week contributes its
**last** available observation. That makes the values Friday closes in a normal
week, and Thursday's close when the Friday is a holiday (or was dropped by the
calendar inner-join); either way the label stays the Friday. Weeks with no
observations at all are dropped entirely, never NaN-filled — the no-forward-fill
rule from Phase 1 applies at every frequency.

### `weekly_roll_flags` (TODO 15)

Daily roll flags in, weekly roll flags out: a week is flagged if **any** of its
days is flagged. The weekly change labeled Friday t spans everything after the
previous Friday through t, so a splice jump anywhere in that span contaminates
the whole weekly observation. Same `"W-FRI"` labeling as TODO 14, so the flags
line up with the weekly changes by date.

### `weekly_hedge_report` (TODO 16)

The weekly counterpart of Phase 3's `optimal_hedge_report`, built entirely from
parts that already exist. Note it takes **price levels**, not changes —
resampling must happen on prices first, then difference. Resample both legs
(TODO 14), difference with `price_changes`, drop flagged weeks on both sides
with `exclude_roll_days` + your weekly flags (TODO 15), then report. Return a
dict with exactly the keys `"n_weeks"`, `"hedge_ratio"`, `"r_squared"`,
`"unhedged_variance"`, `"hedged_variance"`, `"effectiveness"`,
`"naive_effectiveness"` (plain floats).

### `sub_period_report` (TODO 17)

For each `(label, start, end)` period, slice both change series by date (both
endpoints inclusive) and fit the in-sample optimal hedge on that slice alone —
observations outside a period must never influence its row; one test perturbs
outside data and asserts the row is bitwise unchanged. Returns a DataFrame
indexed by the labels with columns `"n_obs"`, `"hedge_ratio"`,
`"effectiveness"`.

## 4. How to test as you go

```bash
uv run pytest                                      # everything
uv run pytest tests/test_robustness.py -q          # this phase only
uv run pytest tests/test_robustness.py -q -x       # stop at first failure
uv run pytest tests/test_robustness.py -k async    # the weekly-beats-daily test
```

Constraints (same as previous phases):

- **Don't edit the tests** — they are the acceptance criteria for this phase.
  Same for the other source modules (`data.py`, `roll.py`), the already-
  implemented Phase 2–4 functions in `hedge.py`, and the CSVs in `data/`.
- Keep the functions **pure** (inputs → return value; no printing, no file I/O,
  no global state) and keep the type hints.
- Any pandas/numpy API is fair game; the TODO comments name the useful ones.

**The code is complete when: `uv run pytest` → `96 passed`.**

## 5. Produce the real numbers

With all tests green, run this from the repo root. It re-runs the daily
benchmark, the weekly re-run, and the sub-period table on the real 2019–2026
LME-vs-futures data:

```bash
uv run python - <<'EOF'
from pathlib import Path

import pandas as pd

from copper_hedge.data import load_aligned
from copper_hedge.hedge import (
    SUB_PERIODS,
    exclude_roll_days,
    optimal_hedge_report,
    price_changes,
    sub_period_report,
    weekly_hedge_report,
)

aligned, dropped = load_aligned(Path("data"))
flags = pd.read_csv(
    "data/hg_roll_flags.csv", parse_dates=["date"], index_col="date"
)["is_roll"]

# Daily benchmark (Phase 3's numbers, LME leg, roll days excluded)
delta_s = exclude_roll_days(price_changes(aligned["lme_usd_per_lb"]), flags)
delta_f = exclude_roll_days(price_changes(aligned["hg_usd_per_lb"]), flags)
daily = optimal_hedge_report(delta_s, delta_f)
print(f"[daily, LME leg]  n={len(delta_s)} obs (roll days excluded)")
print(f"  h* {daily['hedge_ratio']:.4f}  corr {daily['r_squared']**0.5:.4f}  "
      f"R^2 {daily['r_squared']:.4f}  effectiveness {daily['effectiveness']:+.1%}")

# Weekly re-run (Fri-anchored weeks on common days, roll weeks excluded)
weekly = weekly_hedge_report(
    aligned["lme_usd_per_lb"], aligned["hg_usd_per_lb"], flags
)
print(f"\n[weekly, LME leg]  n={weekly['n_weeks']:.0f} weeks (roll weeks excluded)")
print(f"  h* {weekly['hedge_ratio']:.4f}  corr {weekly['r_squared']**0.5:.4f}  "
      f"R^2 {weekly['r_squared']:.4f}  effectiveness {weekly['effectiveness']:+.1%}")
print(f"  naive 1:1 weekly        : {weekly['naive_effectiveness']:+.1%}")
print(f"  daily -> weekly effectiveness: "
      f"{daily['effectiveness']:+.1%} -> {weekly['effectiveness']:+.1%}")

# Sub-period table (daily changes, roll days excluded, 5 regimes)
table = sub_period_report(delta_s, delta_f, SUB_PERIODS)
table["effectiveness"] = table["effectiveness"].map(lambda e: f"{e:+.1%}")
table["hedge_ratio"] = table["hedge_ratio"].map(lambda h: f"{h:.4f}")
print("\n[sub-periods, daily, LME leg]")
print(table.to_string())
EOF
```

### Expected numbers (checked against a reference implementation)

An implementation that follows the contracts exactly should reproduce these on
the committed data snapshot (2019-01-02 → 2026-08-12). The daily line must
print n=1845, h\* 0.5025, R² 0.3405, effectiveness +34.1% — Phase 3's numbers,
unchanged.

| Quantity | Daily | Weekly |
|---|---|---|
| Observations | 1,845 days | **375 weeks** |
| h\* | 0.5025 | **0.7276** |
| Correlation | 0.5836 | **0.8364** |
| R² = effectiveness | 0.3405 (+34.1%) | **0.6996 (+70.0%)** |
| Naive 1:1 on the same observations | +0.7% (Phase 2) | **+60.2%** |

Sub-period table (daily changes, roll days excluded):

| Period | n_obs | h\* | Effectiveness |
|---|---|---|---|
| 2019 calm | **244** | **0.4618** | **+26.6%** |
| 2020 COVID | **246** | **0.4562** | **+23.1%** |
| 2021-23 tightness | **727** | **0.5639** | **+35.4%** |
| 2024 squeeze era | **242** | **0.5026** | **+36.2%** |
| 2025+ tariff era | **386** | **0.4524** | **+34.6%** |

What the numbers are saying:

- **The headline: effectiveness roughly doubles at the weekly frequency,
  +34.1% → +70.0%.** That is the async-close prediction confirmed: hours of
  London/New York timing mismatch are a large part of a one-day change and a
  small part of a one-week change. The measured daily number understates the
  true LME–COMEX relationship; weekly is closer to the hedge's real quality.
- **h\* rises from 0.50 toward 1 (0.73 weekly).** Timing noise in ΔF biases
  the fitted slope toward zero (classic attenuation); as the noise washes out,
  the slope recovers toward the ≈1 you'd expect for two prices of the same
  metal.
- **Even the naive 1:1 hedge works at the weekly frequency (+60.2% vs +0.7%
  daily).** A desk that rebalances weekly and hedges dollar-for-dollar does
  fine; it is the *daily* mark-to-market where the naive hedge fails. Good
  interview material.
- **One sensitivity worth knowing about:** 22 of 397 weeks contain a
  roll-flagged day and are excluded (weeks dropped in every year, not just the
  wild ones). Keeping all 397 weeks would give corr 0.7345 / R² 0.54 instead —
  still far above daily, but lower. The exclusion is the project's standing
  convention (splice jumps are artifacts, not price moves); the honest caveat,
  noted since Phase 2, is that the flag heuristic also catches a few genuinely
  violent days, so a slice of that 0.54 → 0.70 lift comes from dropping real
  crisis weeks. Both numbers are worth remembering.
- **The sub-period pattern is not what you'd guess.** The *violent* regimes
  (2021–23, 2024, 2025+) score best (≈ +35–36%), and the two worst years are
  2020 COVID (+23.1%) and calm 2019 (+26.6%). The reason: daily effectiveness
  is corr², and the async-close timing noise is roughly constant in size — in
  quiet markets it dominates the small daily moves (low corr), while in
  violent markets the big common moves swamp it. 2020's poor daily score is
  almost pure timing artifact: measured weekly, 2020 has the *highest*
  correlation in the sample (≈ 0.92).
- **h\* is stable across all five regimes (0.45–0.56).** The relationship the
  hedge relies on did not break even in the squeeze and tariff years — which
  is *why* Phase 4's out-of-sample numbers degraded so little. (The 2025
  dislocation shows up as the OOS engine's brief dive toward 0, and in basis
  levels — Phase 6's story — not in the full-year regression.)

## 6. Completion checklist

- [ ] `uv run pytest` → **96 passed**, with `tests/` unmodified
- [ ] The Section 5 script runs and prints all three blocks
- [ ] The printed numbers match the expected tables above
- [ ] **Report the numbers back before pushing anything to main** — reply with
      the script output (or the tables) plus anything that looked off or
      surprising. This step has slipped in all three previous phases: the
      implementation reached main before the numbers were cross-checked.
      Every time the check happened to pass, but the order exists for the
      time it doesn't — **numbers first, push after they're confirmed.**

Committing locally is fine (conventional message, e.g.
`feat: implement weekly and sub-period robustness checks (phase 5)`).
