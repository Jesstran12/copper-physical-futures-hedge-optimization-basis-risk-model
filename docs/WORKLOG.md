# WORKLOG — Copper Hedge & Basis Analysis

Session-by-session history, newest first. Whoever runs a session appends one entry using
this template — plain English, so the other of us can review it without reading code.

> **Template**
>
> ## YYYY-MM-DD — <phase or purpose>
> - **What was done:** steps taken, in order.
> - **Choices made & why:** every design decision and its rationale.
> - **Quality:** test results, key numbers, figures produced.
> - **Added / changed / deleted:** exact files touched.

---

## 2026-09-04 — Repo reorganized for publication

- **What was done:** Cleaned the repo so the published page leads with the work,
  not the process. Moved the six phase instruction docs to `docs/phases/` and
  `PROJECT_LOG.md`, `WORKLOG.md`, `SETUP.md` to `docs/`; renamed `run_phase_4.py`
  to `scripts/rolling_hedge_figure.py` and gave it a docstring. Stripped the 21
  numbered TODO hint blocks left over from the phase handoffs out of
  `src/copper_hedge/` (`roll.py`, `hedge.py`, `basis.py`); the docstring
  contracts stay, and the two no-lookahead `shift(1)` notes were kept as regular
  comments. Removed the `.gitkeep` placeholders and the empty `notebooks/`
  folder. Updated every cross-reference: the README's reproduction paragraph,
  SETUP's command table and stale Phase 1 test count, PROJECT_LOG's Current
  State, deliverables list and repo tree, and the phase docs' `SETUP.md` /
  `PROJECT_LOG.md` mentions, which now carry `docs/` paths.
- **Choices made & why:** The instruction docs stay in the repo instead of being
  deleted: they are the evidence of the test-first handoff process, and the
  README points at them for reproduction. Only forward-looking references were
  repathed; historical log entries keep their original wording. The Phase 7 box
  stays unticked pending the owner's verification pass, with the delivery
  recorded in a note under it.
- **Quality:** `uv run pytest` still **115 passed** after the comment strip.
  `scripts/rolling_hedge_figure.py` re-run from the repo root reproduces every
  out-of-sample headline (+33.5% / +33.1% / +33.8% optimal vs +0.6% naive) and
  rewrites the committed figure byte-identical.
- **Added / changed / deleted:** Moved ten files into `docs/` and `scripts/`;
  changed `src/copper_hedge/roll.py`, `hedge.py`, `basis.py` (comments only),
  `README.md` (final paragraph), `docs/SETUP.md`, `docs/PROJECT_LOG.md`, and the
  six `docs/phases/*.md`; deleted three `.gitkeep` files.

---

## 2026-09-04 — Phase 7 README finished

- **What was done:** The README draft was finished with an owner editing pass:
  the remaining placeholders filled, the case-study material rebuilt as two
  prose case studies (the May 2024 squeeze, and the 2025 tariff episode as its
  own section), the limitations section completed, then a layout pass (centered
  title block, badges, one-line contents, figure subheadings, module table).
- **Choices made & why:** An owner pass on the collaborator's draft instead of a
  second collaborator round; the draft's substance was kept and folded back in
  as prose, its unverifiable market prices left out.
- **Quality:** Every cited number was re-verified line by line against the
  numbers-pack script before writing; suite unchanged at **115 passed**; only
  `README.md` touched, over several local commits.
- **Added / changed / deleted:** Changed `README.md` only.

---

## 2026-09-02 — Phase 7 scaffolded as a writing assignment

- **What was done:** Packaged the README write-up the same way as the code
  phases, adapted for prose. `README.md` now carries the section skeleton —
  nine sections, each with a TODO W# block saying exactly what it must
  contain — and `PHASE7_INSTRUCTIONS.md` carries the plain-English brief, a
  section-by-section guide, the house writing rules, and a §4 paste-and-run
  "numbers pack" script that prints every number the README may cite, with
  its expected output included (verified against a fresh run before
  shipping — it reproduces every Phase 2–6 headline exactly). A complete
  reference README was written first to prove the template out, same rule as
  the code phases' reference implementations, and stays with the project
  owner for the close-out comparison. One local commit; the phase's
  checklist stays unticked until the draft comes back and is read.
- **Choices made & why:** Logged in PROJECT_LOG's Decisions table. The two
  that matter: the case-study half-page is written by whoever drafts the
  README, in their own words — it's the section a reader remembers, so it
  shouldn't read like filled-in blanks; and because this phase's deliverable
  IS the document, the handback is the draft itself (sent back or pushed to
  a branch) for a read before anything merges to main.
