# Phase 7 Instructions — The README Write-Up

This phase is different from Phases 2–6: **no code**. The analysis is finished — 115
tests green, four figures committed, every number verified. Phase 7 turns it into the
document people will actually read: a results-driven `README.md`. The skeleton is
already in place — nine sections, each with a `TODO W#` block saying what goes there.
Write the sections, delete the TODO blocks as you go.

The reader to have in mind: a recruiter or desk quant giving the repo three minutes.
They should leave knowing the headline numbers, believing them (because the honest
out-of-sample and weekly counterparts are right there), and remembering the May 2024
story.

> **One process request, same as last time.** In every previous phase the work was
> pushed to main before being reported back. This phase it matters even more — this is
> the public face of the repo. **Send the draft first** (or push it to a branch), and
> merge to main only after it's been read and confirmed. Local commits any time; main
> waits.

---

## 1. What this phase does, in plain English

Phases 1–6 produced numbers; Phase 7 produces the *argument*. The README's job is to
make three claims and back each with the numbers you'll generate in §4:

1. **The optimal hedge works, honestly measured** — about a third of daily variance
   removed *out of sample*, while the naive 1:1 hedge removes roughly nothing daily.
2. **The daily numbers understate the hedge** — measured weekly, where exchange
   closing-time mismatch washes out, effectiveness doubles.
3. **What the hedge can't remove is basis risk, and it's real money** — the May 2024
   squeeze cost a "fully hedged" 1,000 t desk about $754k in ten days, and 2025 ran
   the same movie 4× bigger.

Everything you need exists already: the skeleton (`README.md`), the figures
(`figures/`), the numbers (one script, §4), and the background reading
(`docs/PROJECT_LOG.md` for the project's design and decisions; `PHASE2_INSTRUCTIONS.md`
through `PHASE6_INSTRUCTIONS.md` §1 and §5 for what each phase found and why the
surprising numbers are right — the "What the numbers are saying" notes there are
exactly the explanations the README needs in prose form).

## 2. Setup and starting state

Follow `docs/SETUP.md` if the environment isn't set up, then:

```bash
uv sync
uv run pytest    # expected: 115 passed — and it must still say that when you're done
```

**This phase changes exactly one file: `README.md`.** No edits to `src/`, `tests/`,
`data/`, `figures/`, or the other docs. The suite is the tripwire: if it doesn't say
`115 passed` at the end, something was touched that shouldn't have been.

## 3. Section-by-section guidance

| TODO | Section | The one job it has |
|---|---|---|
| W1 | Headline results | The findings in 30 seconds, numbers included |
| W2 | The four figures | The story told visually, captions carrying numbers |
| W3 | The finance, in one page | Make h\*, effectiveness, and basis mean something |
| W4 | Data | Three series, the rules, the honest row counts |
| W5 | Results in detail | Every number with its honest counterpart |
| W6 | Case study | The May 2024 story, in your own words |
| W7 | From ratio to contracts | The desk translation worked example |
| W8 | Limitations | What this analysis cannot claim |
| W9 | Reproducing | Clone → running tests in one minute |

House writing rules (these are the acceptance criteria as much as the checklist is):

- **Lead with results.** Numbers first, method later. No section opens with throat-
  clearing ("In this project, we will...").
- **Never report an in-sample number without its out-of-sample counterpart nearby**,
  and never a daily headline without the weekly context. The credibility of the whole
  document lives in this pairing.
- **Real numbers only, from the §4 output.** No placeholders, no rounding a number
  you didn't generate, no "approximately 35%" when the script says +34.1%.
- **Plain English carries the finance.** First paragraph of W3 must survive a smart
  reader who knows no finance. Jargon that earns its place gets one-line definitions.

Per-section notes:

- **W1.** Two or three sentences plus a small table (6–8 rows max). The one comparison
  that must be unmissable: optimal OOS (~+33%) vs naive 1:1 (+0.6%) on the same days.
- **W2.** Suggested order: `price_series` (the setting) → `basis_over_time` (the
  villain) → `rolling_hedge_ratio` (the estimate a desk would have had) →
  `pnl_distribution` (what hedging buys). A caption is 2–4 sentences that tell the
  reader what to *see*, with a number — not a restatement of the title. Honest note
  for the last one: the narrowing is visibly modest; that IS the +34% daily story, so
  don't oversell it.
- **W3.** The three formulas worth showing: h\* = Cov(ΔS,ΔF)/Var(ΔF); e = 1 −
  Var(hedged)/Var(unhedged); b = S − F. The one identity worth stating: a 1:1 hedger's
  daily P&L *is* the daily basis change, exactly. And the units defense: price changes
  in $/lb (not returns) because hedging in contract terms is a price-change problem —
  a contract is 25,000 lb and P&L per contract is 25,000 × the price change.
