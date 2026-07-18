# WATCH

> Workflow Automation & Technical Control Hub

WATCH is a local-first IT automation and operational-control workbench. It manages approved public targets, executes repeatable read-only checks, records immutable evidence, detects changes, creates traceable actions, and generates review-ready reports.

## Stable release

WATCH **v0.1.0** is published as the first stable release. The release includes the non-empty `WATCH-v0.1.0-windows.zip` package and is verified by a repository-native release check.

## Portfolio purpose

WATCH is the flagship project for the **IT Automation Engineer** path in Rafael Alba's technical portfolio. It is deliberately separated from OPSCORE infrastructure investigation, INFIOS application-support incident work, and TRACE IAM evidence.

WATCH controls **which workflow runs, against which target, with what result, what changed, and what action is required**.

## Current verified capability

```text
local target inventory
  -> persisted interval schedules
  -> deterministic due-occurrence calculation
  -> read-only latest-due work planning
  -> bounded one-shot latest-due execution
  -> rollback-safe Windows Task Scheduler adapter
  -> atomic idempotent claims
  -> explicit at-most-once occurrence execution
  -> missed-boundary and stale-execution visibility
  -> bounded operator-controlled retry attempts
  -> read-only retry-attempt evidence visibility
  -> DNS and public-address validation
  -> address-pinned HTTP and redirect inspection
  -> response timing, page title, and TLS expiry evidence
  -> deterministic findings and previous-run comparison
  -> action creation, acknowledgement, and resolution
  -> immutable run history and reports
  -> local operator API and read-only workbench
  -> Playwright browser and screenshot proof
```

Collected evidence includes HTTP status, final URL, redirects, response duration, resolved IP addresses, page title, TLS days remaining, selected public response metadata, and structured DNS, HTTP, timeout, and TLS errors.

For every HTTP redirect hop, WATCH validates the hostname, connects directly to a selected public IP, and preserves the original hostname for the Host header and TLS SNI/certificate verification.

## Quick start on Windows

```powershell
.\WATCH.ps1 setup
.\WATCH.ps1 verify
.\WATCH.ps1 demo
.\WATCH.ps1 export
```

The export command verifies the repository, runs the deterministic demo, generates a scheduler plan, and creates a review ZIP in `Downloads`.

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

## Plan latest due work without changing state

```powershell
.\WATCH.ps1 plan `
  -EvaluatedAt "2026-07-14T20:00:00+02:00" `
  -Workspace ".watch-data"
```

The command emits machine-readable JSON. It considers at most one latest due boundary per schedule and classifies it without creating a claim or invoking the collector.

## Run one bounded foreground due cycle

```powershell
.\WATCH.ps1 run-once `
  -EvaluatedAt "2026-07-14T20:00:00+02:00" `
  -MaxWork 2 `
  -Workspace ".watch-data"
```

The command processes only `ready-to-claim` latest boundaries in deterministic schedule order. `MaxWork` remains between 1 and 10. It runs once, writes a JSON result summary, and exits.

## Windows Task Scheduler lifecycle

WATCH installs at most one current-user scheduled task. Each trigger invokes one bounded foreground run and exits.

### Inspect the definition

```powershell
.\WATCH.ps1 task-plan `
  -TaskName "WATCH-DueRunner" `
  -IntervalMinutes 15 `
  -MaxWork 1 `
  -Workspace ".watch-data" `
  -EvidenceDirectory "artifacts\runner" `
  -OutputPath "artifacts\scheduler-proof\task-plan.json"
```

`task-plan` is read-only and shows the exact executable, quoted arguments, paths, principal, interval, non-overlap policy, and credential policy.

### Install

```powershell
.\WATCH.ps1 task-install `
  -TaskName "WATCH-DueRunner" `
  -IntervalMinutes 15 `
  -MaxWork 1 `
  -Workspace ".watch-data" `
  -EvidenceDirectory "artifacts\runner"
```

The task runs as the current interactive user with limited privilege, stores no password, and uses `IgnoreNew` to prevent overlap. If a same-named task exists, WATCH exports its XML before replacement.

### Verify

```powershell
.\WATCH.ps1 task-verify `
  -TaskName "WATCH-DueRunner" `
  -IntervalMinutes 15 `
  -MaxWork 1 `
  -Workspace ".watch-data" `
  -EvidenceDirectory "artifacts\runner"
