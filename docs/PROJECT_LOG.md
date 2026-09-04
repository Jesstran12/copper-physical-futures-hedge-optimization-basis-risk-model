# Copper Hedge & Basis Analysis — Spec & Feature Log

> **How we use this file:** every working session starts by reading the **Current State**
> block below, then picks up the next unchecked phase in the Feature Log. When a phase is
> done, we tick its boxes, add a one-line completion note, and update Current State. This
> file is the single source of truth for where the project stands.

---

## Current State

| | |
|---|---|
| **Status** | Analysis and write-up complete. Phases 1 to 6 delivered the tested modules and the four figures (suite at **115 passed**); Phase 7 delivered the README write-up, finished 2026-09-04 with an owner editing pass on the collaborator's draft. The repo was then reorganized for publication: process docs moved under `docs/` (phase instructions under `docs/phases/`), the figure script under `scripts/`, and the handoff TODO scaffolding stripped from `src/copper_hedge/`, with the suite unchanged |
| **Next up** | Publish. Phase 8 (talking points and final polish) stays open as optional follow-on work |
| **Last session** | 2026-09-04, repo reorganized for publication |
| **Blockers** | None |

---

## 1. Project overview

You hold physical copper (long spot) and hedge by shorting COMEX copper futures. The project
answers three questions a physical desk lives on:

1. **How many futures to short per unit of physical** — the minimum-variance hedge ratio.
2. **How much risk the hedge removes** — hedge effectiveness, in- and out-of-sample.
3. **Why it is never perfect** — basis risk, quantified and tied to real market events.

**Audience & goals** (agreed at kickoff): interview-prep artifact for commodity-trading
roles, first of a portfolio series (this repo sets the conventions), and desk-usable
numbers — not just a pretty in-sample R².

**Headline deliverable:** out-of-sample variance reduction of the optimal hedge vs. a naive
1:1 hedge, plus quantified residual basis risk.

## 2. The finance

- Minimum-variance hedge ratio: `h* = Cov(ΔS, ΔF) / Var(ΔF) = ρ · σ_S / σ_F` — the slope of
  the OLS regression of spot price changes on futures price changes.
- Hedged position change: `ΔP = ΔS − h·ΔF` (long spot, short h units of futures).
- Hedge effectiveness: `e = 1 − Var(ΔP_hedged) / Var(ΔS)`; in-sample with h = h*, this equals
  the regression R².
- Basis: `b = S − F` (same units). Basis risk = std(Δb), the residual a hedge cannot remove.
- All hedging math uses **price changes in $/lb**, not returns — minimum-variance hedging in
  contract terms is a price-change problem. The README must state and defend this choice.

## 3. Data design (agreed at kickoff)

| Series | Source | Role |
|---|---|---|
| LME cash copper (official settlement, $/tonne) | Westmetall (free, scraped once, CSV committed) | **Primary spot leg** — real physical-market price, gives a true spot-vs-futures basis |
| CPER (US Copper ETF) | yfinance | **Secondary spot proxy** — robustness check only; it holds COMEX futures itself, so effectiveness against it is overstated. This limitation is stated explicitly. |
| HG=F (COMEX copper front-month, $/lb) | yfinance | Hedge instrument |

Rules:

- **Units:** everything converted to **$/lb** (LME: ÷ 2,204.62 lb/tonne) so basis is a true
  price difference and h* is interpretable. Desk translation: 1 COMEX contract = 25,000 lb.
- **Span:** 2019-01-01 → present (~7 years: pre-COVID calm, COVID 2020, 2021–23 tightness,
  May-2024 COMEX squeeze, 2025+).
- **Alignment:** inner join on common trading days (LME/COMEX/NYSE calendars differ); report
  how many rows each mismatch drops. No forward-filling into the regression data.
- **Outliers:** kept — violent days are real hedging days and belong in the risk numbers.
- **Caching:** raw pulls are cleaned once and committed as CSVs under `data/`; analysis runs
  entirely off the committed CSVs. Refresh is manual/on-demand only.
