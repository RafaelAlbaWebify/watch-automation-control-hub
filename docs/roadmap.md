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
- [x] Mocked collector and safety tests
- [x] Safe single-target live CLI with bounded timeouts and redirects
- [x] Linux and Windows proof artifacts

### M1 hardening still open

- [ ] Pin the HTTP transport to the address already validated by WATCH
- [ ] Capture selected response headers and content metadata
- [ ] Add a sanitized committed example of a live-generated report

## M2 — Operator API

- [ ] FastAPI health endpoint
- [ ] Target inventory endpoints
- [ ] Workflow execution endpoint
- [ ] Run history endpoints
- [ ] Action acknowledgement and resolution endpoints
- [ ] Report retrieval endpoints
- [ ] OpenAPI contract tests

## M3 — Recurring execution

- [ ] Schedule definitions
- [ ] Windows Task Scheduler integration
- [ ] Idempotent execution keys
- [ ] Retry and timeout policy
- [ ] Missed-run visibility
- [ ] Scheduled proof package

## M4 — Operator interface

- [ ] Target inventory
- [ ] Run history
- [ ] Change timeline
- [ ] Pending actions
- [ ] Report access
- [ ] Visual audit automation

## Deferred

- n8n integration
- approved notifications
- lead/control workflows
- external system writes
- multi-user authentication
