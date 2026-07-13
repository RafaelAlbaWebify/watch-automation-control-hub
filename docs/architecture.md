# WATCH architecture

## Product boundary

WATCH is an automation-control system. Its responsibility is workflow execution, state, change detection, action lifecycle, and evidence generation.

It is not an infrastructure diagnostic suite. Detailed DNS, port, dependency, and production-service investigation belongs to OPSCORE.

## Layers

```text
Input / configuration
  -> domain validation
  -> workflow orchestration
  -> supplied or collected observations
  -> deterministic analysis
  -> run and action storage
  -> report generation
  -> CLI / future API / future UI
```

## Current M0 modules

- `models.py`: explicit domain contracts.
- `analysis.py`: deterministic finding rules.
- `storage.py`: local JSON persistence.
- `workflow.py`: end-to-end orchestration and duplicate-action control.
- `reports.py`: Markdown and JSON output.
- `cli.py`: automated executable demo.

## M1 extension point

M1 will introduce collector interfaces. A collector produces observations but does not write reports, create actions, persist state, or decide workflow status. This keeps HTTP, TLS, metadata, and DNS collection modular and independently testable.
