# WATCH

> Workflow Automation & Technical Control Hub

WATCH is a local-first IT automation and operational-control workbench. It executes repeatable read-only workflows, records immutable evidence, detects changes, creates traceable actions, and generates review-ready reports.

## Portfolio purpose

WATCH is the flagship project for the **IT Automation Engineer** path in Rafael Alba's technical portfolio.

It is deliberately separated from:

- **OPSCORE**, which investigates infrastructure and production-service evidence.
- **INFIOS**, which structures application-support incidents.
- **TRACE**, which structures IAM and access evidence.

WATCH controls **which workflow runs, against which target, with what result, what changed, and what action is required**.

## Current verified capability

WATCH currently supports an end-to-end public website operational-health workflow:

```text
explicit public target
  -> DNS resolution and public-address validation
  -> bounded HTTP request and redirect inspection
  -> response timing and page-title extraction
  -> TLS certificate expiry inspection
  -> deterministic findings
  -> previous-run comparison
  -> action creation or reuse
  -> immutable run history
  -> Markdown and JSON reports
```

Collected evidence includes:

- HTTP status and final URL;
- redirect chain and redirect count;
- response duration;
- resolved IP addresses;
- page title for HTML responses;
- TLS certificate days remaining;
- structured DNS, HTTP, timeout, and TLS errors.

The TLS connection uses an already validated address while preserving the original hostname for SNI and certificate hostname verification.

## Quick start on Windows

```powershell
.\WATCH.ps1 setup
.\WATCH.ps1 verify
.\WATCH.ps1 demo
.\WATCH.ps1 export
```

The export command verifies the repository, runs the demo, and creates a review ZIP directly in `Downloads`.

## Run a live read-only check

```powershell
.\.venv\Scripts\python.exe -m watch.cli collect https://example.com
```

Optional parameters:

```powershell
.\.venv\Scripts\python.exe -m watch.cli collect https://example.com `
  --timeout-seconds 10 `
  --workspace .watch-data
```

Generated evidence is stored below `.watch-data`:

```text
.watch-data/
├── runs/
├── actions/
└── reports/
```

## Automated proof

Every pull request runs:

- Ruff linting;
- strict mypy checks;
- pytest with coverage;
- deterministic demo generation;
- Windows operator verification;
- Windows review ZIP export;
- Linux and Windows proof-artifact upload.

## Safety boundaries

WATCH is read-only first.

Current controls include:

- one explicit target per live command;
- HTTP and HTTPS only through the validated target model;
- public-address validation before each redirect hop;
- blocking of private, loopback, link-local, reserved, and other non-public addresses;
- a five-redirect limit;
- explicit 1–60 second timeouts;
- normal TLS certificate and hostname verification;
- no authentication, form submission, crawling, credential storage, or external modification.

Known limitation: the HTTP library performs its own DNS resolution after validation, so transport-level HTTP address pinning remains tracked in Issue #11. TLS inspection is already pinned to a validated address.

See [docs/safety-boundaries.md](docs/safety-boundaries.md) and [docs/roadmap.md](docs/roadmap.md).

## Repository layout

```text
src/watch/           domain, workflow, collectors, storage, reports, and CLI
tests/               automated proof
samples/             public-safe sample inputs
scripts/             setup, verification, demo, and review export
docs/                architecture, roadmap, safety, and milestone evidence
.github/workflows/   Linux and Windows GitHub verification
.watch-data/         generated local state, ignored by Git
```

## Next milestone

The next practical milestone is an operator API for target inventory, workflow execution, run history, reports, and action acknowledgement. Transport-level HTTP address pinning remains a security-hardening prerequisite before broader scheduling or multi-target execution.