- **Futures roll:** HG=F is a spliced front-month series; roll dates inject artificial jumps
  into ΔF. Detect roll dates (contract-change / price-gap heuristic against the COMEX copper
  active-month calendar: Mar, May, Jul, Sep, Dec) and **exclude flagged ΔF observations from
  regressions**; keep them in charts, flagged. Roll risk gets its own discussion (contango/
  backwardation talking point).

## 4. Methodology

1. **Baselines:** variance of unhedged ΔS; naive 1:1 hedge (h = 1) variance. The benchmark to beat.
2. **In-sample optimal hedge:** OLS of ΔS on ΔF (statsmodels) on the full sample; slope = h*,
   R² = in-sample effectiveness; report variance reduction vs. naive.
3. **Out-of-sample (the methodological heart):** rolling estimation with **60d and 120d
   windows plus an expanding window**, each applied strictly one step ahead (estimate on
   `[t−w, t)`, apply at `t`) — no lookahead anywhere. Report OOS effectiveness per window,
   compare to in-sample, and explain the degradation and the window-size bias/variance tradeoff.
4. **Async-close robustness:** COMEX settles ~1pm ET, CPER closes 4pm ET, LME fixes ~1pm
   London — asynchronous closes attenuate daily correlations. Re-run the core numbers on
   **weekly changes** and explain why weekly effectiveness is higher.
5. **Sub-period table:** h* and effectiveness for ~5 regimes (2019 calm, 2020 COVID,
   2021–23 tightness, 2024 squeeze era, 2025+), alongside the rolling-h* chart.
6. **Basis analysis:** basis level and std(Δb) over time in $/lb; show residual hedged risk ≈
   basis risk; annotate major events on the chart; **half-page case study of the May 2024
   COMEX–LME squeeze** (record ~$1,000+/tonne COMEX premium) showing what it did to a short-
   futures hedger's P&L that month.
7. **Desk translation:** one worked example — e.g., long 1,000 t of cathode, h* = 0.85 →
   short ⌊0.85 × 2,204,620 / 25,000⌉ = 75 contracts — including the rounding-error impact.
   Core analysis stays in clean per-lb terms.

## 5. Metrics to report

- Naive 1:1 hedge variance reduction (%)
- Optimal in-sample effectiveness (R²)
- Optimal out-of-sample effectiveness (%) per window (60d / 120d / expanding)
- **Headline:** OOS variance reduction vs. naive 1:1
- Basis volatility std(Δb), $/lb, and as share of residual hedged variance
- Daily vs. weekly effectiveness comparison
- Sub-period h* and effectiveness table

## 6. Deliverables

- `README.md` — the presented deliverable, results-driven: headline numbers + four figures
  first, then finance, method, honest limitations (CPER proxy, roll, async closes, LME/COMEX
  grade & location differences). It took the place of the analysis notebook in the original
  plan; every number it cites prints from the numbers-pack script in
  `docs/phases/PHASE7_INSTRUCTIONS.md`.
- Four figures in `figures/`: normalized price series; basis over time (event-annotated);
  rolling hedge ratio (multi-window); hedged vs. unhedged ΔP distribution.
- Tested modules in `src/copper_hedge/` with the pytest suite (115 tests) as the
  reproduction guarantee.
- `TALKING_POINTS.md` — interview rehearsal: Cov/Var derivation, why R² = effectiveness, basis
  risk one-liner, contango/roll explanation, each slotted with the project's actual numbers,
  likely follow-ups, and 2–3 resume-line variants with real figures (Phase 8, not started).

## 7. Repo structure