- **Quality:** No code changed; the suite stays at **115 passed** and the
  checklist uses that as the tripwire (this phase touches exactly one file).
  New numbers verified for the desk-translation section: 1,000 t at
  h\* 0.5025 → short **44** COMEX contracts, rounding away only 0.0017 pp of
  effectiveness; the naive 1:1 hedge would short 88.
- **Added / changed / deleted:** Added `PHASE7_INSTRUCTIONS.md`. Changed
  `README.md` (one-paragraph stub → section skeleton), `PROJECT_LOG.md`
  (Current State, scaffold note, Decisions row), and `WORKLOG.md` (this
  entry). Nothing deleted; nothing pushed.

---

## 2026-09-02 — Phase 6 verified & closed out

- **What was done:** Pulled the Phase 6 implementation (commits `e017a9c` —
  the four TODO functions in `src/copper_hedge/basis.py` — and `0507f8e`, the
  two figures), confirmed `tests/` and `data/` were unmodified, ran the full
  suite, ran the instructions doc's Section 5 script on the real data,
  compared every printed number against the expected tables, and spot-checked
  the code against the reference implementation. Ticked Phase 6 in the log,
  updated Current State, and drafted the half-page May-2024 case-study
  narrative for the Phase 7 README; one local close-out commit.
- **Choices made & why:** None new — pure verification against the shipped
  contracts. One note for the next phase: the numbers-before-push order
  slipped again — please report the Section 5 numbers back before pushing, so
  the check-back can confirm them against a fresh run rather than after the
  fact.
- **Quality:** **115 passed** — exactly the "complete" count. Every Section 5
  number matched the expected tables exactly (basis mean −0.0592 $/lb, std(Δb)
  0.0531; May-2024 run-up −$754,097 / snap-back +$665,286 / whole month
  +$67,234 on 1,000 t; 2025 blowout −$2,810,701 / collapse +$2,873,867), the
  Δb ≡ 1:1-residual identity held to the last bit on real data, and a local
  re-run of the Section 5 script reproduced both committed figures
  byte-identical. The implementation matched the reference logic throughout
  (naming and comment differences only) — nice clean work.
- **Added / changed / deleted:** Changed `PROJECT_LOG.md` (Phase 6 ticked +
  completion note, Current State), `src/copper_hedge/basis.py` (added the
  missing trailing newline, no code change), and `WORKLOG.md` (this entry).
  Nothing deleted; nothing pushed.

---

## 2026-09-01 — Phase 6 scaffolded as a self-contained assignment

- **What was done:** Packaged Phase 6 (basis analysis + the squeeze case
  studies) the same way as Phases 2–5: a new module `src/copper_hedge/basis.py`
  with four documented function stubs (TODO 18–21), 19 ready-made tests in
  `tests/test_basis.py` written first and validated against a reference
  implementation, and `PHASE6_INSTRUCTIONS.md` — self-contained, with a
  paste-and-run Section 5 script that prints the phase's real-data numbers and
  saves the two figures (`basis_over_time.png`, `pnl_distribution.png`), plus
  expected-numbers tables checked against the reference. Doc updates and one
  local commit; the phase's checklist stays unticked until the numbers come
  back and are confirmed.
- **Choices made & why:** Logged in PROJECT_LOG's Decisions table. Two worth
  highlighting: (a) the tests enforce the phase's central identity — the daily
  basis change IS the 1:1 hedger's residual P&L, exactly — from two independent
  routes, so "basis risk is the risk a hedge cannot remove" ships as a tested
  equation; (b) the May 2024 case study reports three windows (run-up,
  snap-back, whole month) because the full month nets out to almost nothing —
  the wash-out is the lesson, and hiding it behind a single month-end number
  would miss the point. The 2025 tariff windows were added alongside: the data
  shows that dislocation is ~4× the size of May 2024.
- **Quality:** Reference implementation took the full suite to **115 passed**
  before stripping; the shipped starting state is **19 failed / 96 passed**,
  every failure a clean `NotImplementedError` at a numbered TODO, all previous
  phases still green. The embedded script was diffed byte-identical against
  the copy actually run, and both figures passed their visual checks.
