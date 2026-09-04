# Phase 3 Instructions — The Optimal Hedge Ratio, In-Sample

This document specifies the Phase 3 work: the function signatures, docstrings, and
tests already exist in the repo — **the bodies of 4 functions** (marked `TODO 7` …
`TODO 10` in `src/copper_hedge/hedge.py`) are left to implement. The tests define
the acceptance criteria: the phase's code is complete when the suite goes green,
after which one script produces the phase's real-data numbers.

Nothing else in the repo needs to change. Background on the whole project is in
`README.md` and `docs/PROJECT_LOG.md` (Phase 3 is this piece of work). Phase 2's roll
flags and baselines feed directly into this phase.

---

## 1. What this phase does, in plain English

Phase 2 established the benchmark: hedging copper 1-for-1 with futures barely
helps on daily data (+0.7% variance reduction with roll days excluded — the two
prices are fixed in different cities at different times of day, so their daily
moves are only loosely correlated, and a full-size hedge adds nearly as much noise
as it removes). Phase 3 computes the hedge that copper desks actually use: the
**minimum-variance (optimal) hedge ratio h\***.

The idea in one line: instead of shorting 1 unit of futures per unit of copper,
short the amount that history says minimizes the variance of the combined
position. That amount has a closed form:

```
h* = Cov(ΔS, ΔF) / Var(ΔF)
```

which is exactly the **slope of the OLS regression** of spot changes on futures
changes. And the regression's **R² is exactly the fraction of variance the h\*
hedge removes** in-sample — "hedge effectiveness". These are the two identities
this phase implements, and the tests check both (one test computes effectiveness
from variances and R² from a correlation and asserts they agree — that agreement
is mathematics, not coincidence, and it must hold to ~12 decimal places).

Two more things the phase pins down:

- **Roll days stay out of the regression.** Phase 2 flagged the days where the
  spliced futures series jumps because of a contract switch (the flags are
  committed in `data/hg_roll_flags.csv`). Those fake jumps must not contaminate
  the fitted slope, so one small helper filters flagged dates out of any change
  series before fitting.
- **Both spot legs.** The regression runs twice: LME cash (the primary,
  real-physical-market leg, in $/lb) and the CPER copper ETF (a secondary
  robustness check, in **$/share** — see the units note in section 5).

"In-sample" means the ratio is fitted and evaluated on the same data — the
flattering version, like grading your own homework. It is the reference point;
the honest out-of-sample version is the next phase.

## 2. Setup

Follow `docs/SETUP.md` if the environment isn't set up yet. Then:

```bash
uv sync          # one-time: reproduce the exact environment
uv run pytest    # run the full test suite
```

**Expected starting state: `18 failed, 40 passed`.** Every failure says
`NotImplementedError: TODO n` with n in 7–10 — those are the 4 functions to
implement, all in `src/copper_hedge/hedge.py`. The 40 passes are Phases 1–2,
which must stay green throughout. An import error or any other failure mode
instead means an environment problem — fix that first.

## 3. Where the code goes

| TODO | Function | Verified by (`tests/test_optimal_hedge.py`) |
|---|---|---|
| 7 | `optimal_hedge_ratio` | `TestOptimalHedgeRatio` |
| 8 | `in_sample_r_squared` | `TestInSampleRSquared` |
| 9 | `exclude_roll_days` | `TestExcludeRollDays` |
| 10 | `optimal_hedge_report` | `TestOptimalHedgeReport` |

Each TODO site has a comment block with step-by-step notes and the pandas methods
worth looking at. The **docstring above each TODO is the contract** — it states
exactly what goes in and what must come out.

Suggested order: 7 → 8 → 9 → 10 (7 and 8 are one-liners, 9 is a small filter,
10 composes everything).

### `optimal_hedge_ratio` (TODO 7)

The Cov/Var formula, literally: sample covariance of the two change series over
the sample variance of the futures changes. pandas `.cov()` and `.var()` both
default to `ddof=1`, so they compose correctly as-is. If you prefer to fit an
actual regression (`statsmodels.api.OLS` with a constant), the slope is the same
number to floating precision — the tests accept either route.

### `in_sample_r_squared` (TODO 8)

The R² of that regression, which for a one-variable regression is just the
squared correlation: pandas `.corr()`, then square it. Note it is direction-blind
— a spot leg that moved perfectly *opposite* to futures would still score 1.0
(the hedge ratio would simply come out negative).

### `exclude_roll_days` (TODO 9)

Given a change series and a boolean flag series indexed by date (True = roll
day), return the changes with flagged dates removed. The subtlety is index
alignment: the flags may cover more dates or fewer dates than the changes. Look
flags up by date (`.reindex`), treat dates the flags never mention as *not*
flagged (`.fillna(False)`), and keep the unflagged rows. The tests probe exactly
these edge cases.

### `optimal_hedge_report` (TODO 10)

Compose the pieces: fit h\*, build the hedged series with the existing
`hedged_changes`, and return a dict with exactly the keys `"hedge_ratio"`,
`"r_squared"`, `"unhedged_variance"`, `"hedged_variance"`, `"effectiveness"`
(plain floats). One rule: compute `"effectiveness"` from the variances (the
existing `variance_reduction`), **not** by copying the R² value — the whole point
of the identity test is that two independently computed numbers coincide.

## 4. How to test as you go