```
Individual-Project-1/
├── README.md                    # the write-up: results, figures, finance, limitations
├── pyproject.toml / uv.lock     # uv-managed environment
├── data/                        # committed cleaned CSVs, the source of truth
├── figures/                     # the four charts the README embeds
├── src/copper_hedge/
│   ├── data.py                  # loading, cleaning, unit conversion, alignment
│   ├── roll.py                  # roll-date detection/flagging
│   ├── hedge.py                 # hedge ratios, effectiveness, OOS engine, weekly/regime reports
│   └── basis.py                 # basis stats + case-study P&L windows
├── tests/                       # pytest — all math is unit-tested (115 tests)
├── scripts/
│   └── rolling_hedge_figure.py  # regenerates figures/rolling_hedge_ratio.png
└── docs/                        # the process record
    ├── PROJECT_LOG.md           # this file — living spec & feature log
    ├── WORKLOG.md               # session-by-session work log, newest first
    ├── SETUP.md                 # environment setup guide
    └── phases/                  # the self-contained phase handoff instructions (2–7)
```

## 8. Feature log

> One phase per session, strictly. A phase is **done** when: code + tests pass
> (`uv run pytest`), figures/outputs updated if applicable, this checklist ticked with a
> completion note, Current State updated, and a local commit made.

### Phase 0 — Project setup
- [x] uv project init (`pyproject.toml`, Python ≥3.12, deps: pandas, numpy, statsmodels, matplotlib, yfinance, requests, beautifulsoup4, pytest, jupyter)
- [x] Repo skeleton (`src/copper_hedge/`, `tests/`, `data/`, `notebooks/`, `figures/`, `.gitignore`)
- [x] README stub: one paragraph on the goal

*Done 2026-08-13: uv env on Python 3.12.13 with all 9 deps locked in `uv.lock`; src-layout package `copper_hedge` installed; 2 smoke tests pass via `uv run pytest`.*

### Phase 1 — Data layer
- [x] yfinance pull for HG=F and CPER (note: yfinance now auto-adjusts by default — be explicit about which close is used)
- [x] Westmetall LME-cash scraper (polite, run-once) + cleaning to tidy CSV
- [x] Unit conversion to $/lb; inner-join alignment; dropped-row accounting
- [x] Committed snapshot CSVs in `data/`
- [x] Sanity figure: normalized price series of all three legs (`figures/price_series.png`)
- [x] Tests: unit conversion, alignment behavior on synthetic misaligned calendars

*Done 2026-08-13: raw unadjusted Close for both yfinance legs (`auto_adjust=False`; CPER
verified to have zero splits/distributions so raw = honest price); Westmetall scraped once,
politely (8 year-pages, 2s apart, honest User-Agent) → `data/lme_cash_settlement.csv`
($/tonne + $/lb, 1,924 rows); aligned inner-join = 1,875 rows 2019-01-02 → 2026-08-12,
dropping LME 49 / HG 42 / CPER 36 rows to calendar mismatch; aligned view is derived at load
time by tested `load_aligned()` (three CSVs stay the single source of truth); 16 tests pass.*

### Phase 2 — Roll detection + baselines
- [x] Roll-date detection for HG=F (active-month calendar + gap heuristic); flags stored alongside data
- [x] Unhedged variance; naive 1:1 hedge variance; naive variance reduction number
- [x] Tests: roll flagging on synthetic jump series; baseline variance math

*Scaffolded 2026-08-16 as a self-contained assignment: `PHASE2_INSTRUCTIONS.md` + stubs in
`src/copper_hedge/roll.py` / `hedge.py` + tests in `tests/test_roll.py` /
`tests/test_hedge.py`.*

*Done 2026-08-20: implementation pulled and verified — 40/40 tests pass, `tests/` and
`data/` unmodified, and the Section 5 script reproduces every expected number exactly
(29 roll flags; unhedged daily variance 0.002977 ($/lb)²; naive 1:1 reduction +0.7%
roll days excluded / −34.1% all days). `data/hg_roll_flags.csv` (1,874 flag rows,
2019-01-03 → 2026-08-12) committed alongside the other data files.*

