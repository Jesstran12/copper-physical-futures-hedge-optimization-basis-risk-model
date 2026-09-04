# Phase 6 Instructions — Basis Analysis + the 2024/2025 Case Studies

This document specifies the Phase 6 work: the function signatures, docstrings, and
tests already exist in the repo — **the bodies of 4 functions** (marked `TODO 18` …
`TODO 21` in the new module `src/copper_hedge/basis.py`) are left to implement. The
tests define the acceptance criteria: the phase's code is complete when the suite
goes green, after which one script produces the phase's real-data numbers and saves
its two figures.

Nothing else in the repo needs to change. Background on the whole project is in
`README.md` and `docs/PROJECT_LOG.md` (Phase 6 is this piece of work).

> **One process request before anything else.** In each of the four previous
> phases, the implementation was pushed to main before the numbers were reported
> back. Every time the check happened to pass — but the order exists for the time
> it doesn't. This phase: run the Section 5 script, **send the output first, and
> push only after it's been confirmed.** Local commits any time; the push waits.

---

## 1. What this phase does, in plain English

Phases 2–5 measured how much risk a futures hedge removes. Phase 6 names and
measures what's left. The **basis** is the spot price minus the futures price,
`b = LME cash − HG front month`, both in $/lb. It matters because of an identity,
not a metaphor: a hedger who is long 1 lb of physical copper and short 1 lb of
futures has daily P&L `dS − dF`, which **is** the daily change in the basis,
exactly. "Basis risk is the risk a hedge cannot remove" is an equation, and the
tests enforce it to the last bit.

Most of the sample the basis wiggles in a modest band around zero. Twice it broke
loose, and those two episodes are the story chapter of the whole project:

- **May 2024 — the COMEX squeeze.** Shorts in COMEX copper were forced to buy
  back; COMEX spiked far above LME. In two weeks the basis collapsed by ~34
  cents/lb — a dollar-for-dollar hedged position (the "safe" one) lost that
  entire move, then won most of it back into month-end. Month-end P&L looks
  fine; the mark-to-market ride in between is the lesson.
- **2025 — the tariff dislocation.** As US copper tariffs were anticipated,
  COMEX built a premium LME never had, grinding the basis to **−$1.32/lb** by
  late July — then gave essentially all of it back **in one day** (Jul 31) when
  refined copper was exempted. Roughly 4× the size of the famous May 2024 move.

The four functions to implement: the basis series itself, a descriptive report
(level stats + the volatility of daily basis changes), a report linking the
hedge's residual risk to basis risk, and a windowed P&L calculator that powers
the case studies above. The two committed figures this phase adds
(`figures/basis_over_time.png`, `figures/pnl_distribution.png`) are produced by
the Section 5 script — no plotting code goes in `src/`.

Roll handling carries over from Phases 2–5: a roll-flagged day's `dF` splice
jump pollutes that day's `db` identically, so **basis-change statistics exclude
flagged days** — while basis **level** statistics use every day (the level is a
real price difference on every date).

## 2. Setup

Follow `docs/SETUP.md` if the environment isn't set up yet. Then:

```bash
uv sync          # one-time: reproduce the exact environment
uv run pytest    # run the full test suite
```

**Expected starting state: `19 failed, 96 passed`.** Every failure says
`NotImplementedError: TODO n` with n in 18–21 — those are the 4 functions to
implement, all in `src/copper_hedge/basis.py`. The 96 passes are Phases 1–5 and
must stay green throughout. An import error or any other failure mode instead
means an environment problem — fix that first.

## 3. Where the code goes

| TODO | Function | Verified by (`tests/test_basis.py`) |
|---|---|---|
| 18 | `basis_series` | `TestBasisSeries` |
| 19 | `basis_report` | `TestBasisReport` |
| 20 | `residual_risk_report` | `TestResidualRiskReport` |
| 21 | `window_pnl` | `TestWindowPnl` |