- **Added / changed / deleted:** Added `src/copper_hedge/basis.py` (stubs),
  `tests/test_basis.py`, `PHASE6_INSTRUCTIONS.md`. Changed `PROJECT_LOG.md`
  (Current State, Phase 6 scaffold note, two Decisions rows) and `WORKLOG.md`
  (this entry). One local commit; nothing pushed. **Reminder for the
  implementation session: report the Section 5 numbers back before pushing —
  see the note at the top of the instructions doc.**

---

## 2026-09-01 — Phase 5 verified & closed out

- **What was done:** Pulled the Phase 5 implementation (commit `0be1963` —
  the four TODO functions in `src/copper_hedge/hedge.py`, nothing else
  touched), ran the full suite, ran the instructions doc's Section 5 script
  on the real data, compared every printed number against the expected
  tables, and spot-checked the code against the reference implementation.
  Ticked Phase 5 in the log and updated Current State; one local close-out
  commit.
- **Choices made & why:** None new — pure verification against the shipped
  contract. The close-out commit adds only a missing trailing newline at the
  end of `hedge.py` (no functional change).
- **Quality:** **96 passed** — the exact complete state — with `tests/` and
  `data/` untouched. Every number matches: daily benchmark unchanged (n=1845,
  h* 0.5025, effectiveness +34.1%); weekly n=375 Fri–Fri weeks, h* 0.7276,
  corr 0.8364, effectiveness **+70.0%** (async-close prediction confirmed —
  effectiveness roughly doubles weekly), naive 1:1 +60.2% weekly vs +0.7%
  daily; sub-period table cell-for-cell (2019 +26.6%, 2020 +23.1%, 2021–23
  +35.4%, 2024 +36.2%, 2025+ +34.6%; h* stable 0.45–0.56). The implementation
  is substantively identical to the reference (naming/composition style
  only). Process note, once more: the push again came before the numbers
  report — four phases running now. **Numbers first, push after they're
  confirmed** — let's actually do it that way for Phase 6.
- **Added / changed / deleted:** Changed `src/copper_hedge/hedge.py`
  (trailing newline only), `PROJECT_LOG.md` (Phase 5 ticked, close-out note,
  Current State), `WORKLOG.md` (this entry). One local commit.

---

## 2026-08-24 — Phase 5 packaged as a self-contained assignment

- **What was done:** Phase 5 (the robustness checks — the weekly re-run of the
  core numbers and the five-regime sub-period table) is ready to hand off,
  same format as before: `PHASE5_INSTRUCTIONS.md` (committed, self-contained)
  + 4 stubbed functions with numbered TODOs (14–17) in
  `src/copper_hedge/hedge.py` + 20 ready-made tests in
  `tests/test_robustness.py`. The tests were validated green against a working
  reference implementation before being shipped as stubs, and the instructions
  doc's Section 5 script was run against that reference, so its
  expected-numbers tables reflect the real committed data.
- **Choices made & why:** Weekly means Friday-anchored calendar weeks on the
  common trading days, each week contributing its last available observation —
  the one weekly definition that never forward-fills — and a week containing
  any roll-flagged day is excluded from the weekly regression, carrying the
  Phase 2–4 convention to the weekly frequency (the instructions doc reports
  the numbers with and without that exclusion, since it is material). The
  weekly re-run stays in-sample on the LME leg: its job is to measure how much
  the London/New-York timing mismatch depresses the daily numbers, not to
  re-prove out-of-sample honesty (that was Phase 4). The five regimes sit on
  calendar-year boundaries and each is fitted independently — one test blows
  up all data outside a period and requires its row to come back bitwise
  unchanged.
- **Quality:** Reference run: full suite green (96 passed). Shipped starting
  state: **19 failed / 77 passed**, every failure a `NotImplementedError` at a
  TODO; complete = **96 passed**. Expected real-data numbers are in the
  instructions doc's Section 5 (headline preview: weekly effectiveness comes
  out roughly double the daily number — the async-close prediction confirmed —
  and the sub-period pattern is a genuine surprise worth reading before
  implementing). One process note, once more and in bold in the checklist:
  **report the numbers back before pushing to main** — the order has slipped
  in all three phases so far; numbers first, push after they're confirmed.
- **Added / changed / deleted:** Added `PHASE5_INSTRUCTIONS.md` and
  `tests/test_robustness.py`. Changed `src/copper_hedge/hedge.py` (module
  docstring, the provided `SUB_PERIODS` constant, and the four documented
  stubs), PROJECT_LOG.md (Current State, Phase 5 scaffold note, two Decisions
  rows), and this log. Nothing deleted.

---

## 2026-08-23 — Phase 4 implementation verified and closed out

