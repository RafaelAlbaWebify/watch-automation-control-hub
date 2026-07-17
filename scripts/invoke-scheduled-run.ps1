param(
    [ValidateRange(1, 10)]
    [int]$MaxWork = 1,

    [Parameter(Mandatory = $true)]
    [string]$Workspace,

    [Parameter(Mandatory = $true)]
    [string]$EvidenceDirectory
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EvaluatedAt = [DateTimeOffset]::UtcNow.ToString("o")
$Timestamp = [DateTimeOffset]::UtcNow.ToString("yyyyMMdd-HHmmss-fff")
New-Item -ItemType Directory -Path $EvidenceDirectory -Force | Out-Null
$OutputPath = Join-Path $EvidenceDirectory "scheduled-run-$Timestamp.json"

& (Join-Path $Root "WATCH.ps1") run-once `
    -EvaluatedAt $EvaluatedAt `
    -MaxWork $MaxWork `
    -Workspace $Workspace `
    -OutputPath $OutputPath

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "WATCH scheduled invocation PASS" -ForegroundColor Green
Write-Host "Evaluation time (UTC): $EvaluatedAt" -ForegroundColor Cyan
Write-Host "Evidence: $OutputPath" -ForegroundColor Cyan
