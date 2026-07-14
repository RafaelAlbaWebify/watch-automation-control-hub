param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "verify", "demo", "export", "api", "plan", "run-once")]
    [string]$Command = "verify",

    [string]$EvaluatedAt,

    [ValidateRange(1, 10)]
    [int]$MaxWork = 1,

    [string]$Workspace,

    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

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
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
