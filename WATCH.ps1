param(
    [Parameter(Position = 0)]
    [ValidateSet(
        "setup",
        "verify",
        "demo",
        "export",
        "api",
        "plan",
        "run-once",
        "task-plan",
        "task-install",
        "task-verify",
        "task-uninstall",
        "task-rollback"
    )]
    [string]$Command = "verify",

    [string]$EvaluatedAt,

    [ValidateRange(1, 10)]
    [int]$MaxWork = 1,

    [string]$Workspace,

    [string]$OutputPath,

    [string]$TaskName = "WATCH-DueRunner",

    [ValidateRange(5, 1440)]
    [int]$IntervalMinutes = 15,

    [string]$EvidenceDirectory,

    [string]$StatePath
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-TaskSchedulerAction {
    param([Parameter(Mandatory = $true)][string]$Action)
    & (Join-Path $Root "scripts\task-scheduler.ps1") `
        -Action $Action `
        -TaskName $TaskName `
        -IntervalMinutes $IntervalMinutes `
        -MaxWork $MaxWork `
        -Workspace $Workspace `
        -EvidenceDirectory $EvidenceDirectory `
        -StatePath $StatePath `
        -OutputPath $OutputPath
}

switch ($Command) {
    "setup"  { & (Join-Path $Root "scripts\setup.ps1") }
    "verify" { & (Join-Path $Root "scripts\verify.ps1") }
    "demo"   { & (Join-Path $Root "scripts\run-demo.ps1") }
    "export" { & (Join-Path $Root "scripts\export-review.ps1") }
    "api"    { & (Join-Path $Root "scripts\run-api.ps1") }
    "plan" {
        if (-not $EvaluatedAt) {
            throw "-EvaluatedAt is required for the plan command."
        }
        & (Join-Path $Root "scripts\plan-due.ps1") `
            -EvaluatedAt $EvaluatedAt `
            -Workspace $Workspace `
            -OutputPath $OutputPath
    }
    "run-once" {
        if (-not $EvaluatedAt) {
            throw "-EvaluatedAt is required for the run-once command."
        }
        & (Join-Path $Root "scripts\run-due-once.ps1") `
            -EvaluatedAt $EvaluatedAt `
            -MaxWork $MaxWork `
            -Workspace $Workspace `
            -OutputPath $OutputPath
    }
    "task-plan" { Invoke-TaskSchedulerAction -Action "plan" }
    "task-install" { Invoke-TaskSchedulerAction -Action "install" }
    "task-verify" { Invoke-TaskSchedulerAction -Action "verify" }
    "task-uninstall" { Invoke-TaskSchedulerAction -Action "uninstall" }
    "task-rollback" { Invoke-TaskSchedulerAction -Action "rollback" }
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
