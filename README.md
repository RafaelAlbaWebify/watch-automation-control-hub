# WATCH

> Workflow Automation & Technical Control Hub

WATCH is a local-first IT automation and operational-control workbench. It manages operational targets, executes repeatable read-only workflows, records immutable run evidence, detects changes, creates traceable actions, and generates review-ready reports.

## Portfolio purpose

WATCH is the flagship project for the **IT Automation Engineer** path in Rafael Alba's technical portfolio.

The project is deliberately separated from:

- **OPSCORE**, which investigates infrastructure and production-service evidence.
- **INFIOS**, which structures application-support incidents.
- **TRACE**, which structures IAM and access evidence.

WATCH controls **which workflow runs, against which target, with what result, what changed, and what action is required**.

## Current status

**M0 repository foundation and executable contract.**

The repository currently includes:

- explicit domain contracts;
- target validation;
- deterministic finding generation;
- duplicate-action prevention;
- Markdown and JSON report generation;
- local JSON run/action storage;
- CLI demo workflow;
- automated tests;
- GitHub Actions verification and proof artifacts.

Live external website collection is intentionally deferred to M1. The current executable slice uses supplied observations so that the workflow lifecycle can be proved without unreliable network-dependent tests.

## First executable vertical slice

```text
target definition
  -> validated observations
  -> deterministic findings
  -> compare with previous run
  -> create or reuse operational actions
  -> save immutable run history
  -> generate Markdown and JSON reports
```

## Local verification

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m watch.cli demo --workspace .watch-data
```

## Repository layout

```text
src/watch/           application and domain code
tests/               automated proof
samples/             public-safe sample inputs
.github/workflows/   GitHub verification
.watch-data/         generated local state, ignored by Git
```

## Safety

WATCH is read-only first. It does not modify websites, DNS, domains, client systems, or external accounts. It does not send email or contact leads. It does not store credentials.

## M1 direction

The next milestone will add a public website collector for:

- HTTP status;
- redirect chain;
- response duration;
- TLS certificate expiry;
- basic page metadata;
- basic DNS resolution.

Those observations will feed the already-defined workflow, finding, action, history, and report contracts.