### Phase 3 — Optimal hedge, in-sample
- [x] OLS ΔS-on-ΔF (roll-flagged obs excluded); h*, R², variance reduction vs. naive
- [x] Both spot legs (LME primary, CPER secondary) — comparison table
- [x] Tests: h* equals hand-computed Cov/Var on synthetic data; in-sample e = R² identity

*Scaffolded 2026-08-20 as a self-contained assignment: `PHASE3_INSTRUCTIONS.md` +
stubs (TODO 7–10) in `src/copper_hedge/hedge.py` + tests in
`tests/test_optimal_hedge.py`, including the h* = Cov/Var hand-check and the
effectiveness = R² identity test. Expected real-data numbers are in the
instructions doc's Section 5 table.*

*Done 2026-08-22: implementation pulled and verified — 58/58 tests pass, `tests/`
and `data/` unmodified, and the Section 5 script reproduces every number in the
instructions doc's expected table exactly (both legs; the effectiveness = R²
identity agrees to ~1e-16). Close-out commit also reverted a whitespace-only
reformat of `roll.py` (a file the instructions asked to leave untouched) and fixed
one misindented comment line — no functional changes.*

### Phase 4 — Out-of-sample engine
- [x] Rolling one-step-ahead h* at 60d, 120d, expanding; strict no-lookahead
- [x] OOS effectiveness per window vs. naive and vs. in-sample; degradation discussion
- [x] Rolling hedge-ratio figure (`figures/rolling_hedge_ratio.png`)
- [x] Tests: no-lookahead guard (shifting future data must not change past estimates); engine on synthetic data with known time-varying beta

*Verified & closed out 2026-08-23. The implementation (commits `9362ba7` + `b5be13c`,
TODO 11–13 in `hedge.py`) was pulled and cross-checked: suite **76 passed** — the
exact complete state named in the instructions doc, with all three no-lookahead
attack tests green — `tests/` and `data/` untouched, the code spot-checked against
the reference implementation (substantively identical; the one-step shift placed
correctly), and a fresh run of `run_phase_4.py` reproduced every cell of the
Section 5 expected table exactly: OOS 60d +33.5% (1,785 eval days) / 120d +33.1%
(1,725) / expanding +33.8% (1,785); naive +0.6% on the same days; in-sample h*
0.5025 / +34.1% unchanged; ratio-path min/median/max all exact. The figure passes
its eyeball checks (warm-up gap, paths orbiting 0.5, real dips late 2020 and late
2025) and is now committed. Process note: the push again preceded the numbers
report — the checklist order stands for Phase 5.*

*Scaffolded 2026-08-22 as a self-contained assignment: `PHASE4_INSTRUCTIONS.md` +
stubs (TODO 11–13) in `src/copper_hedge/hedge.py` + 18 tests in
`tests/test_oos_hedge.py`, including three tests that attack the no-lookahead rule
directly and an engine test on synthetic data whose true beta shifts mid-sample.
Expected real-data numbers and the figure description are in the instructions
doc's Section 5.*

### Phase 5 — Robustness: weekly + sub-periods
- [x] Weekly-change (Fri–Fri common days) re-run of core numbers; daily-vs-weekly comparison + async-close explanation
- [x] Sub-period table (5 regimes) of h* and effectiveness
- [x] Tests: weekly resampling correctness

*Verified & closed out 2026-09-01. The implementation (commit `0be1963`, TODO 14–17
in `hedge.py`, no other file touched) was pulled and cross-checked: suite
**96 passed** — the exact complete state named in the instructions doc —
`tests/` and `data/` untouched, the code spot-checked against the reference
implementation (substantively identical), and the Section 5 script reproduced
every cell of the expected tables exactly: daily benchmark unchanged (n=1845,
h* 0.5025, +34.1%); weekly n=375 Fri–Fri weeks, h* 0.7276, corr 0.8364,
effectiveness **+70.0%**, naive 1:1 +60.2% — the async-close prediction
confirmed, effectiveness roughly doubling at the weekly frequency; sub-periods
2019 +26.6%, 2020 +23.1%, 2021–23 +35.4%, 2024 +36.2%, 2025+ +34.6% with h*
stable 0.45–0.56 throughout. Close-out commit adds only a missing trailing
newline in `hedge.py`. Process note: the push again preceded the numbers
report (fourth time) — the checklist order stands for Phase 6.*

