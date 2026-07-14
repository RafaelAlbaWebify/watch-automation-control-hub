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
  -> explicit single-target execution
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
├── runs/
├── actions/
└── reports/
```

## Run the local operator API

```powershell
.\WATCH.ps1 api
```

The default local endpoints are:

- API health: `http://127.0.0.1:8000/api/health`
- interactive OpenAPI documentation: `http://127.0.0.1:8000/docs`
- target inventory: `http://127.0.0.1:8000/api/targets`
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
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/actions
POST /api/actions/{action_id}/acknowledge
POST /api/actions/{action_id}/resolve
GET  /api/reports/{run_id}.md
```

The execution endpoint is explicit and operates on one enabled registered target per request. It persists the resulting run, findings, actions, history, and reports in the configured workspace. It does not introduce scheduling, batch execution, retries, background tasks, or external remediation.

The API reads and writes only one startup-configured local workspace. Request parameters cannot select arbitrary filesystem paths. Target and action writes affect local WATCH state only.

## Automated proof

Every pull request runs:

- Ruff linting;
- strict mypy checks;
- pytest with coverage;
- deterministic demo generation;
- FastAPI contract and OpenAPI tests;
- Windows operator verification;
- Windows review ZIP export;
- Linux and Windows proof-artifact upload.

Superseded branch runs are cancelled automatically so only the latest commit consumes CI capacity.

## Safety boundaries

WATCH is read-only first.

Current controls include:

- explicit local target registration;
- explicit one-target execution;
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
- no authentication bypass, form submission, crawling, credential storage, scheduling, batch execution, or external modification.

See [docs/safety-boundaries.md](docs/safety-boundaries.md) and [docs/roadmap.md](docs/roadmap.md).

## Repository layout

```text
src/watch/           domain, targets, actions, workflow, collectors, storage, reports, CLI, and API
tests/               automated proof
samples/             public-safe sample inputs
scripts/             setup, verification, demo, API, and review export
docs/                architecture, roadmap, safety, and milestone evidence
.github/workflows/   Linux and Windows GitHub verification
.watch-data/         generated local state, ignored by Git
```

## Next milestone

M2 and HTTP transport hardening are complete as bounded foundations. The next milestone is M3 design for schedules, idempotent execution, retry policy, missed-run visibility, and Windows Task Scheduler integration.
