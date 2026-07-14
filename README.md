# WATCH

> Workflow Automation & Technical Control Hub

WATCH is a local-first IT automation and operational-control workbench. It manages approved public targets, executes repeatable read-only checks, records immutable evidence, detects changes, creates traceable actions, and generates review-ready reports.

## Portfolio purpose

WATCH is the flagship project for the **IT Automation Engineer** path in Rafael Alba's technical portfolio.

It is deliberately separated from:

- **OPSCORE**, which investigates infrastructure and production-service evidence.
- **INFIOS**, which structures application-support incidents.
- **TRACE**, which structures IAM and access evidence.

WATCH controls **which workflow runs, against which target, with what result, what changed, and what action is required**.

## Current verified capability

WATCH currently supports:

```text
local target inventory
  -> persisted interval schedule definitions
  -> deterministic due-occurrence calculation
  -> atomic idempotent occurrence claims
  -> explicit at-most-once occurrence execution
  -> bounded read-only missed/interrupted attention visibility
  -> DNS resolution and public-address validation
  -> address-pinned HTTP request and redirect inspection
  -> response timing and page-title extraction
  -> TLS certificate expiry inspection
  -> deterministic findings
  -> previous-run comparison
  -> action creation or reuse
  -> action acknowledgement and resolution
  -> immutable run history
  -> Markdown and JSON reports
  -> local operator API
  -> read-only operator dashboard
```

Collected evidence includes:

- HTTP status and final URL;
- redirect chain and redirect count;
- response duration;
- resolved IP addresses;
- page title for HTML responses;
- TLS certificate days remaining;
- structured DNS, HTTP, timeout, and TLS errors.

For each HTTP redirect hop, WATCH resolves and validates the hostname, connects directly to a validated public IP, and preserves the original hostname in the HTTP Host header and TLS SNI/certificate verification. TLS expiry inspection uses the same validated-address boundary.

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

The command starts the combined read-only dashboard and existing JSON API on loopback.

Default operator pages:

- dashboard: `http://127.0.0.1:8000/`
- target inventory: `http://127.0.0.1:8000/targets`
- run history: `http://127.0.0.1:8000/runs`
- action history: `http://127.0.0.1:8000/actions`
- human-readable report: `http://127.0.0.1:8000/reports/{run_id}`

Default API endpoints:

- API health: `http://127.0.0.1:8000/api/health`
- interactive OpenAPI documentation: `http://127.0.0.1:8000/docs`
- target inventory: `http://127.0.0.1:8000/api/targets`
- schedule configuration: `http://127.0.0.1:8000/api/schedules`
- occurrence history: `http://127.0.0.1:8000/api/occurrences`
- run history: `http://127.0.0.1:8000/api/runs`
- action history: `http://127.0.0.1:8000/api/actions`

Implemented API operations:

```text
GET  /api/health
GET  /api/targets
GET  /api/targets/{target_id}
POST /api/targets
PUT  /api/targets/{target_id}
POST /api/targets/{target_id}/runs
GET  /api/schedules
GET  /api/schedules/{schedule_id}
POST /api/schedules
PUT  /api/schedules/{schedule_id}
POST /api/schedules/{schedule_id}/occurrences/evaluate
GET  /api/occurrences
POST /api/occurrences/attention
GET  /api/occurrences/{execution_key}
POST /api/occurrences/{execution_key}/execute
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/actions
POST /api/actions/{action_id}/acknowledge
POST /api/actions/{action_id}/resolve
GET  /api/reports/{run_id}.md
```

Schedule definitions link one immutable schedule ID to one existing target, store an enabled state, a timezone-aware start time normalized to UTC, and an interval from 5 minutes to 7 days.

Occurrence evaluation requires an explicit timezone-aware timestamp. WATCH calculates the latest due boundary, derives a deterministic execution key, and uses exclusive local file creation to claim that occurrence once. Repeated evaluation returns the existing claim. Disabled schedules or targets and evaluations before the start time produce explicit no-claim results.

