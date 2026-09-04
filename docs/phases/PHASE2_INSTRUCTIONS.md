# Phase 2 Instructions — Roll Detection + Hedge Baselines

This document specifies the Phase 2 work: the function signatures, docstrings, and
tests already exist in the repo — **the bodies of 6 functions** (marked `TODO 1` …
`TODO 6`) are left to implement. The tests define the acceptance criteria: the phase's
code is complete when the suite goes green, after which one script produces the
phase's real-data numbers.

Nothing else in the repo needs to change. Background on the whole project is in
`README.md` and `docs/PROJECT_LOG.md` (Phase 2 is this piece of work).

---

## 1. What this phase does, in plain English

This project studies hedging physical copper with COMEX copper futures. Phase 2 has
two jobs:

**Job A — flag the fake jumps ("roll days") in the futures series.**
`HG=F` is a *spliced* price history: it stitches successive futures contracts
(March, May, July, September, December — the "active months") into one series. On
the day the series silently switches from one contract to the next, the price can
jump even though nobody trading actually experienced that move — it's just the
price difference between two different contracts. Those fake jumps would pollute
every statistic we compute from day-to-day price changes, so we detect and flag
them. The heuristic: a day is suspicious only if it falls in a **calendar window**
where rolls happen (an active month, or the last week just before one) **and** its
price change is abnormally large versus recent history (more than 4× the trailing
median daily move).

**Job B — compute the benchmark ("baseline") risk numbers.**
How risky is unhedged copper (the variance of its daily price changes)? And how
much does the *naive* hedge — short exactly 1 unit of futures per unit of copper —
reduce that variance? Every later phase's "optimal" hedge is judged against these
two baselines.

Conventions that matter (the tests enforce them):

- Everything is in **dollars per pound ($/lb)** and uses **price changes**
  (today − yesterday, in dollars), *not* percentage returns.
- **No lookahead, ever**: anything computed "as of day t" may only use data from
  strictly before t. One test explicitly rewrites the future and checks the past
  doesn't change.
- Variance means **sample variance** (`ddof=1` — the pandas `.var()` default).

## 2. Setup

Follow `docs/SETUP.md` if the environment isn't set up yet (installs `uv` and the
project environment). Then:

```bash
uv sync          # one-time: reproduce the exact environment
uv run pytest    # run the full test suite
```