- **What was done:** Pulled the Phase 4 implementation from main (commits
  `9362ba7` and `b5be13c` — the second removes a stray duplicate of the run
  script) and ran the full cross-check: the commits touch only
  `src/copper_hedge/hedge.py`, `run_phase_4.py`, and the figure, with `tests/`
  and `data/` untouched; `uv run pytest` comes back **76 passed** — the exact
  complete state named in `PHASE4_INSTRUCTIONS.md`, with all three
  no-lookahead tests green — and an independent re-run of `run_phase_4.py`
  reproduced every cell of the instructions doc's expected table exactly. The
  figure passes its description's checks: a warm-up gap at the left edge,
  hedge-ratio paths orbiting 0.5, the 60-day line jumpiest and the expanding
  line nearly flat, and the two real dips (late 2020, late 2025) both visible.
  Phase 4 is ticked in PROJECT_LOG.md and `figures/rolling_hedge_ratio.png` is
  now committed.
- **Choices made & why:** None — pure verification against the contracts and
  expected numbers fixed when the assignment was packaged; no deviations
  found, no tidy-up needed.
- **Quality:** 76 passed. Headline numbers (LME leg, roll days excluded):
  out-of-sample effectiveness **+33.5% / +33.1% / +33.8%** for the 60d / 120d /
  expanding windows vs **+0.6%** for the naive 1:1 hedge on the same days, and
  in-sample +34.1% unchanged — the honest number sits under one point below
  the in-sample one, which is the good outcome. One process note, repeated
  from the completion checklist: **the numbers should come back before the
  push to main** — this phase was again pushed first. The check passed, but
  the order exists for the time it doesn't; let's hold to it for Phase 5.
- **Added / changed / deleted:** Changed PROJECT_LOG.md (Current State, Phase 4
  ticked + verification note) and this log. Arrived via the pull: implemented
  `src/copper_hedge/hedge.py`, new `run_phase_4.py`, committed
  `figures/rolling_hedge_ratio.png`. Nothing deleted.

---

## 2026-08-22 — Phase 4 packaged as a self-contained assignment