- **W4.** Include: 1,875 aligned rows (2019-01-02 → 2026-08-12), the dropped-row
  counts per leg, 29 roll flags with a one-line explanation of why roll days are
  excluded from regressions, outliers kept. Say plainly that CPER holds futures — that
  belongs here AND in limitations.
- **W5.** The §4 output blocks B–E map one-to-one onto this section. The three
  explanations that must appear in prose: why OOS barely degrades from in-sample
  (stable h\* across regimes); why weekly doubles daily (async closes — COMEX ~1pm New
  York, LME ~1pm London, CPER 4pm New York); why violent regimes hedge *better* daily
  (constant-size timing noise, swamped by big moves — 2020's weekly corr ≈0.92 shows
  its bad daily number is artifact). CPER's h\* is $/share-per-$/lb — say it's
  unit-dependent; only its R²/effectiveness compare cleanly.
- **W6.** The one section that's pure storytelling — half a page, prose, no table.
  Block F has the six windows. The arc that works: what a squeeze is (shorts must buy
  back; COMEX tore away from LME) → the ten-day run-up in concrete P&L on 1,000 t →
  the snap-back → the whole-month number that looks like nothing happened → why that
  wash-out is the *trap* (mark-to-market losses and margin calls are real even when
  month-end nets flat) → one or two sentences on 2025 as the bigger, slower sequel
  with a one-day ending. Write it to be retold out loud.
- **W7.** Block G, walked through: 2,204,620 lb × 0.5025 / 25,000 = 44.31 → short 44;
  what rounding costs (nearly nothing — say the actual number); naive 1:1 = 88
  contracts as the contrast.
