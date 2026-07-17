param(
    [switch]$SkipVerification
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not $SkipVerification) {
    & (Join-Path $Root "scripts\verify.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & (Join-Path $Root "scripts\run-demo.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$SchedulerProof = Join-Path $Root "artifacts\scheduler-proof"
$SchedulerPlan = Join-Path $SchedulerProof "task-plan.json"
New-Item -ItemType Directory -Path $SchedulerProof -Force | Out-Null
& (Join-Path $Root "WATCH.ps1") task-plan `
    -TaskName "WATCH-DueRunner" `
    -IntervalMinutes 15 `
    -MaxWork 1 `
    -Workspace (Join-Path $Root ".watch-data") `
    -EvidenceDirectory (Join-Path $Root "artifacts\runner") `
    -OutputPath $SchedulerPlan | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path $SchedulerPlan)) {
    throw "Scheduler proof plan was not created."
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Downloads = Join-Path $HOME "Downloads"
if (-not (Test-Path $Downloads)) { $Downloads = $Root }

$Stage = Join-Path $env:TEMP "WATCH_REVIEW_$Timestamp"
$Zip = Join-Path $Downloads "WATCH_REVIEW_$Timestamp.zip"
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path $Stage | Out-Null

$Include = @(
    "README.md",
    "WATCH.ps1",
    "pyproject.toml",
    "src",
    "tests",
    "samples",
    "scripts",
    "docs",
    ".github",
    ".watch-data",
    "artifacts\scheduler-proof"
)
foreach ($Item in $Include) {
    $Source = Join-Path $Root $Item
    if (Test-Path $Source) { Copy-Item $Source -Destination $Stage -Recurse -Force }
}

$Verification = if ($SkipVerification) { "PREVERIFIED" } else { "PASS" }
[ordered]@{
    project = "WATCH"
    generated_at = (Get-Date).ToString("o")
    verification = $Verification
    source_root = $Root
    scheduler_plan = "artifacts/scheduler-proof/task-plan.json"
    scheduler_install_performed = $false
} | ConvertTo-Json | Set-Content (Join-Path $Stage "manifest.json") -Encoding UTF8

Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $Zip -Force
Remove-Item $Stage -Recurse -Force
Write-Host "WATCH export PASS" -ForegroundColor Green
Write-Host $Zip -ForegroundColor Cyan