Executing an occurrence is also explicit. WATCH revalidates the schedule and target, creates a permanent exclusive execution marker, transitions the occurrence to `executing`, then invokes the existing collector and workflow once. Completed and partial workflow runs are linked through `run_id`. Collector exceptions are retained as terminal `failed` occurrence evidence.

The permanent execution marker provides an at-most-once collection boundary across process restarts. A repeated request returns the existing executing or terminal occurrence and does not invoke the collector again. This deliberately favors duplicate prevention over automatic recovery after an interrupted execution.

Occurrence attention inspection provides read-only operational visibility. The caller supplies an explicit evaluation time, a grace period from 1 to 1,440 minutes, and a lookback from 1 to 100 interval boundaries. WATCH reports:

- `missed-unclaimed` when an enabled schedule boundary is older than the grace period but has no occurrence record;
- `executing-stale` when an occurrence remains in `executing` beyond the grace period.

Attention inspection derives the same deterministic keys used for claims but creates no records, changes no state, invokes no collector, and performs no recovery. The bounded lookback prevents an old schedule from generating an unbounded response.

The direct target execution endpoint continues to operate on one enabled registered target per request and persists the resulting run, findings, actions, history, and reports.

The API and dashboard read and write only one startup-configured local workspace. Request parameters cannot select arbitrary filesystem paths. Target, schedule, occurrence, execution-marker, and action writes affect local WATCH state only. Dashboard pages are read-only against that workspace.

## Automated proof

Every pull request runs:

- Ruff linting;
- strict mypy checks;
- pytest with coverage;
- deterministic demo generation;
- FastAPI contract and OpenAPI tests;
- read-only dashboard route and empty-state tests;
- Windows operator verification;
- Windows review ZIP export;
- Linux and Windows proof-artifact upload.

Superseded branch runs are cancelled automatically so only the latest commit consumes CI capacity.

## Safety boundaries

WATCH is read-only first.

Current controls include:

- explicit local target registration;
- schedule configuration without automatic execution;
- immutable schedule IDs and target linkage;
- UTC-normalized schedule start times and bounded intervals;
- deterministic UTC occurrence boundaries and keys;
- exclusive, restart-safe local occurrence claims;
- disabled schedule and target claim guards;
- claim evaluation with no collector or workflow-run side effects;
- explicit single-occurrence execution only;
- permanent execution markers preventing duplicate collection across restarts;
- controlled occurrence states: claimed, executing, completed, partial, failed, and reserved missed;
- collector failures retained as bounded local evidence;
- read-only missed-boundary and stale-execution visibility;
- bounded 1–100 occurrence attention lookback and 1–1,440 minute grace period;
- no state change, claim, collection, or retry from attention inspection;
- HTTP and HTTPS only through the validated target model;
- disabled targets rejected before collection;
- public-address validation before each redirect hop;
- direct HTTP connection to the selected validated IPv4 or IPv6 address;
- original Host header and TLS SNI/certificate hostname verification preserved;
- blocking of private, loopback, link-local, reserved, and mixed public/private DNS answers;
- environment-derived proxy routing disabled for the internal live collector;
- a five-redirect limit;
- explicit 1–60 second timeouts;
- normal TLS certificate and hostname verification;
- API workspace configured at startup rather than supplied by requests;
- controlled local-only action state transitions;
- read-only dashboard pages with no execution or state-transition controls;
- no authentication bypass, form submission, crawling, credential storage, retries, automatic recovery, Task Scheduler installation, batch execution, or external modification.

See [docs/safety-boundaries.md](docs/safety-boundaries.md) and [docs/roadmap.md](docs/roadmap.md).

## Repository layout

```text
src/watch/           domain, services, collectors, storage, reports, CLI, API, and web workbench
 tests/              automated unit, API, and dashboard route proof
samples/             public-safe sample inputs
scripts/             setup, verification, demo, workbench launch, and review export
docs/                architecture, roadmap, safety, and milestone evidence
.github/workflows/   Linux and Windows GitHub verification
.watch-data/         generated local state, ignored by Git
```

## Next milestone

The next bounded slice is M4.2: add a deterministic sample workspace, Playwright semantic browser tests, CI-generated dashboard screenshots, and failure traces before expanding the interface or returning to Task Scheduler and retry work.