Each TODO site has a comment block with step-by-step notes and the pandas methods
worth looking at. The **docstring above each TODO is the contract** — it states
exactly what goes in and what must come out. Suggested order: 18 → 19 → 20 → 21
(18 is a one-liner the others lean on; 20 and 21 are independent of 19).

### `basis_series` (TODO 18)

Spot minus futures, elementwise, on the shared index. That's the whole function —
it exists so "the basis" has exactly one definition in the codebase. Sign
convention matters and is tested: **negative basis = futures above spot**, which
is what both 2024 and 2025 dislocations look like.

### `basis_report` (TODO 19)

Descriptive statistics, composed from parts that already exist. Level stats
(`mean`, `std`, `min`, `max`, count) over **all** days; then difference the basis
with `price_changes`, drop roll-flagged days with `exclude_roll_days`, and report
the surviving count and std. Return a dict with exactly the keys `"n_days"`,
`"mean_basis"`, `"std_basis"`, `"min_basis"`, `"max_basis"`, `"n_delta_obs"`,
`"std_delta_basis"` (plain floats).

### `residual_risk_report` (TODO 20)

The linkage report: what the optimal hedge leaves behind, next to what the basis
does. Fit h\* with `optimal_hedge_ratio`, build the optimal residual with
`hedged_changes`, and build the basis-change series as `delta_spot −
delta_futures` directly — one test checks that route agrees with a 1:1 hedge
computed independently, which is only meaningful if this function does the basis
arithmetic itself. Return a dict with exactly the keys `"hedge_ratio"`,
`"unhedged_variance"`, `"residual_variance"`, `"residual_std"`,
`"basis_change_variance"`, `"basis_change_std"`, `"basis_share_of_residual"`
(plain floats; the share is basis-change variance over residual variance).

### `window_pnl` (TODO 21)

The case-study engine: slice both price series to `[start, end]` (pandas `.loc`
date slicing, both endpoints inclusive), take last-minus-first moves, and report
the P&L of the standing position (long 1 lb physical, short `hedge_ratio` lb of
futures) through that window. Eleven documented keys — levels, moves, and the
three P&L legs. A short is a **negative** exposure: its P&L is `−hedge_ratio ×
futures_move`. An empty window raises `ValueError`; a single-observation window
has zero moves. With `hedge_ratio = 1` the hedged P&L must equal the basis move
identically — that identity is the case study's punchline and a test.

## 4. How to test as you go

```bash
uv run pytest                                  # everything
uv run pytest tests/test_basis.py -q           # this phase only
uv run pytest tests/test_basis.py -q -x        # stop at first failure
uv run pytest tests/test_basis.py -k identical # the identity tests
```

Constraints (same as previous phases):

- **Don't edit the tests** — they are the acceptance criteria for this phase.
  Same for the other source modules (`data.py`, `roll.py`, `hedge.py`) and the
  CSVs in `data/`.
- Keep the functions **pure** (inputs → return value; no printing, no file I/O,
  no global state) and keep the type hints. Plotting stays in the Section 5
  script, never in `src/`.
- Any pandas/numpy API is fair game; the TODO comments name the useful ones.

**The code is complete when: `uv run pytest` → `115 passed`.**

## 5. Produce the real numbers and the two figures

With all tests green, run this from the repo root. It prints the basis
statistics, the residual-risk linkage, and both case studies, and saves the
phase's two figures into `figures/`:

