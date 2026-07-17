# WATCH V1 readiness procedure

WATCH has completed the automated M0–M4 implementation roadmap. V1 readiness is a release-validation phase, not a new feature milestone.

## Automatically proven on every pull request

The GitHub Actions matrix verifies:

- Ruff linting and strict mypy checks;
- the complete pytest suite with coverage;
- deterministic demo generation;
- Linux verification and proof artifacts;
- the standard Windows operator workflow and review ZIP export;
- a clean Windows checkout with no pre-existing `.venv` or `.watch-data`;
- `WATCH.ps1 setup`, `verify`, `demo`, `plan`, `run-once`, and `task-plan` through the documented entry point;
- no-network empty-workspace planning and one-shot execution;
- Task Scheduler manifest generation without persistent installation;
- JSON and Markdown V1 readiness reports;
- Playwright Chromium navigation, accessibility, console, and screenshot proof.

The automated audit fails when required files or commands disappear, version metadata is missing, or an implementation-roadmap item becomes incomplete.

## Manual release blockers

CI cannot honestly complete these checks:

1. Install and verify the WATCH scheduled task on the intended Windows workstation.
2. Produce a sanitized report from an explicitly approved live public target.
3. Review the installation and first-run workflow interactively from a clean checkout.
4. Confirm the final portfolio screenshots and public repository presentation.
5. Approve and create the first stable release tag.

These items remain visible in `docs/roadmap.md` and in every generated readiness report.

## Workstation validation sequence

From a clean Windows checkout:

```powershell
.\WATCH.ps1 setup
.\WATCH.ps1 verify
.\WATCH.ps1 demo
.\WATCH.ps1 task-plan -TaskName "WATCH-DueRunner" -IntervalMinutes 15 -MaxWork 1
.\WATCH.ps1 task-install -TaskName "WATCH-DueRunner" -IntervalMinutes 15 -MaxWork 1
.\WATCH.ps1 task-verify -TaskName "WATCH-DueRunner" -IntervalMinutes 15 -MaxWork 1
```

After observing at least one scheduled invocation and its JSON evidence:

```powershell
.\WATCH.ps1 task-uninstall -TaskName "WATCH-DueRunner"
```

When an earlier same-named task was backed up and restoration is required:

```powershell
.\WATCH.ps1 task-rollback -TaskName "WATCH-DueRunner"
```

The operator must confirm that the task uses the intended current user, limited privilege, no stored password, the expected interval and paths, and `IgnoreNew` overlap prevention.

## Live-run evidence boundary

A live example requires explicit target approval. Use only a low-risk public target that the operator is authorized to check. The committed example must be reviewed for URLs, headers, error details, and any other identifying or sensitive content before publication.

No live public check is performed automatically by the V1 readiness CI job.

## Release decision

The first stable tag should be created only when:

- automated readiness reports `PASS` with no automated blockers;
- all five manual blockers are completed and checked in the roadmap;
- the clean-checkout operator experience is acceptable;
- the review ZIP and portfolio evidence are current;
- no unresolved release-blocking issue remains.

Until then, the package version remains a pre-V1 project version and the repository must not claim that a stable V1 release has been completed.