*Scaffolded 2026-08-24 as a self-contained assignment: `PHASE5_INSTRUCTIONS.md` +
stubs (TODO 14–17) in `src/copper_hedge/hedge.py` + 20 tests in
`tests/test_robustness.py`, including an async-close synthetic that requires the
weekly R² to beat the daily one, roll-week exclusion checks, and a sub-period
isolation test (data outside a period must never move its row). The five regime
definitions ship as the `SUB_PERIODS` constant. Expected real-data numbers are
in the instructions doc's Section 5 tables.*

### Phase 6 — Basis analysis + 2024 case study
- [x] Basis series (LME cash − HG, $/lb), std(Δb), residual-risk linkage
- [x] Event-annotated basis figure (`figures/basis_over_time.png`): COVID, 2021–22 tightness, May-2024 squeeze, 2025 US tariff dislocation (COMEX–LME premium blowout and collapse)
- [x] May-2024 COMEX–LME squeeze case study: what happened to the hedger's P&L that month
- [x] Hedged vs. unhedged ΔP distribution figure (`figures/pnl_distribution.png`)
- [x] Tests: basis math

*Scaffolded 2026-09-01 as a self-contained assignment: `PHASE6_INSTRUCTIONS.md` +
stubs TODO 18–21 in the new `src/copper_hedge/basis.py` (`basis_series`,
`basis_report`, `residual_risk_report`, `window_pnl`) + 19 ready-made tests in
`tests/test_basis.py`, validated against a reference implementation. The tests
enforce the phase's central identity — the daily basis change IS the 1:1 hedger's
residual P&L, to the last bit — plus the Var(residual) = (1−R²)·Var(ΔS) identity
and the roll-exclusion convention on basis changes (level stats use all days).
Both figures are produced by the instructions doc's Section 5 script, which also
prints the case-study numbers (May 2024 squeeze run-up/snap-back/whole-month, and
the 2025 tariff blowout and one-day collapse). Expected real-data numbers are in
the instructions doc's Section 5 tables.*

*Verified & closed out 2026-09-02: the implementation passed the full check-back —
**115 passed** with `tests/` and `data/` unmodified since the skeleton, every
Section 5 printed number an exact match to the expected tables (basis mean
−0.0592 $/lb, std(Δb) 0.0531; May-2024 run-up −$754,097 / snap-back +$665,286 /
whole month +$67,234 on 1,000 t; 2025 blowout −$2,810,701 / collapse +$2,873,867),
and a local re-run of the Section 5 script reproduced both committed figures
byte-identical. The half-page May-2024 narrative is drafted and lands in the
Phase 7 README.*

### Phase 7 — README write-up
- [ ] Results-driven README: headline numbers, four figures, finance, method, desk-translation worked example (1,000 t → integer contracts + rounding impact), honest limitations