```bash
uv run pytest                                        # everything
uv run pytest tests/test_optimal_hedge.py -q         # this phase only
uv run pytest tests/test_optimal_hedge.py -q -x      # stop at first failure
uv run pytest tests/test_optimal_hedge.py -k identity  # one test by keyword
```

Constraints (same as Phase 2):

- **Don't edit the tests** — they are the acceptance criteria for this phase.
  Same for `src/copper_hedge/data.py`, `src/copper_hedge/roll.py`, and the CSVs
  in `data/`.
- Keep the functions **pure** (inputs → return value; no printing, no file I/O,
  no global state) and keep the type hints.
- Any pandas/numpy/statsmodels API is fair game; the TODO comments name the
  useful ones.

**The code is complete when: `uv run pytest` → `58 passed`.**

## 5. Produce the real numbers

With all tests green, run this from the repo root. It fits the optimal hedge on
the real 2019–2026 data (roll-flagged days excluded via the committed
`data/hg_roll_flags.csv`) and prints the phase's headline numbers for both spot
legs:

```bash
uv run python - <<'EOF'
from pathlib import Path

import pandas as pd

from copper_hedge.data import load_aligned
from copper_hedge.hedge import (
    exclude_roll_days,
    naive_hedge_report,
    optimal_hedge_report,
    price_changes,
)

aligned, dropped = load_aligned(Path("data"))
flags = pd.read_csv(
    "data/hg_roll_flags.csv", parse_dates=["date"], index_col="date"
)["is_roll"]

# The hedge leg: futures price changes with roll-flagged days excluded
delta_f = exclude_roll_days(price_changes(aligned["hg_usd_per_lb"]), flags)

for label, column, unit in [
    ("LME (primary)", "lme_usd_per_lb", "$/lb"),
    ("CPER (secondary)", "cper_usd_per_share", "$/share"),
]:
    delta_s = exclude_roll_days(price_changes(aligned[column]), flags)
    opt = optimal_hedge_report(delta_s, delta_f)
    naive = naive_hedge_report(delta_s, delta_f)
    print(f"\n[{label} spot leg, in {unit}]  n={len(delta_s)} (roll days excluded)")
    print(f"  optimal hedge ratio h*  : {opt['hedge_ratio']:.4f}")
    print(f"  in-sample R^2           : {opt['r_squared']:.4f}")
    print(f"  effectiveness at h*     : {opt['effectiveness']:+.1%}")
    print(f"  naive 1:1 reduction     : {naive['variance_reduction']:+.1%}")
EOF
```

### Expected numbers (checked against a reference implementation)

An implementation that follows the contracts exactly should reproduce these on
the committed data snapshot (2019-01-02 → 2026-08-12; n = 1,845 after excluding
the 29 flagged roll days):

| Quantity | LME leg (primary) | CPER leg (secondary) |
|---|---|---|
| Optimal hedge ratio h\* | **0.5025** | **5.7437** † |
| In-sample R² | **0.3405** | **0.7215** |
| Effectiveness at h\* | **+34.1%** (= R², by identity) | **+72.2%** (= R², by identity) |
| Naive 1:1 reduction (Phase 2 baseline) | **+0.7%** | +22.9% † |

† **CPER units note:** CPER is quoted in $/share (≈ $25–35 over the sample)
while futures changes are in $/lb, so its h\* of ≈ 5.7 means "short 5.7 lb-worth
of futures per share" — a number whose *size* is an accident of share pricing,
not a market fact. The same goes for its "naive 1:1" row (1 lb per share is an
arbitrary ratio). Its R² and effectiveness, by contrast, are scale-invariant and
fully comparable.

What the numbers are saying:

- **LME h\* ≈ 0.50, not ≈ 1:** because the daily LME–COMEX correlation is only
  ≈ 0.58 (prices fixed ~5 time-zones apart), the variance-minimizing hedge is
  roughly half-size. Fitting instead of assuming turns the naive hedge's +0.7%
  into **+34.1%** — the phase's headline improvement.
- **In-sample R² ≈ 0.34 is honest, not disappointing.** It is daily-frequency
  effectiveness against a *genuinely different* physical-market price. The
  ~66% that remains is basis risk plus the timing mismatch — both get their own
  analysis in later phases (measured weekly, the correlation rises sharply).
- **CPER scores ≈ 0.72, double the LME leg.** Expected — CPER itself holds COMEX
  futures, so regressing it on futures is nearly futures-on-futures. That gap
  (0.72 vs 0.34) is the project's evidence for why CPER is only a robustness
  check and not the primary spot leg.
- **Effectiveness must equal R² exactly** in your printout (both legs). If the
  two lines differ beyond the last decimal, something is wrong even if the tests
  pass — report it rather than shipping it.

## 6. Completion checklist

- [ ] `uv run pytest` → **58 passed**, with `tests/` unmodified
- [ ] The Section 5 script runs and prints both legs' numbers
- [ ] The printed numbers match the expected table above
- [ ] **Report the numbers back before pushing anything to main** — reply with
      the eight numbers from the table (or the full script output) plus anything
      that looked off or surprising. Last phase the implementation landed on
      main before the numbers were cross-checked; the check happened to pass,
      but the order matters: numbers first, then the push after they're
      confirmed against the reference.

Committing locally is fine (conventional message, e.g.
`feat: implement in-sample optimal hedge (phase 3)`).
