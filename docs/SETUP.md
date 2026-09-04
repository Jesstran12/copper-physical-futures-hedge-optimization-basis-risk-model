# Environment Setup Guide

How to get this project running on a fresh machine. Takes about five minutes; the only
things installed globally are `git` and `uv`.

## 1. Prerequisites

- **git** — comes with Xcode Command Line Tools on macOS (`xcode-select --install`);
  on Windows use [Git for Windows](https://git-scm.com/download/win).
- **uv** — the Python package/environment manager this project uses. Install it:

  ```bash
  # macOS (Homebrew)
  brew install uv

  # macOS / Linux (no Homebrew)
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

You do **not** need to install Python yourself — uv downloads the right version
(≥ 3.12, pinned by `pyproject.toml`) automatically.

## 2. Clone and sync

```bash
git clone git@github.com:Jesstran12/Individual-Project-1.git
cd Individual-Project-1
uv sync
```

`uv sync` reads `uv.lock` and reproduces the exact environment (same package versions on
every machine). It creates a local `.venv/` folder — never activate it or pip-install into
it by hand; always go through `uv run`.

## 3. Verify the setup

```bash
uv run pytest
```

All 115 tests should pass. If they do, the environment is correct — this is
the only check you need.

## 4. Day-to-day commands

Everything runs through `uv run`, which guarantees the locked environment is used:

| Task | Command |
|---|---|
| Run the test suite | `uv run pytest` |
| Regenerate the rolling hedge-ratio figure | `uv run python scripts/rolling_hedge_figure.py` (from the repo root) |
| Run any script | `uv run python <script.py>` |
| Add a new dependency | `uv add <package>` (updates `pyproject.toml` + `uv.lock` — commit both) |

## 5. Data — do not refetch

The CSVs under `data/` are the committed source of truth (LME cash from Westmetall, HG=F
and CPER from Yahoo Finance). All analysis runs off these files; **nothing needs network
access after cloning**. Refresh them only deliberately, by agreement — the Westmetall
scrape in particular is designed to run once, politely, not on every machine.

## 6. Troubleshooting

- **`uv: command not found` after installing** — restart the terminal (the installer adds
  uv to your PATH, which only takes effect in new shells).
- **`git clone` asks for credentials / fails with "Permission denied (publickey)"** — you're
  cloning over SSH without a key set up. Either
  [add an SSH key to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh),
  or clone over HTTPS instead:
  `git clone https://github.com/Jesstran12/Individual-Project-1.git`.
- **Tests fail on a fresh clone** — run `uv sync` again and make sure you're inside the
  project folder; if it persists, check that `uv.lock` matches the repo (no local edits).
- **Wrong Python picked up** — always use `uv run …`; calling plain `python`/`pytest` can
  hit a system Python instead of the project environment.

## 7. Repo conventions (quick reference)

- One phase of work per session — see `docs/PROJECT_LOG.md` for the current state, the
  phase history, and the full decisions log.
- All math lives in `src/copper_hedge/` with pytest unit tests.
- Keep `uv.lock` committed so every machine reproduces the same environment.