*Scaffolded 2026-09-02 as a self-contained writing assignment: `README.md` holds the
section skeleton (nine TODO W# blocks, each saying what its section must contain) and
`PHASE7_INSTRUCTIONS.md` holds the per-section briefs, the house writing rules
(results first; never an in-sample number without its out-of-sample counterpart; real
numbers only), and a §4 numbers-pack script whose expected output was verified against
a fresh run — it reproduces every Phase 2–6 headline number exactly and adds the
phase's one new computation, the desk translation (1,000 t at h\* 0.5025 → short 44
COMEX contracts; rounding costs 0.0017 pp of effectiveness; naive 1:1 = 88 contracts).
A complete reference README was written first to prove the template out (same rule as
the code phases' reference implementations) and stays with the project owner for the
close-out comparison. This phase changes exactly one file; the suite stays 115 passed.*

*Delivered 2026-09-04: the collaborator's draft was finished with an owner editing pass
(case studies expanded into the May 2024 squeeze and the 2025 tariff episode, the
limitations section completed, layout polished). Every cited number traces to the §4
numbers pack; the suite stayed at **115 passed** with only `README.md` touched. The box
stays unticked until the owner's final verification pass.*

### Phase 8 — TALKING_POINTS.md + polish
- [ ] Talking points with actual numbers slotted in; likely follow-up questions
- [ ] Resume-line variants with real figures
- [ ] Final pass: figure styling consistency, repo ready to publish

## 9. Decisions log

| Decision | Choice | Why |
|---|---|---|
| Spot leg | LME cash primary + CPER secondary | CPER holds futures — futures-on-futures inflates R² and fakes the basis; LME cash gives a real basis |
| Units | Everything in $/lb, price changes (not returns) | True basis, interpretable h*, contract-terms hedging |
| Async closes | Daily primary + weekly robustness | Close-time mismatch attenuates daily correlation; explaining it is a talking point |
| Roll handling | Detect + flag, exclude from regressions | Splice jumps pollute ΔF; back-adjusting from individual contracts is data-plumbing risk |
| OOS design | 60d + 120d + expanding, one-step-ahead | Shows window bias/variance tradeoff; no lookahead |
| LME sourcing | One-time polite scrape, CSV committed | Reproducible without hammering the site |
| Desk realism | Worked example only (no integer-contract backtest) | Credibility without complicating every downstream number |
| Basis narrative | Stats + annotations + May-2024 case study | The squeeze is the perfect "basis risk hurts a physical desk" story |
| Data hygiene | Inner join, keep outliers | Crisis days are real hedging days |
| Sample | 2019→present, full sample + 5 sub-periods | Regime coverage incl. COVID and the squeeze |
| Engineering | Tested src/ + thin notebook, TDD, uv | Template for the portfolio series |
| Session pacing | One phase per session, strict | Predictable handoffs; spec never drifts |
| Publishing | Local commits only; push once the work is finished | No half-finished work public |
| CPER units | Keep $/share, column named `cper_usd_per_share` (decided 2026-08-13) | No physical $/lb conversion exists for an ETF share; R²/effectiveness are scale-invariant, so honesty beats an arbitrary rescale. CPER h* gets a units footnote in Phase 3 |
| Phase 3 contract | h* and R² specified as closed-form sample moments (Cov/Var, corr²) with statsmodels OLS documented as an equivalent accepted route; effectiveness computed from variances independently of R² so the identity test is meaningful; regressions reuse the committed `data/hg_roll_flags.csv` (2026-08-20) | Same estimator either way (verified identical on real data); moment form keeps the functions pure and directly testable; reusing committed flags keeps Phase 2's sample definition |
| CPER naive-1:1 row footnoted | CPER's naive 1:1 comparison is reported but marked unit-dependent, like its h* (2026-08-20) | "h = 1" in $/share-vs-$/lb units is an arbitrary ratio; only R²/effectiveness are scale-invariant |
| Phase 4 contract | One-step-ahead h* = trailing Cov/Var moments (ddof=1, same estimator as Phase 3) computed rolling/expanding then shifted one step; rolling windows require a full window of prior observations (windows count roll-excluded trading observations); expanding uses a 60-observation burn-in matching the shortest rolling window; the engine runs on roll-excluded changes for estimation and evaluation, and every reported number (including the naive comparison) is computed on the same defined-ratio evaluation days; the figure is produced by the instructions script, keeping the library functions pure (2026-08-22) | The single one-step shift is the entire no-lookahead guarantee and is directly testable; consistent roll handling carries the "roll days excluded" convention into the OOS numbers; same-days evaluation keeps comparisons apples-to-apples |
| Phase 4 legs | OOS engine reported on the LME (primary) leg only (2026-08-22) | The CPER robustness point (futures-on-futures scores ≈2× higher) was already made in-sample in Phase 3; repeating it out-of-sample adds surface area without new information |
| Phase 5 contract | Weekly = Friday-anchored calendar weeks on the common trading days, each contributing its last observation (labeled by the Friday; empty weeks dropped, never filled), differenced into weekly changes; a week containing any roll-flagged day is excluded from the weekly regression; the weekly re-run is in-sample on the LME leg; sub-periods = calendar-year regime boundaries (2019 \| 2020 \| 2021–23 \| 2024 \| 2025+) fitted independently per period on the daily roll-excluded changes, endpoints inclusive (2026-08-24) | Last-common-day weeks never forward-fill; a splice jump contaminates the weekly change spanning it exactly as it does the daily one; the weekly run measures async-close attenuation (out-of-sample honesty was Phase 4's job) and stays on the primary leg; calendar years keep the regime boundaries simple and defensible |
| Weekly roll-exclusion sensitivity reported | Excluding the 22 roll-contaminated weeks (of 397, spread across every year) materially lifts the weekly correlation; the instructions doc reports the numbers both ways (2026-08-24) | The exclusion is the standing convention, but the flag heuristic can catch genuinely violent real days too, so honesty wants both numbers on record |
| Phase 6 contract | The basis gets ONE definition in code (`basis_series` = LME cash − HG front month, $/lb; negative = COMEX premium — both dislocations point down); basis LEVEL stats use all days while basis CHANGE stats exclude roll-flagged days; `residual_risk_report` computes the basis-change route itself (Δb = ΔS − ΔF) rather than reusing the naive hedge helper, so the Δb ≡ 1:1-residual identity test compares independently computed numbers; `window_pnl` = inclusive date slicing, last-minus-first moves, short leg = −h·ΔF, ValueError on an empty window; both figures are produced by the instructions script, keeping plotting out of `src/`; nothing in the phase rolls or expands, so the no-lookahead guard is replaced by the identity tests (2026-09-01) | One definition prevents sign/units drift across the write-ups; Δb inherits ΔF's splice jumps, so the exclusion convention carries; independently computed identity partners keep "basis risk IS the 1:1 hedger's residual" a tested equation rather than a slogan |
| Phase 6 case-study windows | The spec says "that month", but May 2024 first-to-last is only +0.0305 $/lb — the squeeze washes out at month ends. The case study reports the run-up (Apr 30 → May 14, the basis trough), the snap-back (May 14 → 31), and the whole month side by side, plus the 2025 sequel (Jan 2 → Jul 25 blowout, Jul 25 → Aug 5 collapse spanning the Jul 30 exemption) (2026-09-01) | The month-end wash-out IS the lesson — month-end accounting looks fine while the mark-to-market ride in between is what hurts — so all three windows are needed to tell it honestly |
| Phase 7 delivery | The README is written as a handoff too — the first writing one: a TODO-sectioned skeleton in `README.md` + `PHASE7_INSTRUCTIONS.md` (section briefs, writing rules, verified numbers pack). The collaborator drafts every section, including the May-2024 case study in her own words; a reference README written up front proves the template completable, and the project owner gives the draft a read and final edit before it merges to main (2026-09-02) | Extends the phase-handoff pattern to prose: the frozen data snapshot makes every citable number exactly checkable, the checklist makes "done" objective, and a read-before-merge keeps quality control on the repo's public face |
| Notebook dropped from scope | `notebooks/hedge_analysis.ipynb` left the plan; `README.md` is the presented deliverable and the empty `notebooks/` folder was removed in the publication cleanup (2026-09-04) | The results-driven README already carries the full narration; a thin notebook restating it would add maintenance cost without adding information |
