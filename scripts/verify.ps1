$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "Python was not found. Run .\WATCH.ps1 setup after installing Python 3.11 or later."
    }
    $Python = $PythonCommand.Source
}

& $Python -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m mypy src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$WrapperProof = Join-Path $Root "artifacts\wrapper-proof"
$WrapperWorkspace = Join-Path $WrapperProof "workspace"
$PlanOutput = Join-Path $WrapperProof "due-plan.json"
$RunOutput = Join-Path $WrapperProof "due-run.json"
$TaskPlanOutput = Join-Path $WrapperProof "task-plan.json"
$TaskEvidence = Join-Path $WrapperProof "scheduled-evidence"
$TaskState = Join-Path $WrapperProof "scheduler-state.json"
if (Test-Path $WrapperProof) {
    Remove-Item -Recurse -Force $WrapperProof
}
New-Item -ItemType Directory -Path $WrapperProof -Force | Out-Null

& (Join-Path $Root "WATCH.ps1") plan `
    -EvaluatedAt "2026-07-14T10:20:00Z" `
    -Workspace $WrapperWorkspace `
    -OutputPath $PlanOutput | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path $PlanOutput)) {
    throw "WATCH plan wrapper did not create JSON evidence."
}
$PlanRaw = Get-Content -Raw $PlanOutput
if (-not $PlanRaw.Trim().StartsWith("[")) {
    throw "WATCH plan wrapper output is not a JSON array."
}

& (Join-Path $Root "WATCH.ps1") run-once `
    -EvaluatedAt "2026-07-14T10:20:00Z" `
    -MaxWork 1 `
    -Workspace $WrapperWorkspace `
    -OutputPath $RunOutput | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path $RunOutput)) {
    throw "WATCH run-once wrapper did not create JSON evidence."
}
$RunPayload = Get-Content -Raw $RunOutput | ConvertFrom-Json
if ($RunPayload.selected -ne 0 -or $RunPayload.max_work -ne 1) {
    throw "WATCH run-once wrapper returned an unexpected empty-workspace summary."
}

& (Join-Path $Root "WATCH.ps1") task-plan `
    -TaskName "WATCH-CI-Proof" `
    -IntervalMinutes 30 `
    -MaxWork 2 `
    -Workspace $WrapperWorkspace `
    -EvidenceDirectory $TaskEvidence `
    -StatePath $TaskState `
    -OutputPath $TaskPlanOutput | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path $TaskPlanOutput)) {
    throw "WATCH task-plan wrapper did not create JSON evidence."
}
$TaskPlan = Get-Content -Raw $TaskPlanOutput | ConvertFrom-Json
if ($TaskPlan.task_name -ne "WATCH-CI-Proof") {
    throw "WATCH task-plan did not preserve the task name."
}
if ($TaskPlan.interval_minutes -ne 30 -or $TaskPlan.max_work -ne 2) {
    throw "WATCH task-plan did not preserve interval or maximum-work limits."
}
if ($TaskPlan.stores_credentials -ne $false) {
    throw "WATCH task-plan must not store credentials."
}
if ($TaskPlan.multiple_instances -ne "IgnoreNew") {
    throw "WATCH task-plan must prevent overlapping task instances."
}
if ($TaskPlan.principal_logon_type -ne "Interactive" -or $TaskPlan.run_level -ne "Limited") {
    throw "WATCH task-plan must use the current interactive user at limited privilege."
}
if ($TaskPlan.action_arguments -notmatch "invoke-scheduled-run.ps1") {
    throw "WATCH task-plan does not invoke the scheduled one-shot adapter."
}
if ($TaskPlan.action_arguments -notmatch "-MaxWork 2") {
    throw "WATCH task-plan did not forward MaxWork."
}

Write-Host "WATCH verification PASS" -ForegroundColor Green
Write-Host "Wrapper proof: $WrapperProof" -ForegroundColor Cyan