- **What was done:** Phase 4 (the out-of-sample engine — the honest version of
  Phase 3's number) is ready to hand off, same format as before:
  `PHASE4_INSTRUCTIONS.md` (committed, self-contained) + 3 stubbed functions
  with numbered TODOs (11–13) in `src/copper_hedge/hedge.py` + 18 ready-made
  tests in `tests/test_oos_hedge.py`. The tests were validated green against a
  working reference implementation before being shipped as stubs, and the
  instructions doc's Section 5 script was run against that reference, so its
  expected-numbers table and figure description reflect the real committed
  data.
- **Choices made & why:** The phase's whole point is the **no-lookahead rule**
  — a hedge ratio applied on day t may only use data from before day t — so the
  test suite attacks that rule from three separate angles instead of trusting
  one check, and also runs the engine on synthetic data whose true relationship
  shifts mid-sample to prove the windows adapt the way the bias/variance story
  says. Roll-flagged days stay excluded throughout, carrying the convention
  from Phases 2–3, and every reported number (including the naive 1:1
  comparison) is measured on the same evaluation days so the comparisons are
  fair. The phase's figure (`figures/rolling_hedge_ratio.png`) is produced by
  the instructions doc's final script and gets committed at close-out.
- **Quality:** Reference run: full suite green (76 passed). Shipped starting
  state: **18 failed / 58 passed**, every failure a `NotImplementedError` at a
  TODO; complete = **76 passed**. Expected real-data numbers and what the
  figure should look like are in the instructions doc's Section 5 (LME leg,
  roll days excluded — headline preview: the optimal hedge holds up
  out-of-sample, and the naive 1:1 hedge doesn't). One process note, now
  written into the completion checklist in bold: **report the numbers back
  before pushing to main** — in both previous phases the push came first; the
  order matters even when the check passes.
- **Added / changed / deleted:** Added `PHASE4_INSTRUCTIONS.md` and
  `tests/test_oos_hedge.py`. Changed `src/copper_hedge/hedge.py` (module
  docstring extended + 3 new stubbed functions with contract docstrings),
  PROJECT_LOG.md (Current State, Phase 4 scaffold note, Decisions rows), and
  this log. Nothing deleted.

---

## 2026-08-22 — Phase 3 implementation verified and closed out

- **What was done:** Pulled the Phase 3 implementation from main and ran the full
  cross-check: the commit touches only `src/copper_hedge/hedge.py` (tests and
  data untouched), `uv run pytest` comes back **58 passed** — the exact complete
  state named in `PHASE3_INSTRUCTIONS.md` — and the Section 5 script reproduces
  every number in the instructions doc's expected table exactly, on both spot
  legs. The effectiveness-equals-R² identity (the phase's built-in math check)
  agrees to about 12 decimal places, which is what "computed independently and
  still coincide" should look like. Phase 3 is done.
- **Choices made & why:** Two cosmetic touch-ups went into the close-out commit:
  `roll.py` picked up a whitespace-only re-indent (it's on the do-not-edit list
  for this phase, so it was restored byte-for-byte) and one comment line in
  `hedge.py` was misindented. Neither changed behavior — the suite was re-run
  after and still passes 58/58.
- **Quality:** Headline numbers (2019–2026 daily data, 1,845 days after
  excluding the 29 flagged roll days): LME leg — optimal hedge ratio 0.5025,
  in-sample R² 0.3405, effectiveness +34.1% versus the naive 1:1 hedge's +0.7%.
  CPER leg — hedge ratio 5.7437 per share (units footnote in the instructions
  doc), R² 0.7215, effectiveness +72.2%. CPER scoring roughly double the LME leg
  is the expected pattern and confirms the robustness check works. One process
  ask for next time: hand the numbers back for the cross-check *before* pushing
  to main — same note as Phase 2; the order matters even when the check passes.
- **Added / changed / deleted:** Pulled the implementation commit; close-out
  commit adds the doc updates (PROJECT_LOG checklist ticked + Current State,
  this entry) and the two cosmetic reverts. No test, data, or logic changes.

---

## 2026-08-20 — Phase 3 packaged as a self-contained assignment

- **What was done:** Phase 3 (the in-sample optimal hedge ratio) is now ready to
  hand off, same format as Phase 2: `PHASE3_INSTRUCTIONS.md` (committed,
  self-contained) + 4 stubbed functions with numbered TODOs (7–10) in
  `src/copper_hedge/hedge.py` + 18 ready-made tests in
  `tests/test_optimal_hedge.py`. The tests were validated green against a working
  reference implementation before being shipped as stubs, and the instructions
  doc's Section 5 script was run against that reference so its expected-numbers
  table reflects the real committed data.
- **Choices made & why:** The hedge ratio and R² are specified by their closed
  forms (covariance over variance; squared correlation), with a statsmodels OLS
  fit documented as an equally valid route — both were verified to give identical
  numbers. Regressions reuse the committed `data/hg_roll_flags.csv` from Phase 2
  rather than recomputing flags. The new tests live in their own file so the
  Phase 2 test files stay untouched. One process change from last time, now
  spelled out in the completion checklist: report the numbers back **before**
  pushing to main, so the cross-check happens before anything lands.
- **Quality:** Reference run: full suite green (58 passed). Shipped starting
  state: **18 failed / 40 passed**, every failure a `NotImplementedError` at a
  TODO; complete = **58 passed**. Expected real-data numbers are in the
  instructions doc's table (both spot legs, roll days excluded). A trailing-newline
  nit in `hedge.py` from Phase 2 was fixed in passing.
- **Added / changed / deleted:** Added `PHASE3_INSTRUCTIONS.md` and
  `tests/test_optimal_hedge.py`. Changed `src/copper_hedge/hedge.py` (docstring +
  4 new stubbed functions), PROJECT_LOG.md (Current State, Phase 3 scaffold note,
  Decisions rows), and this log. Nothing deleted.

---

## 2026-08-20 — Phase 2 verified and closed out

- **What was done:** Pulled the Phase 2 implementation (all 6 TODOs) and verified it:
  ran the full test suite, confirmed `tests/` and `data/` were untouched, ran the
  instructions doc's Section 5 script to produce the real-data numbers, and
  cross-checked the code against the reference implementation. Everything checks out,
  so Phase 2 is ticked in PROJECT_LOG.md and the roll-flag file is now committed.
- **Choices made & why:** The four headline numbers hadn't been reported back yet, so
  they were generated and checked on this side — same verification either way. One
  process note for next phase: hand the numbers back before pushing to main, as the
  instructions doc asks, so the cross-check happens before anything lands.
- **Quality:** 40/40 tests pass. Every number matches the reference exactly: 29 roll
  days flagged (2019-01-03 → 2026-08-12); unhedged daily variance 0.002977 ($/lb)²;
  naive 1:1 variance reduction +0.7% with roll days excluded and −34.1% on all days.
  Two cosmetic nits noted for a future touch-up (a parameter not forwarded in
  `flag_roll_days`, a missing trailing newline) — neither affects any result.
- **Added / changed / deleted:** Added `data/hg_roll_flags.csv` (1,874 flag rows).
  Changed PROJECT_LOG.md (Phase 2 ticked, Current State) and this log. No source code
  changed.

---

## 2026-08-17 — Phase 2 skeleton pushed

- **What was done:** Pushed the Phase 2 handoff to GitHub as a single commit, "Phase 2
  skeleton", so the other of us can pull and start implementing.
- **Choices made & why:** The local work-in-progress commits (scaffold, tone rewrite,
  rename, gitignore) were squashed into one commit for a clean public history, matching
  how this repo has been published so far.
- **Quality:** Pre-push state verified: suite at 23 failed / 17 passed (the intended
  starting point — every failure is a `NotImplementedError` at a TODO), working tree
  clean, reference solutions confirmed ignored.
- **Added / changed / deleted:** No file changes beyond this log entry; history
  squashed and pushed.

---

## 2026-08-17 — Reference-solution files added to .gitignore

- **What was done:** Added an `ANSWER_KEY_*` pattern to `.gitignore` so the local
  reference solutions for Phase 2 (and any later phase) can never be committed or
  pushed from any clone.
- **Choices made & why:** They were previously ignored by a per-machine git setting;
  the committed `.gitignore` makes the protection portable.
- **Quality:** `git check-ignore` confirms the files match the rule; suite unchanged at
  23 failed / 17 passed.
- **Added / changed / deleted:** Changed `.gitignore` only.

---

## 2026-08-17 — Handoff doc renamed to PHASE2_INSTRUCTIONS.md

- **What was done:** Renamed `ASSIGNMENT_PHASE2.md` → `PHASE2_INSTRUCTIONS.md`, retitled
  it "Phase 2 Instructions", and updated all references (PROJECT_LOG.md and the TODO
  comments in `src/copper_hedge/roll.py` / `hedge.py`).
- **Choices made & why:** Rename only, no content changes; earlier log entries keep the
  old name since they describe the file as it was then.
- **Quality:** Test suite unchanged: 23 failed / 17 passed, the intended starting state.
- **Added / changed / deleted:** One rename plus reference updates; nothing else.

---

## 2026-08-17 — Tone pass on the Phase 2 handoff doc

- **What was done:** Rewrote `ASSIGNMENT_PHASE2.md` to read as a professional
  implementation guide rather than a school assignment, and matched the wording of the
  TODO comments in `src/copper_hedge/roll.py` and `hedge.py`.
- **Choices made & why:** Framing only — the tasks, commands, tests, and every expected
  number are unchanged from the validated 2026-08-16 run. Filename kept because other
  docs reference it.
- **Quality:** Test suite unchanged: 23 failed / 17 passed, the intended starting state.
- **Added / changed / deleted:** Changed the three files above; nothing added or deleted.

---

## 2026-08-16 — Phase 2 packaged as a hand-off assignment

- **What was done:** Phase 2 (roll detection + hedge baselines) was set up as a
  self-contained assignment so the other of us can implement it: (1) two new modules,
  `src/copper_hedge/roll.py` and `src/copper_hedge/hedge.py`, written as stubs — full
  docstrings state each function's contract and 6 numbered TODO blocks mark exactly
  where the code goes; (2) the graders written first: 24 new tests in
  `tests/test_roll.py` and `tests/test_hedge.py`, including an explicit no-lookahead
  test (rewriting future data must not change past roll flags) and hand-computed
  variance numbers; (3) `ASSIGNMENT_PHASE2.md` — background in plain English, setup,
  task-by-task guidance, how to test, a paste-and-run script that produces the real
  numbers, and the expected zones to land in.
- **Choices made & why:** The tests ship complete and must not be edited — implement
  until green (keeps the project's tests-first rule and makes the contract unambiguous).
  Before shipping the stubs, the whole assignment was solved end-to-end with a reference
  implementation (kept off the public repo) to confirm the tests pass and the real-data
  numbers are sensible; the expected zones in the assignment come from that run.
- **Quality:** Reference run: 40/40 tests pass; 29 roll days flagged over 2019→2026
  (≈4/year, plausible against COMEX copper's ~5 rolls/year). Notable finding: the naive
  1:1 daily hedge barely helps on this data (≈ +0.7% variance reduction excluding roll
  days, negative including them) — asynchronous closes (LME fixes 1pm London, COMEX
  settles 1pm New York) cap the daily correlation near 0.54, and 2025's tariff
  dislocation made the hedge badly counterproductive that year. That is the honest
  baseline the optimal hedge of Phase 3+ has to beat. As committed, the suite
  intentionally reads 23 failed / 17 passed — every failure is a `NotImplementedError`
  at a TODO, which is the assignment's starting state.
- **Added / changed / deleted:** Added the two stub modules, the two test files, and
  `ASSIGNMENT_PHASE2.md`. Phase 1 code, tests, and data untouched. Nothing deleted.

---

## 2026-08-13 — Publishing housekeeping: clean public repo pushed to GitHub

- **What was done:** No analysis work — this session prepared and published the repo.
  (1) Verified the new machine's setup: uv 0.12.3 installed, `uv sync` reproduced the
  environment from `uv.lock`, all 16 tests pass, git history intact. (2) Consolidated our
  scattered working notes into `PROJECT_LOG.md` — a single spec-and-feature-log document
  with everything in one place (all phases, numbers, decisions); the rougher draft notes
  stay local and out of the published repo. (3) Published with a **fresh single-commit
  history** ("Initial Commit") so the public repo starts clean, without the messy
  work-in-progress commits; the full old history is kept locally on the
  `backup-pre-publish` branch. (4) First push went to a mistakenly created new repo
  (`sonha2409/copper-hedge-analysis`) because this clone had lost its remote; corrected by
  repointing `origin` to the original shared repo
  **github.com/Jesstran12/Individual-Project-1** and force-pushing the clean `main` there
  (safe: the remote's old tip was an ancestor of our local backup, so nothing was lost).
  The mistaken repo is pending deletion (needs a GitHub token scope only the owner can
  grant).
- **Choices made & why:** Ignore rules for the local draft notes live in
  `.git/info/exclude` (a local git file that never publishes) instead of the committed
  `.gitignore`, so the public `.gitignore` stays generic.
- **Quality:** 16/16 tests pass on the new machine. Published tree contains exactly 17
  files (code, tests, three data CSVs, one figure, README, PROJECT_LOG.md, pyproject/lock,
  .gitignore); a final text search over the published tree confirmed no stray references to
  the local draft notes.
- **Added / changed / deleted:** Added `PROJECT_LOG.md` and the local `backup-pre-publish`
  branch. Changed `.gitignore` (draft-notes entries moved to `.git/info/exclude`). Nothing
  deleted from disk — the local notes remain on our machines, just untracked. Analysis
  state unchanged: Phase 2 (roll detection + baselines) is still next.

---

## 2026-08-13 — Phase 1: Data layer

- **What was done:** Built the project's entire data foundation, test-first. (1) Wrote
  failing tests, then the code, for the two core operations: converting LME prices from
  dollars-per-tonne to dollars-per-pound (divide by 2,204.62), and lining three price series
  up on the days all three markets actually traded (an "inner join" — any day missing from
  one calendar is thrown out, never filled in). (2) Downloaded the LME copper cash price
  history from Westmetall exactly once, politely: 8 pages (one per year 2019–2026), two
  seconds apart, with a User-Agent that says who we are — raw pages saved outside the repo,
  cleaned result committed as `data/lme_cash_settlement.csv`. (3) Pulled COMEX copper futures
  (HG=F) and the CPER copper ETF from Yahoo Finance and committed both as CSVs. (4) Aligned
  all three and drew the sanity chart `figures/price_series.png`, all series normalized to
  1.0 at Jan 2019 so they can share one picture.
- **Choices made & why:** Used the **raw, unadjusted closing price** for both Yahoo series
  (yfinance silently adjusts by default — we turn that off and say so). Verified CPER has
  had zero splits or payouts since 2019, so its raw close is the honest price; futures have
  nothing to adjust. CPER stays in $/share per the decision already recorded in the
  decisions log. The three per-leg CSVs are the single source of truth; the aligned table is
  rebuilt from them on demand by a tested function rather than committed as a fourth CSV (no
  chance of the two ever disagreeing). The date-alignment code drops days with missing
  values instead of copying yesterday's price forward — copied prices would fake correlation.
- **Quality:** `uv run pytest` — **16 tests pass** (unit conversion, alignment on synthetic
  mismatched calendars, no-forward-fill behavior, Westmetall HTML parsing incl. holiday
  rows, CSV loading, chart normalization). Key numbers: **1,875 aligned rows** spanning
  **2019-01-02 → 2026-08-12**; calendar alignment dropped 49 LME / 42 HG / 36 CPER rows
  (holiday mismatches — normal). Our earlier "1,600–1,800 rows" estimate was written for a
  shorter "2019→now"; at 7.6 years, ~246 trading days/year × 7.6 ≈ 1,870, so 1,875 is right
  on target. Prices sane: LME $2.09–$6.56/lb, HG $2.12–$6.70/lb, CPER $13.03–$40.85/share.
  The chart shows all three moving together, the 2020 COVID dip, the May-2024 squeeze spike,
  and COMEX trading visibly above LME through 2025 (tariff dislocation) — exactly the
  stories later phases will quantify.
- **Added / changed / deleted:** Added `src/copper_hedge/data.py` (conversion, alignment,
  Westmetall parser, CSV loader, yfinance fetcher, chart normalizer), `tests/test_data.py`,
  `tests/test_westmetall.py`, `data/lme_cash_settlement.csv`, `data/hg_front_month.csv`,
  `data/cper.csv`, `figures/price_series.png`. Ticked Phase 1 in the feature log with a
  completion note and moved Current State to Phase 2; appended this entry. Deleted nothing.

---

## 2026-08-13 — Phase 0: Project setup

- **What was done:** Set up the empty-but-working project. Created `pyproject.toml` (the
  project's recipe file), let uv build a fresh Python 3.12.13 environment and install all
  nine libraries the spec calls for (pandas, numpy, statsmodels, matplotlib, yfinance,
  requests, beautifulsoup4, pytest, jupyter), created the folder skeleton (`src/copper_hedge/`
  for the math code, `tests/`, `data/`, `notebooks/`, `figures/`), wrote a one-paragraph
  README describing the project's goal, and added a small "smoke test" that simply checks the
  environment works. Ran the tests and the environment verification command — both passed.
- **Choices made & why:** Package is laid out in "src layout" (code lives under
  `src/copper_hedge/`) exactly as the spec's repo-structure diagram shows. Dependencies were
  added with `uv add` so exact versions are pinned in `uv.lock` — either of us can recreate
  the identical environment. Empty folders (`data/`, `notebooks/`, `figures/`) got a tiny
  placeholder file (`.gitkeep`) because git cannot track empty folders. The smoke test only
  checks that the package and core libraries import — there is no real math to test yet;
  real tests arrive with Phase 1 (TDD). The existing `.gitignore` from the restart already
  covered everything needed, so it was left untouched.
- **Quality:** `uv run pytest` — 2 tests passed. `uv run python -c "import pandas,
  statsmodels; print('environment OK')"` prints `environment OK`. No figures yet (none due
  this phase).
- **Added / changed / deleted:** Added `pyproject.toml`, `uv.lock`, `README.md`,
  `src/copper_hedge/__init__.py`, `tests/test_smoke.py`, and `.gitkeep` placeholders in
  `data/`, `notebooks/`, `figures/`. Ticked Phase 0 in the feature log with a completion
  note and pointed Current State at Phase 1; appended this entry. Deleted nothing.

---

## 2026-08-13 — Project restart

- **What was done:** Wiped the project back to a clean slate — a decision we made together
  after reviewing where the first attempt stood. All code, tests, data CSVs, figures, the
  notebook, the Python environment, the old log, and the entire git history (Phase 0 and
  Phase 1 commits) were deleted. Kept: the spec and `.gitignore`.
  A brand-new git history was started with a single restart commit.
- **Choices made & why (all agreed between us):** fresh git history rather than a
  "removal" commit on top of the old one (old work intentionally unrecoverable); drop the
  data CSVs rather than carry them over (Phase 1 will re-pull yfinance and re-scrape
  Westmetall once, politely, when it comes around); reset the spec's progress markers — Phase 0 and
  Phase 1 checkboxes unticked, completion notes removed, Current State set back to "not
  started". The spec content itself (finance, methodology, decisions log) is unchanged.
- **Quality:** nothing to test — no code exists yet. Working tree is clean.
- **Added / changed / deleted:** deleted `src/`, `tests/`, `data/`, `figures/`,
  `notebooks/`, `pyproject.toml`, `uv.lock`, `.python-version`, `.venv/`, `README.md`,
  the old log, the old `.git/`. Changed the spec (progress reset only). Started this
  fresh log.
