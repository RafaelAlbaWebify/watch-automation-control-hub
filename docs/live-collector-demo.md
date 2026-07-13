# Live collector demo

This scenario demonstrates the current public, read-only WATCH workflow without requiring private data or credentials.

## Prerequisites

```powershell
.\WATCH.ps1 setup
.\WATCH.ps1 verify
```

## Run

```powershell
.\.venv\Scripts\python.exe -m watch.cli collect https://example.com `
  --timeout-seconds 10 `
  --workspace .watch-data
```

## Expected behavior

WATCH should:

1. validate the URL through the target model;
2. resolve the hostname;
3. reject non-public addresses;
4. make one bounded read-only HTTP request;
5. validate and inspect each redirect destination;
6. record the final HTTP status, URL, redirect chain, and response time;
7. inspect the TLS certificate through a validated address while retaining the hostname for SNI and certificate verification;
8. save an immutable run record;
9. compare against the preceding run for the same target identifier;
10. create or reuse operational actions;
11. generate Markdown and JSON reports.

## Generated evidence

```text
.watch-data/
├── runs/<run-id>.json
├── actions/<action-id>.json
└── reports/
    ├── <run-id>.md
    └── <run-id>.json
```

## Review points

The operator should verify:

- the command prints `WATCH COLLECTION COMPLETE`;
- the run status is `completed` when all checks succeed;
- the run status is `partial` when DNS, HTTP, or TLS evidence contains an error;
- the Markdown report separates observations, changes, findings, actions, and limitations;
- repeating the same unresolved finding does not create duplicate open actions.

## Safety limitations

- This is a single-target command, not a scanner.
- WATCH does not authenticate, submit forms, crawl, or modify external systems.
- HTTP destinations are validated before each request, but the current HTTP transport still performs its own DNS resolution. Transport-level HTTP address pinning is tracked in Issue #11.
- TLS inspection is connected to an address that WATCH already validated, while the original hostname remains active for SNI and certificate verification.