```bash
uv run python - <<'EOF'
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from copper_hedge.basis import (
    basis_report,
    basis_series,
    residual_risk_report,
    window_pnl,
)
from copper_hedge.data import load_aligned
from copper_hedge.hedge import (
    exclude_roll_days,
    hedged_changes,
    optimal_hedge_ratio,
    price_changes,
)

LB_PER_CONTRACT = 25_000       # one COMEX HG contract
LB_PER_1000_TONNES = 2_204_620  # a 1,000 t cathode position

aligned, dropped = load_aligned(Path("data"))
flags = pd.read_csv(
    "data/hg_roll_flags.csv", parse_dates=["date"], index_col="date"
)["is_roll"]
spot, futures = aligned["lme_usd_per_lb"], aligned["hg_usd_per_lb"]

# Basis level and change statistics
rep = basis_report(spot, futures, flags)
basis = basis_series(spot, futures)
print("[basis = LME cash - HG front month, $/lb]")
print(f"  n={rep['n_days']:.0f} days   mean {rep['mean_basis']:+.4f}   "
      f"level std {rep['std_basis']:.4f}")
print(f"  min {rep['min_basis']:+.4f} ({basis.idxmin().date()})   "
      f"max {rep['max_basis']:+.4f} ({basis.idxmax().date()})")
print(f"  std(db) {rep['std_delta_basis']:.4f} $/lb per day "
      f"on n={rep['n_delta_obs']:.0f} roll-excluded change obs")

# Residual-risk linkage (daily changes, roll days excluded)
delta_s = exclude_roll_days(price_changes(spot), flags)
delta_f = exclude_roll_days(price_changes(futures), flags)
link = residual_risk_report(delta_s, delta_f)
print("\n[residual risk vs basis risk, daily, roll days excluded]")
print(f"  h* {link['hedge_ratio']:.4f}   unhedged var "
      f"{link['unhedged_variance']:.6f} ($/lb)^2")
print(f"  optimal residual: var {link['residual_variance']:.6f}   "
      f"std {link['residual_std']:.4f} $/lb")
print(f"  basis change:     var {link['basis_change_variance']:.6f}   "
      f"std {link['basis_change_std']:.4f} $/lb  (= the 1:1 hedger's residual,"
      " identically)")
print(f"  basis variance / optimal residual variance: "
      f"{link['basis_share_of_residual']:.2f}x")

# Case study: the May 2024 COMEX squeeze, then the 2025 tariff sequel
def show(title, w, hedge_desc):
    per_contract = w["hedged_pnl_per_lb"] * LB_PER_CONTRACT
    per_1000t = w["hedged_pnl_per_lb"] * LB_PER_1000_TONNES
    print(f"\n  {title} ({w['n_days']:.0f} trading days, {hedge_desc})")
    print(f"    LME   {w['spot_start']:.4f} -> {w['spot_end']:.4f}   "
          f"move {w['spot_move']:+.4f}")
    print(f"    COMEX {w['futures_start']:.4f} -> {w['futures_end']:.4f}   "
          f"move {w['futures_move']:+.4f}")
    print(f"    basis move {w['basis_move']:+.4f}   hedged P&L "
          f"{w['hedged_pnl_per_lb']:+.4f} $/lb")
    print(f"    = {per_contract:+,.0f} USD per contract-vs-25,000-lb   "
          f"= {per_1000t:+,.0f} USD on 1,000 t")

h_star = link["hedge_ratio"]
print("\n[case study: May 2024 COMEX squeeze, 1 lb long LME vs short futures]")
show("Run-up, Apr 30 -> May 14 (the squeeze)",
     window_pnl(spot, futures, 1.0, "2024-04-30", "2024-05-14"), "1:1 hedge")
show("Same run-up at the fitted ratio",
     window_pnl(spot, futures, h_star, "2024-04-30", "2024-05-14"),
     f"h* = {h_star:.4f}")
show("Snap-back, May 14 -> May 31",
     window_pnl(spot, futures, 1.0, "2024-05-14", "2024-05-31"), "1:1 hedge")
show("The whole calendar month, May 1 -> May 31",
     window_pnl(spot, futures, 1.0, "2024-05-01", "2024-05-31"), "1:1 hedge")

print("\n[the 2025 sequel: tariff premium blowout and one-day collapse]")
show("Blowout, Jan 2 -> Jul 25 2025",
     window_pnl(spot, futures, 1.0, "2025-01-02", "2025-07-25"), "1:1 hedge")
show("Collapse, Jul 25 -> Aug 5 2025 (exemption announced Jul 30)",
     window_pnl(spot, futures, 1.0, "2025-07-25", "2025-08-05"), "1:1 hedge")

# Figure 1: basis over time, event-annotated
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(basis.index, basis, lw=0.8, color="tab:blue")
ax.axhline(0.0, color="black", lw=0.8, alpha=0.6)
ax.set_ylabel("basis = LME cash - HG front month ($/lb)")
ax.set_title("LME-COMEX copper basis, 2019-2026")
events = [
    ("2020-03-25", "COVID crash:\nbasis holds", (-90, -35), "left"),
    ("2021-04-27", "2021-22 tightness", (-30, -45), "left"),
    ("2024-05-14", "May 2024\nCOMEX squeeze", (-40, -55), "left"),
    ("2025-07-25", "2025 tariff premium\nblowout (-$1.32)", (-15, 10), "right"),
    ("2025-07-31", "Jul 31 2025: exemption,\none-day collapse", (-70, 25), "right"),
]
for date, label, offset, align in events:
    d = pd.Timestamp(date)
    ax.annotate(
        label,
        xy=(d, basis.loc[d]),
        xytext=offset,
        textcoords="offset points",
        fontsize=8,
        ha=align,
        arrowprops=dict(arrowstyle="->", lw=0.8, color="gray"),
    )
ax.margins(x=0.01)
fig.tight_layout()
fig.savefig("figures/basis_over_time.png", dpi=150)
print("\nsaved figures/basis_over_time.png")

# Figure 2: hedged vs unhedged daily P&L distribution
hedged = hedged_changes(delta_s, delta_f, optimal_hedge_ratio(delta_s, delta_f))
fig, ax = plt.subplots(figsize=(9, 5.5))
bins = 120
ax.hist(delta_s, bins=bins, alpha=0.55, color="tab:red",
        label=f"unhedged dS  (std {delta_s.std():.4f} $/lb)")
ax.hist(hedged, bins=bins, alpha=0.65, color="tab:blue",
        label=f"hedged dS - h*dF  (std {hedged.std():.4f} $/lb)")
ax.set_xlim(-0.35, 0.35)
ax.set_xlabel("daily P&L per lb of copper ($/lb)")
ax.set_ylabel("days")
ax.set_title(
    "Daily P&L distribution, unhedged vs optimally hedged "
    f"(h* = {optimal_hedge_ratio(delta_s, delta_f):.2f}, roll days excluded)"
)
ax.legend()
fig.tight_layout()
fig.savefig("figures/pnl_distribution.png", dpi=150)
print("saved figures/pnl_distribution.png")
EOF
```

