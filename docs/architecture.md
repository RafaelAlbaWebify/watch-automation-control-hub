# WATCH architecture

## Product boundary

WATCH is an automation-control system. Its responsibility is workflow execution, state,
change detection, action lifecycle, and evidence generation.

It is not an infrastructure diagnostic suite. Detailed DNS, port, dependency, and
production-service investigation belongs to OPSCORE.

## Current layers

```text
Target and schedule configuration
  -> deterministic due-work planning
  -> atomic occurrence claim
  -> bounded workflow execution
  -> read-only observation collection
  -> deterministic analysis and previous-run comparison
  -> immutable run, attempt, and occurrence evidence
  -> action lifecycle and report generation
  -> local API / operator workbench / Windows Task Scheduler adapter
```

## Core responsibilities

- `models.py`: explicit domain contracts.
- `schedules.py` and `runner.py`: persisted schedules, due-boundary planning, and
  bounded latest-due execution.
- `occurrences.py`: restart-safe occurrence state and missed/stale attention evidence.
- `attempts.py`: bounded operator-controlled retry evidence without rewriting the
  original occurrence.
- `collectors/`: read-only HTTP, DNS, redirect, timing, page-title, and TLS evidence.
- `analysis.py`: deterministic findings and change interpretation.
- `workflow.py`: orchestration, previous-run comparison, persistence, and
  duplicate-action control.
- `storage.py`: local JSON persistence for operational evidence.
- `reports.py`: review-ready Markdown and JSON reports.
- `webapp.py` and web modules: local API and read-only operator workbench.
- Windows scheduler tooling: one current-user, limited-privilege scheduled task that
  invokes one bounded foreground run and exits.

## Execution safety

Planning is read-only and does not invoke collectors. Occurrences use deterministic
execution keys and atomic claims so a schedule boundary is not collected twice.
Retries are separate, bounded attempts with an operator reason and do not alter the
original occurrence evidence.

The Windows Task Scheduler adapter uses the current interactive user, limited
privilege, no stored password, and `IgnoreNew` overlap protection. Existing task XML
is retained before replacement so rollback can restore the previous task definition.

WATCH does not perform external remediation, bypass authentication, submit forms,
crawl arbitrary sites, or modify monitored systems.

## Portfolio review path

The deterministic reviewer workspace exposes one automation-control thread across the
same production-shaped layers:

```text
Schedule -> Occurrence -> Run -> Change -> Action
```

The dashboard links directly into each retained evidence view so reviewers can follow
the control loop without treating WATCH as a website-monitoring or infrastructure
diagnostic product.
