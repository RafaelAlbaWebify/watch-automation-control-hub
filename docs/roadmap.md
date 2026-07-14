# WATCH roadmap

## M0 — Repository foundation

- [x] Product and safety boundary
- [x] Domain contracts
- [x] Deterministic findings
- [x] Run history
- [x] Action lifecycle foundation
- [x] Duplicate-action prevention
- [x] Markdown and JSON reports
- [x] CLI demo
- [x] Tests and GitHub CI
- [x] Automated Windows setup, verification, demo, and review export

## M1 — Website operational health collector

- [x] HTTP status and final URL
- [x] Redirect chain
- [x] Response duration
- [x] TLS certificate expiry
- [x] Page title extraction
- [x] Basic DNS resolution
- [x] Public-address validation for each redirect hop
- [x] HTTP transport pinned to a selected validated IPv4 or IPv6 address
- [x] Original Host and TLS SNI/certificate verification preserved
- [x] Mixed public/private DNS responses blocked
- [x] Mocked collector and safety tests
- [x] Safe single-target live CLI with bounded timeouts and redirects
- [x] Linux and Windows proof artifacts

### M1 evidence improvements still open

- [ ] Capture selected response headers and content metadata
- [ ] Add a sanitized committed example of a live-generated report

## M2 — Operator API

- [x] FastAPI health endpoint
- [x] Persistent target inventory list, detail, create, and update endpoints
- [x] Explicit single-target execution endpoint for a registered target
- [x] Disabled-target execution guard
- [x] Run history list and detail endpoints
- [x] Action history endpoint
- [x] Action acknowledgement and resolution endpoints
- [x] Markdown report retrieval endpoint
- [x] OpenAPI contract tests
- [x] Explicit startup workspace configuration
- [x] Windows operator API launch command

## M3 — Recurring execution

### M3.1 — Schedule configuration

- [x] Persisted interval schedule definitions
- [x] One immutable target link per schedule
- [x] Timezone-aware start time normalized to UTC
- [x] Interval bounded from 5 minutes to 7 days
- [x] Schedule list, detail, create, and update API
- [x] Configuration-only safety proof with no collector invocation

### M3.2 — Due evaluation, claims, controlled execution, and visibility

- [x] Deterministic occurrence calculation
- [x] Idempotent execution keys
- [x] Atomic occurrence claims
- [x] Restart-safe occurrence records
- [x] Disabled schedule and target guards
- [x] Occurrence list, detail, and evaluation API
- [x] Claim-only safety proof with no collector invocation
- [x] Explicit single-occurrence execution endpoint
- [x] Permanent at-most-once execution markers
- [x] Completed and partial run linkage
- [x] Failed collector evidence retained on the occurrence
- [x] Restart-safe terminal-state idempotency
- [x] Bounded missed-unclaimed boundary visibility
- [x] Stale executing occurrence visibility
- [x] Explicit grace and lookback limits
- [x] Read-only attention API and persistence proof
- [ ] Explicit bounded retry policy with separate attempt evidence

### M3.3 — Windows Task Scheduler adapter

- [ ] One due-runner scheduled task
- [ ] Dry-run and verification commands
- [ ] Installation and uninstall workflow
- [ ] Rollback-safe local configuration
- [ ] Scheduled proof package

## M4 — Operator interface

### M4.1 — Read-only operator dashboard

- [x] Combined local workbench preserving the existing JSON API
- [x] Operational summary dashboard
- [x] Target inventory with latest-run state
- [x] Run history with finding counts, changes, and report links
- [x] Pending and historical action visibility with stable finding codes
- [x] Human-readable report access
- [x] Empty-state and populated-state route tests
- [x] Linux and Windows CI proof

### M4.2 — Browser proof

- [x] Deterministic public-safe sample workspace
- [x] Playwright Chromium semantic workflow tests
- [x] Browser console-error validation
- [x] CI-generated dashboard, target, run, action, and report screenshots
- [x] Browser trace retention on failure
- [x] Dedicated visual-proof artifact

### M4.3 — Scheduling views

- [x] Schedule inventory
- [x] Occurrence history
- [x] Missed-boundary attention visibility
- [x] Stale-execution attention visibility
- [x] Schedule and occurrence dashboard metrics
- [x] Playwright semantic checks and screenshots
- [ ] Change timeline

## Deferred

- n8n integration
- approved notifications
- lead/control workflows
- external system writes
- multi-user authentication