### Expected numbers (checked against a reference implementation)

An implementation that follows the contracts exactly should reproduce these on
the committed data snapshot (2019-01-02 → 2026-08-12).

Basis statistics ($/lb):

| Quantity | Value |
|---|---|
| Days (level stats, all days) | **1,875** |
| Mean basis | **−0.0592** |
| Basis level std | **0.1571** |
| Minimum | **−1.3237** on **2025-07-25** |
| Maximum | **+0.2037** on **2026-02-12** |
| std(db), roll days excluded | **0.0531** on **1,845** obs |

Residual-risk linkage (daily, roll days excluded — the h\* line must print
0.5025, matching Phases 3–5):

| Quantity | Value |
|---|---|
| h\* | 0.5025 |
| Unhedged variance | 0.002842 ($/lb)² |
| Optimal residual variance / std | **0.001874** / **0.0433 $/lb** |
| Basis-change variance / std | **0.002823** / **0.0531 $/lb** |
| Basis variance ÷ residual variance | **1.51×** |

Case studies (1:1 hedge unless noted; per-lb, then scaled by 25,000 lb per
contract and 2,204,620 lb per 1,000 t):

| Window | LME move | COMEX move | Hedged P&L $/lb | On 1,000 t |
|---|---|---|---|---|
| Squeeze run-up, Apr 30 → May 14 2024 | +0.0469 | **+0.3890** | **−0.3421** | **−$754,097** |
| Same window at h\* = 0.5025 | +0.0469 | +0.3890 | −0.1485 | −$327,433 |
| Snap-back, May 14 → May 31 2024 | −0.0417 | −0.3435 | **+0.3018** | +$665,286 |
| Whole month, May 1 → May 31 2024 | +0.0880 | +0.0575 | +0.0305 | +$67,234 |
| Tariff blowout, Jan 2 → Jul 25 2025 | +0.5001 | **+1.7750** | **−1.2749** | **−$2,810,701** |
| Collapse, Jul 25 → Aug 5 2025 | −0.0959 | −1.3995 | **+1.3036** | +$2,873,867 |

