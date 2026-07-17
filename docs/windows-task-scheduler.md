# Windows Task Scheduler operating guide

WATCH uses one current-user Windows Task Scheduler task to invoke the bounded one-shot due runner. It does not install a service, daemon, background Python process, or one task per target.

## Safety model

The registered task:

- runs as the current interactive Windows user;
- uses limited privilege;
- stores no password or credential;
- prevents overlapping instances with `IgnoreNew`;
- invokes one foreground WATCH process and exits;
- generates the evaluation timestamp at runtime in UTC;
- preserves the existing `MaxWork` limit from 1 to 10;
- writes one JSON result under the configured evidence directory;
- does not retry failed work automatically.

The default task name is `WATCH-DueRunner`. The default interval is 15 minutes, the default `MaxWork` is 1, and the default workspace is `.watch-data` below the repository root.

## 1. Inspect the task definition

Always inspect the plan before installation:

```powershell
.\WATCH.ps1 task-plan `
  -TaskName "WATCH-DueRunner" `
  -IntervalMinutes 15 `
  -MaxWork 1 `
  -Workspace ".watch-data" `
  -EvidenceDirectory "artifacts\runner" `
  -OutputPath "artifacts\scheduler-proof\task-plan.json"
```

This command is read-only. It emits the exact executable, quoted arguments, paths, principal, interval, non-overlap setting, execution limit, and credential policy.

## 2. Install or replace the task

```powershell
.\WATCH.ps1 task-install `
  -TaskName "WATCH-DueRunner" `
  -IntervalMinutes 15 `
  -MaxWork 1 `
  -Workspace ".watch-data" `
  -EvidenceDirectory "artifacts\runner"
```

If a task with the same name already exists, WATCH exports its XML before replacement. Installation state is stored by default in:

```text
.watch-data\scheduler\task-state.json
```

Previous task XML files are stored below:

```text
.watch-data\scheduler\backups\
```

Installation does not delete existing WATCH targets, schedules, occurrences, runs, actions, reports, attempts, or runner evidence.

## 3. Verify the registered task

Use the same settings used during installation:

```powershell
.\WATCH.ps1 task-verify `
  -TaskName "WATCH-DueRunner" `
  -IntervalMinutes 15 `
  -MaxWork 1 `
  -Workspace ".watch-data" `
  -EvidenceDirectory "artifacts\runner"
```

Verification compares the registered executable, arguments, working directory, non-overlap policy, and limited run level with the requested manifest. A mismatch returns a non-zero exit code.

## 4. Inspect scheduled evidence

Each trigger invokes:

```text
scripts\invoke-scheduled-run.ps1
```

That script generates the current UTC timestamp and invokes the existing bounded command:

```text
WATCH.ps1 run-once
```

Scheduled result files use this pattern:

```text
artifacts\runner\scheduled-run-YYYYMMDD-HHMMSS-fff.json
```

The normal occurrence, run, action, and report records remain in the configured WATCH workspace.

## 5. Uninstall WATCH scheduling

```powershell
.\WATCH.ps1 task-uninstall -TaskName "WATCH-DueRunner"
```

Uninstall removes the registered task but preserves scheduler state, previous-task backup XML, WATCH operational records, and runner evidence.

## 6. Roll back to a previous task

Rollback is available only when installation backed up an existing same-named task:

```powershell
.\WATCH.ps1 task-rollback -TaskName "WATCH-DueRunner"
```

Rollback removes the current task and restores the saved XML. It fails safely when no backup is available.

## CI and proof boundary

Windows CI executes `task-plan` against an isolated temporary workspace and validates the generated JSON contract. The review ZIP includes:

```text
artifacts\scheduler-proof\task-plan.json
```

CI deliberately does not leave a persistent task on the hosted runner. Real installation, verification, uninstall, and rollback must be executed on the intended Windows workstation by its operator.