**Expected starting state: `23 failed, 17 passed`.** Every failure says
`NotImplementedError: TODO n` — those are the 6 functions to implement. (The 17
passes are Phase 1's data layer plus one test on a provided constant.) An import
error or any other failure mode instead means an environment problem — fix that
first.

## 3. Where the code goes

| TODO | File | Function | Verified by |
|---|---|---|---|
| 1 | `src/copper_hedge/roll.py` | `is_roll_candidate` | `tests/test_roll.py::TestRollCandidateWindow` |
| 2 | `src/copper_hedge/roll.py` | `flag_roll_days` | `tests/test_roll.py::TestFlagRollDays` |
| 3 | `src/copper_hedge/hedge.py` | `price_changes` | `tests/test_hedge.py::TestPriceChanges` |
| 4 | `src/copper_hedge/hedge.py` | `hedged_changes` | `tests/test_hedge.py::TestHedgedChanges` |
| 5 | `src/copper_hedge/hedge.py` | `variance_reduction` | `tests/test_hedge.py::TestVarianceReduction` |
| 6 | `src/copper_hedge/hedge.py` | `naive_hedge_report` | `tests/test_hedge.py::TestNaiveHedgeReport` |

Each TODO site has a comment block with step-by-step notes and the pandas methods
worth looking at. The **docstring above each TODO is the contract** — it states
exactly what goes in and what must come out.

Suggested order: 3 → 4 → 5 → 6 (each is roughly one line, and they build on each
other), then 1, then 2 (the only genuinely fiddly one).

### `is_roll_candidate` (TODO 1 — the calendar window)

Given dates, return a boolean Series: is each date inside a plausible roll window?
That means the date's month is an active month (Mar/May/Jul/Sep/Dec), **or** the
date is in the last `pre_days` (default 7) calendar days of the month immediately
before an active month. Two edge cases the tests check: month lengths differ
(Feb 2024 has 29 days), and the month after December is January.

### `flag_roll_days` (TODO 2 — window + abnormal jump)

Flag day t only if **all three** hold: (1) t is in the roll window; (2) at least
`min_history` (20) price changes exist strictly before t; (3) t's absolute price
change exceeds `gap_mult` (4) × the median absolute change over the `lookback`
(60) most recent changes **strictly before t**. That "strictly before" is the
no-lookahead rule — the day's own jump must not inflate its own threshold. In
pandas, `.shift(1)` before `.rolling(...)` is the standard trick.

### The hedge baselines (TODOs 3–6)

All four are short. `price_changes` = day-over-day differences. `hedged_changes` =
`ΔS − h·ΔF` (long copper, short h futures). `variance_reduction` =
`1 − Var(hedged)/Var(unhedged)` (1.0 = perfect hedge, 0 = useless, negative = the
hedge *added* risk). `naive_hedge_report` composes them at h = 1 and returns the
three headline floats in a dict (exact keys are in the docstring).

## 4. How to test as you go

```bash
uv run pytest                                  # everything
uv run pytest tests/test_hedge.py -q           # one file
uv run pytest tests/test_roll.py -q -x         # stop at first failure
uv run pytest tests/test_roll.py -k lookahead  # one test by keyword
```

Reading a failure: pytest prints the assert that failed with the actual vs
expected values — look at the first `assert` line, not the traceback top.

Constraints:

- **Don't edit the tests** — they are the acceptance criteria for this phase.
  Same for `src/copper_hedge/data.py` and the CSVs in `data/`.
- Keep the functions **pure** (inputs → return value; no printing, no file I/O,
  no global state) and keep the type hints.
- Any pandas/numpy API is fair game; the TODO comments name the useful ones.

**The code is complete when: `uv run pytest` → `40 passed`.**

## 5. Produce the real numbers

With all tests green, run this from the repo root. It applies the new functions to
the real 2019–2026 data, saves the roll flags next to the other data files, and
prints the phase's headline numbers:

```bash
uv run python - <<'EOF'
from pathlib import Path

from copper_hedge.data import load_aligned
from copper_hedge.hedge import naive_hedge_report, price_changes
from copper_hedge.roll import flag_roll_days

aligned, dropped = load_aligned(Path("data"))

# 1. Roll flags on the futures leg, saved alongside the data
flags = flag_roll_days(aligned["hg_usd_per_lb"])
flags.rename("is_roll").to_csv("data/hg_roll_flags.csv", index_label="date")
print(f"Roll days flagged: {int(flags.sum())} "
      f"({flags.index[0].date()} to {flags.index[-1].date()})")
print("Per year:")
print(flags.groupby(flags.index.year).sum().to_string())

# 2. Baselines: unhedged vs naive 1:1 hedge (LME spot leg)
ds = price_changes(aligned["lme_usd_per_lb"])
df = price_changes(aligned["hg_usd_per_lb"])
keep = ~flags.reindex(ds.index).fillna(False)

for label, s, f in [("all days", ds, df),
                    ("roll days excluded", ds[keep], df[keep])]:
    r = naive_hedge_report(s, f)
    print(f"\n[{label}]  n={len(s)}")
    print(f"  unhedged daily variance : {r['unhedged_variance']:.6f} ($/lb)^2")
    print(f"  naive 1:1 hedge variance: {r['hedged_variance']:.6f} ($/lb)^2")
    print(f"  naive variance reduction: {r['variance_reduction']:+.1%}")
EOF
```

### Expected numbers (checked against a reference implementation)

An implementation that follows the contracts exactly should reproduce these on the
committed data snapshot (2019-01-02 → 2026-08-12):

| Quantity | Expected |
|---|---|
| Roll days flagged | **29** (≈ 4/year; anything in 25–35 means a defensible variant, 0 or 200 means a bug) |
| Unhedged daily variance | **≈ 0.0030 ($/lb)²** (a daily standard deviation of ≈ 5.5 cents/lb) |
| Naive 1:1 reduction, roll days excluded | **≈ +0.7%** (yes, nearly zero) |
| Naive 1:1 reduction, all days | **≈ −34%** (yes, negative) |

**A near-zero/negative reduction is the correct answer, not a bug.** Two real
effects cause it: (1) LME's price is fixed around 1pm London while COMEX settles
around 1pm New York, so the two "daily changes" cover different windows and their
daily correlation is only ≈ 0.54 — too weak for a full-size 1:1 hedge, which ends
up adding almost as much noise as it removes; (2) in 2025, US tariff fears blew
the COMEX price out far above the LME price and then it collapsed back, so that
year the "hedge" was wildly counterproductive (≈ −350% for 2025 alone). That is
exactly why the project exists: later phases fit the *optimal* (smaller) hedge
ratio and show how much better it does. This baseline is the number they'll beat.

## 6. Completion checklist

- [x] `uv run pytest` → **40 passed**, with `tests/` unmodified
- [ ] The Section 5 script runs and `data/hg_roll_flags.csv` exists (1,875 rows)
- [ ] The printed numbers land in the expected zones above
- [ ] Report back: the four numbers from the table, plus anything that looked off
      or surprising along the way

Committing locally is fine (conventional message, e.g.
`feat: implement roll detection and hedge baselines (phase 2)`), but **don't push
to main directly** — hand the numbers back first so they can be cross-checked
against the reference before anything lands.
