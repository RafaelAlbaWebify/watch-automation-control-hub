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

### M1 evidence improvements

- [x] Capture normalized content type and actual body byte count
- [x] Persist only an explicit allowlist of public response headers
- [x] Bound persisted response-header values
- [x] Prove that cookies and arbitrary trace headers are excluded
- [x] Add a sanitized deterministic committed report example
- [x] Add a sanitized committed example produced by an explicitly approved live run

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

#### M3.2 retry evidence

- [x] Separate deterministic attempt identity
- [x] Dedicated attempt and attempt-lock persistence
- [x] Retry eligibility restricted to failed occurrences
- [x] Enabled schedule and target guards preserved
- [x] Required non-blank operator reason stored on every attempt
- [x] Three retry attempts numbered independently from 1 to 3
- [x] Original occurrence remains byte-for-byte unchanged
- [x] Completed, partial, and failed retry evidence retained separately
- [x] Linux and Windows service proof
- [x] Retry and attempt-history API
- [x] OpenAPI request-body and HTTP error-mapping proof
- [x] Read-only operator attempt visibility
- [x] Browser proof for attempt history

### M3.3 — One-shot runner and Windows Task Scheduler adapter

- [x] Read-only due-work planning endpoint and CLI command
- [x] Deterministic latest-boundary classification per schedule
- [x] Byte-for-byte read-only planning proof
- [x] Collector non-invocation proof
- [x] One-shot bounded runner with explicit result summary
- [x] Deterministic 1–10 maximum-work selection
- [x] Completed, partial, and failed result mapping
- [x] Repeated-invocation no-recollection proof
- [x] Machine-readable foreground CLI command
- [x] Windows dry-run and one-shot wrapper commands
- [x] Empty-workspace wrapper verification and JSON evidence
- [x] One current-user due-runner scheduled-task definition
- [x] Runtime UTC timestamp adapter
- [x] Dry-run task manifest
- [x] Install, verify, uninstall, and rollback commands
- [x] Existing-task XML backup before replacement
- [x] Limited privilege, no stored credentials, and non-overlap policy
- [x] Rollback-safe local scheduler state
- [x] Scheduler plan included in the review ZIP
- [x] Windows CI scheduler-manifest proof without persistent installation

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

### M4.4 — Change timeline

- [x] Baseline and changed-run chronology
- [x] Previous-run linkage
- [x] Changed-field visibility
- [x] Finding and action counts per run
- [x] Human-readable report links
- [x] Empty-state and populated-state tests
- [x] Playwright semantic proof and screenshot

### M4.5 — Operator navigation and drill-down

- [x] Consistent navigation to all operator pages
- [x] Target-focused detail page
- [x] Target configuration and status summary
- [x] Target schedule, run, action, and change evidence
- [x] Cross-page links into target detail
- [x] Not-found and OpenAPI-exclusion tests
- [x] Browser proof and target-detail screenshot

### M4.6 — Interface usability and accessibility

- [x] Active-page navigation state
- [x] Responsive narrow-screen table handling
- [x] Primary navigation and main-content landmarks
- [x] Keyboard-visible skip link and focus styling
- [x] Keyboard-focused Playwright proof
- [x] Apply severity and status visual hierarchy to every evidence table
- [x] Add accessible captions to every evidence table
- [x] Remove the unused duplicate change-timeline module

### M4.7 — Retry attempt visibility

- [x] Read-only attempt history page
- [x] Attempt identity, occurrence, number, reason, status, timestamps, run, and error evidence
- [x] Dashboard attempt metric
- [x] Active navigation and accessible table caption
- [x] HTML escaping for operator reasons and errors
- [x] Report links for run-backed attempts
- [x] Empty-state and OpenAPI-exclusion proof
- [x] Playwright semantic proof and attempt screenshot

## V1 readiness review

- [x] Install, verify, invoke, and remove a temporary WATCH task on a real hosted Windows runner
- [x] Produce one explicitly approved sanitized live-run example
- [x] Review installation and first-run operator experience from a clean Windows checkout
- [x] Confirm final portfolio screenshots and repository presentation through Playwright
- [ ] Tag the first stable release

The hosted Windows scheduler proof validates the complete task lifecycle in a disposable real Windows environment. Installation on any particular long-lived workstation remains an optional deployment action rather than a release blocker.

## Deferred

- n8n integration
- approved notifications
- lead/control workflows
- external system writes
- multi-user authentication