What the numbers are saying:

- **The unhedged-variance number differs from Phase 2's on purpose.** Phase 2's
  0.002977 was all 1,874 days; this report's 0.002842 is the 1,845 roll-excluded
  days — the same convention as Phases 3–5. Consistency check, not a bug.
- **The identity is exact:** the basis-change std (0.0531) IS the 1:1 hedger's
  residual daily risk, to the last bit. That turns "basis risk" from jargon into
  the literal P&L volatility of the fully hedged desk.
- **The 1.51× share** says the optimal daily hedge (h\* ≈ 0.5) leaves LESS risk
  than the full basis wiggle: hedging dollar-for-dollar over-trades the noisy
  daily relationship, so the 1:1 hedger carries about 50% more residual variance
  than the h\* hedger. (Phase 5 showed the flip side: weekly, where timing noise
  washes out, 1:1 works fine.)
- **May 2024 in one breath:** COMEX spiked 39 cents in ten trading days while
  LME barely moved (+5 cents) — a short-futures hedger was down **34 cents/lb
  (−$754k on 1,000 t)** at the worst mark, then won most of it back by
  month-end (+30 cents). The whole-month row (+$67k) is the trap: month-end
  accounting says "fine", but the desk had to survive the margin calls in
  between. That is what "basis risk hurts a physical desk" means.
- **2025 is the sequel, 4× bigger and slower:** the tariff premium ground the
  basis to −$1.32/lb over seven months (−$2.8M on 1,000 t at the worst mark),
  then the Jul 30 exemption news gave essentially all of it back in ONE session.
  Both directions of the round trip are real P&L a hedger had to fund or
  explain.
- **Figure eyeball checks:** `basis_over_time.png` — modest band around zero
  (mostly inside ±$0.15) through 2023, the sharp May-2024 spike to −0.38, the
  huge sustained 2025 dislocation to −1.32 with a vertical one-day snap back to
  ~0, all five event labels legible. `pnl_distribution.png` — the hedged
  (blue) histogram is visibly narrower than the unhedged (red), std 0.0533 →
  0.0433; the narrowing is real but modest at the daily frequency (that IS the
  +34% daily story), and the surviving width and outliers ARE basis + timing
  risk.

## 6. Completion checklist

- [ ] `uv run pytest` → **115 passed**, with `tests/` unmodified
- [ ] The Section 5 script runs, prints all four blocks, and saves both figures
- [ ] The printed numbers match the expected tables above
- [ ] Both figures pass the eyeball checks above
- [ ] Commit locally: the four function bodies in `src/copper_hedge/basis.py`
      plus the two PNGs in `figures/` (conventional message, e.g.
      `feat: implement basis analysis and case-study engine (phase 6)`)
- [ ] **Report the numbers back BEFORE pushing anything to main.** Reply with
      the script output (or the tables) plus anything that looked off or
      surprising, and wait for the confirmation. This is the step that has
      slipped in **all four** previous phases — see the note at the top of this
      document. Numbers first; push after they're confirmed.
