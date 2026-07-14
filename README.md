# WATCH

> Workflow Automation & Technical Control Hub

WATCH is a local-first IT automation and operational-control workbench. It manages approved public targets, executes repeatable read-only checks, records immutable evidence, detects changes, creates traceable actions, and generates review-ready reports.

## Portfolio purpose

WATCH is the flagship project for the **IT Automation Engineer** path in Rafael Alba's technical portfolio. It is deliberately separated from OPSCORE infrastructure investigation, INFIOS application-support incident work, and TRACE IAM evidence.

WATCH controls **which workflow runs, against which target, with what result, what changed, and what action is required**.

## Current verified capability

```text
local target inventory
  -> persisted interval schedules
  -> deterministic due-occurrence calculation
  -> atomic idempotent claims
  -> explicit at-most-once occurrence execution
  -> missed-boundary and stale-execution visibility
  -> DNS and public-address validation
  -> address-pinned HTTP and redirect inspection
  -> response timing, page title, and TLS expiry evidence
  -> deterministic findings and previous-run comparison
  -> action creation, acknowledgement, and resolution
  -> immutable run history and reports
  -> local operator API
  -> read-only operator workbench
  -> target-focused evidence drill-down
  -> Playwright browser and screenshot proof
```

Collected evidence includes HTTP status, final URL, redirects, response duration, resolved IP addresses, page title, TLS days remaining, and structured DNS, HTTP, timeout, and TLS errors.

For every HTTP redirect hop, WATCH validates the hostname, connects directly to a selected public IP, and preserves the original hostname for the Host header and TLS SNI/certificate verification.

## Quick start on Windows

```powershell
.\WATCH.ps1 setup
.\WATCH.ps1 verify
.\WATCH.ps1 demo
.\WATCH.ps1 export
```

The export command verifies the repository, runs the deterministic demo, and creates a review ZIP in `Downloads`.

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

Generated evidence is stored under `.watch-data`:

```text
.watch-data/
├── targets/
├── schedules/
├── occurrences/
├── occurrence-locks/
├── runs/
├── actions/
└── reports/
```

## Run the local operator workbench

```powershell
.\WATCH.ps1 api
```

The command starts the combined read-only workbench and existing JSON API on loopback.

Operator pages:

- dashboard: `http://127.0.0.1:8000/`
- target inventory: `http://127.0.0.1:8000/targets`
- target detail: `http://127.0.0.1:8000/targets/{target_id}`
- schedule inventory: `http://127.0.0.1:8000/schedules`
- occurrence history: `http://127.0.0.1:8000/occurrences`
- missed/stale attention: `http://127.0.0.1:8000/attention`
- run history: `http://127.0.0.1:8000/runs`
- change timeline: `http://127.0.0.1:8000/changes`
- action history: `http://127.0.0.1:8000/actions`
- human-readable report: `http://127.0.0.1:8000/reports/{run_id}`

Every operator page uses the same navigation. Target links from the dashboard, schedules, occurrences, attention, runs, changes, and actions open a consolidated target page showing configuration, schedules, run/change history, findings, resulting actions, and report links.

Default API endpoints:

- health: `http://127.0.0.1:8000/api/health`
- OpenAPI: `http://127.0.0.1:8000/docs`
- targets: `http://127.0.0.1:8000/api/targets`
- schedules: `http://127.0.0.1:8000/api/schedules`
- occurrences: `http://127.0.0.1:8000/api/occurrences`
- runs: `http://127.0.0.1:8000/api/runs`
- actions: `http://127.0.0.1:8000/api/actions`

The API and workbench use one startup-configured local workspace. Request parameters cannot select arbitrary filesystem paths. HTML pages are read-only and excluded from the OpenAPI contract.

## Scheduling and occurrence safety

Schedule definitions link one immutable schedule ID to one target, normalize starts to UTC, and bound intervals from 5 minutes to 7 days.

Occurrence evaluation derives deterministic UTC boundaries and execution keys. Exclusive local files provide restart-safe claims and permanent at-most-once execution markers. Disabled schedules and targets are rejected before collection.

Attention inspection is read-only. It reports `missed-unclaimed` boundaries and `executing-stale` occurrences using bounded grace and lookback values. It creates no claims, invokes no collector, changes no state, and performs no recovery.

## Automated proof

Every pull request runs:

- Ruff linting;
- strict mypy checks;
- pytest with coverage;
- deterministic demo generation;
- FastAPI and OpenAPI contract tests;
- read-only route, navigation, not-found, and target-detail tests;
- Playwright Chromium semantic navigation;
- browser console-error validation;
- screenshots for dashboard, target detail, schedules, occurrences, attention, runs, changes, actions, and reports;
- Playwright trace retention on browser failure;
- Windows operator verification and review ZIP export;
- Linux, Windows, and visual proof-artifact upload.

## Safety boundaries

WATCH is read-only first. Current controls include explicit target registration, bounded timeouts and redirects, public-address validation, direct connections to validated IP addresses, normal TLS verification, disabled-target guards, startup-configured workspace isolation, local-only action transitions, and read-only operator pages.

WATCH does not bypass authentication, submit external forms, crawl sites, store credentials, automatically retry or recover interrupted execution, install Task Scheduler jobs, execute batches, or modify external systems.

See [docs/safety-boundaries.md](docs/safety-boundaries.md) and [docs/roadmap.md](docs/roadmap.md).

## Repository layout

```text
src/watch/           domain, services, collectors, storage, reports, CLI, API, and workbench
tests/               unit, API, route, navigation, and target-detail proof
samples/             public-safe sample inputs
scripts/             setup, verification, demo, browser proof, launch, and review export
docs/                architecture, roadmap, safety, and milestone evidence
.github/workflows/   Linux, Windows, and browser verification
.watch-data/         generated local state, ignored by Git
```

## Next milestone

The next bounded interface slice is M4.6: usability and accessibility improvements such as active navigation state, responsive tables, stronger status hierarchy, keyboard proof, and accessible table/landmark review. Retry policy and Windows Task Scheduler integration remain separate later decisions.