```

### Uninstall or roll back

```powershell
.\WATCH.ps1 task-uninstall -TaskName "WATCH-DueRunner"
```

```powershell
.\WATCH.ps1 task-rollback -TaskName "WATCH-DueRunner"
```

Uninstall preserves WATCH operational data and scheduler backup evidence. Rollback restores a previous same-named task only when installation created a valid XML backup.

Scheduled invocations generate the evaluation timestamp at runtime in UTC and save result files under `artifacts\runner`. See [docs/windows-task-scheduler.md](docs/windows-task-scheduler.md) for the full operating procedure.

## Local state

```text
.watch-data/
├── targets/
├── schedules/
├── scheduler/
│   ├── task-state.json
│   └── backups/
├── occurrences/
├── occurrence-locks/
├── attempts/
├── attempt-locks/
├── runs/
├── actions/
└── reports/
```

## Run the local operator workbench

```powershell
.\WATCH.ps1 api
```

The command starts the combined read-only workbench and JSON API on loopback.

Operator pages:

- dashboard: `http://127.0.0.1:8000/`
- target inventory: `http://127.0.0.1:8000/targets`
- target detail: `http://127.0.0.1:8000/targets/{target_id}`
- schedule inventory: `http://127.0.0.1:8000/schedules`
- occurrence history: `http://127.0.0.1:8000/occurrences`
- missed/stale attention: `http://127.0.0.1:8000/attention`
- retry-attempt history: `http://127.0.0.1:8000/attempts`
- run history: `http://127.0.0.1:8000/runs`
- change timeline: `http://127.0.0.1:8000/changes`
- action history: `http://127.0.0.1:8000/actions`
- report: `http://127.0.0.1:8000/reports/{run_id}`

Default API endpoints include health, targets, schedules, occurrences, attempts, due-work planning, runs, actions, and reports. The API and workbench use one startup-configured local workspace. Request parameters cannot select arbitrary filesystem paths. HTML pages are read-only and excluded from OpenAPI.

## Scheduling and execution safety

- Schedule starts are normalized to UTC and intervals are bounded from 5 minutes to 7 days.
- Planning is read-only and invokes no collector.
- The one-shot runner processes only `ready-to-claim` items and enforces `MaxWork` from 1 to 10.
- Atomic claims and permanent execution markers prevent duplicate collection.
- Retries require a reason, are limited to three attempts, and never rewrite the original occurrence.
- The scheduled task uses the current interactive user, limited privilege, no stored credential, a 5–1,440 minute interval, and `IgnoreNew` overlap prevention.
- One trigger invokes one foreground process and exits.
- CI validates the scheduler manifest and the V1 release gate validates a temporary real task lifecycle without leaving a persistent task behind.

## Automated proof

Every pull request runs:

- Ruff linting;
- strict mypy checks;
- pytest with coverage;
- deterministic demo generation;
- FastAPI and OpenAPI contract tests;
- planner, runner, retry, route, and workbench tests;
- Windows wrapper and scheduler-manifest proof;
- Windows review ZIP export including `artifacts/scheduler-proof/task-plan.json`;
- Playwright Chromium semantic navigation and screenshots;
- Linux, Windows, clean-checkout, and visual proof-artifact upload.

The V1 release gates additionally verify an approved bounded live check, a temporary real Windows Task Scheduler lifecycle, desktop/mobile Playwright human-style review, portfolio screenshot selection, release publication, and the stable Windows asset.

## Safety boundaries

WATCH is read-only first. It does not bypass authentication, submit external forms, crawl sites, store credentials, automatically retry or recover interrupted execution, retry stale executing work, create one scheduled task per target, run as SYSTEM, install a password-backed task, or modify external systems.

See [docs/safety-boundaries.md](docs/safety-boundaries.md), [docs/windows-task-scheduler.md](docs/windows-task-scheduler.md), and [docs/roadmap.md](docs/roadmap.md).

## Repository layout

```text
src/watch/           domain, services, collectors, storage, reports, CLI, API, and workbench
tests/               unit, API, route, navigation, planner, runner, and operator proof
samples/             public-safe sample inputs
scripts/             setup, verification, scheduler, runner, browser proof, launch, and review export
docs/                architecture, roadmap, safety, scheduler, examples, and release evidence
.github/workflows/   Linux, Windows, browser, V1 validation, and release verification
.watch-data/         generated local state, ignored by Git
```

## Roadmap status

The original M0–M4 roadmap and the WATCH v0.1.0 release-readiness checklist are complete. Future work is intentionally deferred to post-v0.1 milestones such as approved notifications, integrations, external writes, and multi-user operation.
