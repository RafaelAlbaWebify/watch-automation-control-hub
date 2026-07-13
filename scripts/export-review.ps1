$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

& (Join-Path $Root "scripts\verify.ps1")
& (Join-Path $Root "scripts\run-demo.ps1")

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Downloads = Join-Path $HOME "Downloads"
if (-not (Test-Path $Downloads)) { $Downloads = $Root }

$Stage = Join-Path $env:TEMP "WATCH_REVIEW_$Timestamp"
$Zip = Join-Path $Downloads "WATCH_REVIEW_$Timestamp.zip"
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path $Stage | Out-Null

$Include = @("README.md", "pyproject.toml", "src", "tests", "samples", "docs", ".github", ".watch-data")
foreach ($Item in $Include) {
    $Source = Join-Path $Root $Item
    if (Test-Path $Source) { Copy-Item $Source -Destination $Stage -Recurse -Force }
}

[ordered]@{
    project = "WATCH"
    generated_at = (Get-Date).ToString("o")
    verification = "PASS"
    source_root = $Root
} | ConvertTo-Json | Set-Content (Join-Path $Stage "manifest.json") -Encoding UTF8

Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $Zip -Force
Remove-Item $Stage -Recurse -Force
Write-Host "WATCH export PASS" -ForegroundColor Green
Write-Host $Zip -ForegroundColor Cyan