- **W8.** Required, one short paragraph or bullet each: (1) CPER holds futures —
  effectiveness against it is overstated by construction; (2) HG=F is a spliced
  front-month series — the roll heuristic can also catch genuinely violent days near
  roll windows, so part of the clean-sample lift is real days excluded; (3) closes
  aren't simultaneous across exchanges — daily correlations attenuated, weekly is the
  fairer read; (4) LME vs COMEX grade and location differences — the two are distinct
  markets exactly when it matters (that's what 2024/2025 proved). Add anything else
  you noticed while writing.
- **W9.** `uv sync`, `uv run pytest` → 115 passed, committed CSVs are the source of
  truth (nothing refetches), and one sentence on which module does what (`data.py`,
  `roll.py`, `hedge.py`, `basis.py`).

## 4. The numbers pack

Run this from the repo root. It prints every number the README cites, in labeled
blocks (A–G) the guidance above refers to. Cite from this output — not from memory,
not from other docs.

```bash
uv run python - <<'EOF'
from pathlib import Path

import pandas as pd

from copper_hedge.basis import basis_report, basis_series, residual_risk_report, window_pnl
from copper_hedge.data import load_aligned
from copper_hedge.hedge import (
    exclude_roll_days,
    naive_hedge_report,
    optimal_hedge_report,
    out_of_sample_report,
    price_changes,
    sub_period_report,
    weekly_hedge_report,
)

LB_PER_CONTRACT = 25_000        # one COMEX HG contract
LB_PER_1000_TONNES = 2_204_620  # a 1,000 t cathode position

aligned, dropped = load_aligned(Path("data"))
flags = pd.read_csv(
    "data/hg_roll_flags.csv", parse_dates=["date"], index_col="date"
)["is_roll"]
spot, futures = aligned["lme_usd_per_lb"], aligned["hg_usd_per_lb"]
cper = aligned["cper_usd_per_share"]

print("[A. data]")
print(f"  aligned rows {len(aligned)}   "
      f"{aligned.index[0].date()} -> {aligned.index[-1].date()}")
print(f"  rows dropped by calendar mismatch: {dropped}")
print(f"  roll-flagged days: {int(flags.sum())}")

delta_s = exclude_roll_days(price_changes(spot), flags)
delta_f = exclude_roll_days(price_changes(futures), flags)
delta_c = exclude_roll_days(price_changes(cper), flags)

print("\n[B. in-sample daily, roll days excluded]")
naive = naive_hedge_report(delta_s, delta_f)
opt = optimal_hedge_report(delta_s, delta_f)
opt_c = optimal_hedge_report(delta_c, delta_f)
print(f"  n obs {len(delta_s)}")
print(f"  LME  leg: h* {opt['hedge_ratio']:.4f}   R^2 {opt['r_squared']:.4f}   "
      f"effectiveness {opt['effectiveness']*100:+.1f}%   "
      f"naive 1:1 {naive['variance_reduction']*100:+.1f}%")
print(f"  CPER leg: h* {opt_c['hedge_ratio']:.4f} $/share per $/lb (unit-dependent)   "
      f"R^2 {opt_c['r_squared']:.4f}   effectiveness {opt_c['effectiveness']*100:+.1f}%")

print("\n[C. out-of-sample daily, LME leg, one step ahead]")
for name, window in [("60d rolling", 60), ("120d rolling", 120), ("expanding", None)]:
    rep = out_of_sample_report(delta_s, delta_f, window=window)
    print(f"  {name:<12} n {rep['n_days']:.0f}   "
          f"OOS effectiveness {rep['oos_effectiveness']*100:+.1f}%   "
          f"naive 1:1 same days {rep['naive_effectiveness']*100:+.1f}%")

print("\n[D. weekly (Fri-Fri) + sub-periods, LME leg]")
wk = weekly_hedge_report(spot, futures, flags)
print(f"  weekly: n {wk['n_weeks']:.0f} weeks   h* {wk['hedge_ratio']:.4f}   "
      f"R^2 {wk['r_squared']:.4f}   effectiveness {wk['effectiveness']*100:+.1f}%   "
      f"naive 1:1 {wk['naive_effectiveness']*100:+.1f}%")
sub = sub_period_report(delta_s, delta_f)
for label, row in sub.iterrows():
    print(f"  {label:<18} n {row['n_obs']:>4.0f}   h* {row['hedge_ratio']:.4f}   "
          f"effectiveness {row['effectiveness']*100:+.1f}%")

print("\n[E. basis + residual risk]")
rep = basis_report(spot, futures, flags)
basis = basis_series(spot, futures)
print(f"  basis (LME - HG, $/lb): n {rep['n_days']:.0f}   mean {rep['mean_basis']:+.4f}   "
      f"level std {rep['std_basis']:.4f}")
print(f"  min {rep['min_basis']:+.4f} ({basis.idxmin().date()})   "
      f"max {rep['max_basis']:+.4f} ({basis.idxmax().date()})")
print(f"  std(db) {rep['std_delta_basis']:.4f} on n {rep['n_delta_obs']:.0f} roll-excluded obs")
link = residual_risk_report(delta_s, delta_f)
print(f"  optimal residual std {link['residual_std']:.4f} vs basis-change std "
      f"{link['basis_change_std']:.4f}   basis var / residual var "
      f"{link['basis_share_of_residual']:.2f}x")

print("\n[F. case-study windows, 1:1 hedge, per lb and on 1,000 t]")
windows = [
    ("May 2024 run-up   Apr 30 -> May 14", "2024-04-30", "2024-05-14"),
    ("May 2024 snap-back May 14 -> May 31", "2024-05-14", "2024-05-31"),
    ("May 2024 whole month May 1 -> May 31", "2024-05-01", "2024-05-31"),
    ("2025 blowout      Jan 2 -> Jul 25", "2025-01-02", "2025-07-25"),
    ("2025 collapse     Jul 25 -> Aug 5", "2025-07-25", "2025-08-05"),
]
for title, start, end in windows:
    w = window_pnl(spot, futures, 1.0, start, end)
    print(f"  {title:<38} LME {w['spot_move']:+.4f}  COMEX {w['futures_move']:+.4f}  "
          f"hedged {w['hedged_pnl_per_lb']:+.4f} $/lb  "
          f"= {w['hedged_pnl_per_lb']*LB_PER_1000_TONNES:+,.0f} USD on 1,000 t")

print("\n[G. desk translation, 1,000 t of cathode]")
h = opt["hedge_ratio"]
exact = h * LB_PER_1000_TONNES / LB_PER_CONTRACT
n_contracts = round(exact)
h_implied = n_contracts * LB_PER_CONTRACT / LB_PER_1000_TONNES

def effectiveness_at(hh: float) -> float:
    hedged = delta_s - hh * delta_f
    return 1.0 - hedged.var() / delta_s.var()

print(f"  h* {h:.4f} x 2,204,620 lb / 25,000 lb = {exact:.2f} -> short {n_contracts} contracts")
print(f"  implied ratio {h_implied:.4f}   under-hedged by "
      f"{h*LB_PER_1000_TONNES - n_contracts*LB_PER_CONTRACT:,.0f} lb")
print(f"  effectiveness at h* {effectiveness_at(h)*100:.4f}%  "
      f"vs at {n_contracts} contracts {effectiveness_at(h_implied)*100:.4f}%  "
      f"(rounding costs {abs(effectiveness_at(h)-effectiveness_at(h_implied))*100:.4f} pp)")
print(f"  naive 1:1 would be {round(LB_PER_1000_TONNES/LB_PER_CONTRACT)} contracts")
EOF
```

### Expected output (verified on the committed data snapshot)

The data is frozen, so your run should reproduce this **exactly**. If any line
differs, stop and say so before writing it into the README.

```
[A. data]
  aligned rows 1875   2019-01-02 -> 2026-08-12
  rows dropped by calendar mismatch: {'lme_usd_per_lb': 49, 'hg_usd_per_lb': 42, 'cper_usd_per_share': 36}
  roll-flagged days: 29

[B. in-sample daily, roll days excluded]
  n obs 1845
  LME  leg: h* 0.5025   R^2 0.3405   effectiveness +34.1%   naive 1:1 +0.7%
  CPER leg: h* 5.7437 $/share per $/lb (unit-dependent)   R^2 0.7215   effectiveness +72.2%

[C. out-of-sample daily, LME leg, one step ahead]
  60d rolling  n 1785   OOS effectiveness +33.5%   naive 1:1 same days +0.6%
  120d rolling n 1725   OOS effectiveness +33.1%   naive 1:1 same days +0.6%
  expanding    n 1785   OOS effectiveness +33.8%   naive 1:1 same days +0.6%

[D. weekly (Fri-Fri) + sub-periods, LME leg]
  weekly: n 375 weeks   h* 0.7276   R^2 0.6996   effectiveness +70.0%   naive 1:1 +60.2%
  2019 calm          n  244   h* 0.4618   effectiveness +26.6%
  2020 COVID         n  246   h* 0.4562   effectiveness +23.1%
  2021-23 tightness  n  727   h* 0.5639   effectiveness +35.4%
  2024 squeeze era   n  242   h* 0.5026   effectiveness +36.2%
  2025+ tariff era   n  386   h* 0.4524   effectiveness +34.6%

[E. basis + residual risk]
  basis (LME - HG, $/lb): n 1875   mean -0.0592   level std 0.1571
  min -1.3237 (2025-07-25)   max +0.2037 (2026-02-12)
  std(db) 0.0531 on n 1845 roll-excluded obs
  optimal residual std 0.0433 vs basis-change std 0.0531   basis var / residual var 1.51x

[F. case-study windows, 1:1 hedge, per lb and on 1,000 t]
  May 2024 run-up   Apr 30 -> May 14     LME +0.0469  COMEX +0.3890  hedged -0.3421 $/lb  = -754,097 USD on 1,000 t
  May 2024 snap-back May 14 -> May 31    LME -0.0417  COMEX -0.3435  hedged +0.3018 $/lb  = +665,286 USD on 1,000 t
  May 2024 whole month May 1 -> May 31   LME +0.0880  COMEX +0.0575  hedged +0.0305 $/lb  = +67,234 USD on 1,000 t
  2025 blowout      Jan 2 -> Jul 25      LME +0.5001  COMEX +1.7750  hedged -1.2749 $/lb  = -2,810,701 USD on 1,000 t
  2025 collapse     Jul 25 -> Aug 5      LME -0.0959  COMEX -1.3995  hedged +1.3036 $/lb  = +2,873,867 USD on 1,000 t

[G. desk translation, 1,000 t of cathode]
  h* 0.5025 x 2,204,620 lb / 25,000 lb = 44.31 -> short 44 contracts
  implied ratio 0.4990   under-hedged by 7,796 lb
  effectiveness at h* 34.0549%  vs at 44 contracts 34.0532%  (rounding costs 0.0017 pp)
  naive 1:1 would be 88 contracts
```

Two numbers that look inconsistent but aren't — worth knowing before a reader asks:

- Block B's "naive 1:1 +0.7%" and block C's "+0.6%" are both right: B is all 1,845
  roll-excluded days, C is the 1,785/1,725 evaluation days where an OOS ratio exists.
- The unhedged variance differs from `PHASE2_INSTRUCTIONS.md`'s 0.002977 because
  Phase 2 used all 1,874 change days; every later phase (and this README) uses the
  1,845 roll-excluded convention.

## 5. Completion checklist

- [ ] Every `TODO W#` block in `README.md` is replaced by a written section
- [ ] Every number in the README appears in the §4 output (spot-check by grepping a
      few: 0.5025, +33.5%, +70.0%, 0.0531, −754,097, 44)
- [ ] No in-sample number stands without its out-of-sample counterpart nearby, and
      the daily/weekly pairing is stated
- [ ] Limitations cover all four required items (§3, W8)
- [ ] All four figures are embedded and render on the repo page
- [ ] `uv run pytest` still says **115 passed** and `git status` shows only
      `README.md` modified
- [ ] The 3-minute test: read it top to bottom timed — a first-time reader gets the
      headline, the four charts, and the May-2024 story inside three minutes
- [ ] Commit locally (e.g. `docs: results-driven README (phase 7)`) — then **send the
      draft back before it goes to main.** This is a document with an audience; it
      gets one round of reading first. Numbers were the handback in Phases 2–6; here
      it's the draft itself.
